# 16-Dimension Annotation Engine — Algorithm Reference

Detailed implementations for each of the 16 annotation dimensions.
These are reference implementations — copy, adapt, and calibrate to your sport.

## Data Format

Input: `np.ndarray` of shape `(N, 15, 3)` where:
- N = number of frames
- 15 = landmark indices: [0(nose), 7(left_ear), 8(right_ear), 11(left_shoulder), 12(right_shoulder), 13(left_elbow), 14(right_elbow), 15(left_wrist), 16(right_wrist), 23(left_hip), 24(right_hip), 25(left_knee), 26(right_knee), 27(left_ankle), 28(right_ankle)]
- 3 = (x, y, z) in normalized coordinates [0,1]

## Index map

```python
IDX = {
    "nose": 0, "left_ear": 1, "right_ear": 2,
    "left_shoulder": 3, "right_shoulder": 4,
    "left_elbow": 5, "right_elbow": 6,
    "left_wrist": 7, "right_wrist": 8,
    "left_hip": 9, "right_hip": 10,
    "left_knee": 11, "right_knee": 12,
    "left_ankle": 13, "right_ankle": 14,
}
```

## A1-A6: Joint Angle Computation

```python
def _get_side_indices(side: str) -> dict:
    """Get racket-side joint indices"""
    if side == "right":
        return {"shoulder": IDX["right_shoulder"], "elbow": IDX["right_elbow"],
                "wrist": IDX["right_wrist"], "hip": IDX["right_hip"],
                "knee": IDX["right_knee"], "ankle": IDX["right_ankle"],
                "o_shoulder": IDX["left_shoulder"], "o_hip": IDX["left_hip"]}
    else:
        return {"shoulder": IDX["left_shoulder"], ...}

def _angle(a, b, c) -> float:
    """Three-point angle in degrees"""
    v1 = a - b
    v2 = c - b
    cos = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-8)
    return float(np.degrees(np.arccos(np.clip(cos, -1.0, 1.0))))

def compute_joint_angles(landmarks_seq, side):
    """Per-frame 6-angle computation"""
    sidx = _get_side_indices(side)
    angles = {"elbow": [], "shoulder": [], "knee": [], "hip": [], "waist_twist": [], "wrist": []}
    
    for f in range(len(landmarks_seq)):
        lm = landmarks_seq[f]
        
        # A1: Elbow angle
        if not nan_any(lm[[sidx["shoulder"], sidx["elbow"], sidx["wrist"]]]):
            angles["elbow"].append(_angle(lm[sidx["shoulder"]], lm[sidx["elbow"]], lm[sidx["wrist"]]))
        
        # A2: Shoulder angle
        if not nan_any(lm[[sidx["elbow"], sidx["shoulder"], sidx["hip"]]]):
            angles["shoulder"].append(_angle(lm[sidx["elbow"]], lm[sidx["shoulder"]], lm[sidx["hip"]]))
        
        # A3: Knee angle
        if not nan_any(lm[[sidx["hip"], sidx["knee"], sidx["ankle"]]]):
            angles["knee"].append(_angle(lm[sidx["hip"]], lm[sidx["knee"]], lm[sidx["ankle"]]))
        
        # A4: Hip angle
        if not nan_any(lm[[sidx["shoulder"], sidx["hip"], sidx["knee"]]]):
            angles["hip"].append(_angle(lm[sidx["shoulder"]], lm[sidx["hip"]], lm[sidx["knee"]]))
        
        # A5: Waist twist (shoulder-line vs hip-line angle difference)
        if not nan_any(lm[[sidx["o_shoulder"], sidx["shoulder"], sidx["o_hip"], sidx["hip"]]]):
            s_vec = lm[sidx["shoulder"]][:2] - lm[sidx["o_shoulder"]][:2]
            h_vec = lm[sidx["hip"]][:2] - lm[sidx["o_hip"]][:2]
            s_angle = np.arctan2(s_vec[1], s_vec[0])
            h_angle = np.arctan2(h_vec[1], h_vec[0])
            twist = np.degrees(s_angle - h_angle)
            if twist > 90: twist -= 180
            if twist < -90: twist += 180
            angles["waist_twist"].append(round(twist, 1))
        
        # A6: Wrist angle (simplified — needs hand landmarks for accuracy)
        angles["wrist"].append(10.0)  # default neutral value
    
    # Aggregate to statistics
    result = {}
    for name, values in angles.items():
        if values:
            arr = np.array(values)
            result[name] = {
                "mean": round(float(np.mean(arr)), 1),
                "std": round(float(np.std(arr)), 1),
                "max": round(float(np.max(arr)), 1),
                "min": round(float(np.min(arr)), 1),
                "values": [round(v, 1) for v in arr],  # full sequence for phase detection
            }
        else:
            result[name] = {"mean": 0, "std": 0, "max": 0, "min": 0, "values": []}
    return result
```

