# OpenVLA Mobile Robot Control: Step-by-Step Guide

This guide details how to control a Raspberry Pi-based mobile robot using the 7-Billion parameter OpenVLA Vision-Language-Action model.

Since the model is too large to run on the Raspberry Pi, we use a Client-Server Architecture:
* **Server (Laptop)**: Alienware Ubuntu 24.04 laptop with an RTX 4090 (16GB VRAM). Runs the AI and an API.
* **Client (Pi)**: Raspberry Pi OS (Bookworm). Captures images via Picamera2, sends them to the laptop, and drives the motors based on discrete commands.

## Part 1: Server Setup (Ubuntu 24.04 Laptop)

### 1. Prerequisites
Ensure you have the proprietary NVIDIA drivers installed (check by running nvidia-smi in the terminal).

Install Miniconda (or Conda) to manage your Python environment without conflicting with Ubuntu 24.04's strict system Python:
```
mkdir -p ~/miniconda3
wget [https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh](https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh) -O ~/miniconda3/miniconda.sh
bash ~/miniconda3/miniconda.sh -b -u -p ~/miniconda3
rm -rf ~/miniconda3/miniconda.sh
~/miniconda3/bin/conda init bash
source ~/.bashrc
```
### 2. Create the Environment & Install Dependencies

Create a clean Python 3.10 environment:
```
conda create -n openvla python=3.10 -y
conda activate openvla
```
Install PyTorch and the required libraries. Note the specific `timm` version—OpenVLA will crash with newer 1.x versions.
```
# Install PyTorch (CUDA 12.1)
pip install torch torchvision torchaudio --index-url [https://download.pytorch.org/whl/cu121](https://download.pytorch.org/whl/cu121)

# Install Server & AI tools
pip install transformers accelerate bitsandbytes fastapi uvicorn python-multipart protobuf sentencepiece pillow scipy opencv-python requests

# CRITICAL: Install compatible version of TIMM
pip install "timm==0.9.16"
```
(Optional) Install Flash Attention for better performance:
```
pip install flash_attn-2.8.3+cu12torch2.5cxx11abiFALSE-cp310-cp310-linux_x86_64.whl
```
### 3. The Server Script (server.py)

Create a file named server.py on your laptop. We use 8-bit quantization to fit the model safely within your 16GB VRAM. See the file `server.py` in this folder.

## Part 2: Local Testing (Optional but Recommended)

Before deploying to the Raspberry Pi, you can verify that the AI and server are working correctly by using your laptop's local webcam. This isolates network and Pi hardware issues from AI issues.

### 1. The Local Test Script (local_test.py)

Create a file named local_test.py on your laptop in the same directory as your server script: `local_test.py`

### 2. Running the Local Test

Open a terminal, activate your environment and run the server: 
```
conda activate openvla
python server.py
```

Open a second terminal, activate your environment, and run: 
```
conda activate openvla
python local_test.py
```

A video window will open showing your webcam feed. Wave your hand in front of the camera to act as an obstacle and watch the raw linear and angular outputs update in real-time in the terminal!



## Part 3: Client Setup (Raspberry Pi)

### 1. Install Dependencies & Fix NumPy Conflict

Raspberry Pi OS Bookworm natively supports picamera2. However, modern virtual environments often pull numpy 2.x, which breaks picamera2 binaries.On your Raspberry Pi:
```
# Create and activate a virtual environment (if you use one)
python -m venv openvla_env --system-site-packages
source openvla_env/bin/activate

# Install requests and OpenCV
pip install requests opencv-python

# CRITICAL: Downgrade NumPy to 1.x to maintain compatibility with picamera2
pip uninstall numpy -y
pip install "numpy<2.0"

# you might need to downgrade opencv to work with numpy 1.x
pip install "opencv-python<4.10"

# Make sure the picamera is already installed
sudo apt install python3-picamera2
```

### 2. The Client Script (pi_robot.py)

Create this script on your Pi. It converts the AI's continuous outputs into Discrete Actions (Forward, Left, Right, Stop). See the file `pi_robot.py` in the same folder.

## Part 4: Running the System
1. Find your Laptop's IP: Open a terminal on your laptop and type: `hostname -I`. Note the IP address (e.g., 192.168.1.50). 
2. Update the Pi Script: Open `pi_robot.py` on the Raspberry Pi and change SERVER_URL to match the laptop's IP.
3. Start the Server:On the Laptop:
```
conda activate openvla
python server.py
```
Wait until it says "Uvicorn running on http://0.0.0.0:8000"

4. Start the Robot:On the Raspberry Pi:
```
source openvla_env/bin/activate
python pi_robot.py
```
### Troubleshooting
1. **Robot turns the wrong way:** Swap the `turn_right()` and `turn_left()` function calls inside the `execute_command()` `if/elif` block.
2. **Robot stops too much:** Lower the `MOVE_THRESHOLD` from `0.15` to `0.10`.
3. **Robot jitters left/right:** Increase the `TURN_THRESHOLD` from `0.20` to `0.25`.


### Images

| Server side log | Client side log|
|--------------- | -------------|
|![server](./images/server_log.png)|![client](./images/client_log.png) |

