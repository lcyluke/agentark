# P0 Video Collection Pipeline: End-to-end Walkthrough

## Context

This document records a full P0 (6-category, 21-video) video collection run for the badminton labeling system. The pipeline produced **1,417 pure-action clips** from 21 instructional YouTube videos (~300MB total), then fed them through MediaPipe PoseLandmarker skeletal tracking.

## Source Categories and Initial Video Acquisition

| Category | Videos | Total Size | Chinese yt-dlp Search | Fallback YouTube ID |
|:---------|:------:|:----------:|:---------------------|:-------------------|
| 发球 (serve) | 7 | 113MB | `羽毛球 发球 教学` | J81WcES8Q2g (反手发平高) |
| 平抽挡 (drive) | 3 | 36MB | `羽毛球 平抽 教学` | 3TJXAvzykJU |
| 挑球 (lob) | 2 | 24MB | `羽毛球 挑球 教学` | Xq1kNnO5tac |
| 接杀防守 (block) | 3 | 30MB | `羽毛球 挡网 教学` | LqwiUemqUQc |
| 接发球 (serve_return) | 3 | 37MB | `羽毛球 接发球 教学` | R1Z9ASD310A |
| 过渡球 (transition) | 3 | 61MB | `羽毛球 过渡球 教学` | CX6TYztWj8w |

## yt-dlp Download Strategy

### Key parameters
```
-f "18"                    # Format 18 = 360p MP4 with audio. Most reliable across YouTube.
--max-filesize 150M        # Avoid downloading full match videos (can be 1GB+)
-o "category/%(id)s.%(ext)s"  # Organize by category subdirectory
```

### Why format 18?
`best[height<=720][ext=mp4]` fails on ~20% of YouTube videos (format not available). Format 18 (360p MP4) has been stable for a decade. 360p is sufficient for MediaPipe Pose (256×256 input resolution).

### Parallel downloads
Run 6-10 concurrent downloads (each in a separate `terminal()` call or `&` in shell). Average time: 30-90s per video. Success rate: ~90% (transient SSL/timeout errors on ~10%, yt-dlp auto-retries).

### Transient error patterns (safe to ignore — yt-dlp handles these):
- `[SSL] record layer failure (_ssl.c:2590)` — plaintext-size-boundary issue, retried automatically
- `Got error: NNNNN bytes read, MMMM more expected.` — partial read, retried
- `WARNING: [youtube] No supported JavaScript runtime` — format extraction warning, non-fatal with `-f "18"`
- `[download] Got error: N bytes read, M more expected. Retrying (1/10)...` — 100% self-healing within 1-3 retries

## Scene + Silence Detection Algorithm

### v1 (failed approach)
```python
SCENE_THRESHOLD = 0.35
ffmpeg -i video.mp4 -vf "select='gt(scene,0.35)',showinfo" ...
```
Result: A 695s tutorial video produced **1 clip** (entire video). Missed all talking→demo→talking transitions.

### v2 (working approach)
Combines two independent signals:
```python
SCENE_THRESHOLD = 0.15     # Low threshold catches visual transitions
SILENCE_NOISE = "-30dB"     # Audio noise floor
MIN_SILENCE = 0.5           # Seconds of silence = boundary
MIN_CLIP_DURATION = 3.0     # Minimum clip to extract (skip micro-gaps)
MAX_CLIP_DURATION = 60.0    # Max action clip (pure demos are 5-45s)
```

**ffmpeg commands:**
```bash
# Visual scene transitions:
ffmpeg -i input.mp4 -vf "select='gt(scene,0.15)',showinfo" -vsync vfr -f null - 2>&1

# Audio silence detection:
ffmpeg -i input.mp4 -af "silencedetect=noise=-30dB:d=0.5" -f null - 2>&1
```

### Merging algorithm

```python
def classify_segment(start, end):
    dur = end - start
    if dur < 3:    return "too_short"     # skip
    if dur <= 60:  return "action_demo"   # ← extract this
    if dur <= 180: return "talking"       # save for transcript
    return "oversized"                     # skip (rare)
```

### Results comparison
| Metric | v1 (scene only 0.35) | v2 (scene 0.15 + silence) |
|:-------|:--------------------:|:-------------------------:|
| Total clips | 147 | 1,417 |
| Average clips/video | 7 | 67 |
| Largest single-video clips | 1 (695s segment) | 993 clips from 55min serve tutorial |
| Clip granularity | 30-700s | 3-60s (average: 4-8s) |
| Whisper feasibility | Can't transcribe 695s | 300s preview = fast |

**Why the huge difference for serve:** The 55-minute serve tutorial (`serve_bh_flick_J81WcES8Q2g.mp4`, 3320s, 129MB) contained one continuous recording where a coach demonstrated 40+ different serve techniques back-to-back with brief pauses between each. v1 treated it as 1 clip. v2's silence detection caught the 0.5-2s pauses between demonstrations, splitting it into 993 individual serve demonstrations.

## File Organization

```
data/
├── raw_videos/
│   ├── serve/             # Original 360p MP4 downloads
│   ├── drive/
│   ├── lob/
│   ├── block/
│   ├── serve_return/
│   └── transition/
├── processed_videos/      # Extracted action clips
│   ├── serve/
│   │   └── serve_bh_short_KpfGkEJ4jq0/
│   │       ├── serve_bh_short_KpfGkEJ4jq0_demo000_0s.mp4
│   │       ├── serve_bh_short_KpfGkEJ4jq0_demo001_6s.mp4
│   │       └── ... (44 clips)
│   ├── drive/...
│   └── ...
├── transcripts/           # Whisper JSON + formatted TXT
├── skeletons/             # MediaPipe per-frame landmarks
│   ├── serve/
│   │   └── serve_bh_short_KpfGkEJ4jq0/
│   │       └── serve_bh_short_KpfGkEJ4jq0_demo000_0s.json
│   └── ...
└── raw_videos/
    └── counter_attack/    # P1 downloaded separately (6 videos)
```

