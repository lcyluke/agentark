---
name: pose-video-analysis
description: Build human-movement analysis pipelines from video using MediaPipe Pose (or similar) — pose estimation, action/event segmentation, biomechanical metric extraction, diagnosis, and annotated-video output. Use for sports technique analysis (badminton/tennis/golf/running form), exercise form checking, gait analysis, gesture/rep counting, or any "analyze how a person moves in this video" task.
---

# Pose-Based Video Movement Analysis

A reusable pipeline for turning a video of a person moving into structured
analysis: per-frame skeleton → detected events (strokes/reps/steps) →
biomechanical metrics → diagnosis → annotated output video.

## Pipeline shape

```
video → PoseEstimator (per-frame 33 landmarks)
      → event segmentation (peak detection on a motion signal)
      → per-event metrics (joint angles, extension, rotation, speed)
      → rule-based diagnosis (+ optional LLM natural-language coaching)
      → visualizer (skeleton + labels burned into output mp4)
```

Keep these as separate modules — `pose_estimator`, `analyzer`,
`coach/diagnoser`, `visualizer`, `cli`. They have independent failure modes
and the analyzer/diagnoser must be testable without real video.

## Critical setup pitfall: MediaPipe version (and the fix for 0.10.35+)

**`mediapipe` builds ≥0.10.20 ship WITHOUT the legacy `mp.solutions` API**.
`import mediapipe as mp; mp.solutions.pose` raises
`AttributeError: module 'mediapipe' has no attribute 'solutions'`.

### Fix option A: pin a version with the legacy API (preferred for existing codebases)

`mediapipe==0.10.14` works (verified on Apple Silicon / Python 3.9+).
Put the exact pin in `requirements.txt`, not a floor (`>=`).

```bash
pip install mediapipe==0.10.14
python -c "import mediapipe as mp; assert hasattr(mp,'solutions'); from mediapipe.python.solutions import pose; print('legacy pose API ok')"
```

### Fix option B: use the new `PoseLandmarker` API (for 0.10.35+)

If the environment already has 0.10.35 (e.g. a Hermes venv), the old API is
simply not available. Switch to the new Task API:

```python
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

# Step 1: download the model file (one-time)
# curl -L -o pose_landmarker_lite.task \
#   "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"

options = vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="pose_landmarker_lite.task"),
    running_mode=vision.RunningMode.IMAGE,
    min_pose_detection_confidence=0.4,
)
detector = vision.PoseLandmarker.create_from_options(options)

# Step 2: detect on each image — supports MULTI-PERSON by default
img = cv2.imread("photo.jpg")
mp_img = mp.Image(
    image_format=mp.ImageFormat.SRGB,
    data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB),
)
result = detector.detect(mp_img)  # result.pose_landmarks is a list

# Each element of result.pose_landmarks is a NormalizedLandmarkList
for person_idx, landmarks in enumerate(result.pose_landmarks):
    nose = landmarks[0]
    rwrist = landmarks[16]
    lwrist = landmarks[15]
    # landmarks[i].x, .y, .z are normalized 0-1, same convention as old API
    # No .visibility field in PoseLandmarker output
```

Key differences from the legacy API:
- `PoseLandmarker.create_from_options()` returns more detail (blendshapes, segmentation masks optional)
- **No `.visibility` field** on individual landmarks — all keypoints are assumed visible by the model. When piping into code that expects `(x, y, z, visibility)`, use `l.visibility if hasattr(l, 'visibility') else 1.0`.
- Uses a separate `.task` model file that must be downloaded (~5.7MB for lite)
- The old hand-built `FramePose` dataclass needs to be updated to accept landmarks without the visibility column, or the detection pipeline needs a shim

### Detection of whether legacy API exists (runtime check)

```python
import mediapipe as mp
has_legacy = hasattr(mp, "solutions")
has_tasks = hasattr(mp, "tasks")
# Use the appropriate code path
```

## Key technique: adaptive peak detection for event segmentation

Detecting "when did a stroke/rep/impact happen" from a motion signal
(e.g. dominant-wrist speed = frame-to-frame landmark displacement × fps):

A **pure global threshold** (`mean + std`, or `max * k`) **misses
low-energy events** — a soft drop shot or a light rep never crosses a bar
set by a powerful smash. The fix is **global threshold + local prominence**:

```python
global_thr = max(speeds.mean() + 0.5*speeds.std(), speeds.max() * 0.25)
win = max(int(fps * 0.5), 3)          # local neighborhood ~0.5s
for each local maximum i where speeds[i] >= global_thr:
    baseline = np.median(speeds[i-win : i+win])
    if speeds[i] >= max(global_thr, baseline * 2.0):   # stands out locally
        accept (respecting a min_gap ~0.4s between events)
```

The `baseline * 2.0` local-prominence gate catches softer events the global
bar would drop, while `min_gap` prevents double-counting one motion. Tune
`win`, the prominence multiplier, and `min_gap` to the sport's tempo.

