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
# =========================
# ALWAYS access alert_history with lock to prevent race conditions
latest_alert = None
alert_history = deque(maxlen=50)
