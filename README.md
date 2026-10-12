# Webcam Security Alarm

Build your own webcam motion alarm with Python and OpenCV, as shown on [DyogoCodes](https://www.youtube.com/@dyogocodes).

## Features

- Live camera feed with motion boxes and a flashing alarm border.
- Portrait 9:16 display or full landscape view.
- Automatic portrait crop that follows movement.
- Audible alert on macOS; terminal bell fallback on other systems.
- Local frame processing with no image uploads or recordings.

## Quick start

Install Python 3 and download this repository using **Code > Download ZIP**, then extract it and open a terminal in the extracted folder.

### macOS / Linux

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python webcam_security_alarm_v2.py
```

### Windows PowerShell

```powershell
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe webcam_security_alarm_v2.py
```

Keep the camera still and allow three seconds for calibration. Move in view to trigger the alarm.

## Controls

Click the camera window before using the keys.

| Key | Action |
| --- | --- |
| Q / Esc | Quit |
| P | Switch portrait / landscape |
| C | Switch cropped / full camera view |
| R | Recalibrate |

## Camera setup and troubleshooting

Edit `CAMERA_INDEX` near the top of the script. Start with `0` for the default webcam and try `1` or `2` for other connected cameras. Indices depend on the device and can change.

For an iPhone, first enable Continuity Camera on a compatible Mac and iPhone, then choose its camera index. Allow camera access for the app launching Python under macOS **System Settings > Privacy & Security > Camera**. Restart that app after changing permissions.

Close other apps using the camera if frames cannot be read. Install `opencv-python`, not the headless package, because this project opens a camera window.

Increase `MIN_MOTION_AREA` to ignore smaller movements. Press R after moving the camera or changing the scene. Lighting changes can also trigger motion.

## Scope

This is an educational motion detection demo. It does not identify people or intruders, send notifications, or run standalone on an ESP32. It is not a replacement for a dedicated security system. On Windows and Linux, the terminal bell may be muted by system settings.

## Creator

[YouTube](https://www.youtube.com/@dyogocodes) | [Instagram](https://www.instagram.com/dyogocodes) | [Linktree](https://linktr.ee/dyogocodes)
