import cv2
import time
import os
import shutil
import secrets
from fastapi import FastAPI, UploadFile, File, Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware

from config.config import settings
from pipeline import shared_state
from pipeline.async_engine import trigger_source_switch

app = FastAPI()

# Global tracker for active views
last_view_time = 0

# Auto-pause watchdog
@app.on_event("startup")
async def startup_event():
    import threading
    def watchdog():
        while True:
            time.sleep(5)
            if shared_state.system_active and (time.time() - last_view_time > 15):
                print("[SYSTEM] Auto-pausing AI engine (no active viewers)...")
                with shared_state.state_lock:
                    shared_state.system_active = False
                # Wipe metrics immediately on auto-pause
                shared_state.reset_state()
    
    threading.Thread(target=watchdog, daemon=True).start()

# =========================
# SECURITY CONFIG
# =========================
security = HTTPBasic()

def authenticate(credentials: HTTPBasicCredentials = Depends(security)):
    is_correct_username = secrets.compare_digest(credentials.username, settings.ADMIN_USERNAME)
    is_correct_password = secrets.compare_digest(credentials.password, settings.ADMIN_PASSWORD)
    
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username

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
# Global tracker for active views
last_view_time = 0

def generate_frames():
    global last_view_time
    target_delay = 0.03   # ~30 FPS browser refresh limit

    while True:
        last_view_time = time.time() # Update activity

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
            "latest_alert": shared_state.latest_alert,
            "locations": shared_state.latest_locations
        }


# =========================
# ALERT HISTORY
# =========================
@app.get("/alerts")
def alerts():

    # Hold lock while converting deque to list
    with shared_state.state_lock:
        alert_list = list(shared_state.alert_history)

    parsed_alerts = []
    for alert_str in alert_list:
        
        alert_type = "UNKNOWN ALERT"
        alert_score = 0.0
        alert_time = ""
        
        parts = alert_str.split(" | ")
        for part in parts:
            if part.startswith("ALERT:"):
                alert_type = part.replace("ALERT:", "").strip()
            elif part.startswith("score="):
                try:
                    alert_score = float(part.split("=")[1])
                except Exception:
                    pass
            elif part.startswith("time="):
                alert_time = part.split("=")[1]
                
        parsed_alerts.append({
            "type": alert_type,
            "score": alert_score,
            "timestamp": alert_time
        })

    return {
        "alerts": parsed_alerts
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
@app.post("/switch_to_live")
def switch_to_live():
    # Calling with None forces engine to fallback to CAMERA_INDEX or VIDEO_SOURCE
    with shared_state.state_lock:
        shared_state.system_active = True
    trigger_source_switch(None)
    return {"status": "success", "message": "Switched to live feed"}


@app.post("/stop_system")
def stop_system():
    with shared_state.state_lock:
        shared_state.system_active = False
        shared_state.active_source = "None"
    # Mandatory global reset for a clean dashboard
    shared_state.reset_state()
    return {"status": "success", "message": "System stopped"}


@app.post("/upload_video")
def upload_video(file: UploadFile = File(...)):
    # Save the file temporarily
    upload_dir = "temp_uploads"
    os.makedirs(upload_dir, exist_ok=True)
    
    # Clean previous uploads to save space
    for f in os.listdir(upload_dir):
        try:
            os.remove(os.path.join(upload_dir, f))
        except Exception:
            pass
            
    file_path = os.path.join(upload_dir, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    abs_path = os.path.abspath(file_path)
    with shared_state.state_lock:
        shared_state.system_active = True
    trigger_source_switch(abs_path)
    return {"status": "success", "message": f"Switched to video {file.filename}"}


# =========================
# SECURE SNAPSHOT LOGS
# =========================
@app.get("/snapshots")
def list_snapshots(username: str = Depends(authenticate)):
    snapshot_dir = "logs/snapshots"
    if not os.path.exists(snapshot_dir):
        return {"snapshots": []}
    
    files = [f for f in os.listdir(snapshot_dir) if f.endswith(".jpg")]
    files.sort(reverse=True) # Newest first
    return {"snapshots": files}

@app.get("/snapshots/{filename}")
def get_snapshot(filename: str, username: str = Depends(authenticate)):
    file_path = os.path.join("logs/snapshots", filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Snapshot not found")
    
    return FileResponse(file_path)
