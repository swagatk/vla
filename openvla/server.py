# server.py
import torch
import uvicorn
import numpy as np
from fastapi import FastAPI, UploadFile, File
from transformers import AutoModelForVision2Seq, AutoProcessor
from PIL import Image
import io
import time

# Initialize API
app = FastAPI()

# CONFIGURATION
MODEL_PATH = "openvla/openvla-7b"
device = "cuda"

print("Loading OpenVLA in 4-bit quantization...")
# Load Processor
processor = AutoProcessor.from_pretrained(MODEL_PATH, trust_remote_code=True)

# Load Model (4-bit to fit in 16GB VRAM)
model = AutoModelForVision2Seq.from_pretrained(
    MODEL_PATH,
    attn_implementation="flash_attention_2", # Change to "eager" if flash-attn not installed
    torch_dtype=torch.bfloat16,
    low_cpu_mem_usage=True,
    trust_remote_code=True,
    load_in_4bit=True 
)

@app.post("/control")
async def control_robot(file: UploadFile = File(...), instruction: str = "move forward avoiding obstacles"):
    try:
        # 1. Read Image
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # --- ADD THIS DEBUG CODE ---
        # Save every 10th image to check what the robot sees
        if int(time.time()) % 2 == 0: 
            image.save("debug_robot_view.jpg")
    # ---------------------------

        # 2. Prepare Prompt
        # We prompt the model to predict the action
        prompt = f"In: What action should the robot take to {instruction}? \nOut:"
        inputs = processor(prompt, image).to(device, dtype=torch.bfloat16)

        # 3. Inference
        with torch.inference_mode():
            action = model.predict_action(**inputs, unnorm_key="bridge_orig", do_sample=True, temperature=0.6)#, top_p=0.9, max_new_tokens=16)

        # 4. Map Arm Action to Wheels (The "Sim-to-Real" Heuristic)
        # OpenVLA Output: [x, y, z, roll, pitch, yaw, gripper]
        # x (forward/back) -> Linear Velocity
        # y (left/right)   -> Angular Velocity (Turning)
        
        # Add this DEBUG print
        print(f"RAW MODEL OUTPUT: {action.tolist()}") 

        raw_forward = float(action[0])
        raw_turn = float(action[1])
        
        return {
            "linear": raw_forward,
            "angular": raw_turn,
            "raw_action": action.tolist()
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # 0.0.0.0 allows external access from the Pi
    uvicorn.run(app, host="0.0.0.0", port=8000)