# Composite Training Video Pipeline

Combine 4-view skeleton breakdown + MimicMotion face-swapped video into a single side-by-side training video (1920×1080).

## Architecture

```
Inputs:
  ├── MimicMotion output:  1024×576 MP4 (face-swapped real video, your face)
  └── breakdown_renderer:  1152×1152 MP4 (4-view skeleton grid)

Pipeline:
  1. Read both videos frame-by-frame, align frame count
  2. Scale breakdown grid: 1152→960 (maintain aspect), pad to 960×1080
  3. Scale MimicMotion: 1024×576 → 960×1080 (stretch + letterbox, or center crop)
  4. np.hstack([left, right]) → 1920×1080
  5. Overlay phase labels on left panel
  6. Write to output MP4
```

## Implementation

```python
import cv2, numpy as np, imageio
from pathlib import Path

def composite_training_video(
    mimic_path: str,          # Path to MimicMotion output MP4
    breakdown_path: str,      # Path to breakdown_renderer output MP4
    output_path: str,         # Output MP4 path
    phases: list[str],        # Phase labels per frame index
    fps: int = 8,
) -> str:
    """
    Side-by-side composite: left=4-view skeleton, right=face-swapped real video.
    Returns output path.
    """
    cap_m = cv2.VideoCapture(mimic_path)
    cap_b = cv2.VideoCapture(breakdown_path)
    writer = imageio.get_writer(output_path, fps=fps, codec='libx264', quality=8)
    frame_idx = 0
    while True:
        ret_m, frame_m = cap_m.read()
        ret_b, frame_b = cap_b.read()
        if not ret_m or not ret_b:
            break
        # frame_m is BGR uint8, (576, 1024, 3)
        # frame_b is BGR uint8, (1152, 1152, 3)
        # Scale left (breakdown) to 960 height
        scale = 960 / frame_b.shape[0]
        new_w = int(frame_b.shape[1] * scale)
        left = cv2.resize(frame_b, (new_w, 960))
        # Center-crop width to 960
        if new_w > 960:
            offset = (new_w - 960) // 2
            left = left[:, offset:offset+960]
        elif new_w < 960:
            pad = (960 - new_w) // 2
            left = cv2.copyMakeBorder(left, 0, 0, pad, 960-new_w-pad,
                                       cv2.BORDER_CONSTANT, value=[0, 0, 0])
        # Add phase label
        phase = phases[min(frame_idx, len(phases)-1)] if phases else ""
        cv2.putText(left, phase, (20, 40), cv2.FONT_HERSHEY_SIMPLEX,
                    1.0, (255, 255, 255), 2, cv2.LINE_AA)
        # Scale right (MimicMotion) to 960 height
        scale_r = 960 / frame_m.shape[0]
        new_w_r = int(frame_m.shape[1] * scale_r)
        right = cv2.resize(frame_m, (new_w_r, 960))
        if new_w_r > 960:
            offset_r = (new_w_r - 960) // 2
            right = right[:, offset_r:offset_r+960]
        elif new_w_r < 960:
            pad_r = (960 - new_w_r) // 2
            right = cv2.copyMakeBorder(right, 0, 0, pad_r, 960-new_w_r-pad_r,
                                        cv2.BORDER_CONSTANT, value=[0, 0, 0])
        # Composite
        combined = np.hstack([left, right])  # (960, 1920, 3)
        writer.append_data(combined)
        frame_idx += 1
    cap_m.release()
    cap_b.release()
    writer.close()
    return output_path
```

## Handling frame count mismatch

MimicMotion and breakdown_renderer may produce different frame counts:
```python
# Pad shorter video with its last frame
max_frames = max(len(mimic_frames), len(breakdown_frames))
while len(mimic_frames) < max_frames:
    mimic_frames.append(mimic_frames[-1])
while len(breakdown_frames) < max_frames:
    breakdown_frames.append(breakdown_frames[-1])
```

## Phase label generation

```python
def phase_labels_for_frames(total_frames: int, phase_transitions: list[tuple[int, str]]) -> list[str]:
    """Convert phase transitions to per-frame label list."""
    labels = [""] * total_frames
    for i in range(total_frames):
        current = "准备"
        for trans_idx, trans_name in sorted(phase_transitions):
            if i >= trans_idx:
                current = trans_name
        labels[i] = current
    return labels
```

## Verification

Always save a verification frame:
```python
Image.fromarray(combined[..., ::-1]).save("verify_frame.png")
# Check: mean > 30 (not all black) and < 250 (not all white)
# Check: both left and right halves visible
```

## Performance

- Frame-by-frame OpenCV read + resize: ~30ms/frame for 72 frames → ~2.5s
- imageio write: ~0.5s
- Total: ~3s per video on any CPU