## P1: Power Timing

```python
def compute_power_timing(angle_results, phases):
    """Power timing [lower_body, core, upper_arm, wrist] — each in [0,1]"""
    n_frames = max(len(angle_results.get("knee", {}).get("values", [])), 1)
    
    velocity_peaks = {}
    for joint in ["knee", "hip", "shoulder", "elbow", "wrist"]:
        series = np.array(angle_results.get(joint, {}).get("values", []))
        if len(series) > 3:
            vel = np.abs(np.gradient(series))
            velocity_peaks[joint] = int(np.argmax(vel)) / n_frames
        else:
            velocity_peaks[joint] = 0.5
    
    lower = velocity_peaks.get("knee", 0.3) * 0.6 + velocity_peaks.get("hip", 0.5) * 0.4
    core = velocity_peaks.get("hip", 0.5)
    upper = (velocity_peaks.get("shoulder", 0.6) + velocity_peaks.get("elbow", 0.7)) / 2
    wrist = velocity_peaks.get("wrist", 0.8)
    
    # Ensure ascending order
    timing = [lower, core, upper, wrist]
    for i in range(1, 4):
        if timing[i] < timing[i-1]:
            timing[i] = timing[i-1] + 0.01
    
    return [round(float(t), 3) for t in timing]
```

## P2: Explosive Power

```python
def compute_explosive_power(landmarks_seq, side, phases):
    """Explosive power via wrist acceleration in normalized space"""
    sidx = _get_side_indices("right")  # or from side parameter
    wrist_pos = landmarks_seq[:, sidx["wrist"], :2]
    
    # CRITICAL: Remove NaN before derivative computation
    valid = ~np.any(np.isnan(wrist_pos), axis=1)
    if np.sum(valid) < 5: return 50.0
    wrist_valid = wrist_pos[valid]
    
    diffs = np.diff(wrist_valid, axis=0)
    velocities = np.linalg.norm(diffs, axis=1)
    if len(velocities) < 3: return 50.0
    
    accelerations = np.abs(np.diff(velocities))
    
    impact_frame = phases.get("impact_frame", int(len(accelerations) * 0.6))
    if impact_frame >= len(accelerations): impact_frame = len(accelerations) - 1
    
    pre_impact = accelerations[:impact_frame + 1]
    if len(pre_impact) == 0: return 50.0
    
    max_accel = float(np.max(pre_impact))
    if max_accel <= 0: return 50.0
    
    # Normalized coord scale: max_accel ≈ 0.1-1.0
    score = min(100, max(0, max_accel * 15))
    return round(score, 1)
```

## P3: Relaxation Score

```python
def compute_relaxation_score(landmarks_seq, side, phases):
    """Relaxation via jerk (d³p/dt³) in backswing phase — lower jerk = more relaxed"""
    sidx = _get_side_indices(side)
    
    backswing_start, backswing_end = phases.get("backswing_frames", [0, 0])
    if backswing_end <= backswing_start: return 50.0
    
    segment = landmarks_seq[backswing_start:backswing_end + 1, sidx["wrist"], :2]
    if len(segment) < 10: return 50.0
    
    valid = ~np.any(np.isnan(segment), axis=1)
    if np.sum(valid) < 8: return 50.0
    pts = segment[valid]
    
    v = np.diff(pts, axis=0)
    if len(v) < 3: return 50.0
    v_mag = np.linalg.norm(v, axis=1)
    
    a = np.diff(v_mag)
    if len(a) < 2: return 50.0
    
    j = np.abs(np.diff(a))
    if len(j) == 0: return 50.0
    
    mean_jerk = float(np.mean(j))
    # Normalized coord: very relaxed <0.01, normal 0.01-0.05, tense >0.05
    score = max(0, min(100, 100 - mean_jerk * 500))
    return round(score, 1)
```

## P4: Jump Height

