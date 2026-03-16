from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import cv2
import time

from pipeline import shared_state


app = FastAPI()

# =========================
# CORS CONFIGURATION
# =========================
# Allow frontend to make requests from different origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # React/Next.js dev server
        "http://localhost:5173",      # Vite dev server
        "http://localhost:8501",      # Streamlit
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:8501",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# =========================
# VIDEO STREAM GENERATOR
# =========================
def generate_frames():

    target_delay = 0.03   # ~30 FPS browser refresh limit

    while True:

        # copy frame reference quickly (MINIMAL lock)
        with shared_state.state_lock:
            frame = shared_state.latest_frame

        if frame is None:
            time.sleep(0.02)
            continue

        # IMPORTANT: Encode OUTSIDE the lock to avoid blocking other threads
        success, buffer = cv2.imencode(".jpg", frame)

        if not success:
            continue

        frame_bytes = buffer.tobytes()

        yield (
            b'--frame\r\n'
            b'Content-Type: image/jpeg\r\n\r\n' +
            frame_bytes +
            b'\r\n'
        )

        time.sleep(target_delay)


# =========================
# VIDEO STREAM ENDPOINT
# =========================
@app.get("/video_stream")
def video_stream():

    return StreamingResponse(
        generate_frames(),
        media_type="multipart/x-mixed-replace; boundary=frame"
    )


# =========================
# SYSTEM STATUS
# =========================
@app.get("/system_status")
def system_status():

    with shared_state.state_lock:

        return {
            "system": "running",
            "fps": float(shared_state.system_fps),
            "people_count": int(shared_state.people_count),
            "weapon_detected": bool(shared_state.weapon_detected),
            "gru_score": float(shared_state.latest_gru),
            "risk_score": float(shared_state.latest_risk),
            "risk_trend": float(shared_state.latest_trend),
            "latest_alert": shared_state.latest_alert
        }


# =========================
# ALERT HISTORY
# =========================
@app.get("/alerts")
def alerts():

    # Hold lock while converting deque to list
    with shared_state.state_lock:
        alert_list = list(shared_state.alert_history)

    return {
        "alerts": alert_list
    }


# =========================
# RISK HISTORY
# =========================
@app.get("/risk_history")
def risk_history():

    # Hold lock while converting deque to list
    with shared_state.state_lock:
        risk_list = list(shared_state.risk_history)

    return {
        "risk_history": risk_list
    }


# =========================
# HEALTH CHECK
# =========================
@app.get("/health")
def health():

    return {"status": "ok"}
