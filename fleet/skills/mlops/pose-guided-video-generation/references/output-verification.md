# Output Verification Protocol for Pose-Guided Video Generation

Verified through 25-video batch failure (2026-06-03) and subsequent analysis.

## Frame Analysis Script

Always run this after generating ANY single video or before a batch completes:

```python
import cv2, numpy as np, os

def verify_frame(frame_path: str) -> dict:
    """
    Analyze a single frame PNG. Save frames[0].png alongside every MP4 output.
    
    Returns dict with verdict: 'human', 'skeleton', 'empty', 'dark'
    """
    img = cv2.imread(frame_path)
    if img is None:
        return {"verdict": "empty", "error": "cannot read"}
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    b, g, r = cv2.split(img)
    
    brightness = gray.mean()
    unique_colors = len(np.unique(img.reshape(-1, 3), axis=0))
    blue_bias = (b > r + 30).sum() / img.size * 100
    skin = ((r > 80) & (r < 220) & (g > 50) & (g < 180) & 
            (b < r) & (r - b > 20)).sum() / img.size * 100
    edges = cv2.Canny(gray, 30, 100).sum() / 255 / gray.size * 100
    dark_pixels = (gray < 10).sum() / gray.size * 100
    
    print(f"  Brightness:  {brightness:.0f}")
    print(f"  Unique cols: {unique_colors}")
    print(f"  Blue bias:   {blue_bias:.0f}%")
    print(f"  Skin:        {skin:.1f}%")
    print(f"  Edges:       {edges:.1f}%")
    print(f"  Dark pixels: {dark_pixels:.0f}%")
    
    result = {
        "brightness": brightness,
        "unique_colors": unique_colors,
        "blue_bias_pct": blue_bias,
        "skin_pct": skin,
        "edge_pct": edges,
        "dark_pct": dark_pixels,
    }
    
    if skin > 3 and blue_bias < 15 and edges > 5:
        result["verdict"] = "human"
        print("  ✅ HUMAN — real person video")
    elif blue_bias > 30 and edges > 10:
        result["verdict"] = "skeleton"
        print("  ❌ SKELETON RENDER — pipeline needs fixing")
    elif brightness < 30 or edges < 3:
        result["verdict"] = "empty/noise"
        print("  ❌ EMPTY/NOISE — model generated nothing")
    else:
        result["verdict"] = "ambiguous"
        print("  ⚠ AMBIGUOUS — check manually")
    
    return result
```

## Known-good Thresholds (Real Human Video)

| Metric | Good (Human) | Skeleton Render | Empty/Failure |
|:-------|:------------:|:---------------:|:-------------:|
| Brightness | 100-220 | 60-100 | <30 |
| Unique colors | >5000 | 1000-5000 | <500 |
| Blue bias (B>R+30) | <15% | **>30%** (key indicator) | <10% |
| Skin tone | **>3%** | <1% | <0.5% |
| Edge density | >5% | >10% | <3% |
| R-channel mean | >80 | <70 (B dominates) | any |

## Quick Batch Verification

```bash
# For a batch of videos, check the first frame of each
for f in output/demo/*.mp4; do
  name=$(basename "$f")
  ffmpeg -y -i "$f" -vframes 1 "/tmp/verify/${name}.png" 2>/dev/null
  python3 -c "
import cv2, numpy as np
img = cv2.imread('/tmp/verify/${name}.png')
if img is None: exit()
g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
b,_,r = cv2.split(img)
blue = (b > r+30).sum()/img.size*100
print(f'${name}: brightness={g.mean():.0f} blue_bias={blue:.0f}%')
if blue > 30: print('  -> SKELETON!')
else: print('  -> OK')
"
done
```

## Debugging Failures

| Symptom | Likely Cause | Fix |
|:--------|:-------------|:----|
| `blue_bias > 30%` | Missing `noise_aug_strength=0` or `min_guidance_scale` | Add both params to pipeline call |
| All black (brightness <10) | Reference photo not loaded | Check `Image.open()` path |
| Green/glitched video, correct file size | `cv2.VideoWriter(*"mp4v")` on headless Linux | Use `imageio.get_writer(codec='libx264')` |
| Low brightness on skeleton side only | Skeleton render default too dark | Apply `eq=brightness=0.15:contrast=1.2` filter |
| Animation flickers between frames | No temporal attention or high guidance | Reduce `max_guidance_scale` to 2.0 |
