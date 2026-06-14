# Multi-View 3D Skeleton Breakdown Rendering

Generate a 4-view training video from a single MediaPipe skeleton sequence, using z-axis depth to simulate multiple camera angles.

## Use case

A user uploads their photo → MimicMotion generates a face-swapped video of them doing a badminton stroke. They need to see the **same action from 4 angles** to understand the full motion. This module renders a 2×2 grid showing front, right-45°, right side, and right-rear views of their skeleton, phase-labeled and composited into a single training video.

## Algorithm

### Step 1: 3D skeleton from MediaPipe landmarks

MediaPipe Pose returns 33 landmarks with `(x, y, z, visibility)` where:
- `x, y` = normalized 0–1 image coordinates
- `z` = depth (negative = closer to camera, positive = farther)
- `z` range is approximately [-0.5, 0.5]

```python
# Convert to 2D canvas coordinates
cx, cy = lm[0] * W, lm[1] * H  # (x, y)
cz = lm[2] * D                   # z-depth scaled to pixels
```

### Step 2: 3D rotation for virtual camera angles

Treat each landmark as a 3D point `(cx − W/2, cy − H/2, cz)` centered at origin, rotate around the Y-axis, then project back.

```python
import numpy as np

def rotate_around_y(points_3d, angle_deg):
    """Rotate (N, 3) points around Y axis by angle_deg."""
    rad = np.radians(angle_deg)
    c, s = np.cos(rad), np.sin(rad)
    R = np.array([[c, 0, s],
                  [0, 1, 0],
                  [-s, 0, c]])
    return points_3d @ R.T

# Four camera angles
ANGLES = [
    ("Front", 0),
    ("Right-45°", 45),
    ("Right side", 90),
    ("Right-rear", 135),
]
```

For each angle:
1. `rotated = rotate_around_y(points_3d, angle)`
2. Project to 2D: `proj_x = rotated[:, 0] + W/2`, `proj_y = rotated[:, 1] + H/2`
3. Simulated perspective: multiply z-distance into scale: `scale = 1.0 + rotated[:, 2] * 0.3` then `proj_x = (rotated[:, 0] * scale) + W/2`
4. Clip to canvas bounds
5. Draw bones + joint circles on a 576×576 canvas

### Step 3: Bone connections (MediaPipe 33-keypoint topology)

```python
BONES = [
    (11, 12),   # shoulders (连接肩膀)
    (11, 13), (13, 15),  # left arm (左臂)
    (12, 14), (14, 16),  # right arm (右臂)
    (11, 23), (12, 24),  # torso (躯干)
    (23, 24),            # hips (髋部)
    (23, 25), (25, 27), (27, 29), (27, 31),  # left leg (左腿)
    (24, 26), (26, 28), (28, 30), (28, 32),  # right leg (右腿)
    (11, 0), (12, 0),    # neck to nose (脖子到头)
    (0, 1), (1, 2), (2, 3), (3, 7),     # face chain
    (0, 4), (4, 5), (5, 6), (6, 8),     # face chain
    (9, 10),                              # mouth
]
```

Drawing parameters:
- Canvas: 576×576 black background (BGR for OpenCV)
- Bone line: `(100, 200, 255)` (light blue), thickness 3
- Joint circle: `(255, 255, 255)` white, radius 4, filled
- Joints at `x < 0 or x > W or y < 0 or y > H` are still drawn at clip boundary (important for edge-of-frame views)

### Step 4: Phase auto-detection from right-wrist signal

Track the right wrist (landmark 16) y-coordinate over the sequence. The y-axis is inverted in image coordinates (0 = top, 1 = bottom), so "up" means lower y values and "down" means higher y values.

