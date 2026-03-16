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
weapon_queue = queue.Queue(maxsize=settings.FRAME_QUEUE_SIZE)
people_queue = queue.Queue(maxsize=settings.FRAME_QUEUE_SIZE)


# =========================
# ENGINE SHUTDOWN FLAG
# =========================
shutdown_event = threading.Event()
source_switch_event = threading.Event()
target_video_source = None

def trigger_source_switch(new_source=None):
    global target_video_source, active_tracks
    target_video_source = new_source
    # Immediate reset for a clean transition
    shared_state.reset_state()
    with last_people_metadata_lock:
        active_tracks.clear()
        last_people_metadata.clear()
    source_switch_event.set()

# =========================
# GLOBAL STATE
# =========================
frame_count = 0
frame_count_lock = threading.Lock()  # Synchronize frame_count access

weapon_boxes = []
weapon_boxes_lock = threading.Lock()
weapon_signal = 0
weapon_signal_lock = threading.Lock()
weapon_seen_frames = 0
weapon_confidence_history = deque(maxlen=3)  # Shortened to 3 for snappier response

# Logging throttle (only log once per second, not every frame)
last_log_time = time.time()
LOG_INTERVAL = 1.0  # Log every 1 second

feature_buffer = deque(maxlen=settings.SEQUENCE_LENGTH)
trajectory_history = {}
trajectory_lock = threading.Lock()
trajectory_cleanup_counter = 0  # Track for periodic cleanup

# Persistent boxes for rendering during skipped detection frames
last_people_metadata = []
last_people_metadata_lock = threading.Lock()
active_tracks = {} # Global tracker state for cleanup


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

    shared_state.active_source = source_info

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

    with trajectory_lock:
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
    
    with trajectory_lock:
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
    global cap, camera_initialized, frame_count, trajectory_history, weapon_confidence_history

    if not camera_initialized or cap is None:
        logger.warning("Camera not initially initialized, will wait for valid source")

    while not shutdown_event.is_set():

        if source_switch_event.is_set():
            logger.info("Source switch requested, resetting AI engine state...")
            if cap is not None:
                cap.release()
            
            with frame_count_lock:
                frame_count = 0
            
            with frame_queue.mutex:
                frame_queue.queue.clear()
            with behavior_queue.mutex:
                behavior_queue.queue.clear()
                
            with trajectory_lock:
                trajectory_history.clear()
            weapon_confidence_history.clear()
            feature_buffer.clear()
            
            with shared_state.state_lock:
                shared_state.risk_history.clear()
                shared_state.alert_history.clear()
                shared_state.latest_risk = 0.0
                shared_state.latest_gru = 0.0
                shared_state.latest_trend = 0.0
                shared_state.people_count = 0
                shared_state.weapon_detected = 0
                shared_state.latest_frame = np.zeros((settings.FRAME_HEIGHT, settings.FRAME_WIDTH, 3), dtype=np.uint8)

            try:
                if target_video_source is not None:
                    cap = cv2.VideoCapture(target_video_source)
                    source_info = f"Upload: {target_video_source}"
                else:
                    if settings.VIDEO_SOURCE:
                        cap = cv2.VideoCapture(settings.VIDEO_SOURCE)
                        source_info = settings.VIDEO_SOURCE
                    else:
                        cap = cv2.VideoCapture(settings.CAMERA_INDEX)
                        source_info = f"Camera {settings.CAMERA_INDEX}"
                
                if cap.isOpened():
                    cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings.FRAME_WIDTH)
                    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings.FRAME_HEIGHT)
                    camera_initialized = True
                    shared_state.active_source = source_info
                    logger.info(f"Switched source to: {source_info}")
                else:
                    logger.error(f"Failed to open new source: {source_info}")
                    cap = None
                    camera_initialized = False
            except Exception as e:
                logger.error(f"Error switching source: {e}")
                cap = None
                camera_initialized = False
            
            source_switch_event.clear()

        if not shared_state.system_active:
            if cap is not None:
                logger.info("System inactive, releasing camera...")
                cap.release()
                cap = None
                camera_initialized = False
            time.sleep(1.0)
            continue

        if not camera_initialized or cap is None:
            time.sleep(1.0)
            continue

        # Throttling logic for video files
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        frame_delay = 1.0 / source_fps if source_fps > 0 else 0
        read_start = time.time()

        try:
            ret, frame = cap.read()

            if not ret:
                logger.warning("Failed to read frame or end of stream")
                # Recovery / Watchdog logic
                time.sleep(1.0)
                if target_video_source is not None or settings.VIDEO_SOURCE:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, 0) # Loop video
                else:
                    # Camera lost? Try to re-init
                    logger.info("Attempting to reconnect camera...")
                    cap.release()
                    cap = cv2.VideoCapture(settings.CAMERA_INDEX)
                continue

            if frame is None or frame.size == 0:
                continue

            try:
                # Use non-blocking put to avoid slowing down reader
                frame_queue.put(frame, block=False)
            except queue.Full:
                pass

            # Precise Throttling
            if source_fps > 0:
                elapsed = time.time() - read_start
                sleep_time = frame_delay - elapsed
                if sleep_time > 0:
                    time.sleep(sleep_time)

        except Exception as e:
            logger.error(f"Critical error in camera reader: {e}")
            time.sleep(2.0)
    
    logger.info("Camera reader shutdown")


