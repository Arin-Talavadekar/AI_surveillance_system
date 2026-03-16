import sys
import os
import cv2
import numpy as np

# Ensure root directory is in path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline import shared_state
from alerts.alert_manager import trigger_alert

def main():
    print("--- Simulating Email Alert ---")
    
    # 1. Provide a dummy frame to shared state
    # Create a simple red 480x360 image to simulate visual evidence
    dummy_frame = np.zeros((360, 480, 3), dtype=np.uint8)
    dummy_frame[:] = (0, 0, 255) # Red background
    cv2.putText(dummy_frame, 'SIMULATED RIOT FRAME', (50, 180), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
    
    with shared_state.state_lock:
        shared_state.latest_raw_frame = dummy_frame
        shared_state.people_count = 15
        shared_state.weapon_detected = True
        shared_state.latest_trend = 0.125
        
    # 2. Trigger the alert
    # This should internally invoke send_email_alert on a background thread
    print("Triggering alert in 3 seconds...")
    import time
    time.sleep(3)
    
    trigger_alert("FIX VERIFICATION ALERT", score=0.99)
    
    print("Alert triggered. Please check console for SMTP logging and your inbox for the email.")
    print("Waiting 10 seconds for background email thread to finish...")
    time.sleep(10)
    print("Done.")

if __name__ == "__main__":
    main()
