# SmolVLA

This document provides step-by-step instructions to set up the environment, install `lerobot`, and execute the code in this folder.

## Prerequisites
- Anaconda or Miniconda installed on your system.
- Python 3.10+ (recommended).

## Installation

1. **Create and activate a new Conda environment:**
   ```bash
   conda create -n lerobot python=3.10 -y
   conda activate lerobot
   ```

2. **Install LeRobot:**
   You can install the Hugging Face `lerobot` package directly via pip:
   ```bash
   pip install lerobot
   ```
   *(Alternatively, if you require the latest version from source, clone the [huggingface/lerobot](https://github.com/huggingface/lerobot) repository and run `pip install -e .` inside it.)*

3. **Install additional dependencies (if any):**
   Depending on the specific requirements of the scripts in this folder, you might need extra Python packages. Install them as needed:
   ```bash
   pip install requests fastapi uvicorn torch  # Example dependencies
   ```

## Execution Instructions

Ensure your conda environment is activated before running any scripts:
```bash
conda activate lerobot
```

### 1. Start the Server
If the project relies on a server-client API architecture, start the server first:
```bash
python server_smol.py
```

### 2. Run the Robot/Client Code
Run the script responsible for handling the Pi robot operations:
```bash
python pi_robot_smol.py
```

### 3. Run the Local Test
Use the local test script to verify that inference or control is working correctly:
```bash
python local_test_smol.py
```

## Notes
- Make sure the server and client are configured to communicate on the correct ports/IP addresses as defined in the respective Python scripts.
