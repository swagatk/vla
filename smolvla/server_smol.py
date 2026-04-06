import torch
import uvicorn
from fastapi import FastAPI, UploadFile, File
from transformers import AutoModelForVision2Seq, AutoProcessor
from PIL import Image
import io
import time

app = FastAPI()

# SmolVLA is much smaller and faster
MODEL_ID = "lerobot/smol-vla-instruct"
device = "cuda"

print(f"Loading {MODEL_ID} to RTX 4090...")
processor = AutoProcessor.from_pretrained(MODEL_ID, trust_remote_code=True)
model = AutoModelForVision2Seq.from_pretrained(
    MODEL_ID,
    torch_dtype=torch.bfloat16,
    device_map=device,
    trust_remote_code=True
)

@app.post("/control")
async def control_robot(file: UploadFile = File(...), instruction: str = "reach forward"):
    try:
        t_start = time.time()
        image_data = await file.read()
        image = Image.open(io.BytesIO(image_data)).convert("RGB")

        # SmolVLA inference
        inputs = processor(f"In: {instruction} \nOut:", image).to(device)
        
        with torch.inference_mode():
            # SmolVLA uses the same predict_action logic
            action = model.predict_action(**inputs)

        latency = (time.time() - t_start) * 1000
        print(f"Inference: {latency:.2f}ms | Action: {action.tolist()[:2]}")

        return {
            "linear": float(action[0]),
            "angular": float(action[1])
        }
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)