```python
def compute_jump_height(landmarks_seq):
    """Jump height via hip center y-coordinate change, with baseline correction"""
    hip_center = np.mean([landmarks_seq[:, IDX["left_hip"]], landmarks_seq[:, IDX["right_hip"]]], axis=0)
    y_series = hip_center[:, 1]
    
    # Must distinguish weight-shift from actual jump
    valid_mask = ~np.any(np.isnan(hip_center), axis=1)
    if np.sum(valid_mask) < 10: return {"jump_height_cm": 0, "has_jump": False}
    
    y_valid = y_series[valid_mask]
    window = 5
    y_smooth = np.convolve(y_valid, np.ones(window)/window, mode='same')
    
    baseline = float(np.median(y_smooth[:10])) if len(y_smooth) > 10 else float(y_smooth[0])
    y_diff = baseline - y_smooth
    
    above_baseline = np.where(y_diff > 0.02)[0]
    if len(above_baseline) < 3:
        # No jump — use raw range as approximation
        pixel_jump = float(np.max(y_valid) - np.min(y_valid))
    else:
        peak_idx = above_baseline[np.argmax(y_diff[above_baseline])]
        pre_range = y_smooth[:peak_idx]
        dip_idx = np.argmax(pre_range) if len(pre_range) > 5 else 0
        takeoff_y = float(pre_range[dip_idx]) if len(pre_range) > 5 else float(baseline)
        peak_y = float(y_smooth[peak_idx])
        pixel_jump = takeoff_y - peak_y
    
    # Pixel-to-cm via torso-length ratio
    shoulder_center = np.mean([landmarks_seq[0, IDX["left_shoulder"]], landmarks_seq[0, IDX["right_shoulder"]]], axis=0)
    torso_pixels = float(np.linalg.norm(shoulder_center[:2] - hip_center[0][:2]))
    ratio = 50.0 / (torso_pixels if 0.05 < torso_pixels < 0.5 else 0.15)
    
    height_cm = round(pixel_jump * ratio, 1)
    height_cm = round(height_cm * 0.3, 1) if height_cm > 60 else height_cm  # cap correction
    
    return {"jump_height_cm": height_cm, "has_jump": 3.0 < height_cm < 60.0}
```

## P5: Chain Efficiency

```python
def compute_chain_efficiency(angle_results):
    """Evaluate timing correctness + energy transfer across 5 joints"""
    joints = ["knee", "hip", "shoulder", "elbow", "wrist"]
    
    velocities = {}
    for j in joints:
        series = np.array(angle_results.get(j, {}).get("values", []))
        velocities[j] = np.abs(np.gradient(series)) if len(series) > 3 else np.zeros(10)
    
    peak_times = {j: int(np.argmax(velocities[j])) for j in joints}
    peak_values = {j: float(np.max(velocities[j])) for j in joints}
    
    # Timing score: correct sequential order
    timing_correct = sum(1 for i in range(len(joints)-1) if peak_times[joints[i]] < peak_times[joints[i+1]])
    timing_score = timing_correct / (len(joints) - 1)
    
    # Energy score: sufficient transfer between adjacent joints
    energy_correct = sum(1 for i in range(len(joints)-1) if peak_values[joints[i+1]] >= peak_values[joints[i]] * 0.5)
    energy_score = energy_correct / (len(joints) - 1)
    
    return round((timing_score * 0.6 + energy_score * 0.4) * 100, 1)
```

## Body Part Analysis (B1, B2)

Foot analysis and palm/grip analysis are underdeveloped in the current implementation. They work as placeholders:

- **Foot landing type**: Use ankle y-coordinate relative to the foot tip at impact frame. If foot_tip.y > ankle.y → forefoot landing. Heel-first landings are detectable when ankle drops faster than foot-tip.
- **Grip tension**: Use angular micro-vibrations of the wrist during backswing (same signal as relaxation, but only the high-frequency component). Std of direction-change angles < 10° = relaxed grip, > 30° = tense grip.

These need side-view or foot-level video for accuracy, which standard 45° camera setups don't provide well.

## Grade Level Estimation (L1-L9)

```python
def estimate_grade(metrics: dict) -> int:
    """Weighted score → L1-L9"""
    score = (metrics.get("chain_efficiency", 50) * 0.3
             + metrics.get("explosive_power", 50) * 0.3
             + metrics.get("relaxation", 50) * 0.2
             + min(100, metrics.get("jump_height", 0) * 2.5) * 0.2)
    
    if score < 15: return 1
    if score < 25: return 2
    if score < 35: return 3
    if score < 45: return 4
    if score < 55: return 5
    if score < 65: return 6
    if score < 75: return 7
    if score < 85: return 8
    return 9
```

This is an INITIAL heuristic — calibrate against real coach ratings after you have 50+ annotated samples.
