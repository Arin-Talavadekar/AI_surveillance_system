import time
import os
import logging
import platform
import threading

from config.config import settings
from pipeline import shared_state


# =========================
# LOG DIRECTORY
# =========================
os.makedirs("logs", exist_ok=True)


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