## Always ship a `selftest` that bypasses the CV stack

MediaPipe is trained on real humans — synthetic stick-figure videos get
~17% detection and zero events, so a video-based `demo` can't verify the
analyzer/diagnoser logic. **Add a `selftest` subcommand that constructs
synthetic landmark sequences directly** (hand-built `FramePose` arrays for
a "good" and a "flawed" execution) and runs them through
analyzer → diagnoser → report. This exercises event detection, action
classification, every diagnosis branch, and the coaching output with no
video, no network, no model weights — and it doubles as a regression test
that surfaced the threshold bug above.

## Critical domain limitation: MediaPipe is single-person & near-shot

**MediaPipe Pose is a single-person, near-shot model.** On broadcast /
wide-angle / multi-person footage (e.g. a gym match filmed from the stands,
sports TV coverage) detection rate collapses to near-zero and the few
detected frames produce **garbage biomechanical metrics** (knee_bend 0.00,
recovery 20%, etc.). The analyzer is *not* wrong — the footage type is
wrong for the model.

**Set this expectation BEFORE promising results, and state required footage
up front:** near/medium shot, single person filling a good fraction of the
frame, stable tripod, side/rear ~45° angle. A phone on a tripod of one
player is the ideal input; a downloaded pro match is usually the wrong
input despite being "real badminton." Surface the limitation honestly when
the user supplies broadcast footage rather than reporting confident-looking
but meaningless numbers. If multi-person / wide-angle is a hard
requirement, escalate to a multi-person model (e.g. YOLOv8-pose,
RTMPose) — note this as the upgrade path, don't pretend MediaPipe handles it.

## Reference / pro-comparison module (when "compare to a pro" is asked)

Add a `reference_library` module that scores a user's metrics against a
benchmark and decomposes the gap:

- **Two-tier benchmarks**: ship an expert-prior `BUILTIN_BENCHMARKS` dict
  (per action-type target metric values from coaching norms) so it works
  offline, *and* optionally a `reference_db.json` built from real videos
  that overrides the prior. Load DB on top of priors (merge, DB wins).
- **Build the DB by percentile aggregation, not mean**: run the analyzer
  over a corpus of pro videos, bucket events by action type, take the
  **~75th percentile** of each metric (represents stable high-level
  performance — robust to bad frames, captures "pro target").
- **Scoring**: per-metric `ratio = clip(user/pro, 0, 1)`, weighted sum →
  0–100; surface the single biggest-gap metric so the coach can focus.
- Pitfall: don't feed already-annotated output videos back into
  `build_reference` (double-counts and pollutes the baseline) — only raw
  source clips. Wide-angle pro footage also produces bad baselines for the
  same single-person-model reason above.

## Footwork / locomotion analysis (lower-body sport metrics)

