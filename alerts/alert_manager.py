import time
import os
import logging
import platform
import threading
import smtplib
import ssl
import cv2
from email.message import EmailMessage

from config.config import settings
from pipeline import shared_state


# =========================
# LOG DIRECTORY
# =========================
os.makedirs("logs", exist_ok=True)
os.makedirs("logs/snapshots", exist_ok=True)


# =========================
# LOGGING CONFIG
# =========================
logger = logging.getLogger("alert_logger")

if not logger.handlers:

    handler = logging.FileHandler("logs/alerts.log")
    formatter = logging.Formatter("%(asctime)s - %(message)s")

    handler.setFormatter(formatter)

    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


# =========================
# ALERT STATE
# =========================
last_alert_time = 0
last_alert_type = None


# =========================
# SOUND ALERT (NON-BLOCKING)
# =========================
def play_sound():

    if platform.system() != "Windows":
        return

    try:
        import winsound

        # run sound in separate thread to avoid blocking detection loop
        threading.Thread(
            target=lambda: winsound.Beep(2000, 500),
            daemon=True
        ).start()

    except Exception:
        pass


# =========================
# EMAIL ALERT (NON-BLOCKING)
# =========================
def send_email_alert(alert_type, score, timestamp):

    # Fast fail if disabled or unconfigured
    if not hasattr(settings, 'ENABLE_EMAIL_ALERTS') or not settings.ENABLE_EMAIL_ALERTS:
        return
    if "your_email" in settings.SMTP_USERNAME:
        logger.warning("Email alerts enabled but credentials not configured in settings.")
        return

    def email_worker():
        try:
            # Safely extract all required information
            with shared_state.state_lock:
                frame = shared_state.latest_raw_frame.copy() if shared_state.latest_raw_frame is not None else None
                people_metadata = list(shared_state.latest_people_boxes)
                weapon_boxes = list(shared_state.latest_weapon_boxes)
                people_count = shared_state.people_count
                weapon = shared_state.weapon_detected
                trend = shared_state.latest_trend

            # Proceed only if we have a frame
            if frame is None:
                logger.warning("Skipped email alert: No raw frame available.")
                return

            # Draw custom boxes for the alert snapshot
            # People: Green (Normal) or Red (Anomalous)
            # Weapons: Blue
            for box, is_anomalous, pid in people_metadata:
                x1, y1, x2, y2 = map(int, box)
                color = (0, 0, 255) if is_anomalous else (0, 255, 0) # Red if anomalous, else Green
                label = f"ANOMALY ID:{pid}" if is_anomalous else f"ID:{pid}"
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            for box, w_score in weapon_boxes:
                x1, y1, x2, y2 = map(int, box)
                color = (255, 0, 0) # Blue for weapons (as requested)
                cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                cv2.putText(frame, "WEAPON", (x1, y2 + 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)

            # Construct message
            msg = EmailMessage()
            msg["Subject"] = f"🚨 URGENT: {alert_type}"
            msg["From"] = settings.ALERT_EMAIL_SENDER
            msg["To"] = ", ".join(settings.ALERT_EMAIL_RECIPIENT) if isinstance(settings.ALERT_EMAIL_RECIPIENT, list) else settings.ALERT_EMAIL_RECIPIENT

            body = (
                f"🚨 {alert_type} DETECTED 🚨\n\n"
                f"Time: {timestamp}\n"
                f"Camera: {shared_state.active_source}\n\n"
                f"SECURITY METRICS:\n"
                f" - Risk Score: {score:.2f} ({(score*100):.0f}%)\n"
                f" - Crowd Size: {people_count} individuals\n"
                f" - Weapon Found: {'YES' if weapon else 'NO'}\n"
                f" - Escalation Trend: {trend:+.3f}\n\n"
                f"Visual evidence is attached."
            )
            msg.set_content(body)

            # Encode frame to JPEG
            ret, buffer = cv2.imencode('.jpg', frame)
            if ret:
                msg.add_attachment(buffer.tobytes(), maintype='image', subtype='jpeg', filename='alert_frame.jpg')
                
                # Save locally to logs/snapshots
                snapshot_filename = f"snapshot_{timestamp.replace(' ', '_').replace(':', '-')}.jpg"
                snapshot_path = os.path.join("logs/snapshots", snapshot_filename)
                cv2.imwrite(snapshot_path, frame)
                logger.info(f"Snapshot saved locally: {snapshot_path}")

            # Send via SMTP
            logger.info("Sending email alert via SMTP...")
            context = ssl.create_default_context()
            
            # Use SMTP_SSL for port 465, or STARTTLS for port 587
            if settings.SMTP_PORT == 465:
                with smtplib.SMTP_SSL(settings.SMTP_SERVER, settings.SMTP_PORT, context=context) as server:
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
                    server.starttls(context=context)
                    server.login(settings.SMTP_USERNAME, settings.SMTP_PASSWORD)
                    server.send_message(msg)

            logger.info(f"Email alert sent successfully to {settings.ALERT_EMAIL_RECIPIENT}.")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    # Launch worker thread
    threading.Thread(target=email_worker, daemon=True).start()


# =========================
# ALERT FUNCTION
# =========================
def trigger_alert(alert_type, score=None):

    global last_alert_time, last_alert_type

    now = time.time()

    # =========================
    # COOLDOWN PROTECTION
    # =========================
    if now - last_alert_time < settings.ALERT_COOLDOWN:
        return

    # =========================
    # DUPLICATE ALERT PROTECTION
    # =========================
    if alert_type == last_alert_type and now - last_alert_time < 10:
        return

    last_alert_time = now
    last_alert_type = alert_type

    message = f"ALERT: {alert_type}"

    if score is not None:
        message += f" | score={score:.2f}"

    message += f" | time={time.strftime('%H:%M:%S')}"

    print(message)

    # =========================
    # SAFE LOGGING
    # =========================
    try:
        logger.info(message)
    except Exception:
        pass

    # =========================
    # UPDATE SHARED STATE
    # =========================
    try:

        with shared_state.state_lock:

            shared_state.latest_alert = message
            shared_state.alert_history.append(message)

    except Exception:
        pass

    # =========================
    # SOUND ALERT
    # =========================
    play_sound()

    # =========================
    # EMAIL ALERT
    # =========================
    timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
    send_email_alert(alert_type, score if score is not None else 0.0, timestamp)
