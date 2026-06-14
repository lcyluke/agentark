# Motion Templates — Landmark Reference & Per-Technique Signatures

## MediaPipe 33-Landmark Reference

Access pattern: `landmarks[index][axis]` where axis=0(x),1(y),2(z),3(visibility).

**Key indices for badminton analysis:**

| Index | Name | Use |
|:-----:|:-----|:----|
| 0 | Nose | Head position |
| 11 | Left shoulder | Stance width reference |
| 12 | Right shoulder | Stance width + arm origin |
| 14 | Right elbow | Elbow angle (racket arm) |
| 15 | Left wrist | Off-hand position |
| 16 | Right wrist | **Primary motion signal** (racket hand) |
| 23 | Left hip | Lower body reference |
| 24 | Right hip | Lower body reference |
| 25 | Left knee | Squat depth (left) |
| 26 | Right knee | **Primary squat depth** |
| 27 | Left ankle | Foot position (left) |
| 28 | Right ankle | Foot position (right) |

**Coordinate system:**
- Y-axis: 0.0 = top of frame, 1.0 = bottom
- Lower Y = higher physical position (arm raised above head = wrist_y ≈ 0.25)
- Higher Y = lower physical position (arm at waist = wrist_y ≈ 0.65)
- Higher knee Y = deeper squat (knee_y ≈ 0.70+)

## Per-Technique Motion Signatures

### 🖐️ 接杀挡网 (Defense Block)
- Stance: moderate, shoulder_y ≈ 0.46
- Knee: slight bend, knee_y ≈ 0.60
- Arm: extended forward, wrist_y ≈ 0.47, elbow near straight (~50°)
- Motion range: small wrist movement (range ≈ 0.28)
- Key indicator: elbow_angle > 45° (arm extended, not flexed)

### 🔝 接杀低挑 (Defense Lob)
- Stance: moderate, shoulder_y ≈ 0.47
- Knee: **deep bend**, knee_y ≈ 0.68 → 0.74 peak
- Arm: **flexed then whip**, elbow ≈ 33° at moment of strike
- Motion range: moderate wrist movement (range ≈ 0.20)
- Key indicator: knee_y > 0.65 AND wrist_range < 0.25

### ⚡ 接杀反击 (Defense Counter)
- Stance: dynamic, shoulder_y ≈ 0.46
- Knee: deep at start (0.67), rapid extension
- Arm: **fast raise**, wrist_y ≈ 0.33 at peak (highest arm)
- Motion range: large wrist movement (range ≈ 0.30)
- Key indicator: wrist_y dips below 0.35 AND rapid knee extension

## Action Segmentation Algorithm

To auto-detect which moves a video contains:

```python
def segment_actions(skeleton):
    """Segment (T,33,4) skeleton into labeled action chunks."""
    wrist_y = skeleton[:, 16, 1]
    knee_y = skeleton[:, 26, 1]
    elbow_angles = compute_elbow_angles(skeleton)

    segments = []
    window = 30  # ~1 second at 30fps

    for t in range(0, len(skeleton) - window, window // 2):
        w_mean = float(wrist_y[t:t+window].mean())
        k_mean = float(knee_y[t:t+window].mean())
        w_range = float(wrist_y[t:t+window].max() - wrist_y[t:t+window].min())
        e_mean = float(np.mean(elbow_angles[t:t+window]))

        # Classification rules
        if k_mean > 0.65 and w_range < 0.25:
            label = "defense_lob"    # Deep squat + controlled wrist
        elif w_mean < 0.40:
            label = "defense_counter" # High arm position
        elif e_mean > 45:
            label = "defense_block"  # Extended elbow
        else:
            label = "unknown"

        segments.append((t, t+window, label))

    return segments
```

## DTW Feature Selection

For badminton motion comparison, the 3-feature vector (hip_y, wrist_y, shoulder_y)
outperforms full 33×3 point matching because:
1. Hockey-stick invariant — racket presence doesn't matter
2. Height invariant — normalized to body proportions
3. Computationally cheap — O(T²) on 3-dim, not 99-dim

The cost function should use normalized Euclidean distance to account for
different body proportions between user and benchmark.
