import time
import cv2
import requests
import numpy as np
from picamera2 import Picamera2

# --- CONFIGURATION ---
SERVER_URL = "http://192.168.0.204:8000/control"  # <--- REPLACE WITH LAPTOP IP
INSTRUCTION = "reach forward"
SENSITIVITY = 100.0   

# Action Thresholds
TURN_THRESHOLD = 0.20   
MOVE_THRESHOLD = 0.15   

# --- ROBOT CONTROL FUNCTIONS ---
def move_forward():
    print("🚗 ACTION: [0] FORWARD")
    # -> Insert your robot.forward() code here

def turn_right():
    print("↪️ ACTION: [1] TURN RIGHT")
    # -> Insert your robot.turn_right() code here

def turn_left():
    print("↩️ ACTION: [2] TURN LEFT")
    # -> Insert your robot.turn_left() code here

def stop_robot():
    print("🛑 ACTION: STOP")
    # -> Insert your robot.stop() code here

# --- LOGIC ---
def execute_command(linear, angular):
    # Prioritize turning to avoid obstacles
    if angular > TURN_THRESHOLD:
        turn_right()
    elif angular < -TURN_THRESHOLD:
        turn_left()
    elif linear > MOVE_THRESHOLD:
        move_forward()
    else:
        stop_robot()

# Smoothing filters
history_lin, history_ang = [0.0]*3, [0.0]*3
def get_smooth_action(n_lin, n_ang):
    history_lin.pop(0); history_lin.append(n_lin)
    history_ang.pop(0); history_ang.append(n_ang)
    return sum(history_lin)/3, sum(history_ang)/3

def main():
    print("Initializing Picamera2...")
    picam2 = Picamera2()
    # BGR888 is required for OpenCV compatibility
    # Change this line:
    config = picam2.create_video_configuration(main={"size": (320, 240), "format": "BGR888"})
    picam2.configure(config)
    picam2.start()
    
    print(f"✅ Connected to {SERVER_URL}")
    time.sleep(2)

    try:
        while True:
            frame = picam2.capture_array()
            _, img_encoded = cv2.imencode('.jpg', frame)
            
            try:
                response = requests.post(
                    SERVER_URL, files={"file": img_encoded.tobytes()},
                    params={"instruction": INSTRUCTION}, timeout=2.0 
                )
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Boost forward signal slightly to bias towards driving
                    smooth_lin, smooth_ang = get_smooth_action(
                        data["linear"] * SENSITIVITY * 1.2, 
                        data["angular"] * SENSITIVITY
                    )
                    
                    execute_command(smooth_lin, smooth_ang)
            except Exception as e:
                print(f"⚠️ Network Error: {e}")
                stop_robot()

    except KeyboardInterrupt:
        print("\nStopping...")
    finally:
        picam2.stop()
        stop_robot()

if __name__ == "__main__":
    main()