# =========================
# WEAPON WORKER
# =========================
def weapon_worker():
    global weapon_boxes, weapon_confidence_history, weapon_signal

    while not shutdown_event.is_set():
        try:
            # Drop stale frames to reduce lag
            item = None
            while not weapon_queue.empty():
                item = weapon_queue.get_nowait()
            
            if item is None:
                item = weapon_queue.get(timeout=1)
            frame = item
        except queue.Empty:
            continue

        wres = detect_weapon(frame)
        
        current_weapon_boxes = []
        max_weapon_conf = 0.0

        if wres and wres[0].boxes is not None:
            boxes = wres[0].boxes.xyxy.cpu().numpy()
            scores = wres[0].boxes.conf.cpu().numpy()

            for box, score in zip(boxes, scores):
                area = (box[2] - box[0]) * (box[3] - box[1])
                # Relaxed area threshold from 120 to 50 for distant weapon detection
                if score >= settings.WEAPON_CONF and area > 50:
                    current_weapon_boxes.append((tuple(map(int, box)), score))
                    max_weapon_conf = max(max_weapon_conf, score)

        with weapon_boxes_lock:
            weapon_boxes = current_weapon_boxes
            if len(current_weapon_boxes) > 0:
                weapon_confidence_history.append(max_weapon_conf)
            else:
                weapon_confidence_history.append(0.0)

            # ALERT LOGIC: Trigger alert only if smoothed signal is strong
            avg_weapon_conf = np.mean(list(weapon_confidence_history)) if len(weapon_confidence_history) > 0 else 0.0
            
            ALERT_THRESHOLD = 0.40 # Lowered floor from 0.50
            new_weapon_signal = 1 if avg_weapon_conf >= ALERT_THRESHOLD else 0
            
            with weapon_signal_lock:
                weapon_signal = new_weapon_signal
            
            if new_weapon_signal and len(weapon_confidence_history) >= 2:
                if weapon_confidence_history[-1] >= ALERT_THRESHOLD:
                    trigger_alert("Weapon detected", avg_weapon_conf)

    logger.info("Weapon worker shutdown")


