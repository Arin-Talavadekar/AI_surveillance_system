import threading
import time
import uvicorn
import sys
import os

from pipeline.async_engine import start_engine, shutdown_event


# =========================
# START AI ENGINE
# =========================
def run_ai():

    try:
        print("[SYSTEM] Starting AI Engine...")
        start_engine()

    except Exception as e:
        print("[ERROR] AI ENGINE CRASHED:", e)
    finally:
        shutdown_event.set()


# =========================
# START FASTAPI SERVER
# =========================
def run_api():

    print("[SYSTEM] Starting FastAPI server...")

    try:
        server = uvicorn.Server(
            uvicorn.Config(
                "api.fastapi_server:app",
                host="0.0.0.0",
                port=8000,
                reload=False,
                log_level="info",
                access_log=False
            )
        )
        
        # Run until shutdown_event is set
        server.run()
        
    except Exception as e:
        print(f"[ERROR] API SERVER ERROR: {e}")
    finally:
        shutdown_event.set()


# =========================
# MAIN ENTRY
# =========================
if __name__ == "__main__":

    print("\n=== AI Surveillance System Boot ===\n")

    # start AI engine thread
    ai_thread = threading.Thread(
        target=run_ai,
        daemon=False
    )
    ai_thread.start()

    # allow camera + models to initialize
    time.sleep(2)

    # start API server thread
    api_thread = threading.Thread(
        target=run_api,
        daemon=False
    )
    api_thread.start()

    # main loop - wait for CTRL+C or shutdown signal
    try:
        while not shutdown_event.is_set():
            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\n[SYSTEM] Shutdown signal received (CTRL+C)")
        shutdown_event.set()
        
    print("[SYSTEM] Waiting for threads to finish...")
    
    # Wait for threads to finish with timeout
    ai_thread.join(timeout=3)
    api_thread.join(timeout=3)
    
    print("[SYSTEM] System shutdown complete.")
    # Force exit to ensure no ghost threads remain
    os._exit(0)