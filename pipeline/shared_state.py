import threading
from collections import deque


# =========================
# THREAD LOCK
# =========================
state_lock = threading.Lock()


# =========================
# VIDEO STREAM FRAME
# =========================
latest_frame = None
latest_raw_frame = None
active_source = "None"
system_active = False # New flag to control engine activity

# Metadata for alert drawing & radar
latest_people_boxes = []     # List of (box, is_anomalous, pid)
latest_weapon_boxes = []     # List of (box, score)
latest_locations = []        # List of {"id": int, "x": float, "y": float, "is_anomalous": bool}


# =========================
# SYSTEM METRICS
# =========================
system_fps = 0.0
people_count = 0


# =========================
# DETECTION STATUS
# =========================
weapon_detected = False


# =========================
# AI MODEL OUTPUTS
# =========================
latest_gru = 0.0          # GRU anomaly score
latest_risk = 0.0         # ML classifier risk probability
latest_trend = 0.0        # risk escalation trend


# =========================
# TEMPORAL HISTORY (THREAD-SAFE)
# =========================
# used by dashboard / analytics - ALWAYS access with lock
risk_history = deque(maxlen=100)
gru_history = deque(maxlen=100)


# =========================
# TRACKING STATE (optional future use)
# =========================
# allows tracker persistence between frames
tracked_ids = set()


# =========================
# ALERT SYSTEM (THREAD-SAFE)
def reset_state():
    """Wipes all ephemeral metrics and tracking data to return to a 'zero' state."""
    global latest_frame, latest_raw_frame, people_count, weapon_detected
    global latest_gru, latest_risk, latest_trend, latest_alert, latest_locations
    global latest_people_boxes, latest_weapon_boxes
    
    with state_lock:
        latest_people_boxes = []
        latest_weapon_boxes = []
        latest_locations = []
        people_count = 0
        weapon_detected = False
        latest_gru = 0.0
        latest_risk = 0.0
        latest_trend = 0.0
        latest_alert = None
        risk_history.clear()
        gru_history.clear()
        alert_history.clear()
        # reset frames to None or black
        latest_frame = None
        latest_raw_frame = None
# ALWAYS access alert_history with lock to prevent race conditions
latest_alert = None
alert_history = deque(maxlen=50)
