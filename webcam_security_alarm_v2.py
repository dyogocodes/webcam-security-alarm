"""DyogoCodes | Webcam Security Alarm v2

A camera-first, vertical 9:16 motion alarm demo for TikTok, Reels and Shorts.

Install: python3 -m pip install opencv-python numpy
Run:     python3 webcam_security_alarm_v2.py

Controls: Q/Esc quit, P portrait/landscape, C crop/full camera, R recalibrate.

This detects motion, NOT people or intruders specifically. Frames are processed
locally; no images are uploaded. For real security, use a dedicated system.
"""

import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np

# -------------------- Settings --------------------
CAMERA_INDEX = 0             # 0: built-in webcam; 1 or 2: often iPhone Continuity Camera
CAPTURE_WIDTH = 1920         # Requested resolution; camera may choose a lower one
CAPTURE_HEIGHT = 1080
PROCESS_WIDTH = 960          # Motion detection resolution, independent of display quality
PROCESS_HEIGHT = 540
MIN_MOTION_AREA = 2300       # In detection-space pixels; raise to ignore small motions
WARMUP_SECONDS = 3.0
ALARM_HOLD_SECONDS = 1.6
BEEP_COOLDOWN = 3.0
PORTRAIT = True              # True for recording-ready 9:16 output
FILL_CAMERA = True           # True: big cropped camera, False: show whole image
FOLLOW_MOTION = True         # Smoothly follow movement within portrait crop
MIRROR_CAMERA = False        # True for a selfie-style mirrored feed
# --------------------------------------------------

DARK = (20, 17, 14)          # BGR colors for OpenCV
PANEL = (39, 30, 28)
GREEN = (74, 238, 77)
RED = (54, 54, 246)
WHITE = (245, 245, 245)
GRAY = (175, 175, 175)
AMBER = (0, 215, 255)

OUT_W, OUT_H = 720, 1280
CAMERA_TOP = 96
CAMERA_BOTTOM = 1100       # 1004px of the 1280px height: 78% camera!
CAMERA_HEIGHT = CAMERA_BOTTOM - CAMERA_TOP
WINDOW_NAME = "DyogoCodes | Webcam Security Alarm"


def text(img, label, x, y, size=0.75, color=WHITE, thickness=2):
    cv2.putText(img, label, (int(x), int(y)), cv2.FONT_HERSHEY_SIMPLEX,
                size, color, thickness, cv2.LINE_AA)


def play_alarm():
    """Play a macOS alert without blocking the camera loop."""
    if sys.platform == "darwin":
        sound = Path("/System/Library/Sounds/Ping.aiff")
        if sound.exists():
            subprocess.Popen(["afplay", str(sound)], stdout=subprocess.DEVNULL,
                             stderr=subprocess.DEVNULL)
            return
    print("\a", end="", flush=True)


def detect_motion(frame, subtractor, learning_rate=0.003):
    """Return rectangular motion regions in PROCESS_WIDTH/HEIGHT coordinates."""
    fg = subtractor.apply(frame, learningRate=learning_rate)
    _, mask = cv2.threshold(fg, 220, 255, cv2.THRESH_BINARY)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)
    mask = cv2.dilate(mask, kernel, iterations=2)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                   cv2.CHAIN_APPROX_SIMPLE)
    return [cv2.boundingRect(c) for c in contours
            if cv2.contourArea(c) >= MIN_MOTION_AREA]


def upscale_boxes(boxes, raw_shape, processed_shape):
    """Map boxes back to the original sharp camera frame."""
    rh, rw = raw_shape[:2]
    ph, pw = processed_shape[:2]
    sx, sy = rw / pw, rh / ph
    return [(round(x*sx), round(y*sy), round(w*sx), round(h*sy))
            for x, y, w, h in boxes]


