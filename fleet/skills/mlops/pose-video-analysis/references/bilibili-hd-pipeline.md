# Bing (B站) High-Quality Video Pipeline for Pose Training

Covers the end-to-end pipeline: B站 HD source discovery → download → clip extraction → skeleton tracking on 720p/4K footage. Built for building a training dataset for badminton stroke analysis.

## Source discovery & quality assessment

### B站 video quality tiers for pose analysis

| Resolution | Label | Human Size (720p frame) | Joint Accuracy | Suitable For |
|:----------:|:-----:|:-----------------------:|:--------------:|:------------|
| **3840×2160** (4K) | ★★★★★ | ~500px | ≤2° error | Training data gold standard, need ~3-5s/clip processing |
| **1280×720** (720p) | ★★★★☆ | ~300px | ≤5° error | Good enough for production model training, ~1-2s/clip |
| **852×480** (480p) | ★★★☆☆ | ~200px | ≤8° error | OK for supplementary data |
| **640×360** (360p) | ★★☆☆☆ | ~120px | ≤15° error | **Too low** — unreliable joint angles |

### Quick quality check (ffprobe)

```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate,duration -of csv=p=0 video.mp4
# Output: 1280,720,25/1,330.086000  →  1280×720 @ 25fps, 330s
```

### Horizontal vs vertical detection

B站 has many vertical (phone-uploaded) videos. Quick check:
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 video.mp4
# width > height → 横版 (horizontal, good for pose)
# height > width → 竖版 (vertical, not ideal — body cut off)
```

## Cookie-based HD download

### Firefox cookies (preferred method — verified working on macOS 15)

```python
# Extract B站 cookies from Firefox
import browser_cookie3
cj = browser_cookie3.firefox(domain_name='.bilibili.com')
bili_cookies = {c.name: c.value for c in cj}
has_login = all(k in bili_cookies for k in ['SESSDATA', 'bili_jct', 'DedeUserID'])
print(f'B站 cookies: {len(bili_cookies)} total, login: {has_login}')

# Save as Netscape cookie file for yt-dlp
cookie_lines = ["# Netscape HTTP Cookie File"]
for c in cj:
    domain = ".bilibili.com"
    secure = "TRUE" if c.secure else "FALSE"
    cookie_lines.append(f"{domain}\tTRUE\t/\t{secure}\t{int(c.expires) if c.expires else 0}\t{c.name}\t{c.value}")
with open("bilibili_cookies.txt", "w") as f:
    f.write("\n".join(cookie_lines))
```

### Chrome cookies (does NOT work for B站 login — HttpOnly cookies encrypted)

Chrome stores SESSDATA/bili_jct/DedeUserID in encrypted format that `browser_cookie3` cannot read. Only non-login cookies (buvid3, buvid4) are available. Firefox is the only automated option.

## Download command

```bash
# For 720p (most B站 HD videos):
yt-dlp --cookies-from-browser firefox \
  -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  -o "output.mp4" "B站URL或BV号"

# For 4K video:
yt-dlp --cookies-from-browser firefox \
  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best" \
  -o "output.mp4" "B站URL或BV号"

# Download entire channel playlist:
yt-dlp --cookies-from-browser firefox \
  -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  -o "channel/%(title)s.%(ext)s" \
  "https://space.bilibili.com/<MID>/video"
```

## Action clip extraction (scene + silence pipeline)

Adapt the `p0_pipeline_v2.py` approach for B站 content. B站 teaching videos differ from YouTube in pacing and format:

### Key parameter adjustments for B站

```python
SCENE_THRESHOLD = 0.12        # Lower than YouTube (0.15) — B站慢动作镜头过渡更平滑
SILENCE_THRESHOLD = "-30dB"
MIN_SILENCE = 0.3              # Shorter silence threshold — 慢动作间停顿短
MIN_CLIP = 2                   # B站慢动作片段可能很短
MAX_CLIP = 45                  # 纯动作片段上限
MAX_TALK_CLIP = 120            # 讲解段上限
```

### Full pipeline script shape

```python
import json, subprocess, re
from pathlib import Path

