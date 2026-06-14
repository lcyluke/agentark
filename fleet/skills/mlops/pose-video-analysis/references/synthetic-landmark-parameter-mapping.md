# Synthetic Landmark Parameter Mapping Verification

## The problem

When testing ML feature-extraction functions (like `_classify_role`, `_position_z`, `_knee_bend`, `_shoulder_rot`, `_arm_extension`), the standard approach is to write a `make_landmarks()` helper that accepts human-readable parameters and builds the raw 33×4 MediaPipe landmark array.

**The hidden bug:** the helper's internal geometry may NOT produce the feature values the parameter names imply. You think you're testing the classifier, but you're really testing a doubly-unknown combination of (helper correctness × classifier correctness). A classifier can be **perfect** while the test reports "FAIL" because the helper built wrong data.

## The fix: verify parameter mapping before running tests

Before using synthetic landmarks in classifier tests, run a **parameter mapping verification** that isolates the helper → feature pipeline:

```python
# Step 1: for EACH parameter, test that make_landmarks(param=X) 
# produces the correct computed feature value via the REAL module functions
for expected_z in [0.1, 0.5, 0.9]:
    lm = make_landmarks(pos_z_val=expected_z)
    actual = _position_z(lm)           # use the REAL function
    assert abs(actual - expected_z) < 0.05

for expected_knee in [0.0, 0.3, 0.7, 1.0]:
    lm = make_landmarks(knee_val=expected_knee)
    actual = _knee_bend(lm, side)      # use the REAL function
    assert abs(actual - expected_knee) < 0.10

for expected_rot in [0.0, 0.3, 0.6]:
    lm = make_landmarks(rot_val=expected_rot)
    actual = _shoulder_rot(lm)         # use the REAL function
    assert abs(actual - expected_rot) < 0.05

for expected_ext in [0.0, 0.5, 0.85, 1.0]:
    lm = make_landmarks(arm_ext_val=expected_ext)
    actual = _arm_extension(lm, side)  # use the REAL function
    assert abs(actual - expected_ext) < 0.10
```

Every assertion must pass. If any fails, fix `make_landmarks` — the bug is in the helper, not the module.

## Anatomy of a well-mapped synthetic landmark builder

Each physical joint position in the 33×4 array must be computed from the parameter value using the **same formula the real feature extractor uses**, just inverted:

### Position Z → ankle z-depth

```python
# Real formula: _position_z = 1.0 - (ankle_z + 1.0) / 2.0
# Inverted: ankle_z = 1.0 - 2.0 * pos_z_val
ankle_z = 1.0 - 2.0 * pos_z_val
lm[27] = [cx - 0.03, ankle_y, ankle_z, 0.9]  # left ankle
lm[28] = [cx + 0.03, ankle_y, ankle_z, 0.9]  # right ankle
```

### Shoulder rotation → shoulder y-offset

```python
# Real formula: _shoulder_rot = degrees(atan2(dy, dx)) / 60
# where dx = |left_shoulder.x - right_shoulder.x|, dy = |.y - .y|
# Inverted: dy = dx * tan(rot_val * 60)
dx_shoulder = 2 * sw  # shoulder width pixel distance
rot_deg = min(rot_val * 60.0, 89.0)
dy_shoulder = dx_shoulder * np.tan(np.radians(rot_deg))

lm[11] = [cx - sw, cy - 0.08, z, 0.9]           # left shoulder
lm[12] = [cx + sw, cy - 0.08 + dy_shoulder, z, 0.9]  # right shoulder
```

### Knee bend → knee x-offset

```python
# Real formula: _knee_bend = clip((180 - angle(hip, knee, ankle)) / 70, 0, 1)
# For two equal leg segments of length s, knee at midpoint:
# bend angle θ = arccos((d² - s²) / (d² + s²)) where d = knee x-offset
# Inverted: d = s * sqrt((1 + cos(θ)) / (1 - cos(θ)))
# target_angle = 180 - 70 * knee_val → cos(target_angle)
half_y = leg_y_length / 2.0
target_angle = max(110.0, 180.0 - 70.0 * knee_val)
target_cos = np.cos(np.radians(target_angle))
d_sq = half_y**2 * (1.0 + target_cos) / (1.0 - target_cos)
knee_offset = np.sqrt(max(0, d_sq))
lm[26] = [cx + 0.04 + knee_offset, knee_y, z, 0.9]  # right knee
```

### Arm extension → elbow angle

```python
# Real formula: _arm_extension = angle(shoulder, elbow, wrist) / 180
# Inverted: place elbow and wrist so their computed angle = arm_ext_val * 180
arm_angle_deg = arm_ext_val * 180.0
bend_rad = np.radians(180.0 - arm_angle_deg)  # deviation from straight
arm_dir_rad = np.radians(-60)  # arm direction from shoulder

el_x = sh_x + upper_arm_len * np.cos(arm_dir_rad)
el_y = sh_y + upper_arm_len * np.sin(arm_dir_rad)
wr_x = el_x + forearm_len * np.cos(arm_dir_rad + bend_rad)
wr_y = el_y + forearm_len * np.sin(arm_dir_rad + bend_rad)

lm[14] = [el_x, el_y, z, 0.9]  # right elbow
lm[16] = [wr_x, wr_y, z, 0.9]  # right wrist
```

## Debugging checklist when a feature test fails

1. **Isolate**: run `make_landmarks(param=X)` and then the REAL feature function. Print both the parameter and the computed value.
2. **Print ALL intermediate values**: position_z, knee_bend, shoulder_rot, arm_extension, body_lean, racket_hand_up. Don't just look at the final classifier output.
3. **Identify which feature is wrong**: if `pos_z` is correct but `arm_ext` is off, you only need to fix the arm geometry.
4. **Test the feature function standalone**: pass raw landmarks manually (no helper) to verify the feature function itself is correct.
5. **Only fix the helper**, never change the real module to match a buggy helper. The test data must conform to the real code, not vice versa.

## Real example from badminton-coach-ai

In the `_uat_test.py` for `double_analyzer`, the original `make_landmarks` had 3 bugs:

| Parameter | Intended value | Actual computed | Root cause |
|-----------|---------------|----------------|------------|
| `rot_val=0.45` | rot=0.45 | rot=**0.0** | Shoulders only spread wider, no y-offset → no rotation angle |
| `arm_ext_val=0.85` | arm_ext=0.85 | arm_ext=**0.269** | Elbow angle computed as ~47°, not target 153° |
| `knee_val=0.15` | knee=0.15 | knee=**1.000** | Knee offset too large relative to leg segment length |

The fix was rebuilding each joint position to exactly invert the real feature function's formula. **The classifier was correct the entire time** — the test was wrong.

## Key principle

```
Test helper parameters → REAL feature functions → compared to expected values
```

Never skip the middle step. Never assume a parameter name maps correctly to the computed feature without verification.
