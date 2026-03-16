import cv2
import queue
import threading
import time
import numpy as np
from collections import deque
import logging

from config.config import settings
from models.people_detector import detect_people
from models.weapon_detector import detect_weapon
from models.feature_extractor import extract_feature
from models.anomaly_model import predict_anomaly
from models.risk_model import predict_risk
from alerts.alert_manager import trigger_alert
from pipeline import shared_state


# =========================
# LOGGING
# =========================
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# =========================
# QUEUES
# =========================
frame_queue = queue.Queue(maxsize=settings.FRAME_QUEUE_SIZE)
behavior_queue = queue.Queue(maxsize=settings.BEHAVIOR_QUEUE_SIZE)


# =========================
# ENGINE SHUTDOWN FLAG
# =========================
shutdown_event = threading.Event()


# =========================
# GLOBAL STATE
# =========================
frame_count = 0
frame_count_lock = threading.Lock()  # Synchronize frame_count access

weapon_boxes = []
weapon_seen_frames = 0
weapon_confidence_history = deque(maxlen=5)  # Temporal smoothing for weapon detection

# Logging throttle (only log once per second, not every frame)
last_log_time = time.time()
LOG_INTERVAL = 1.0  # Log every 1 second

feature_buffer = deque(maxlen=settings.SEQUENCE_LENGTH)
trajectory_history = {}
trajectory_cleanup_counter = 0  # Track for periodic cleanup


# =========================
# CAMERA SOURCE
# =========================
cap = None
camera_initialized = False

try:
    if settings.VIDEO_SOURCE:
        cap = cv2.VideoCapture(settings.VIDEO_SOURCE)
        source_info = settings.VIDEO_SOURCE
    else:
        cap = cv2.VideoCapture(settings.CAMERA_INDEX)
        source_info = f"Camera {settings.CAMERA_INDEX}"

    if not cap.isOpened():
        logger.error(f"Failed to open camera/video source: {source_info}")
        cap = None
    else:
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
        camera_initialized = True
        logger.info(f"Camera/video source initialized: {source_info}")

except Exception as e:
    logger.error(f"Error initializing camera: {e}")
    cap = None


# =========================
# TRAJECTORY INSTABILITY
# =========================
def compute_trajectory_instability():

    scores = []

    for pid, traj in trajectory_history.items():

        if len(traj) < 3:
            continue

        speeds = []

        for i in range(1, len(traj)):
            x1, y1 = traj[i - 1]
            x2, y2 = traj[i]

            dist = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
            speeds.append(dist)

        scores.append(np.std(speeds))

    if len(scores) == 0:
        return 0

    return min(np.mean(scores) / 20, 1.0)


# =========================
# CLEANUP OLD TRAJECTORIES
# =========================
def cleanup_old_trajectories(current_ids):
    """Remove tracking history for people no longer detected."""
    
    global trajectory_history
    
    stale_ids = [pid for pid in list(trajectory_history.keys()) if pid not in current_ids]
    
    for pid in stale_ids:
        del trajectory_history[pid]


# =========================
# TOP ACTOR SELECTION
# =========================
def select_top_people(boxes, ids, frame, max_people):

    h, w = frame.shape[:2]
    cx_frame = w // 2
    cy_frame = h // 2

    scored = []

    for box, pid in zip(boxes, ids):

        x1, y1, x2, y2 = map(int, box)

        area = (x2 - x1) * (y2 - y1)

        cx = (x1 + x2) // 2
        cy = (y1 + y2) // 2

        dist = np.sqrt((cx - cx_frame) ** 2 + (cy - cy_frame) ** 2)

        score = area - 0.3 * dist

        scored.append((score, (x1, y1, x2, y2), pid))

    scored.sort(reverse=True)

    selected = scored[:max_people]

    boxes_out = [x[1] for x in selected]
    ids_out = [x[2] for x in selected]

    return boxes_out, ids_out


# =========================
# CAMERA THREAD
# =========================
def camera_reader():

    if not camera_initialized or cap is None:
        logger.error("Camera not initialized, cannot read frames")
        return

    while not shutdown_event.is_set():

        try:
            ret, frame = cap.read()

            if not ret:
                if settings.VIDEO_SOURCE:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                    logger.debug("Video restarted from beginning")
                    continue
                else:
                    logger.error("Failed to read frame from camera")
                    continue

            # Validate frame
            if frame is None or frame.size == 0:
                logger.warning("Empty or corrupted frame received")
                continue

            try:
                frame_queue.put(frame, timeout=0.1)
            except queue.Full:
                logger.debug("Frame queue full, dropping frame")
                pass

        except Exception as e:
            logger.error(f"Error in camera reader: {e}")
    
    logger.info("Camera reader shutdown")


