# Peace Sign Blur

Real-time hand gesture detection for macOS (Apple Silicon). When the webcam sees a **peace sign** (index + middle fingers extended, other fingers folded), the live preview is blurred with Gaussian blur. When the gesture disappears, the preview returns to normal immediately.

## Requirements

- macOS with a built-in or external webcam
- Python 3.11 or 3.12 (MediaPipe wheels are not yet available for Python 3.13+)
- Camera permission for Terminal, iTerm, or your IDE

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

## Setup (macOS)

### 1. Clone or open the project

```bash
cd /path/to/Blur
```

### 2. Install Python 3.11 or 3.12 (if needed)

MediaPipe requires a supported Python version. On Apple Silicon, install via Homebrew:

```bash
brew install python@3.12
```

Verify:

```bash
python3.12 --version
```

### 3. Create a virtual environment

```bash
python3.12 -m venv .venv
```

Use `python3.11` instead if that is what you installed.

### 4. Activate the virtual environment

```bash
source .venv/bin/activate
```

Your shell prompt should show `(.venv)`.

### 5. Install dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 6. Grant camera permission

On first run, macOS may prompt for camera access. If not:

1. Open **System Settings → Privacy & Security → Camera**
2. Enable access for the app running Python (e.g. **Terminal**, **iTerm**, or **Cursor**)

If you see a permission error in the terminal, enable the correct app and run again.

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
3. `main.py` blurs the full preview while the gesture is active and draws a status label:
   - **Peace Detected** (green)
   - **No Peace** (red)

## Extending with new gestures

1. Add a value to `GestureType` in `gesture_detector.py`.
2. Implement a method like `is_peace_sign()` (e.g. `is_thumbs_up()`).
3. Update `detect()` to set `active_gesture` based on priority rules.
4. Handle the new gesture in `main.py` (visual effect, label text, etc.).

## Troubleshooting

| Issue | What to try |
|-------|-------------|
| Camera not found | Confirm no other app is exclusively locking the webcam; try device index `1` in `CameraConfig`. |
| Permission denied | Enable camera access in System Settings for your terminal/IDE. |
| Low FPS | Lower capture resolution in `CameraConfig` or reduce `BLUR_KERNEL_SIZE` in `main.py`. |
| Gesture not detected | Ensure your hand is visible, well lit, and fingers are clearly separated. |

## License

MIT (adjust as needed for your use case).