```python
def detect_phases(wrist_ys: np.ndarray) -> list[tuple[int, str]]:
    """Returns list of (frame_idx, phase_name) transitions."""

    # Smooth the signal
    from scipy.ndimage import gaussian_filter1d
    y = gaussian_filter1d(wrist_ys, sigma=1.0)

    # Find peaks (upward motion → local minima in y)
    # Smash stroke pattern: low→high→low→high
    # 准备 (Prep):    wrist rises from ready position
    # 引拍 (Backswing): wrist at highest position, starts descending
    # 击球 (Hit):     wrist at lowest position (contact point)
    # 随挥 (Follow-through): wrist rises again after contact

    # Signature for a smash: wrist starts mid, rises, falls, rises
    # Use slope + position thresholds

    # Simple heuristic:
    total = len(y)
    mid = total // 2
    quarter = total // 4

    # Find the lowest wrist point in the sequence (the "hit")
    hit_idx = np.argmax(y)  # lowest y value = highest on screen → wait, max of y (image coords)

    # Actually: in image coords, "high" = small y, "low" = large y
    # So the "swing down" is y increasing toward the bottom
    # The contact point is the local maximum of y (lowest on screen)

    if total < 4:
        return [(0, "准备")] * total

    # For a typical smash (right-handed):
    # 准备: wrist low (ready) → wrist rising (racket going up)
    # 引拍: wrist high (racket behind head)
    # 击球: wrist dropping fast, lowest point = contact
    # 随挥: wrist rising again (follow through across body)

    # Find the global maximum of y (= lowest point, i.e. the hit)
    peak_idx = np.argmax(y)

    # Find the local maximum before peak (= highest wrist in backswing)
    pre = y[:peak_idx]
    backswing_idx = np.argmin(pre) if len(pre) > 0 else 0

    # Find the local minimum after peak (= end of follow-through)
    post = y[peak_idx:]
    recovery_idx = peak_idx + np.argmin(post) if len(post) > 0 else total - 1

    phases = [
        (0, "准备"),
        (backswing_idx, "引拍"),
        (peak_idx, "击球"),
        (recovery_idx, "随挥"),
    ]
    return phases
```

The `gaussian_filter1d` smoothing is critical — raw wrist positions have frame-to-frame jitter that creates false phase boundaries.

### Step 5: 2×2 grid assembly

```python
def tile_4views(views: dict[str, np.ndarray]) -> np.ndarray:
    """
    views: {"Front": (576,576,3), "Right-45°": ..., "Right side": ..., "Right-rear": ...}
    Returns: (1152, 1152, 3) grid
    """
    top = np.hstack([views["Front"], views["Right-45°"]])
    bottom = np.hstack([views["Right side"], views["Right-rear"]])
    grid = np.vstack([top, bottom])
    return grid
```

Add phase label overlay as white text in the top-left corner of the grid:
```python
cv2.putText(grid, current_phase, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
            1.2, (255, 255, 255), 3, cv2.LINE_AA)
```

### Step 6: Encoding to MP4

**On headless Linux (AutoDL):** Use `imageio.get_writer(codec='libx264')` — OpenCV's `cv2.VideoWriter("mp4v")` produces corrupted green-screen video.

**On macOS:** Either works, but prefer `imageio` for consistency.

```python
import imageio
w = imageio.get_writer(output_path, fps=fps, codec='libx264', quality=8)
for frame in all_frames:
    w.append_data(frame)  # frame is numpy array (H, W, 3), uint8, BGR
w.close()
```

## Integration with composite pipeline

The breakdown video feeds into the composite pipeline (see `pose-guided-video-generation` skill). After generating this 1152×1152 4-view grid video:

1. Scale to 960×960 and pad to 960×1080 (keep aspect ratio)
2. Align with the corresponding MimicMotion frame (scaled to 960×1080)
3. `np.hstack([left_padded, right_padded])` → 1920×1080
4. Render all frames → final composite MP4

## Performance

- **Processing**: ~0.5ms per frame per camera view = ~2ms/frame total
- **72 frames × 4 views**: ~150ms rendering + ~100ms video encoding = ~250ms total
- **Runs on CPU** (no GPU needed)
- **Output size**: ~300KB for 72 frames (black background compresses well)

## Pitfalls

1. **z-axis scale mismatch**: MediaPipe z values are not metric-scale; they work for rotation but don't represent real depth. The `scale = 1.0 + z * 0.3` factor in projection is empirically tuned — use sparing adjustment.
2. **Extreme rotation angles** (135°+) can compress body width unnaturally on a 2D projection. 135° is the practical limit; skip 180° (back view) as the torso blocks arm visibility.
3. **Right-hand bias**: The 4 views assume the player is right-handed (right side = striking side). For left-handed players, mirror the angles or swap to left-side views.
4. **Phase detection fails with <4 frames**: Guard with `if total < 4: return [(0, "准备")]`.
5. **OpenCV font not on headless server**: `cv2.FONT_HERSHEY_SIMPLEX` is available on AutoDL, but verify by saving a test frame. Fallback: add text via PIL if OpenCV fails.
6. **Null frames**: If MimicMotion produces fewer frames than expected, pad with the last frame rather than crashing the composite loop.