# =========================
# DETECTION WORKER
# =========================
def detection_worker():

    global frame_count, weapon_boxes, weapon_seen_frames, trajectory_cleanup_counter, weapon_confidence_history

    fps_counter = 0
    fps_timer = time.time()
    fps = 0

    while not shutdown_event.is_set():

        try:
            frame = frame_queue.get(timeout=1)
        except queue.Empty:
            continue

        frame = cv2.resize(
            frame,
            (settings.FRAME_WIDTH, settings.FRAME_HEIGHT)
        )

        # Validate resized frame
        if frame is None or frame.size == 0:
            logger.warning("Frame resize failed or produced empty frame")
            continue

        annotated = frame.copy()

        with frame_count_lock:
            frame_count += 1
            local_frame_count = frame_count

        people_boxes = []
        people_ids = []

        # =========================
        # PERSON DETECTION
        # =========================
        if local_frame_count % settings.PERSON_INTERVAL == 0:

            results = detect_people(frame)

            if results[0].boxes is not None:

                boxes = results[0].boxes.xyxy.cpu().numpy()
                ids = results[0].boxes.id

                if ids is not None:

                    ids = ids.cpu().numpy().astype(int)

                    boxes, ids = select_top_people(
                        boxes,
                        ids,
                        frame,
                        settings.MAX_TRACKED_PEOPLE
                    )

                    for box, pid in zip(boxes, ids):

                        x1, y1, x2, y2 = box

                        people_boxes.append(box)
                        people_ids.append(pid)

                        cv2.rectangle(
                            annotated,
                            (x1, y1),
                            (x2, y2),
                            (255, 0, 0),
                            2
                        )

                        cv2.putText(
                            annotated,
                            f"ID:{pid}",
                            (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX,
                            0.6,
                            (255, 0, 0),
                            2
                        )

                        cx = (x1 + x2) // 2
                        cy = (y1 + y2) // 2

                        if pid not in trajectory_history:
                            trajectory_history[pid] = []

                        trajectory_history[pid].append((cx, cy))

                        if len(trajectory_history[pid]) > settings.TRAJECTORY_HISTORY:
                            trajectory_history[pid].pop(0)

        # =========================
        # WEAPON DETECTION
        # =========================
        if local_frame_count % settings.WEAPON_INTERVAL == 0:

            wres = detect_weapon(frame)

            weapon_boxes = []
            max_weapon_conf = 0.0

            if wres and wres[0].boxes is not None:

                boxes = wres[0].boxes.xyxy.cpu().numpy()
                scores = wres[0].boxes.conf.cpu().numpy()

                for box, score in zip(boxes, scores):

                    area = (box[2] - box[0]) * (box[3] - box[1])

                    if score >= settings.WEAPON_CONF and area > 400:
                        weapon_boxes.append(tuple(map(int, box)))
                        max_weapon_conf = max(max_weapon_conf, score)

                if len(weapon_boxes) > 0:
                    weapon_confidence_history.append(max_weapon_conf)
                else:
                    weapon_confidence_history.append(0.0)

            else:
                weapon_confidence_history.append(0.0)

        # Temporal smoothing: weapon alert if average confidence >= threshold
        avg_weapon_conf = np.mean(list(weapon_confidence_history)) if len(weapon_confidence_history) > 0 else 0.0
        weapon_signal = 1 if avg_weapon_conf >= settings.WEAPON_CONF else 0

        if weapon_signal and len(weapon_boxes) > 0:

            # Only trigger alert once per detection burst
            if len(weapon_confidence_history) > 0 and weapon_confidence_history[-1] >= settings.WEAPON_CONF:
                trigger_alert("Weapon detected", avg_weapon_conf)

            for b in weapon_boxes:

                x1, y1, x2, y2 = b

                cv2.rectangle(
                    annotated,
                    (x1, y1),
                    (x2, y2),
                    (0, 0, 255),
                    2
                )

                cv2.putText(
                    annotated,
                    f"WEAPON:{avg_weapon_conf:.2f}",
                    (x1, y1 - 10),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2
                )

        people_count = len(people_boxes)

        # =========================
        # CLEANUP TRAJECTORIES PERIODICALLY
        # =========================
        trajectory_cleanup_counter += 1
        if trajectory_cleanup_counter >= 30:  # Clean every ~30 frames
            cleanup_old_trajectories(people_ids)
            trajectory_cleanup_counter = 0

        # =========================
        # SEND TO BEHAVIOR WORKER
        # =========================
        if local_frame_count % settings.FEATURE_INTERVAL == 0:

            try:
                behavior_queue.put(
                    (frame, people_count, weapon_signal, local_frame_count),
                    timeout=0.1
                )
            except queue.Full:
                pass

        # =========================
        # STABLE FPS CALCULATION
        # =========================
        fps_counter += 1

        if fps_counter >= 20:

            now = time.time()
            fps = fps_counter / (now - fps_timer)

            fps_timer = now
            fps_counter = 0

        with shared_state.state_lock:

            risk_val = shared_state.latest_risk
            gru_val = shared_state.latest_gru

        # =========================
        # DEBUG OVERLAY
        # =========================
        if settings.SHOW_DEBUG_OVERLAY:

            cv2.putText(
                annotated,
                f"FPS:{fps:.2f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2
            )

            cv2.putText(
                annotated,
                f"People:{people_count}",
                (10, 60),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

            cv2.putText(
                annotated,
                f"Weapon:{weapon_signal}",
                (10, 85),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 0, 255),
                2
            )

            cv2.putText(
                annotated,
                f"GRU:{gru_val:.2f}",
                (10, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (255, 255, 0),
                2
            )

            cv2.putText(
                annotated,
                f"Risk:{risk_val:.2f}",
                (10, 135),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 255),
                2
            )

        with shared_state.state_lock:

            shared_state.latest_frame = annotated
            shared_state.system_fps = fps
            shared_state.people_count = people_count
            shared_state.weapon_detected = weapon_signal

    logger.info("Detection worker shutdown")


# =========================
# BEHAVIOR WORKER
# =========================
def behavior_worker():

    while not shutdown_event.is_set():

        try:
            frame, people_count, weapon_signal, frame_index = behavior_queue.get(timeout=1)
        except queue.Empty:
            continue

        small = cv2.resize(frame, (224, 224))
        emb = extract_feature(small)

        if emb is None or len(emb) != 1280:
            continue

        feature_buffer.append(emb)

        anomaly = 0.0

        # Use frame_index passed from detection worker (thread-safe)
        if (
            len(feature_buffer) >= settings.SEQUENCE_LENGTH
            and frame_index % settings.GRU_INTERVAL == 0
        ):
            anomaly = predict_anomaly(feature_buffer)

        trajectory_score = compute_trajectory_instability()

        density_score = min(
            people_count / settings.MAX_EXPECTED_PEOPLE,
            1
        )

        risk_score = predict_risk(
            anomaly,
            weapon_signal,
            density_score,
            trajectory_score
        )

        # Log only once per second to reduce verbosity
        global last_log_time
        current_time = time.time()
        if current_time - last_log_time >= LOG_INTERVAL:
            logger.info(f"GRU:{anomaly:.3f} | Risk:{risk_score:.3f} | People:{people_count} | Weapon:{weapon_signal}")
            last_log_time = current_time

        # Minimal lock section - only update AI outputs
        with shared_state.state_lock:

            shared_state.latest_gru = anomaly
            shared_state.latest_risk = risk_score

            shared_state.risk_history.append(risk_score)

            if len(shared_state.risk_history) > 10:

                recent = list(shared_state.risk_history)[-5:]
                older = list(shared_state.risk_history)[-10:-5]

                trend = np.mean(recent) - np.mean(older)

            else:
                trend = 0

            shared_state.latest_trend = trend

        if risk_score >= settings.RIOT_THRESHOLD:

            trigger_alert("RIOT DETECTED", risk_score)

        elif (
            risk_score >= settings.EARLY_WARNING_THRESHOLD
            and trend >= settings.ESCALATION_THRESHOLD
        ):

            trigger_alert("EARLY RIOT WARNING", risk_score)


# =========================
# START ENGINE
# =========================
def start_engine():

    if not camera_initialized:
        logger.error("Camera not initialized. Cannot start engine.")
        return

    threading.Thread(target=camera_reader, daemon=False).start()
    threading.Thread(target=detection_worker, daemon=False).start()
    
    # Launch multiple behavior workers to handle feature extraction in parallel
    for i in range(settings.NUM_BEHAVIOR_WORKERS):
        threading.Thread(target=behavior_worker, daemon=False, name=f"BehaviorWorker-{i}").start()

    logger.info(f"AI Engine running with {settings.NUM_BEHAVIOR_WORKERS} behavior workers")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Shutdown signal received")
        shutdown_event.set()
        time.sleep(2)  # Give threads time to exit
        if cap is not None:
            cap.release()
        logger.info("Engine shutdown complete")