Center-of-mass = midpoint of the two hip landmarks. From its trajectory
derive: total path length, court-coverage bounding box, recovery-to-center
ratio after each event (min distance back to median position within ~0.7s),
stance height (1 − COM.y), stability (inverse of median frame jitter), and
split-step / preparatory-hop count via a fast down-then-up pattern on the
mid-ankle y signal. Gate "recovery/split-step missing" diagnoses on the
presence of detected events (no events ⇒ don't fabricate footwork faults).

## Sourcing reference videos (yt-dlp)

YouTube now hard-walls anonymous downloads ("Sign in to confirm you're not
a bot") even with the android/ios `player_client` extractor args; it
requires real cookies. **macOS Safari cookies are sandbox-protected**
(`Operation not permitted` on `Cookies.binarycookies` without Full Disk
Access) and Chrome/Firefox are often not installed. Robust fallback:
**`archive.org` has openly-licensed real sports footage** — query
`https://archive.org/advancedsearch.php?q=<sport>+AND+mediatype:movies&output=json`,
then `yt_dlp` the `archive.org/details/<id>` page. Use `download_ranges`
with a keyframe-cut callback to grab a short clip instead of a full match.
Keep `cookiesfrombrowser` as an opt-in CLI flag for users who do have
browser cookies available.

## Badminton-specific: multi-action assessment & progressive grading

When building a badminton skill assessment feature (e.g. for a WeChat mini-program), the user's requirement was:

1. **Classify each photo/video into exactly one of 6 badminton strokes**: serve, clear (高远球), drop (吊球), smash (杀球), lift (挑球), net (网前球)
2. **Score each stroke independently** during a multi-photo session
3. **Only produce a final composite grade when ALL 6 strokes have been uploaded** — never give a partial or misleading grade from incomplete data
4. **Reject non-badminton content** before entering the assessment pipeline — distinguish badminton from table tennis, basketball, casual photos, etc.

### Action classification via pose heuristics (photo mode)

For a **single photo** (no speed signal), classify the stroke from body pose alone:

```python
# Key features derived from MediaPipe landmarks:
#   contact_height  = 1.0 - wrist.y  (higher = overhead stroke)
#   arm_extension   = shoulder-elbow-wrist angle / 180°  (1.0 = fully extended)
#   shoulder_rot    = shoulder-line angle vs horizontal / 60° (1.0 = full side-on)
#   knee_bend       = (180° - hip-knee-ankle) / 70° (1.0 = deep lunge)
#   body_lean       = how horizontal the torso-shoulder→hip vector is
#   foot_stance     = "open" (front-back) vs "square" (parallel) via ankle z-diff

# Decision tree (high-confidence branches first):
if height < 0.45 and shoulder_rot < 0.30 and arm_near_horizontal and open_stance:
    → "serve" (发球)       # low hand, forward swing, open stance

if height < 0.35 and knee_bend > 0.30 and arm_ext > 0.55:
    → "lift" (挑球)        # low point, deep knee, arm reaching down

if height < 0.45 and knee_bend > 0.30:
    → "net" (网前球)       # low point, deep lunge

if height > 0.58 and arm_ext > 0.75:
    if lean > 0.20 or shoulder_rot > 0.35:
        → "smash" (杀球)   # high point, full extension, lean forward
    else:
        → "clear" (高远球)  # high point but no lean/rotation

if height > 0.55 and 0.50 ≤ arm_ext ≤ 0.75:
    → "drop" (吊球)        # high point, half-extended (cutting motion)

else fallback:
    → "clear" (low conf)   # unknown → safest default
```

### Multi-photo progressive assessment pattern

Maintain per-user session state:

```python
{
    "user_id": "...",
    "collected": {},       # action_type → {stroke_event, action_score}
    "remaining": [         # actions still needed
        "serve", "clear", "drop", "smash", "lift", "net"
    ],
    "status": "incomplete"  # or "complete"
}
```

Rules:
- Each upload is classified → matched to exactly one of the 6 action types
- If user uploads a 2nd smash, accept it but mark as duplicate (use best score)
- Only when `len(collected) == 6` do you run `SkillGrader.assess(events=list_of_6, source="multi_photo")` with high confidence
- Frontend shows progress bar: `🟢 杀球✅ 🟡 还需要: 吊球 发球 挑球 网前球`
- If user repeatedly uploads the same stroke type, prompt them to try different ones

### Content validation (reject non-badminton)

Add a pre-check before pose → classify:

```python
# Rejection cascade:
# 1. No person detected → "🤔 没看到人呢，请拍打球照片"
# 2. Person but no elevated arm → "肢体动作不太像打球，请重拍"
# 3. Classified action is consistently "clear" with low conf from 3+ attempts
#    → Consider non-badminton content
# 4. Video: inter-event intervals inconsistent with badminton rhythm
#    → Flag for manual review rather than scoring
```

The content validation should be a **separate check** that runs before classification, not mixed into the scoring logic. This keeps the scoring code clean and the rejection reasons user-friendly.

### Video assessment (direct, no frame-splitting needed)

The existing `PoseEstimator.process_video()` already does per-frame analysis. No need to split video into frames manually:

```python
poses = PoseEstimator().process_video(video_path)
events = StrokeAnalyzer(fps=fps).analyze(poses)  # finds all strokes
# Events are naturally multi-type — a rally contains serve, clear, smash...
collected = {e.stroke_type: e for e in set(events)}
if ALL_6_TYPES.issubset(collected):
    grade = SkillGrader().assess(list(collected.values()), source="video")
else:
    missing = ALL_6_TYPES - set(collected)
    grade = partial_result_with_missing_penalty(missing)
```

Video assessment confidence depends on:
- Number of detected strokes per type (more = better consistency estimate)
- Detection stability (frame-to-frame landmark variance)
- If fewer than 2 strokes detected total → fall back to "insufficient data"

### Badminton-specific action: single-frame classifier

The `classify_single_frame(p, side)` function lives in `stroke_analyzer.py` and works for both photo (one FramePose) and video (per-detected-peak) modes. It must handle **no-speed-information** gracefully — photos have zero speed data, so the classifier relies entirely on spatial features.

Pitfall: don't use `wrist_speed` in the single-frame classifier — photos supply a neutral 0.6 placeholder. The height+extension+rotation+lean combination is sufficient.

## Doubles / multi-player analysis (e.g. badminton doubles)

When you need to analyze a **multi-player match** (badminton doubles, tennis doubles, etc.), build a separate `doubles_estimator.py` and `doubles_analysis.py` on top of the existing `PoseEstimator` pattern. The doubles pipeline differs from singles in key ways.

### DoublesPoseEstimator: multi-person skeleton extraction

```python
from mediapipe.tasks.python import vision
options = vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="pose_landmarker_lite.task"),
    running_mode=vision.RunningMode.VIDEO,
    min_pose_detection_confidence=0.4,    # lower to catch more people
    min_tracking_confidence=0.4,
    num_poses=4,                          # max players on court
)
detector = vision.PoseLandmarker.create_from_options(options)

# Per frame:
mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
timestamp_ms = int(frame_idx / fps * 1000)
res = detector.detect_for_video(mp_img, timestamp_ms)

# res.pose_landmarks is now a LIST — one entry per detected person
poses = []
for landmarks in res.pose_landmarks[:4]:
    arr = np.array([[p.x, p.y, p.z, p.visibility or 1.0] for p in landmarks], dtype=np.float32)
    poses.append(FramePose(frame_idx, timestamp, arr))
```

### Player assignment (A1/A2 vs B1/B2)

Use **spatial heuristics** — not a tracking model — to keep it fast and dependency-free:

1. **Split by x-coordinate**: players on the left side of the frame → Team A, right side → Team B
2. **Within each team, sort by y-coordinate**: the player deeper (larger y = further back) = primary attacker (A1/B1), the forward player = net player (A2/B2)
3. Store assignments in a per-frame dict: `{0: "A1", 1: "A2", 2: "B1", 3: "B2"}`

```python
# Centers = hip midpoint of each player
centers = []
for i, pose in enumerate(poses):
    lhip, rhip = pose.landmarks[23], pose.landmarks[24]
    cx, cy = (lhip[0] + rhip[0]) / 2, (lhip[1] + rhip[1]) / 2
    centers.append((i, cx, cy))

# Left half → Team A, right half → Team B
centers.sort(key=lambda c: c[1])
mid = len(centers) // 2
# Within each team: deeper player (bigger y) = 1, forward = 2
```

This is frame-by-frame and doesn't use tracking — the assignment can flip if players cross. For a production system, add a Kalman tracker or simple momentum heuristic to smooth jumps.

### Formation classification (per frame)

Classify each team's formation from two-player positions:

| Formation | Signal | Threshold |
|:---------|:-------|:----------|
| 进攻 (attack) | One player forward, one back | `y_diff > 0.12` AND `x_diff < 0.15` |
| 防守 (defense) | Side-by-side parallel | `x_diff > 0.12` |
| 轮转 (transition) | Neither, mid-movement | None of the above |
| 双压前场 (front court) | Both forward | Both `y < 0.4` |
| 不规则 (mixed) | Players scattered | Fallback |

Use a **sliding window of 5 frames** (majority vote) to stabilize against single-frame noise:

```python
def stable_formation(frames: list, i: int, window: int = 5) -> str:
    window_formations = [frames[j].formation for j in range(i-window, i+window) if 0 <= j < len(frames)]
    return max(set(window_formations), key=window_formations.count)
```

### Rotation event detection

A **rotation** is a team's formation changing from attack → defense → attack (or any pair of distinct formations) within a few seconds. Detect by comparing the stable formation at frame `i-window` vs `i+window`:

```python
rotations = []
for i in range(window, len(frames) - window):
    prev_mode = stable_formation(frames, i - window, window)
    curr_mode = stable_formation(frames, i + window, window)
    if prev_mode != curr_mode:
        rotations.append({
            "frame": i, "time": round(frames[i].timestamp, 2),
            "from": prev_mode, "to": curr_mode,
        })
```

### Doubles skill scoring (8 dimensions)

For each doubles segment, score these dimensions from **motion features** (wrist/hip acceleration, player count stability, zone occupancy):

| Dimension | Signal source |
|:----------|:-------------|
| 平抽快挡 (flat drive) | Wrist movement frequency in mid-front zone |
| 网前扑压 (net kill) | Player count in front zone (% frames) |
| 网前搓球 (front rub) | Fine wrist motion near net |
| 推球分球 (push & split) | Hip-level arm reaches |
| 发接发 (serve/receive) | First-3-second zone activity |
| 中场拦截 (mid block) | Mid-zone occupancy |
| 后场进攻 (back smash) | Attack-formation % |
| 防守挑球 (defense clear) | Defense-formation % |

### Tactics & coordination scoring (10 dimensions)

| Dimension | Scoring method |
|:----------|:--------------|
| 进攻站位意识 | Attack-formation % of total frames |
| 防守站位意识 | Defense-formation % of total frames |
| 轮转时机 | Rotations per minute (ideal: 1-3/min) |
| 空档攻击 | Rotation frequency × 0.8 + 20 |
| 连续进攻 | Max consecutive attack-formation streak × 2 |
| 攻防转换速度 | Total rotation count × 5 |
| 场区覆盖 | Unique court zones occupied (max 4) |
| 补位默契 | % frames with 3+ players detected |
| 球路分配 | Front/back zone balance (50% ideal) |
| 沟通暗示 | Detection-stability proxy |

### Expected accuracy floor

- **Good conditions**: tripod, court-level view, 4 players visible, no severe occlusion → formation classification ~80%, rotation detection ~60%
- **Bad conditions**: shaky camera, extreme angle, 3+ players overlapping → detection drops to ~30% for 4 people. Don't fabricate scores when player_count < 3 most of the time
- MediaPipe PoseLandmarker with `num_poses=4` still **fails on side-by-side crops where the second person is very small** (<30% of the first). The model isn't trained for 2048×1080 frames containing tiny figures — if each player is under ~80px tall, detection is unreliable regardless of `num_poses`

### Output shape

```json
{
  "doubles_skills": { "flat_drive": 72, "net_kill": 55, ... },
  "tactics": { "attack_formation": 82, "rotation_timing": 64, ... },
  "coordination": { "court_coverage": 70, "partner_gap": 58, ... },
  "formation_stats": { "进攻站位": 42.3, "防守站位": 31.5, "轮转中": 18.7, ... },
  "rotation_count": 12,
  "rotations": [...],
  "overall_score": 68.4,
  "training_advice": { "serve_receive": "发球稳定性训练...", ... },
  "total_frames": 5432,
  "duration_sec": 181.1
}
```

### Doubles training skill bank (16 skills × 3 levels)

When building a doubles training system, define 16 specialized skills in 4 categories:

| Category | Skills |
|:---------|:-------|
| 双打技术 (7) | 正手平抽, 反手平抽, 网前扑压, 推球分球, 发接发, 接发球, 中场拦截 |
| 轮转与站位 (4) | 前后轮转, 左右补位, 防守站位, 进攻站位 |
| 战术意识 (3) | 空档攻击, 连续进攻, 攻防转换 |
| 搭档配合 (2) | 场区覆盖, 配合沟通 |

Each skill has 3 levels (L1 basic → L2 intermediate → L3 advanced) with volume, rest, and pass_score (60/65/70). Generate training advice by mapping the analysis score: `< 40` = "low" (basic drills), `40-69` = "mid" (progressive), `≥ 70` = "high" (advanced integration).

## Video privacy pipeline for compliance

When sourcing training videos that contain real players (pro athletes, coach demonstrations), **blur faces and strip audio** before serving to users — this avoids portrait rights issues on platforms like WeChat.

Build a `video_privacy.py` module with three pipeline stages:

```python
def process_video(input_path: str, output_path: str) -> str:
    """Full pipeline: face blur → strip audio → skeleton overlay"""
    blurred = blur_faces(input_path, "/tmp/blurred.mp4")
    no_audio = strip_audio(blurred, "/tmp/silent.mp4")
    final = overlay_skeleton(no_audio, output_path)
    return final
```

### Stage 1: Face blur (MediaPipe Face Detection + Gaussian blur)

```python
import cv2, mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

face_options = vision.FaceDetectorOptions(
    base_options=BaseOptions(model_asset_path="face_detector.task"),
    min_detection_confidence=0.4,
)
face_detector = vision.FaceDetector.create_from_options(face_options)

cap = cv2.VideoCapture(input_path)
fps = cap.get(cv2.CAP_PROP_FPS)
w, h = int(cap.get(3)), int(cap.get(4))
fourcc = cv2.VideoWriter_fourcc(*"mp4v")
out = cv2.VideoWriter(output_path, fourcc, fps, (w, h))

while True:
    ok, frame = cap.read()
    if not ok: break
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    result = face_detector.detect(mp_img)
    if result.detections:
        for detection in result.detections:
            bbox = detection.bounding_box
            x1, y1 = max(0, bbox.origin_x), max(0, bbox.origin_y)
            x2 = min(w, bbox.origin_x + bbox.width)
            y2 = min(h, bbox.origin_y + bbox.height)
            face_roi = frame[y1:y2, x1:x2]
            if face_roi.size > 0:
                k = max(1, min(w, h) // 30)  # adaptive kernel size
                blurred = cv2.GaussianBlur(face_roi, (k if k%2 else k+1, k if k%2 else k+1), 30)
                frame[y1:y2, x1:x2] = blurred
    out.write(frame)

cap.release()
out.release()
```

### Stage 2: Strip audio

```python
import subprocess
subprocess.run([
    "ffmpeg", "-i", input_video,
    "-an",                       # no audio
    "-vcodec", "libx264",
    "-preset", "fast",
    "-crf", "23",
    output_video
], check=True, capture_output=True)
```

### Stage 3: Skeleton overlay (MediaPipe Pose + OpenCV drawing)

After pose detection per frame, draw coloured circles and lines for the 13 tracked landmarks. Use different colours for different players in doubles mode. Add angle labels (e.g. `"肘角 145°"`) at the joint position.

### Download the model file

The face detector model (`face_detector.task`) must be downloaded separately — it's not bundled with mediapipe:

```bash
curl -L -o face_detector.task \
  "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/latest/face_detector.task"
```

The pose model (`pose_landmarker_lite.task`) needs the same treatment:

```bash
curl -L -o pose_landmarker_lite.task \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
```

## Sourcing Chinese badminton training videos (B站)

When the user needs **Chinese-language badminton training videos** (for a WeChat app targeting Chinese users), the reliable video sources are:

For the full B站 HD pipeline (cookie extraction, download, clip extraction, and batch skeleton tracking on 720p/4K footage), see `references/bilibili-hd-pipeline.md`.

### Priority-ordered coach/player list

### Priority-ordered coach/player list

1. **赵剑华 《专家把脉》** series — most authoritative, covers all basics
2. **肖杰** badminton teaching series (高校教材 level)
3. **影子羽毛球** (YouTube/B站 channel) — pure action demos, minimal talk
4. **李玲蔚 《学打羽毛球》** series
5. **李宁/胜利/Yonex 品牌官方教学** (B站 official accounts)
6. **个人教练**: 薛松、王晓理、杜杜、国二女生等

### B站 search patterns

```
https://search.bilibili.com/all?keyword=羽毛球+{skill}+动作示范
https://search.bilibili.com/all?keyword={coach_name}+羽毛球教学
```

For **pure action clips** (no讲解, no slow-motion analysis, just the player demonstrating), filter results to short videos or use the word "示范" in your query.

### Download command (yt-dlp with cookies)

B站 now requires cookies for HD downloads:

```bash
yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  --cookies-from-browser chrome \
  -o "output.mp4" \
  "B站视频URL"
```

If no browser cookies available, try the `--extractor-args "bilibili:prefer_mp4=1"` flag. As a last resort, fall back to archive.org openly-licensed sports footage.

### Video trimming pattern

All downloaded videos need trimming to **pure action segments** (20-45 seconds, no讲解, no blank frames):

```bash
# Find the action start point, then:
ffmpeg -i input.mp4 -ss 00:00:XX -t 30 -c copy output.mp4
```

For precision, step through keyframes:
```bash
ffmpeg -i input.mp4 -vf "select='between(t,XX,YY)',setpts=N/FRAME_RATE/TB" -an action_clip.mp4
```

**Keyframe-mode scene detection for HD/long videos:**

When running scene detection on 4K or long (>10min) videos, ffmpeg's full-decode `select='gt(scene,...)'` can timeout. Use keyframe-only mode for a 100× speedup with equal scene-boundary accuracy:

```bash
# Instead of:
ffmpeg -i video.mp4 -vf "select='gt(scene,0.12)',showinfo" -vsync vfr -f null -

# Use (100x faster on 4K/60fps):
ffmpeg -skip_frame nokey -i video.mp4 -vf "select='gt(scene,0.12)',showinfo" -vsync 0 -f null -
```

### Naming convention

```
data/training_animations/{skill_id}_demo.mp4
```

Where `skill_id` matches the training system's skill key (e.g. `smash_jump`, `net_fh_rub`, `feint_smash_drop`).

## Multi-person detection with occlusion-mask fallback

The `PoseLandmarker` API (mediapipe ≥0.10.20) supports multi-person detection natively via `result.pose_landmarks` being a list. However, it frequently **misses partially occluded people** — a second person whose body is behind or overlapping with the first. The occlusion-mask technique improves detection:

```python
def detect_with_occlusion_fallback(image_path: str, max_people: int = 2):
    """Detect bodies, using occlusion masking to find hidden second person."""
    img = cv2.imread(image_path)
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
    
    detector = _get_detector()
    result = detector.detect(mp_img)
    
    people = []
    for landmarks in result.pose_landmarks[:max_people]:
        arr = np.array([[lm.x, lm.y, lm.z, 1.0] for lm in landmarks], dtype=np.float32)
        people.append(arr)
    
    # If we got fewer than max_people, try masking out the first person
    if len(people) < max_people and len(result.pose_landmarks) > 0:
        h, w = img.shape[:2]
        lm0 = result.pose_landmarks[0]
        
        # Compute bounding box of first person + padding
        xs = [lm.x * w for lm in lm0]
        ys = [lm.y * h for lm in lm0]
        pad_x, pad_y = int(w * 0.1), int(h * 0.15)
        x1 = max(0, int(min(xs)) - pad_x)
        x2 = min(w, int(max(xs)) + pad_x)
        y1 = max(0, int(min(ys)) - pad_y)
        y2 = min(h, int(max(ys)) + pad_y)
        
        # Black out the first person's bounding box and re-detect
        masked = rgb.copy()
        masked[y1:y2, x1:x2] = (0, 0, 0)
        mp_masked = mp.Image(image_format=mp.ImageFormat.SRGB, data=masked)
        result2 = detector.detect(mp_masked)
        
        for landmarks in result2.pose_landmarks:
            if len(people) >= max_people:
                break
            arr = np.array([[lm.x, lm.y, lm.z, 1.0] for lm in landmarks], dtype=np.float32)
            people.append((arr, 0.7))  # reduced confidence for fallback detection
    
    return people[:max_people]
```

**Limitation**: This still fails on side-by-side crop where the second person is very small (<30% of first person's size), completely behind the first person, or at extreme angles (profile/back to camera). The fallback is a best-effort attempt, not a guarantee.

### Batch skeleton pipeline: reuse landmarker across clips

When processing hundreds or thousands of action clips (e.g. from a sports video labeling system), **do not create a new PoseLandmarker per clip**. Creating one and reusing it is ~100× faster because XNNPACK delegate initialization (~4-8s) only happens once:

```python
# WRONG — 4-8s per clip, 1000 clips = 1-2 hours overhead:
for clip in clips:
    with PoseLandmarker.create_from_options(opts) as lm:
        ...

# RIGHT — 4-8s total overhead, same 1000 clips:
with PoseLandmarker.create_from_options(opts) as lm:
    for clip in clips:
        process_clip(lm, clip)  # < 1s per clip
```

The landmarker state is stateless between videos — creating it once and reusing it across multiple clips works correctly. The `detect_for_video(timestamp_ms)` calls need monotonically increasing timestamps across the **entire lifetime** of the landmarker.

**CRITICAL BUG — do NOT reset timestamp to 0 per clip:**

```python
# WRONG — raises ValueError: Input timestamp must be monotonically increasing
with PoseLandmarker.create_from_options(opts) as lm:
    for clip in clips:
        ts = 0                                     # ← BUG: resets per clip
        process_clip(lm, clip, ts) 

# RIGHT — continuously increasing global timestamp:
global_ts = 1
with PoseLandmarker.create_from_options(opts) as lm:
    for clip in clips:
        cap = cv2.VideoCapture(str(clip))
        fps = cap.get(cv2.CAP_PROP_FPS) or 30
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret: break
            rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            mp_img = MPImage(ImageFormat.SRGB, rgb)
            result = lm.detect_for_video(mp_img, global_ts)  # ← continuous counter
            global_ts += int(1000 / fps)
            ...
        cap.release()
```

Tested with 1,573 clips: 100% detection rate with global timestamp vs first-clip-only detection with per-clip reset. The root cause is that `PoseLandmarker` (VIDEO mode) internally binds a tracking state to the timestamp sequence — resetting causes a tracking state mismatch that raises `ValueError`.

**Important:** Must call `cap = cv2.VideoCapture(str(clip_path))` fresh per clip — the landmarker is reusable but the VideoCapture is not.

See the `process_clip(landmarker, clip_path, output_path)` pattern in `sports-video-labeling-system` reference `p0-video-collection-pipeline.md` for the exact implementation.

### Batch call with progress tracking

```python
def process_clip(landmarker, clip_path, output_path):
    cap = cv2.VideoCapture(str(clip_path))
    fps = cap.get(cv2.CAP_PROP_FPS)
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frame_data = []
    ts = 0
    tracked = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret: break
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_img = MPImage(ImageFormat.SRGB, rgb)
        result = landmarker.detect_for_video(mp_img, ts)
        if result.pose_landmarks and len(result.pose_landmarks) > 0:
            lms = result.pose_landmarks[0]
            frame_data.append({
                "f": tracked,
                "lms": [(round(l.x,4), round(l.y,4), round(l.z,4), round(l.visibility if hasattr(l,'visibility') else 1.0, 3))
                        for l in lms]
            })
            tracked += 1
        ts += int(1000 / max(fps, 1))
    
    cap.release()
    # Save JSON
    output_path.parent.mkdir(parents=True, exist_ok=True)
    json.dump({"fps": fps, "tracked_frames": tracked, "frames": frame_data}, output_path, separators=(",", ":"))
    return {"total": total, "tracked": tracked}
```

### Video mode: full PoseLandmarker pipeline (for 0.10.35+)

When migrating a `PoseEstimator` class from the legacy `mp.solutions.pose.Pose()` API to the new `PoseLandmarker` for **video processing**, the changes involve all four files:

#### `pose_estimator.py` — Video processing refactor

**Before (legacy):**
```python
self._pose = mp.solutions.pose.Pose(
    static_image_mode=False,
    model_complexity=1,
    smooth_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
# Per frame:
res = self._pose.process(rgb)   # raw numpy rgb
arr = np.array([[p.x, p.y, p.z, p.visibility] for p in res.pose_landmarks.landmark])
```

**After (PoseLandmarker):**
```python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

options = vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="pose_landmarker_lite.task"),
    running_mode=vision.RunningMode.VIDEO,     # ← VIDEO mode, not IMAGE
    min_pose_detection_confidence=0.5,
    min_tracking_confidence=0.5,
)
detector = vision.PoseLandmarker.create_from_options(options)

# Per frame:
mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
timestamp_ms = int(frame_idx / fps * 1000)
res = detector.detect_for_video(mp_img, timestamp_ms)   # ← NOT .detect()
arr = None
if res.pose_landmarks:
    arr = np.array([[lm.x, lm.y, lm.z, 1.0] for lm in res.pose_landmarks[0]], dtype=np.float32)
```

**Key differences from IMAGE mode:**
- `running_mode=vision.RunningMode.VIDEO` — IMAGE mode will throw or return empty in video contexts
- `.detect_for_video(mp_img, timestamp_ms)` — NOT `.detect()` (that's for images only)
- `timestamp_ms` must be monotonically increasing — calculated from `int(frame_idx / fps * 1000)`
- Store `self._mp` as an instance attribute so `mp.Image()` is accessible in `process_video()`
- **No `.visibility` field** — all landmarks returned as assumed visible. Update `FramePose.point()` to skip the visibility check (or make it configurable): change `if lm[3] < 0.3: return None` to either remove it or bump the threshold lower
- `PoseLandmarker` objects have no `.close()` method — just set to `None` for cleanup

#### `image_assessor.py` — Image processing refactor

Identical to the IMAGE mode pattern in the skill above. Key changes:
- Replace `with mp.solutions.pose.Pose(static_image_mode=True, ...) as pose:` with `PoseLandmarkerOptions(running_mode=IMAGE)` + `.detect()`
- Model path resolution: check both `os.path.join(os.path.dirname(__file__), "..", "pose_landmarker_lite.task")` and `"pose_landmarker_lite.task"` (project root)
- The `.task` model file must exist before creating options — `FileNotFoundError` if missing. Check `os.path.exists(MODEL)` and fall through candidate paths

#### `double_analyzer.py` — Multi-person detection refactor

Same IMAGE-mode pattern. The new API returns `result.pose_landmarks` as a **list** — no `mp.solutions.pose` context manager needed. The occlusion-mask fallback for detecting a second person works the same way under the new API. 

#### `requirements.txt` pin update

Change `mediapipe==0.10.14` to `mediapipe>=0.10.35` to match the installed version. The old pin locks you to a version with the legacy API; the new pin works with either.

### Version-agnostic runtime check

```python
import mediapipe as mp
has_legacy = hasattr(mp, "solutions")
has_tasks = hasattr(mp, "tasks")
# Branch on this at import/class-init time, not per frame
```

## Other lessons

- **Diagnosis = rules, narrative = optional LLM.** Rule engine produces the
  metrics/issues; LLM only rephrases into coaching prose. Gate the LLM on
  `ANTHROPIC_API_KEY`/`OPENAI_API_KEY` and **always fall back to the rule
  report** on any LLM exception so the pipeline runs fully offline.
- **CJK string literals**: avoid embedding ASCII `"` inside Chinese strings
  (`变成"抬手臂"打球`) — Python parses the inner `"` as a string terminator
  → `SyntaxError`. Use `「」` / `『』` / `'…'` for inner quotes.
- **Dominant side detection**: pick the limb (left vs right wrist) with
  higher positional variance rather than assuming right-handed.
- **Joint metrics**: extension = shoulder-elbow-wrist angle / 180; rotation
  = angle of the two-shoulder line vs horizontal; knee bend =
  (180 − hip-knee-ankle angle). Normalize all to 0–1 for reporting + bars.
- Skip landmarks with `visibility < 0.3` as unreliable rather than trusting
  every detected point.

## Verification

`scripts/verify_mediapipe.py` checks the install has the `solutions` API.
Run it right after `pip install` before building anything on top.

`templates/selftest_synthetic_landmarks.py` is a copy-and-adapt harness
that hand-builds MediaPipe-format landmark arrays (with the 33-index map
documented inline) and runs analyzer → footwork → comparison → coach with
no video/network/weights. Reproduce-with-modifications: shape its two
motion segments to a good vs flawed execution for the target sport.

## Reference

`references/badminton-action-classifier.md` — full 6-action signature table,
decision trees for photo and video mode, diagnosis rules per action type.
Load when building a badminton-specific assessment feature.

`references/mediapipe-0.10.35-migration.md` — complete 4-file migration
spec from `mp.solutions.pose` to `PoseLandmarker` API (pose_estimator,
image_assessor, double_analyzer, and requirements.txt). Load when you hit
`AttributeError: module 'mediapipe' has no attribute 'solutions'` and the
installed version is ≥0.10.20.

`references/synthetic-landmark-parameter-mapping.md` — how to verify that
synthetic landmark test-data helpers actually produce the feature values
their parameter names imply (invert-the-real-function pattern). Load when
building or debugging a `make_landmarks`-style test helper for ML
feature-extraction code. Every classifier/analyzer bug you can't reproduce
with synthetic data is probably a helper-geometry bug, not a production bug.

`references/video-motion-analysis-pipeline.md` — end-to-end pipeline from video ingestion through Whisper transcription, motion segmentation, and action template matching (absorbed from `video-motion-analysis-pipeline` skill).

`references/wechat-video-pipeline.md` — end-to-end pipeline from WeChat video
receipt through MediaPipe skeleton extraction, optional InsightFace face swap,
and pro-level comparison scoring. Load when the user sends a training video
via WeChat and wants it analyzed.
