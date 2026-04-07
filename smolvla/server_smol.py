import torch
import uvicorn
import io
import time
from fastapi import FastAPI, UploadFile, File
from PIL import Image
from torchvision import transforms
from transformers import AutoTokenizer

# We use the native LeRobot class for loading
from lerobot.policies.smolvla.modeling_smolvla import SmolVLAPolicy
from lerobot.utils.constants import OBS_LANGUAGE_TOKENS, OBS_LANGUAGE_ATTENTION_MASK

app = FastAPI()

# THE CORRECT ID
MODEL_ID = "lerobot/smolvla_base"
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

print(f"Loading {MODEL_ID} to {'RTX 4090' if torch.cuda.is_available() else 'CPU'} using LeRobot Policy logic...")

# Load Policy and Tokenizer
model = SmolVLAPolicy.from_pretrained(MODEL_ID)
model.to(device)
model.eval()

tokenizer = AutoTokenizer.from_pretrained(model.config.vlm_model_name)

# Helper transforms for images
transform = transforms.Compose([
    transforms.Resize((256, 256)),
    transforms.ToTensor() # Converts to [0.0, 1.0] range
])

@app.post("/control")
async def control_robot(file: UploadFile = File(...), instruction: str = "reach forward"):
    try:
        t_start = time.time()
        image_data = await file.read()
        
        # Open and resize image
        image = Image.open(io.BytesIO(image_data)).convert("RGB")
        img_tensor = transform(image).unsqueeze(0).to(device) # Shape: (1, 3, 256, 256)
        
        # Create empty placeholders for missing keys that the model expects (camera2, camera3, and state)
        empty_img = torch.zeros((1, 3, 256, 256), dtype=torch.float32, device=device)
        empty_state = torch.zeros((1, 6), dtype=torch.float32, device=device)
        
        # Tokenize instruction
        encoded = tokenizer(instruction, return_tensors='pt', padding='max_length', max_length=model.config.tokenizer_max_length)
        lang_tokens = encoded['input_ids'].to(device)
        lang_masks = encoded['attention_mask'].bool().to(device) # <--- Fixed tensor type for condition check
        
        # Run inference using the structure SmolVLA expects
        with torch.inference_mode():
            action = model.select_action({
                "observation.images.camera1": img_tensor,
                "observation.images.camera2": empty_img,
                "observation.images.camera3": empty_img,
                "observation.state": empty_state,
                OBS_LANGUAGE_TOKENS: lang_tokens,
                OBS_LANGUAGE_ATTENTION_MASK: lang_masks
            })

        latency = (time.time() - t_start) * 1000
        print(f"🚀 Inference: {latency:.2f}ms | Action: {action.tolist()}")

        return {
            "linear": float(action[0][0]) if len(action.shape) > 1 else float(action[0]),
            "angular": float(action[0][1]) if len(action.shape) > 1 else float(action[1])
        }
    except Exception as e:
        print(f"Error: {e}")
        return {"error": str(e)}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)