## MediaPipe Skeletal Pipeline (PoseLandmarker)

### API: MediaPipe 0.10.35 tasks API

```python
# CORRECT import path for 0.10.35+:
from mediapipe.tasks.python.vision.pose_landmarker import _RunningMode as RM
from mediapipe.tasks.python.vision import PoseLandmarkerOptions, PoseLandmarker
from mediapipe import Image as MPImage, ImageFormat

opts = PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="models/pose_landmarker.task"),
    running_mode=RM.VIDEO,      # Use RM.VIDEO, not RM.IMAGE!
    num_poses=1,
    min_pose_detection_confidence=0.3,  # Lower = more detection
    min_pose_presence_confidence=0.3,
    min_tracking_confidence=0.3,
    output_segmentation_masks=False
)

# CRITICAL: Use global timestamp across ALL clips when reusing one landmarker
# Resetting to 0 per clip raises ValueError: Input timestamp must be monotonically increasing
global_ts = 1
with PoseLandmarker.create_from_options(opts) as landmarker:
    cap = cv2.VideoCapture(str(clip_path))
    ts = 0
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = MPImage(ImageFormat.SRGB, rgb)
        result = landmarker.detect_for_video(mp_img, ts)  # ← .detect_for_video()
        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            lms = result.pose_landmarks[0]  # first person
            # 33 landmarks, each with .x, .y, .z (no .visibility field)
            arr = [(l.x, l.y, l.z) for l in lms]
        ts += int(1000 / fps)
```

### Key differences from legacy `mp.solutions.pose`:
- **No `.visibility` field.** All landmarks returned as detected (assumed visible). For cross-version compatibility: `l.visibility if hasattr(l, 'visibility') else 1.0`.
- **Requires a `.task` model file** (~5.7MB) downloaded from Google Storage:
  ```bash
  curl -L -o models/pose_landmarker.task "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"
  ```
- **`detect_for_video()` requires timestamp_ms**, not raw frames.
- **Single-use per clip** — `PoseLandmarker.create_from_options()` inside `with` block.
- First detection is slow (4-8s) — XNNPACK delegate initialization. Subsequent frames are fast.

### B站 Format IDs (verified)
| Format ID | Resolution | Codec | Use Case |
|:---------:|:----------:|:------|:---------|
| 30064 | **1280×720** | avc1.640028/64001F | Best for skeleton tracking |
| 30032 | 852×480 | avc1.64001F | Fallback if 720p unavailable |
| 30016 | 640×360 | avc1.64001E | Minimum acceptable |
| 30080 | 1080p+ | avc1.640028 | Rare (requires 大会员) |

Download command: `yt-dlp --cookies cookies.txt -f 30064 "https://www.bilibili.com/video/BVxxx"`

### Model download considerations
- Google Storage is not blocked in China, but downloads are slow (~500KB/s).
- Expected: 5.6MB downloads in ~11 seconds.
- Model path resolution: check project root (`models/pose_landmarker.task`) first, then symlink or copy.

### Running mode choice
- `RM.IMAGE`: Used for single frame analysis. Detect via `.detect(mp_img)`.
- `RM.VIDEO`: Used for clip analysis. Detect via `.detect_for_video(mp_img, timestamp_ms)`.
- `RM.LIVE_STREAM`: For real-time camera feed. Requires `result_callback`.

### GPU vs CPU on macOS
MediaPipe automatically uses Metal GPU on Apple Silicon. This can cause issues in headless/server environments or when running many parallel processes. Disable GPU with:
```python
import os
os.environ["MEDIAPIPE_DISABLE_GPU"] = "1"
```
Set BEFORE importing mediapipe. CPU-only mode is ~2x slower per frame but avoids GPU memory fragmentation in long batch runs.

## Batch Pipeline Lessons

### Clip extraction speed
- 21 videos → 1,417 clips: ~3 minutes total (ffmpeg copy mode is fast).
- No re-encoding (`-c copy`) for speed, but `-c copy` requires frame-accurate slicing. `-ss` before `-i` is faster but less accurate; `-ss` after `-i` is frame-accurate but slower. For skeleton extraction, `-ss <start> -t <duration> -i video -c copy -avoid_negative_ts make_zero` is the right balance.

### Background process management
- Three concurrent pipelines (v2 scene extraction, whisper transcription, P1 download) all ran simultaneously.
- Use `notify_on_complete=true` throughout — each completion auto-notifies.
- Check progress with `process(action="poll", session_id=X)`.
- One pipeline failing doesn't block the others.

### What to do when whisper fails mid-batch
1. Check: is whisper installed in the right Python? `python3 -c "import whisper; print(whisper.__version__)"`
2. Check: numpy version? `pip install "numpy<2"` (numba incompatibility).
3. Strategy: transcribe first 300s audio only (extract mono 16kHz WAV), not full video.
4. Strategy: run whisper per-video (one at a time) not batch-for-loop — if one crashes, the loop doesn't lose progress.

## Next Phase: Annotation Pipeline

After skeleton JSON is generated for all 1,417 clips, the annotation engine (`annotation_engine.py` + `annotation_extensions.py`) processes each. See the 28-dim annotation schema in ANNOTATION_SCHEMA.md.

Expected throughput: ~3-4 clips/second per core (M1 Pro), meaning 1,417 clips ≈ 6-8 minutes total for annotation.
