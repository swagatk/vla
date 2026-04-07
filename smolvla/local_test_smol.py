import cv2
import requests
import time
import sys

# CONFIGURATION
URL = "http://127.0.0.1:8000/control" 
INSTRUCTION = "move forward, turn left or right to avoid obstacles, or stop if too close"

def main():
    print("DEBUG: Script starting...")
    
    # Initialize webcam
    camera_index = 0 
    cap = cv2.VideoCapture(camera_index) 
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)

    if not cap.isOpened():
        print(f"ERROR: Could not open webcam {camera_index}.")
        return

    print(f"DEBUG: Camera opened! Connecting to SmolVLA Server at {URL}...")
    print("DEBUG: Press 'q' in the video window to quit.")

    while True:
        ret, frame = cap.read()
        if not ret: 
            print("ERROR: Failed to read frame from camera.")
            break

        cv2.imshow('Robot View (Laptop Webcam)', frame)

        # Encode image to JPEG
        _, img_encoded = cv2.imencode('.jpg', frame)
        
        try:
            t0 = time.time()
            # Send the image and instruction to the server
            response = requests.post(
                URL,
                files={"file": img_encoded.tobytes()},
                params={"instruction": INSTRUCTION}
            )
            latency = time.time() - t0
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for errors from server
                if "error" in data:
                    sys.stdout.write(f"\r⏱️ {latency:.2f}s | ⚠️ Server Error: {data['error'][:30]}...")
                    sys.stdout.flush()
                    continue

                # The server returns 'linear' and 'angular' values, not an explicit action ID
                linear = data.get("linear", 0.0)
                angular = data.get("angular", 0.0)
                
                # Map the continuous predictions to discrete action IDs
                if angular > 0.01:
                    action_id = 1
                    action_str = "Turn Left"
                elif angular < -0.01:
                    action_id = 2
                    action_str = "Turn Right"
                elif linear > 0.01:
                    action_id = 0
                    action_str = "Move Forward"
                else:
                    action_id = 3
                    action_str = "Stop"
                
                sys.stdout.write(f"\r⏱️ {latency:.2f}s | 🤖 Action ID: {action_id} ({action_str:<15}) [Lin: {linear:.2f}, Ang: {angular:.2f}]   ")
                sys.stdout.flush()
            else:
                print(f"\nServer Error: {response.status_code}")

        except Exception as e:
            print(f"\nConnection Error: {e}")
            time.sleep(1)

        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    print("\nDEBUG: Script finished.")

if __name__ == "__main__":
    main()
