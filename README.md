# AlertI - Driver Drowsiness Detection System
## Overview
AlertI is a real‑time driver drowsiness detection system built with Python, OpenCV, and MediaPipe.  It captures video from a webcam, detects facial landmarks around the eyes, computes the **Eye‑Aspect Ratio (EAR)** and, when the eyes remain closed beyond a calibrated threshold, triggers an audible **voice warning** (or alarm sound) to alert the driver.
The project showcases:
- Live video streaming with a glass‑morphism HUD overlay.
- Dynamic calibration of the baseline EAR.
- Voice‑based warnings using Windows SAPI5 (fallback to `winsound`).
- Cross‑platform‑ready code (tested on Windows 10/11, Python 3.14).
## Features
- **Real‑time eye‑state monitoring** using MediaPipe’s FaceLandmarker task.
- **Dynamic EAR threshold** that adapts after an initial calibration step.
- **Voice warning** ("Driver drowsy!") plus an optional beeping alarm.
- Simple **CLI** (`python main.py`) with hot‑keys:
  - `q`/`ESC` – quit
  - `r` – recalibrate baseline EAR
- Clean, glass‑styled HUD displaying EAR, status, and a flashing alert when drowsy.
## Prerequisites
- Windows 10 or newer (tested on Windows 11)
- Python **3.14** (any 3.x version should work, but the patch for MediaPipe C‑bindings is required for 3.14 on Windows)
- A webcam (built‑in or external)
## Installation
```bash
# Clone the repository (or copy the project folder)
git clone https://github.com/yourusername/AlertI.git
cd AlertI
# Create a virtual environment
python -m venv .venv
.\.venv\Scripts\activate
# Upgrade pip and install requirements
pip install --upgrade pip
pip install -r requirements.txt
```
### MediaPipe Windows Patch (Python 3.14 only)
The MediaPipe binary for Python 3.14 on Windows does not expose the `free` function, causing:
```
AttributeError: function 'free' not found
```
A small patch has been applied automatically in
`mediapipe/tasks/python/core/mediapipe_c_bindings.py` to fall back to `msvcrt.free`. No further action is required.
## Usage
```bash
# Activate the virtual environment if not already active
.\.venv\Scripts\activate
# Run the application
python main.py
```
The program will start the webcam, calibrate the baseline EAR (shown in the console), and then begin monitoring. Press:
- **`r`** – Re‑calibrate the baseline EAR when needed.
- **`q`** or **`ESC`** – Exit the program.
### Voice Warning
If the driver’s eyes stay closed longer than the dynamic threshold, the system will:
1. Play a short beep (via `winsound`).
2. Speak "Driver drowsy!" using Windows SAPI5 TTS (requires `pywin32`).
You can disable the voice warning by editing `config.py`:
```python
ENABLE_VOICE_WARNING = False
```
## Project Structure
```
AlertI/
├─ .venv/                # Virtual environment (not version‑controlled)
├─ config.py             # Global constants (EAR thresholds, landmark indices, etc.)
├─ alarm_manager.py      # Handles beep sound and voice TTS warnings
├─ drowsiness_detector.py# Core detection logic using MediaPipe FaceLandmarker
├─ hud.py                # Glass‑morphism HUD overlay drawn with OpenCV
├─ main.py               # Entry point – video capture and event loop
├─ requirements.txt      # Python dependencies
└─ README.md             # This file
```
## Acknowledgements
- **MediaPipe** – for the high‑performance facial landmark model.
- **OpenCV** – for video capture and drawing utilities.
- **SciPy** – for the `euclidean` distance used in EAR calculation.
- **pywin32** – for Windows COM‑based text‑to‑speech.
- Inspiration from various open‑source driver‑drowsiness demos.