# =========================
# PEOPLE WORKER
# =========================
def people_worker():
    global last_people_metadata, active_tracks
    
    # Lowered from 15 to 8 to minimize "ghost boxes" and stay snappier
    PERSISTENCE_THRESHOLD = 8 
    
    while not shutdown_event.is_set():
        try:
            # Drop stale frames to reduce lag - only get the LATEST frame in queue
            frame = None
            while not people_queue.empty():
                frame = people_queue.get_nowait()
            
            if frame is None:
                frame = people_queue.get(timeout=1)
        except queue.Empty:
            continue
            
        results = detect_people(frame)
        current_metadata = []
        
        # 1. Update unseen count for all existing tracks
        for pid in active_tracks:
            active_tracks[pid]['unseen_count'] += 1
            
        if results[0].boxes is not None:
            boxes = results[0].boxes.xyxy.cpu().numpy()
            ids_raw = results[0].boxes.id
            
            if ids_raw is None:
                ids = np.full(len(boxes), -1, dtype=int)
            else:
                ids = ids_raw.cpu().numpy().astype(int)

            boxes, ids = select_top_people(boxes, ids, frame, settings.MAX_TRACKED_PEOPLE)

            for box, pid in zip(boxes, ids):
                x1, y1, x2, y2 = map(int, box)
                cx, cy = (x1 + x2) // 2, (y1 + y2) // 2
                is_anomalous = False
                
                # Update trajectory and instability (same logic as before)
                if pid > -1:
                    with trajectory_lock:
                        if pid not in trajectory_history:
                            trajectory_history[pid] = []
                        trajectory_history[pid].append((cx, cy))
                        if len(trajectory_history[pid]) >= 3:
                            traj = trajectory_history[pid]
                            speeds = [np.sqrt((traj[i][0]-traj[i-1][0])**2 + (traj[i][1]-traj[i-1][1])**2) for i in range(1, len(traj))]
                            if np.std(speeds) > 15: is_anomalous = True
                        if len(trajectory_history[pid]) > settings.TRAJECTORY_HISTORY:
                            trajectory_history[pid].pop(0)
                        
                    # Refresh or Create Track
                    active_tracks[pid] = {
                        'box': box,
                        'is_anomalous': is_anomalous,
                        'unseen_count': 0
                    }
                else:
                    # Untracked person - just add to current frame only
                    current_metadata.append((box, False, -1))

        # 2. Collect persistent tracks
        final_metadata = current_metadata # start with untracked
        stale_pids = []
        
        for pid, data in active_tracks.items():
            if data['unseen_count'] <= PERSISTENCE_THRESHOLD:
                final_metadata.append((data['box'], data['is_anomalous'], pid))
            else:
                stale_pids.append(pid)
        
        # 3. Cleanup stale tracks
        for pid in stale_pids:
            del active_tracks[pid]
            
        with last_people_metadata_lock:
            last_people_metadata = final_metadata

    logger.info("People worker shutdown")


# =========================
# DETECTION WORKER
# =========================
def detection_worker():

    global frame_count, weapon_boxes, weapon_seen_frames, trajectory_cleanup_counter, weapon_confidence_history, last_people_metadata

    fps_counter = 0
    fps_timer = time.time()
    fps = 0
    
    # Timing accumulation
    total_time = 0
    det_time = 0
    draw_time = 0
    frame_process_count = 0

    while not shutdown_event.is_set():

        start_loop = time.time()
        
        try:
            frame = frame_queue.get(timeout=1)
        except queue.Empty:
            continue

        raw_frame = cv2.resize(
            frame,
            (settings.FRAME_WIDTH, settings.FRAME_HEIGHT)
        )

        # Validate resized frame
        if raw_frame is None or raw_frame.size == 0:
            logger.warning("Frame resize failed or produced empty frame")
            continue

        annotated = raw_frame.copy()

        with frame_count_lock:
            frame_count += 1
            local_frame_count = frame_count

        # =========================
        # TRIGGER ASYNC DETECTION
        # =========================
        # Person Detection
        if local_frame_count % settings.PERSON_INTERVAL == 0:
            try:
                people_queue.put(raw_frame, timeout=0.01)
            except queue.Full:
                pass
                
        # Weapon Detection
        if local_frame_count % settings.WEAPON_INTERVAL == 0:
            try:
                weapon_queue.put(raw_frame, timeout=0.01)
            except queue.Full:
                pass

        # =========================
        # DRAW BOXES (ON EVERY FRAME)
        # =========================
        t1 = time.time()
        
        # Draw People
        with last_people_metadata_lock:
            local_people = last_people_metadata.copy()
            
        current_locations = []
        for box, is_anomalous, pid in local_people:
            x1, y1, x2, y2 = map(int, box)
            
            # 1. Calculate Normalized Location (for radar)
            # We use the bottom-center of the box as the "ground" position
            feet_x = (x1 + x2) / 2
            feet_y = y2
            
            # Normalize to 0.0 - 1.0
            norm_x = feet_x / settings.FRAME_WIDTH
            norm_y = feet_y / settings.FRAME_HEIGHT
            
            current_locations.append({
                "id": int(pid),
                "x": float(np.clip(norm_x, 0.0, 1.0)),
                "y": float(np.clip(norm_y, 0.0, 1.0)),
                "is_anomalous": bool(is_anomalous)
            })

            # 2. Draw Dashboard Overlay (Clean - no IDs)
            # Use semi-transparent or thinner lines for a "professional" look
            color = (50, 50, 255) if is_anomalous else (50, 255, 50) # Softer red/green
            label = "ANOMALY" if is_anomalous else "PERSON"
            cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 1) # Thin 1px line
            
            # Subtler text box
            font_scale = 0.45
            font_thickness = 1
            cv2.putText(annotated, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, font_scale, color, font_thickness)

        # Draw Weapons
        with weapon_boxes_lock:
            local_weapon_boxes = weapon_boxes.copy()
            with weapon_signal_lock:
                local_weapon_signal = weapon_signal

        if len(local_weapon_boxes) > 0:
            for b, score in local_weapon_boxes:
                x1, y1, x2, y2 = b
                color = (255, 0, 0) # Blue for weapons
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated, "WEAPON", (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
        
        draw_time += (time.time() - t1)

        # Use persistent metadata for counts and tracking
        people_count = len(local_people)
        people_ids = [m[2] for m in local_people]

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
                    (raw_frame, people_count, local_weapon_signal, local_frame_count),
                    timeout=0.1
                )
            except queue.Full:
                pass

        # =========================
        # PROFILING AND FPS
        # =========================
        total_time += (time.time() - start_loop)
        frame_process_count += 1
        fps_counter += 1

        if fps_counter >= 30:
            now = time.time()
            fps = fps_counter / (now - fps_timer)
            
            avg_loop = (total_time / frame_process_count) * 1000
            avg_det = (det_time / (frame_process_count/settings.PERSON_INTERVAL)) * 1000 if settings.PERSON_INTERVAL > 0 else 0
            
            logger.info(f"PERF: FPS:{fps:.1f} | AvgLoop:{avg_loop:.1f}ms | AvgDet:{avg_det:.1f}ms")
            
            fps_timer = now
            fps_counter = 0
            total_time = 0
            det_time = 0
            draw_time = 0
            frame_process_count = 0

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
                f"Weapon:{local_weapon_signal}",
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
            shared_state.latest_raw_frame = raw_frame
            shared_state.system_fps = fps
            shared_state.people_count = people_count
            shared_state.weapon_detected = local_weapon_signal
            shared_state.latest_locations = current_locations
            
            with last_people_metadata_lock:
                # Store full metadata (box, is_anomalous, pid) for alert snapshots
                shared_state.latest_people_boxes = [tuple(m) for m in last_people_metadata]
            shared_state.latest_weapon_boxes = local_weapon_boxes

    logger.info("Detection worker shutdown")


