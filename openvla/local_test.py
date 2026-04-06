# local_test.py
print("DEBUG: Script starting...") # <--- If you don't see this, the file isn't running.
import cv2
import requests
import time
import sys

# CONFIGURATION
URL = "http://127.0.0.1:8000/control" 
INSTRUCTION = "move forward, turn left or right to avoid obstacles"
def main():
    print("DEBUG: Inside main function...")
    
    # Try index 0 first. If you have an external USB cam, try 1 or 2.
    # On Ubuntu, sometimes /dev/video0 is locked.
    camera_index = 0 
    cap = cv2.VideoCapture(camera_index) 
    
    # Force a specific resolution (helps with compatibility)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"ERROR: Could not open webcam with index {camera_index}.")
        print("Tip: Try changing 'camera_index' to 1 or -1 in the code.")
        return

    print(f"DEBUG: Camera opened! Connecting to VLA Server at {URL}...")
    print("DEBUG: Press 'q' in the video window to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: 
            print("ERROR: Failed to read frame from camera.")
            break

        # Show the video feed
        cv2.imshow('Robot View (Laptop Webcam)', frame)

        # Encode image
        _, img_encoded = cv2.imencode('.jpg', frame)
        
        try:
            # Send to Server
            t0 = time.time()
            response = requests.post(
                URL,
                files={"file": img_encoded.tobytes()},
                params={"instruction": INSTRUCTION}
            )
            latency = time.time() - t0
            
            if response.status_code == 200:
                data = response.json()
                linear = data.get("linear", 0.0)
                angular = data.get("angular", 0.0)
                
                # Determine action
                if angular > 0.01:
                    action = "Turn Left"
                elif angular < -0.01:
                    action = "Turn Right"
                elif linear > 0.01:
                    action = "Move Forward"
                elif linear < -0.01:
                    action = "Move Backward"
                else:
                    action = "Stop"
                
                # Print output to terminal
                # \r overwrites the line for a cleaner look
                sys.stdout.write(f"\r⏱️ {latency:.2f}s | 🤖 Action: {action:<15} (Lin: {linear:.3f}, Ang: {angular:.3f})   ")
                sys.stdout.flush()
            else:
                print(f"\nServer Error: {response.status_code}")

        except Exception as e:
            print(f"\nConnection Error: {e}")
            time.sleep(1)

        # Press 'q' to exit
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\nDEBUG: Script finished.")

if __name__ == "__main__":
    main()