# MediaPipe 0.10.14 → 0.10.35 Migration

Complete migration spec for a badminton-coach-AI codebase with 4 backend files.

## Why

`mediapipe==0.10.14` shipped the legacy `mp.solutions.pose` API.  
`mediapipe>=0.10.20` removed `mp.solutions` entirely — `import mediapipe as mp; mp.solutions` raises `AttributeError`.  
The new API is `PoseLandmarker` via `mediapipe.tasks.python`.

## Detection of installed version

```python
import mediapipe as mp
print(mp.__version__)
has_legacy = hasattr(mp, "solutions")
has_tasks = hasattr(mp, "tasks")
```

## Migration scope (4 files)

### 1. `requirements.txt`

**Before:** `mediapipe==0.10.14`  
**After:** `mediapipe>=0.10.35`  
(The >= floor allows any 0.10.35+ build, including future patches.)

### 2. `pose_estimator.py` — Video mode

**Changes:**
- Constructor: no longer needs `model_complexity` param (PoseLandmarker model is in the .task file)
- `_lazy_init()`: create `vision.PoseLandmarkerOptions` with `running_mode=vision.RunningMode.VIDEO`
- Use `.create_from_options()` instead of `mp.solutions.pose.Pose()`
- `process_video()`: per-frame, call `detector.detect_for_video(mp_img, timestamp_ms)` — NOT `.detect()`
- `timestamp_ms = int(frame_idx / fps * 1000)` — must be monotonically increasing
- Landmarks are `(x, y, z)` only — no `.visibility` field. Use `1.0` as placeholder when constructing arrays
- `close()`: just set `self._pose = None` — PoseLandmarker doesn't have a `.close()`

**Import changes:**
```python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions
```

### 3. `image_assessor.py` — Image mode (single photo)

**Changes:**
- No context manager (`with mp.solutions.pose.Pose(...) as pose:`) — use `PoseLandmarker.create_from_options()`
- `running_mode=vision.RunningMode.IMAGE` (not VIDEO)
- `.detect(mp_img)` (not `detect_for_video`)
- Model file resolution: try both `os.path.join(os.path.dirname(__file__), "..", "pose_landmarker_lite.task")` and `"pose_landmarker_lite.task"` as fallback

### 4. `double_analyzer.py` — Multi-person image mode

**Changes:**
- Same IMAGE-mode setup as `image_assessor.py`
- `result.pose_landmarks` is a **list** — naturally supports multi-person
- Occlusion-mask fallback (re-detect with first person blacked out) works identically under the new API
- Add `_get_detector()` global cache singleton to avoid reloading the model on each call:
```python
_POSE_DETECTOR = None

def _get_detector():
    global _POSE_DETECTOR
    if _POSE_DETECTOR is None:
        options = vision.PoseLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=MODEL_PATH),
            running_mode=vision.RunningMode.IMAGE,
            min_pose_detection_confidence=0.4,
        )
        _POSE_DETECTOR = vision.PoseLandmarker.create_from_options(options)
    return _POSE_DETECTOR
```

## Model file requirement

The `pose_landmarker_lite.task` (~5.7 MB) file must be present at project root:

```bash
curl -L -o pose_landmarker_lite.task \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
```

Place this at the project root (same level as `requirements.txt`) — all backend files search both the `badminton_coach/` parent dir and project root.

## Verification after migration

```bash
# Test all imports
python -c "from badminton_coach.pose_estimator import PoseEstimator, FramePose; print('pose_estimator OK')"
python -c "from badminton_coach.image_assessor import assess_image; print('image_assessor OK')"
python -c "from badminton_coach.double_analyzer import analyze_doubles, detect_people_count; print('double_analyzer OK')"

# Test webapp startup (imports all modules transitively)
python -c "from badminton_coach.webapp import app; print('webapp OK')"

# Full API test
python -m uvicorn badminton_coach.webapp:app --host 127.0.0.1 --port 8000 &
sleep 2
curl -s -X POST http://127.0.0.1:8000/api/assess -F "file=@test_img_4.jpg" | python -m json.tool | head -10
curl -s -X POST 'http://127.0.0.1:8000/api/doubles?mode=single' -F "file=@test_img_4.jpg" | python -c "import json,sys; d=json.load(sys.stdin); print(d.get('player_a',{}).get('role_cn','?'))"
```

## Pitfalls

- **`FramePose.point()` visibility check**: the old code had `if lm[3] < 0.3: return None` — since PoseLandmarker has no visibility, `lm[3]` is now `1.0` (the z coordinate was moved to index 2). Either remove the visibility check or change the threshold to `if lm[2] < -1.0` (z is always positive in normalized coords).
- **detect_for_video requires timestamp**: forgetting `timestamp_ms` argument causes a silent TypeError. The timestamp must be in milliseconds and strictly increasing.
- **Model file not found**: if the `.task` file doesn't exist at any checked path, `BaseOptions(model_asset_path=...)` raises `FileNotFoundError`. Always check `os.path.exists()` before creating options.
