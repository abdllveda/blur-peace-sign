# Peace Sign Blur

Real-time hand gesture detection. When the webcam sees a **peace sign** (index + middle fingers extended, other fingers folded), the live preview is blurred with Gaussian blur. When the gesture disappears, the preview returns to normal immediately.

## Requirements

- Built-in or external webcam
- Python 3.11 or 3.12 (MediaPipe wheels are not yet available for Python 3.13+)
- Camera permission for your terminal or IDE (especially on macOS)

## Project structure

```
Blur/
├── main.py               # Application entry point and render loop
├── gesture_detector.py   # MediaPipe hand tracking + peace sign logic
├── camera.py             # Webcam open/read/error handling
├── requirements.txt      # Python dependencies
├── README.md             # This file
└── .gitignore
```

## Setup

### 1. Clone or open the project

```bash
cd /path/to/Blur
```

### 2. Install Python 3.11 or 3.12 (if needed)

MediaPipe requires a supported Python version. 
- **macOS**: Install via Homebrew: `brew install python@3.12`
- **Windows**: Download from [python.org](https://www.python.org/downloads/)
- **Linux**: Install via package manager, e.g., `sudo apt install python3.12 python3.12-venv`

Verify:

```bash
python3 --version  # or python --version on Windows
```

### 3. Create a virtual environment

```bash
python3 -m venv .venv  # On Windows, use: python -m venv .venv
```

### 4. Activate the virtual environment

- **macOS / Linux**:
  ```bash
  source .venv/bin/activate
  ```
- **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```

Your shell prompt should show `(.venv)`.

### 5. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Grant camera permission (If required)

- **macOS**: On first run, macOS may prompt for camera access. If not:
  1. Open **System Settings → Privacy & Security → Camera**
  2. Enable access for the app running Python (e.g. **Terminal**, **iTerm**, or **Cursor**)
- **Windows / Linux**: Usually works out of the box, but ensure your user account has permissions to access video devices (e.g., in the `video` group on Linux).

### 7. Run the application

```bash
python main.py
```

### Controls

| Key | Action        |
|-----|---------------|
| `Q` | Quit the app  |

## How it works

1. `camera.py` opens the default webcam and reads BGR frames with warmup and retry logic.
2. `gesture_detector.py` runs MediaPipe Hands on each frame and checks landmark geometry for a peace sign.
3. `main.py` blurs the full preview while the gesture is active.

## Extending with new gestures

1. Add a value to `GestureType` in `gesture_detector.py`.
2. Implement a method like `is_peace_sign()` (e.g. `is_thumbs_up()`).
3. Update `detect()` to set `active_gesture` based on priority rules.
4. Handle the new gesture in `main.py` (visual effect, labels, etc.).

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| Camera not found | Confirm no other app is exclusively locking the webcam; try changing device index in `CameraConfig`. |
| Permission denied | Enable camera access in System Settings (macOS) or check device permissions (Linux). |
| Low FPS | Lower capture resolution in `CameraConfig` or reduce `BLUR_KERNEL_SIZE` in `main.py`. |
| Gesture not detected | Ensure your hand is visible, well lit, and fingers are clearly separated. |
