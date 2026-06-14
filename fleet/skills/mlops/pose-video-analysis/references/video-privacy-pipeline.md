# Video Privacy Pipeline — Face Blur + Audio Strip + Skeleton Overlay

## Why

Training videos sourced from B站/YouTube contain real pro athletes' faces and audio. Serving these directly in a WeChat mini-program creates **肖像权 (portrait rights)** and **隐私 (privacy)** risks. This pipeline removes both.

## One-liner

```python
from badminton_coach.video_privacy import process_video
process_video("input.mp4", "output.mp4")
# Produces: face-blurred + silent + skeleton-overlaid video
```

## Stage 1: Face blur (MediaPipe FaceDetector + OpenCV GaussianBlur)

- Model: `blaze_face_short_range` (download from GCS: ~300KB)
- Detection confidence: 0.4 (catches most profiles/side-faces)
- Blur kernel: `GaussianBlur(kernel=(k,k), sigma=30)` where `k = max(1, min(w,h)//30)`, forced odd
- Process per frame, per detected face bounding box
- Bounding boxes from `detection.bounding_box` (origin_x, origin_y, width, height)

## Stage 2: Strip audio

Simple ffmpeg one-liner:
```bash
ffmpeg -i input.mp4 -an -vcodec libx264 -preset fast -crf 23 output.mp4
```

WeChat mini-program doesn't need audio for training demos — the videos are pure visual reference.

## Stage 3: Skeleton overlay (MediaPipe Pose + OpenCV drawing)

- Track 13 landmarks per player (nose, shoulders, elbows, wrists, hips, knees, ankles)
- Draw coloured circles (radius 4, filled) + connecting lines (thickness 2)
- Optionally add joint angle text labels (e.g. `肘角142°`) for biomechanical analysis
- Colours per player: [Blue, Red, Green, Orange] for up to 4 players
- Overlay opacity: 0.4 — enough to see the skeleton but not obscure the player

## Full pipeline integration

```python
import tempfile, subprocess, cv2, mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

def process_video(input_path: str, output_path: str) -> str:
    t1 = _blur_faces(input_path, "/tmp/step1_blur.mp4")
    t2 = _strip_audio(t1, "/tmp/step2_silent.mp4")
    t3 = _overlay_skeleton(t2, output_path)
    os.remove(t1); os.remove(t2)
    return t3
```

## Performance

- Resolution: 720p H.264
- Processing speed: ~3-5x realtime (i.e., a 30s video takes 6-10s)
- Output size: similar to input +10-15% for skeleton overlay
- Face blur is the bottleneck (frame-by-frame detection); the rest is fast

## Download required models

```bash
# Face detector (300KB)
curl -L -o face_detector.task \
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/face_detector.task"

# Pose landmarker (5.7MB — same as training system)
curl -L -o pose_landmarker_lite.task \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
```