def camera_view(frame, boxes, fill, focus_x):
    """Display sharp camera pixels without changing aspect ratio.

    Returns a 720x1004 video area and the transform from source to displayed
    coordinates. Fill mode crops horizontally, with optional motion-following.
    Fit mode shows the complete image with letterboxing for comparison.
    """
    h, w = frame.shape[:2]
    area_w, area_h = OUT_W, CAMERA_HEIGHT
    scale = (max(area_w / w, area_h / h) if fill
             else min(area_w / w, area_h / h))
    rw, rh = max(1, round(w * scale)), max(1, round(h * scale))
    resized = cv2.resize(frame, (rw, rh), interpolation=cv2.INTER_CUBIC
                         if scale > 1 else cv2.INTER_AREA)
    if fill:
        dx = max(0, min(rw - area_w, round(focus_x * scale - area_w / 2)))
        dy = max(0, (rh - area_h) // 2)
        video = resized[dy:dy + area_h, dx:dx + area_w].copy()
        offset_x, offset_y = -dx, -dy
    else:
        video = np.full((area_h, area_w, 3), (9, 9, 9), dtype=np.uint8)
        dx, dy = (area_w - rw) // 2, (area_h - rh) // 2
        video[dy:dy + rh, dx:dx + rw] = resized
        offset_x, offset_y = dx, dy

    for x, y, bw, bh in boxes:
        x1 = round(x * scale + offset_x)
        y1 = round(y * scale + offset_y)
        x2 = round((x + bw) * scale + offset_x)
        y2 = round((y + bh) * scale + offset_y)
        if x2 <= 0 or x1 >= area_w or y2 <= 0 or y1 >= area_h:
            continue
        a = max(0, x1)
        b = max(0, y1)
        c = min(area_w - 1, x2)
        d = min(area_h - 1, y2)
        cv2.rectangle(video, (a, b), (c, d), GREEN, 4)
        label_y = max(56, b - 32)
        label_x = min(max(5, a), area_w - 150)
        cv2.rectangle(video, (label_x, label_y - 28),
                      (label_x + 142, label_y + 5), GREEN, -1)
        text(video, "MOTION", label_x + 10, label_y - 4,
             0.74, (0, 0, 0), 2)

    # These UI elements stay positioned in view even when crop is panning.
    video[:53] = cv2.addWeighted(video[:53], 0.3,
                                np.zeros_like(video[:53]), 0.7, 0)
    cv2.circle(video, (20, 27), 8, RED, -1)
    text(video, "CAM 01  |  LIVE", 39, 37, 0.75)
    text(video, time.strftime("%H:%M:%S"), area_w - 162, 37, 0.72)
    return video


def render_portrait(frame, boxes, alert, warming_up, flashing, focus_x):
    """Camera-first 720x1280 view, with 78% of its height devoted to video."""
    canvas = np.full((OUT_H, OUT_W, 3), DARK, dtype=np.uint8)

    # Small, clean header, not a third of the screen.
    text(canvas, "WEBCAM SECURITY ALARM", 24, 48, 0.96, WHITE, 3)
    text(canvas, "PYTHON + OPENCV    |    LIVE MOTION DETECTION",
         25, 80, 0.55, GREEN, 2)

    video = camera_view(frame, boxes, FILL_CAMERA, focus_x)
    canvas[CAMERA_TOP:CAMERA_BOTTOM, :] = video
    if alert and flashing:
        cv2.rectangle(canvas, (4, CAMERA_TOP + 3),
                      (OUT_W - 5, CAMERA_BOTTOM - 4), RED, 9)

    status = ("CALIBRATING CAMERA..." if warming_up else
              "ALARM TRIGGERED" if alert else "SYSTEM ARMED")
    color = AMBER if warming_up else RED if alert else GREEN

    # Compact status panel instead of another large card.
    cv2.rectangle(canvas, (20, 1112), (700, 1187), PANEL, -1)
    cv2.rectangle(canvas, (20, 1112), (700, 1187), color, 3)
    text(canvas, status, 37, 1162, 1.0, color, 3)

    # One-line CTA and small branding, designed for screen capture.
    text(canvas, "COMMENT 'ALARM' FOR THE CODE", 25, 1222, 0.78, GREEN, 2)
    text(canvas, "DyogoCodes  |  Q: quit  C: crop/full  P: rotate",
         25, 1258, 0.52, GRAY, 1)
    return canvas


def render_landscape(frame, boxes, alert, warming_up, flashing):
    """Full camera view with overlays at native capture resolution."""
    out = frame.copy()
    h, w = out.shape[:2]
    scale = min(w / 720, h / 480)
    bar = max(45, round(55 * scale))
    out[:bar] = cv2.addWeighted(out[:bar], 0.3,
                               np.zeros_like(out[:bar]), 0.7, 0)
    cv2.circle(out, (round(23*scale), round(26*scale)),
               round(8*scale), RED, -1)
    text(out, "CAM 01  |  LIVE", round(45*scale),
         round(37*scale), 0.78*scale)
    text(out, time.strftime("%H:%M:%S"), w - round(172*scale),
         round(37*scale), 0.72*scale)
    for x, y, bw, bh in boxes:
        cv2.rectangle(out, (x, y), (x+bw, y+bh), GREEN,
                      max(2, round(3*scale)))
    status = "CALIBRATING..." if warming_up else (
        "ALARM TRIGGERED" if alert else "SYSTEM ARMED")
    color = AMBER if warming_up else RED if alert else GREEN
    cv2.rectangle(out, (0, h - bar), (w, h), DARK, -1)
    text(out, status, round(24*scale), h - round(18*scale),
         1.0*scale, color, max(2, round(2*scale)))
    if alert and flashing:
        cv2.rectangle(out, (3, 3), (w-4, h-4), RED, max(4, round(7*scale)))
    return out


def new_subtractor():
    return cv2.createBackgroundSubtractorMOG2(
        history=240, varThreshold=45, detectShadows=True)


def main():
    global PORTRAIT, FILL_CAMERA
    cam = cv2.VideoCapture(CAMERA_INDEX)
    if not cam.isOpened():
        raise RuntimeError("Could not open webcam. Check macOS Settings > "
                           "Privacy & Security > Camera, or change CAMERA_INDEX.")

    # On supported cameras, request higher image quality for sharp close-ups.
    cam.set(cv2.CAP_PROP_FRAME_WIDTH, CAPTURE_WIDTH)
    cam.set(cv2.CAP_PROP_FRAME_HEIGHT, CAPTURE_HEIGHT)
    cam.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    print("Camera resolution: %dx%d" %
          (cam.get(cv2.CAP_PROP_FRAME_WIDTH), cam.get(cv2.CAP_PROP_FRAME_HEIGHT)))
    print("Q: quit  |  P: portrait/landscape  |  C: crop/full  |  R: recalibrate")

    subtractor = new_subtractor()
    calibrated_at = time.monotonic()
    last_motion = -1e6
    last_beep = -1e6
    consecutive_frames = 0
    focus_x = None

    try:
        while True:
            ok, frame = cam.read()
            if not ok:
                print("Could not read camera frame.")
                break
            if MIRROR_CAMERA:
                frame = cv2.flip(frame, 1)

            # Detect on a lightweight copy, display the original HD frame.
            processed = cv2.resize(frame, (PROCESS_WIDTH, PROCESS_HEIGHT),
                                   interpolation=cv2.INTER_AREA)
            now = time.monotonic()
            warming_up = (now - calibrated_at < WARMUP_SECONDS)
            motion_boxes = detect_motion(
                processed, subtractor,
                learning_rate=0.15 if warming_up else 0.003)
            if warming_up:
                motion_boxes = []
                consecutive_frames = 0
            elif motion_boxes:
                consecutive_frames += 1
                if consecutive_frames >= 2:
                    last_motion = now
                    if now - last_beep >= BEEP_COOLDOWN:
                        play_alarm()
                        last_beep = now
            else:
                consecutive_frames = 0

            boxes = upscale_boxes(motion_boxes, frame.shape, processed.shape)
            fw = frame.shape[1]
            if focus_x is None:
                focus_x = fw / 2
            if FOLLOW_MOTION and boxes and FILL_CAMERA and not warming_up:
                # Smoothly track the largest moving region to avoid jerky crops.
                x, y, bw, bh = max(boxes, key=lambda b: b[2]*b[3])
                focus_target = x + bw/2
                focus_x = 0.84 * focus_x + 0.16 * focus_target
            elif not boxes:
                focus_x = 0.995 * focus_x + 0.005 * (fw / 2)

            alert = not warming_up and (now - last_motion < ALARM_HOLD_SECONDS)
            flashing = int(now * 4) % 2 == 0
            if PORTRAIT:
                display = render_portrait(frame, boxes, alert,
                                          warming_up, flashing, focus_x)
            else:
                display = render_landscape(frame, boxes, alert,
                                           warming_up, flashing)

            cv2.imshow(WINDOW_NAME, display)
            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key == ord("p"):
                PORTRAIT = not PORTRAIT
                cv2.destroyAllWindows()
            elif key == ord("c"):
                FILL_CAMERA = not FILL_CAMERA
                print("Camera mode:", "BIG CROP" if FILL_CAMERA else "FULL VIEW")
            elif key == ord("r"):
                subtractor = new_subtractor()
                calibrated_at = time.monotonic()
                last_motion = -1e6
                consecutive_frames = 0
                focus_x = None
    finally:
        cam.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