RAW_DIR = Path("data/raw_videos/bilibili")
OUTPUT_DIR = Path("data/processed_videos/bilibili")

def detect_scenes(path):
    # ffmpeg scene detection at 0.12 threshold
    ...

def detect_silence(path):
    # ffmpeg silencedetect at -30dB / 0.3s
    ...

def classify_segment(start, end):
    dur = end - start
    if dur < MIN_CLIP: return "too_short"
    if dur <= MAX_CLIP: return "action_demo"
    if dur <= MAX_TALK_CLIP: return "talking"
    return "oversized"

# Pipeline: merge scene + silence boundaries → merge tiny gaps → classify → extract action clips
```

## Batch skeleton tracking on B站 footage

### Performance characteristics by resolution

| Resolution | Per-frame processing | 100-frame clip | Perceived speed |
|:----------:|:-------------------:|:--------------:|:---------------:|
| **3840×2160** (4K) | ~15ms/frame | ~3-5s | ~2× slower than 720p |
| **1280×720** (720p) | ~8ms/frame | ~1-2s | Fast |
| **640×360** (360p) | ~5ms/frame | ~0.5-1s | Fastest (but bad quality) |

### Expected tracking rates by resolution

| Resolution | Track Rate | Notes |
|:----------:|:----------:|:------|
| 3840×2160 | **99.8%** | Near-perfect — full body detail, ball/racket visible |
| 1280×720 | **~99%** | Excellent — all joints trackable |
| 640×360 | **98%** | Good stats but high joint angle error (±15°) |

### Batch processing command

```bash
cd ~/path/to/label-system
python3 scripts/skeleton_pipeline.py
```

The pipeline:
1. Scans `data/processed_videos/bilibili/` for `*_demo*.mp4` clips
2. Processes each with a shared `PoseLandmarker` instance (VIDEO mode)
3. Uses **global monotonically increasing timestamps** across all clips
4. Saves JSON: `{fps, total_frames, tracked_frames, track_rate, frames: [{f, lms: [[x,y,z,v],...]}]}`
5. Progress tracked in `data/skeletons/_progress.json`

### Skeleton JSON schema

```json
{
  "fps": 25.0,
  "total_frames": 947,
  "tracked_frames": 945,
  "track_rate": 0.998,
  "video": "flash_backhand_demo001_21s",
  "frames": [
    {"f": 0, "lms": [[0.341, 0.428, -0.111, 1.0], ...]},
    {"f": 1, "lms": [[0.342, 0.427, -0.112, 1.0], ...]}
  ]
}
```

## Quality verification

After processing, verify per-video tracking stats:

```bash
python3 -c "
import json, glob
for f in sorted(glob.glob('data/skeletons/bilibili/**/*.json', recursive=True)):
    d = json.load(open(f))
    print(f'{Path(f).name:<50} | {d[\"total_frames\"]:>4}f | {d[\"tracked_frames\"]:>4}f跟踪 | {d[\"track_rate\"]*100:.1f}%')
"
```

## Pitfalls

1. **B站 4K videos are HUGE**: A 6.5-minute 4K video is ~432MB vs ~17MB for the same content at 720p. Use 4K only for critical training data.
2. **B站 rate limiting**: Downloading multiple videos in quick succession may trigger captcha. Use `--sleep-interval 5` with yt-dlp or batch downloads via a script with delays.
3. **No audio track on shadow_slowmo series**: These are pure slow-motion videos with no audio. The silence-based clip extraction won't detect their boundaries — rely on scene detection alone.
4. **Cookie expiry**: B站 cookies expire ~6 months after extraction. Check `bili_jct` and `SESSDATA` expiry dates when saving. If downloads start returning 360p, re-extract cookies from Firefox.
5. **Old 360p data contamination**: If retraining a model, ensure old 360p skeleton data is excluded from the training set when replacing with 720p/4K data. Keep separate directories or version-tag the data.
