# Badminton Action Classifier Reference

## The 6 action types and their biomechanical signatures

All values assume `side='right'`. Features derived from MediaPipe Pose landmarks.

**Key features:**

| Feature | Derivation | Range | Meaning |
|---------|-----------|-------|---------|
| contact_height | 1.0 - wrist_16.y | 0–1 | Higher = hit point is higher (overhead strokes) |
| arm_extension | ∠(shoulder, elbow, wrist) / 180° | 0–1 | 1.0 = fully extended overhead |
| shoulder_rotation | arctan2(Δy_shoulders, Δx_shoulders) / 60° | 0–1 | 1.0 = full side-on to net |
| knee_bend | (180° - ∠(hip, knee, ankle)) / 70° | 0–1 | 1.0 = deep lunge |
| body_lean | 1.0 - ∠(shoulder→hip vector vs vertical) / 90° | 0–1 | 0 = upright, 1 = parallel to ground |
| foot_stance | diff of L-ankle.z and R-ankle.z | "open"/"square" | open = front-back stance |
| wrist_speed | frame-to-frame wrist displacement × fps (video only) | 0–∞ | Video only; zero for photos |

## Signature table

| Action | height | arm_ext | shoulder_rot | knee_bend | lean | speed (video) | stance |
|--------|--------|---------|-------------|-----------|------|---------------|--------|
| **serve** (发球) | < 0.45 | 0.4–0.7 | < 0.25 | < 0.25 | ≤ 0.15 | < 0.4 | open |
| **clear** (高远球) | > 0.62 | > 0.75 | > 0.35 | 0.15–0.3 | < 0.2 | 0.3–0.55 | open |
| **drop** (吊球) | > 0.55 | 0.50–0.75 | < 0.35 | 0.15–0.3 | < 0.15 | < 0.40 | open |
| **smash** (杀球) | > 0.60 | > 0.75 | > 0.35 | > 0.2 | > 0.20 | > 0.55 | open |
| **lift** (挑球) | < 0.35 | 0.55–0.75 | 0.20–0.40 | > 0.30 | > 0.20 | 0.15–0.5 | open/square |
| **net** (网前球) | < 0.45 | < 0.65 | < 0.30 | > 0.30 | > 0.15 | < 0.35 | open |

## Decision tree order (photo mode, no speed data)

```
1. height < 0.45 AND shoulder_rot < 0.30 AND arm_horizontal AND open_stance → serve
2. height < 0.35 AND knee_bend > 0.30 AND arm_extension > 0.55           → lift
3. height < 0.45 AND knee_bend > 0.30                                     → net
4. height > 0.58 AND arm_extension > 0.75 AND (lean > 0.20 OR rot > 0.35) → smash
5. height > 0.58 AND arm_extension > 0.75 AND NOT(lean/rot)               → clear
6. height > 0.55 AND 0.50 ≤ arm_ext ≤ 0.75                                → drop
7. default                                                                 → clear (low conf)
```

## Decision tree order (video mode, with speed)

```
1. height < 0.45 AND rot < 0.25 AND speed < 0.4 AND open_stance → serve
2. height < 0.35 AND knee > 0.3 AND 0.15 ≤ speed ≤ 0.5          → lift
3. height < 0.45 AND knee > 0.3 AND speed < 0.35                → net
4. height > 0.60 AND arm_ext > 0.75 AND speed > 0.55            → smash
   (if lean > 0.25 → confident smash; if speed > 0.70 → smash regardless)
5. height > 0.62 AND arm_ext > 0.75                              → clear
6. height > 0.55 AND 0.50≤arm_ext≤0.78 AND speed < 0.40         → drop
7. height > 0.55 AND speed > 0.45                                → smash_fallback
8. height > 0.50                                                  → clear_fallback
9. height < 0.40 AND speed < 0.3                                 → net_fallback
10. knee > 0.3                                                   → lift_fallback
11. default                                                      → clear
```

# Ref: arm-horizontal detection for serve

A serve-specific feature: the arm (shoulder→wrist vector) extends roughly horizontally rather than up or down.

```python
# In pixel coords, if arm is 45° from horizontal or less:
arm_angle_to_ground = np.degrees(np.arctan2(abs(wrist.y - shoulder.y), abs(wrist.x - shoulder.x)))
# < 50° = roughly horizontal → serve potential
```

## Diagnosis per action type

| Action | Common flaws to diagnose |
|--------|-------------------------|
| serve | Too much rotation (> 0.3), wrist too fast (> 0.4) |
| smash | Low arm_ext (< 0.7), insufficient rotation (< 0.35), slow wrist (< 0.5) |
| clear | Low arm_ext (< 0.7), insufficient rotation (< 0.35) |
| drop | Low height (allow lower height than smash, < 0.55) |
| lift | Insufficient arm_ext (< 0.5), insufficient knee_bend (< 0.25) |
| net | Insufficient knee_bend (< 0.25) |

---

## Multi-photo progressive assessment (for skill grading features)

When the user uploads photos one by one over time to build a complete skill:

```python
# Per-user session state:
assessment_session = {
    "collected": {},       # { action_type: {stroke_event, score} }
    "remaining": [         # missing action types
        "serve", "clear", "drop", "smash", "lift", "net"
    ],
    "status": "incomplete"
}

# Rule: 6 actions must ALL be collected before a composite L1–L7 grade
if len(collected) == 6:
    result = SkillGrader().assess(list(collected.values()), source="multi_photo")
else:
    # Show progress bar + per-action scores only
    show(f"🟢 {collected.keys()} ✅ 还需要: {remaining}")
```

## Content validation (reject non-badminton before grading)

```python
def content_validation(image_path) -> dict:
    # Cascade: no person → no arm → low-confidence classify → unknown sport
    if no_person_detected:
        return {"valid": False, "reason": "🤔 没看到人呢"}
    action, conf = classify_single_frame(pose)
    if action == "unknown" and conf < 0.3:
        return {"valid": False, "reason": "不太确定这是什么运动"}
    return {"valid": True, "action": action, "confidence": conf}
```

## Multi-person pose detection (for doubles/team sports)

With the new `PoseLandmarker` API (mediapipe ≥0.10.20), multi-person is built in:

```python
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

options = vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="pose_landmarker_lite.task"),
    running_mode=vision.RunningMode.IMAGE,
)
detector = vision.PoseLandmarker.create_from_options(options)

result = detector.detect(mp_img)
# result.pose_landmarks is a list — one entry per detected person
for landmarks in result.pose_landmarks:
    rwrist_y = landmarks[16].y
    side = "right" if landmarks[16].y < landmarks[15].y else "left"
```

Note: unlike the legacy `mp.solutions.pose` API, `PoseLandmarker` output has
**no `.visibility`** field. All 33 landmarks are always returned with (x, y, z).