# =========================
# BEHAVIOR WORKER
# =========================
def behavior_worker():
    global last_log_time
    
    # Persistent state for smoothing
    current_anomaly = 0.0
    ema_alpha = 0.3 # Smoothing factor (lower = smoother/slower)

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

        # Use frame_index passed from detection worker (thread-safe)
        if (
            len(feature_buffer) >= settings.SEQUENCE_LENGTH
            and frame_index % settings.GRU_INTERVAL == 0
        ):
            new_pred = predict_anomaly(feature_buffer)
            # Apply a safety bias (calibration) to suppress background noise
            # Subtracting a small bias and scaling up ensures we only care about high-confidence anomalies
            calibrated = (new_pred - 0.2) / 0.8
            calibrated = np.clip(calibrated, 0.0, 1.0)
            
            # Apply Exponential Moving Average (EMA) to prevent spikes
            current_anomaly = (ema_alpha * calibrated) + ((1 - ema_alpha) * current_anomaly)
            
        anomaly = current_anomaly

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

            if len(shared_state.risk_history) >= 10:
                history_list = list(shared_state.risk_history)
                recent = history_list[-5:]
                older = history_list[-10:-5]
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

    # We don't block start_engine if camera is not initialized anymore, 
    # to allow the API to set a source later if needed.

    threading.Thread(target=camera_reader, daemon=False).start()
    threading.Thread(target=detection_worker, daemon=False).start()
    threading.Thread(target=weapon_worker, daemon=False).start()
    threading.Thread(target=people_worker, daemon=False).start()
    
    # Launch multiple behavior workers to handle feature extraction in parallel
    for i in range(settings.NUM_BEHAVIOR_WORKERS):
        threading.Thread(target=behavior_worker, daemon=False, name=f"BehaviorWorker-{i}").start()

    logger.info(f"AI Engine running with WeaponWorker and {settings.NUM_BEHAVIOR_WORKERS} behavior workers")

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
