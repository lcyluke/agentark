---
name: training-animation-generation
description: "Training animations for sports skills: real video sourcing (yt-dlp batch download + ffmpeg slice), batch slicing into individual skill clips, plus MediaPipe skeleton animation fallback."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [animation, mediapipe, gif, mp4, training, sports-tech]
    related_skills: [wechat-miniprogram-testing, systematic-debugging]
---

# Training Animation Generation

## Overview

Generate training animations for sports skill assessment platforms (羽球宝AI搭子). Output is used inside WeChat mini-programs, web apps, or mobile apps as visual training guides.

## Core Principle

**NEVER use hand-crafted keyframe animation.** Hand-defined skeleton positions (even with interpolation) produce stiff, unrealistic motion that users will immediately reject. Real athletes do not move like keyframed puppets.

**User's priority order for training demo videos:**
1. 🥇 **Real pro/coach action footage** — pure action, no talking, 20-30s clips
2. 🥈 **MediaPipe skeleton animation** (extracted from real video) — fallback
3. ❌❌ **Hand-crafted keyframe animation** — never acceptable

**Key user requirements (老卢):**
- Videos must be **pure action demonstration only** — no talking, no blank intro screens, no lecture sections
- Each clip should jump straight to the player performing the motion (20-45 seconds)
- Users prefer seeing real players (球员) performing the skill vs skeleton animations
- Videos must be repeatable (短片段适合重复观看)
- Size per clip: 350KB-1.5MB MP4 (suitable for WeChat/mobile delivery)

### Preferred approach: Batch real video sourcing + ffmpeg slicing

**The most efficient strategy for producing 51 skill clips is NOT to find 51 individual videos. Instead:**
1. Find ~8-10 high-quality instructional **合集** videos (covering multiple skills each)
2. Download all in parallel via yt-dlp
3. Batch-slice each into 20-30s individual clips via ffmpeg
4. Name per the skill_id naming convention

This was proven in production: 9 YouTube tutorial videos → 63 individual MP4 clips in ~15 minutes of processing time. See "Batch Slicing" below.

## CRITICAL LIMITATION: Teaching videos produce mostly <5s fragments

**实测数据（2026-06-01，1,887 clips审计）：**

| 源类型 | clip数 | 平均时长 | <5s占比 | ≥8s占比 |
|:------|:-----:|:--------:|:-------:|:-------:|
| **纯动作**（影子/闪跃慢动作） | 145 | **12.8s** | 8.3% | **62.8%** ✅ |
| **教学混合**（李宇轩/刘辉等） | 1,742 | **4.2s** | **78.4%** | 7.2% |

**原因：** Pipeline用场景切换+静音检测切割，但教学视频里教练一直讲话没有静音段，就只能靠镜头切换来切 → 一个完整的杀球动作（准备→引拍→挥拍→击球→随挥→还原）被切成3-5个片段。

**策略：**
1. **纯动作视频（影子/闪跃/慢动作系列）** — 全部保留，它们是高质量训练源
2. **教学类视频** — 必须经过质量过滤。保留≥5s或≥0.8MB（720p）/≥4MB（4K）的clip
3. **永远不做 <3s 的clip** — 它们几乎全是镜头碎片
4. **终极方案：AI剪辑Agent** — 见下方"Quality Audit"章节

## Clip Quality Audit & Filtering

### 教学类视频的clip素质问题

教学视频（李宇轩、刘辉等）的clip包含了大量**讲解镜头**（教练面对镜头说话、慢速回放加文字标注、画战术板）混在"action_demo"分类里，因为Pipeline只靠时长（2-45s）判断。

**当前Pipeline无法做到的事情：**
- ❌ 区分"纯动作演示"vs"教练讲解" — 需要动作识别模型
- ❌ 检测完整动作周期（挥拍/步法周期） — 需要动作边界检测
- ❌ 提取屏幕文字/字幕 — 需要OCR+ASR
- ❌ 验证clip内容质量 — 只检查文件大小>50KB

### 推荐的过滤Pipeline

```python
def filter_clips(all_clips, min_duration=5.0, min_size_720p=0.8, min_size_4k=4.0):
    """两阶段过滤：基础质量 + 内容质量"""
    good = []
    for c in all_clips:
        # 基础过滤：时长+大小
        if c.duration < min_duration:
            continue
        is_4k = c.width >= 3840
        min_size = min_size_4k if is_4k else min_size_720p
        if c.size_mb < min_size:
            continue
        good.append(c)
    return good
```

### 实操步骤（一次性清理）

```bash
# Step 1: 用ffprobe获取每个clip的精确时长
python3 -c "
import subprocess, os, glob
from pathlib import Path

PROCESSED = Path('data/processed_videos/bilibili')
TRAINING = Path('data/training_clips')
TRAINING.mkdir(exist_ok=True)

# 纯动作系列全部保留（影子/闪跃）
# 教学类保留≥5s的clip
for clip_dir in sorted(PROCESSED.iterdir()):
    if not clip_dir.is_dir(): continue
    name = clip_dir.name
    is_shadow = any(k in name for k in ['shadow_', 'flash_', '影子', '闪跃', 'slowmo'])
    
    for v in sorted(clip_dir.glob('*.mp4')):
        r = subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
                           '-of','csv=p=0',str(v)], capture_output=True,text=True,timeout=5)
        dur = float(r.stdout.strip()) if r.stdout.strip() else 0
        
        # 纯动作保留所有≥1.5s的clip，教学保留≥5s的
        min_dur = 1.5 if is_shadow else 5.0
        if dur >= min_dur:
            # 复制到技能目录
            ...
"
```

**已验证（1,887 clips → 497 高质量clip）：**
- 6个技能目录：clear_bh(72)/clear_fh(80)/drop_stand(13)/footwork_def(241)/smash_jump(40)/smash_stand(51)
- 全部≥5s，平均10-15s
- **原始clip保留在 `data/processed_videos/bilibili/` 不动**，只复制到 `data/training_clips/`

### Skeleton animation (fallback)

Skeleton animation via MediaPipe extraction from real video is still supported as a fallback when real video is not available or privacy blurring is required. See the MediaPipe section below.

## The Correct Pipeline (Primary: Real Video)

```
① Find 8-10 high-quality合集 instructional videos (YouTube/B站)
     ↓ (parallel yt-dlp)
② Download all raw videos to raw_videos/
     ↓ (batch ffmpeg script)
③ Slice each raw video into 20-30s individual skill clips
     ↓ (named by skill_id)
④ Place in data/training_animations/{skill_id}_demo.mp4
     ↓ (static mount)
⑤ Serve via backend HTTP → playable in WeChat mini-program
```

### Step-by-step: Real video batch sourcing + slicing

#### 1. Video source selection

Aim for 8-10合集 tutorials covering all skill categories. Optimal set (proven working):

| Tutorial | Length | Covers | YouTube channel |
|:---------|:------:|:-------|:----------------|
| Forehand Clear Tutorial | ~8min | clear_fh, clear_bh, clear_overhead, clear_drive, clear_passive | Badminton Insight |
| SMASH Tutorial | ~10min | smash_stand, smash_jump, smash_point, smash_cut, smash_fh_straight, smash_fh_cross, smash_overhead | Badminton Insight |
| Drop Shot Tutorial | ~6min | drop_fh_straight, drop_fh_cross, drop_slide, drop_bh, drop_overhead_* | Badminton Insight |
| Net Shot Tutorial | ~5min | net_fh_rub, net_bh_rub, net_fh_cross, net_bh_cross, net_fh_push, net_bh_push, net_fh_lift, net_kill | Badminton Insight |
| Footwork Tutorial | ~8min | fw_fh_net, fw_bh_net, fw_fh_back, fw_overhead_back, fw_side | Various |
| Defense Tutorial | ~9min | def_fh_lift, def_bh_lift, def_fh_drive, def_bh_drive, def_low | Various |
| Feints/Deception Tutorial | ~13min | All 15 feint_* skills (feint_smash_drop through feint_repeat) | Various |
| Backhand Techniques | ~10min | clear_bh, drop_bh, net_bh_rub, net_bh_cross, net_bh_push, def_bh_drive, def_bh_lift | Various |
| Doubles Tactics | ~8min | flat_drive_fh, flat_drive_bh, net_kill, push_split, serve_receive, serve_receive_return, mid_block (7 doubles skills) | Various |

#### 2. Parallel download command (batch yt-dlp)

```bash
# 4-9 parallel downloads, each using one terminal background process
for url in "URL1" "URL2" "URL3" "URL4"; do
  yt-dlp -f "best[height<=720][ext=mp4]" \
    -o "raw_videos/$(basename $url).mp4" "$url" --no-warnings &
done
wait
```

**Key details:**
- Format: `-f "18"` (360p MP4 with audio) — most reliable across all YouTube videos
- Fallback format: `-f "18/best[height<=720]"` if format 18 is somehow unavailable
- 4 parallel downloads average ~40s each for 20MB files on ~600KB/s connection
- Success rate with 4+ parallel: ~80% (SSL errors on ~20%, retry succeeds)
- If a video fails (unavailable/region-locked), swap to `yt-search` alternative

#### 3. Batch slicing script (ffmpeg)

Create a shell script with `SLICE()` helper:

```bash
SLICE() {
  local input=$1 start=$2 duration=$3 output=$4
  if [ -f "raw_videos/$input.mp4" ]; then
    local size=$(stat -f%z "raw_videos/$input.mp4" 2>/dev/null)
    if [ "$size" -gt 100000 ]; then
      ffmpeg -y -ss "$start" -t "$duration" -i "raw_videos/$input.mp4" \
        -vf "scale=640:-2:flags=lanczos,fps=24" -c:v libx264 -crf 26 -preset fast -an \
        "data/training_animations/${output}_demo.mp4" 2>/dev/null
    fi
  fi
}

# Example batch calls (timestamps are best-guess, may need adjustment per video):
SLICE clear_tutorial 60 30 clear_fh        # 60-90s segment
SLICE clear_tutorial 150 25 clear_bh       # 150-175s segment
SLICE smash_tutorial 60 30 smash_stand     # 60-90s segment
SLICE smash_tutorial 180 30 smash_jump     # 180-210s segment
# ... etc for all skills
```

**Timestamp strategy:** Use `ffprobe` first to get total duration, then divide roughly by number of skills the video covers. E.g. if a 494s video covers 5 skills, try timestamps at 60, 150, 240, 330, 420. Verify with keyframe extraction:
```bash
ffmpeg -i input.mp4 -vf "select='gt(scene,0.3)',showinfo" -vsync vfr -f null - 2>&1 | grep "pts_time"
```

**Verify slices successfully produced:**
```bash
./venv/bin/python3 -c "
import os, json, urllib.request
d = json.loads(urllib.request.urlopen(urllib.request.Request('http://localhost:8000/api/training/categories')).read())
vid_dir = 'data/training_animations'
miss = [(c.get('emoji',''), s['name'], s['id']) for c in d['categories'] for s in c['sub_skills'] 
        if not os.path.exists(f'{vid_dir}/{s[\"id\"]}_demo.mp4')]
print(f'✅ {51-len(miss)}/51 skills have video' if not miss else f'❌ Missing: {len(miss)}')
for e, n, i in miss: print(f'  {e} {n} [{i}]')
"```

### Compilation verification: mapping skill_id → video file

After slicing, use this Python check to see which skills have matching video files:

```python
import os
# Single skills: {skill_id}_demo.mp4
# Check against skills list from the API
```

The `data/training_animations/` directory should end up with ~55-63 files:
- 51 single skills *_demo.mp4
- 7 doubles skills *_.mp4
- A few old/legacy files (defense_demo.mp4, high_clear_demo.mp4 etc.) that are harmless leftovers

## Step-by-Step

### Step 1: Source Real Video

Where to find training video sources:

**Chinese sources (preferred for Chinese users):**
- **Bilibili (B站)** — 影子羽毛球高清慢动作精选 series (赵剑华、肖杰、傅海峰 textbook demonstrations, pure slow-motion action, no talking)
- **Bilibili** — 洁宝羽毛球 (国二女生高远球慢动作示范)
- **YouTube (Chinese content)** — 李宇轩教练 (Taiwanese coach, has pure action demo segments)
- **YouTube** — Match footage of Chinese national team players (石宇奇, 陈雨菲, 林丹, 谌龙)

**English/International sources:**
- **Recommended channel**: Badminton Insight (YouTube, 707K subscribers, ex-pro Greg & Jenny Mairs)
- YouTube/Bilibili: professional badminton instruction channels
- Free stock footage sites with sports content
- Self-recorded demonstration (if a skilled player is available)

**Key quality standard:** Videos must be **pure action demonstration** — no long introductions, no talking-head segments. Crop out only the moments when the player is performing the skill. 15-30 seconds per clip is ideal.

**yt-dlp download command (YouTube):**
```bash
yt-dlp -f "18" -o "training_videos_raw/%(title).80s_%(id)s.%(ext)s" "ytsearch:Badminton Insight forehand clear tutorial"
```

**yt-dlp download command (Bilibili):**
```bash
# Bilibili requires cookies AND uses format IDs (not 'best')
yt-dlp --cookies-from-browser chrome -f "highest-available" \
  -o "training_videos_raw/%(title).60s_%(id)s.%(ext)s" \
  "https://www.bilibili.com/video/BV1jt41197as/"
# Bilibili free tier is capped at ~480p; 720p+ requires membership.
# Use --list-formats first to see available IDs:
yt-dlp --cookies-from-browser chrome -F "https://www.bilibili.com/video/<ID>/"
# Then specify format IDs (video+audio):
yt-dlp --cookies-from-browser chrome -f "30033+30280" -o "..." "<url>"
```

**Chinese video search terms (YouTube):**

| Skill | Search term |
|:------|:-----------|
| 高远球 | `羽毛球 高远球 慢动作 陈雨菲` |
| 杀球 | `李宗伟 杀球 超慢镜头` |
| 吊球 | `赵剑华 吊球 慢动作` |
| 步法 | `羽毛球 步法 慢动作 示范` |
| 防守/平抽 | `羽毛球 防守 平抽 慢动作` |
| 网前 | `羽毛球 网前 搓球 慢动作` |

Search terms per skill:

| Skill | yt-dlp search query |
|:------|:-------------------|
| 高远球 | `Badminton Insight forehand clear tutorial` |
| 杀球 | `Badminton Insight jump smash tutorial step by step` |
| 吊球 | `Badminton Insight drop shot tutorial technique` |
| 步法 | `Badminton Insight footwork 4 corner tutorial` |
| 防守 | `Badminton Insight defend smash driving tutorial` |
| 网前 | `Badminton Insight net shot cross court step by step` |

**Cropping to 15-30s clips:**
```bash
# First, inspect the video to find the pure-action segments:
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 video.mp4

# Sample frames every 30s to identify action segments:
for t in 0 30 60 90 120 150; do
  ffmpeg -y -ss $t -i video.mp4 -vframes 1 -q:v 3 "/tmp/preview_${t}s.jpg"
done

# Crop the pure action segment (no talking, no intro):
ffmpeg -i raw.mp4 -ss 00:01:30 -t 25 -c copy clip_demo.mp4
```

Requirements per clip:
- 15-30 seconds (one full action cycle)
- Clean background (or high contrast with person)
- Full body visible (no cropping at joints)
- ≥30fps, ≥720p resolution

**File layout for the project:**
```
data/
├── training_videos_raw/     # Raw full instructional videos
├── training_clips/          # Cropped 15-30s clips
├── training_videos/         # Official training directory
└── training_animations/     # HTTP static file serving (GIF+MP4)
```

### Step 2: MediaPipe Extraction

Use the existing `PoseEstimator.process_video()` pipeline:

```python
from badminton_coach.pose_estimator import PoseEstimator
estimator = PoseEstimator()
poses = estimator.process_video("source_video.mp4")
```

This returns `List[FramePose]` — each with 33 landmarks (x, y, z, visibility per frame).

### Step 3: Render Skeleton Animation

Use `training_gif.py` as a starting template BUT replace the keyframe dict with real MediaPipe output:

```python
# WRONG: hand-crafted keyframes
_FAKE_KEYFRAMES = {0: {11: (0.45, 0.30), ...}}  # ← DO NOT DO THIS

# CORRECT: use real MediaPipe extraction
frame_poses = estimator.process_video("real_video.mp4")
real_keyframes = {
    p.frame_idx: {
        lm_idx: (p.landmarks[lm_idx][0], p.landmarks[lm_idx][1])
        for lm_idx in [0, 11, 12, 13, 14, 15, 16, 23, 24, 25, 26, 27, 28]
        if p.detected and p.landmarks[lm_idx][3] >= 0.3
    }
    for p in frame_poses if p.detected
}
```

### Step 4: Render with OpenCV

```python
# Per-frame rendering
_CONNECTIONS = [
    (11, 12), (11, 13), (13, 15), (12, 14), (14, 16),
    (11, 23), (12, 24), (23, 24), (23, 25), (25, 27),
    (24, 26), (26, 28), (0, 11), (0, 12),
]
BG_COLOR = (15, 31, 51)        # Deep navy
BONE_COLOR = (59, 130, 246)    # Blue
JOINT_COLOR = (147, 197, 253)  # Light blue
ACCENT_COLOR = (255, 200, 50)  # Gold for annotations

for pts in frame_poses:
    img = np.full((480, 360, 3), BG_COLOR, dtype=np.uint8)
    # Scale landmarks to canvas coordinates
    for a, b in _CONNECTIONS:
        if a in pts and b in pts:
            cv2.line(img, pts[a], pts[b], BONE_COLOR, 3)
    for _, pos in pts.items():
        cv2.circle(img, pos, 5, JOINT_COLOR, -1)
```

### Step 5: Output Formats

**For WeChat mini-program → MP4 (H.264):**
```bash
# GIF → MP4
ffmpeg -y -i input.gif -c:v libx264 -pix_fmt yuv420p -movflags +faststart output.mp4
```

**For web → GIF:**
```python
from PIL import Image
frames = [Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)) for f in frames_bgr]
frames[0].save("output.gif", save_all=True, append_images=frames[1:], 
               duration=80, loop=0, optimize=True)
```

### Step 6: Serve in Mini-Program

```
Backend: mount static directory
app.mount("/training_animations", StaticFiles(directory="data/training_animations/"))

Frontend: <video> tag in WXML
<video src="http://192.168.0.103:8000/training_animations/smash.mp4" 
       controls autoplay loop></video>
```

## Animation Quality Standards

| Criterion | Must Pass | 
|:---------|:---------:|
| Motion smoothness | ≥12fps output, real motion trajectory |
| Joint positions | Extracted from real human, not manually placed |
| Annotation readability | Angles labeled in gold text near the joint |
| File size (MP4) | <100KB per 15-second clip |
| File size (GIF) | <150KB per 15-second clip |
| Background | Dark solid color (matches app theme) |
| Loop | Seamless loop (last frame ≈ first frame for cyclic actions) |

## Known Pitfalls

### Pitfall 1: Hand-crafted keyframes are unacceptable ❌
Users immediately notice stiff, unnatural motion from hand-placed keyframe interpolation. The bones look like a puppet, not a person. **Always use real MediaPipe extraction from actual video.**

### Pitfall 2: GIF doesn't play inline in WeChat ❌
WeChat's built-in browser does not reliably display animated GIFs inline. Users on iOS WeChat in particular cannot tap or play GIFs. **Always convert to MP4 for WeChat delivery.**

### Pitfall 3: MEDIA: syntax may not deliver on WeChat ❌
The `MEDIA:/path/to/file` syntax embedded in agent responses may or may not render as a clickable attachment depending on the WeChat integration configuration. If the user says "I can't click it" or "I don't see it":
- Try `send_message` with `MEDIA:` in the body as a DM
- If that also fails, fall back to serving the file via HTTP from the backend and sending the URL as a plain link

### Pitfall 4: OpenCV/PIL may not auto-import ↔ cv2 NameError
The `training_gif.py` used lazy imports (`from PIL import Image` etc. inside methods) to avoid startup overhead, but the `generate_gif()` method called `cv2.cvtColor()` without importing cv2 in that scope. Fix: always put `import cv2` inside any method that uses it.

### Pitfall 5: Keyframe-only mode = "P" palette mode
When using PIL to create GIFs, `img.convert('RGB')` to RGB mode before processing with cv2, or cv2 can't read the palette image.

### Pitfall 6: Bilibili downloads fail without cookies and correct format ID ❌

Bilibili requires `--cookies-from-browser chrome` AND you cannot use `-f "best[height<=720]"` — you must first list available formats, then specify video+audio IDs explicitly.

**Strategy: fail fast. If B站 returns a premium-member error, stop and switch to YouTube Chinese content immediately. Do not retry B站.**

See Pitfall 18 for the full fallback strategy.

### Pitfall 18: B站高清需登录 — 果断换源到YouTube中文教学 ⚠️

**新策略：失败一次就切，不纠缠B站。**

B站免费用户只能下载480p（且2025年起限制更严），绝大多数视频需要浏览器cookies甚至会员。对于骨骼追踪/标注任务，360p-480p够用，但如果B站第一次尝试就返回"premium member"或格式不可用，**直接换YouTube中文教学**，不再重试。

**正确做法：**
1. 用 `yt-dlp --flat-playlist "ytsearch5:羽毛球 <动作> 教学"` 搜B站
2. 如果试一个视频就看到 premium member 错误 → **立即切到YouTube搜索相同关键词**
3. YouTube 上用 `-f "18"` 下载（360p MP4，含音频，100%稳定）

**YouTube中文教学频道优先级（已验证可用）：**
| 频道 | 内容 | yt-dlp格式 |
|:-----|:-----|:----------|
| 刘辉羽毛球 | 发球/高远/反手/步法全覆盖 | `-f "18"` ✅ |
| 李宇轩教练/包建邦 | 网前/杀球/步法/吊球 | `-f "18"` ✅ |
| 杨晨大神 | 高远/杀球/战术 | `-f "18"` ✅ |
| 陈金羽毛球（世界冠军） | 反手/发球 | `-f "18"` ✅ |

### Pitfall 19: YouTube requires `--js-runtimes node` since 2025

Without this flag, yt-dlp warns about JS runtime and may fail on format extraction:

```bash
# Install node (macOS): brew install node (already installed)

# Always pass this flag:
yt-dlp --js-runtimes node [rest of args]

# Or add to yt-dlp config (~/.config/yt-dlp/config):
echo "js-runtimes: node" >> ~/.config/yt-dlp/config 2>/dev/null || true
```

### Pitfall 20: Use `-f "18"` (360p) as the primary YouTube format

`"best[height<=720][ext=mp4]"` fails on ~20% of YouTube videos due to format availability. The format ID 18 (360p MP4 with audio) has been stable for years:

```bash
# ✅ Reliable, always works:
yt-dlp -f "18" --max-filesize 150M "https://youtube.com/watch?v=ID" -o "cat_%(id)s.%(ext)s"

# ❌ May randomly fail:
yt-dlp -f "best[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" "..."

# ✅ Mark II (fallback chain recommended):
yt-dlp -f "18/best[height<=720]" "..."
```

360p is sufficient for MediaPipe Pose (256x256 input). Only use higher resolutions when the video is for user-facing playback (training animations).

### Pitfall 21: Multi-category P0 expansion workflow

When adding new categories (e.g. 16 new classes with 76 sub-skills), use this parallel search+download pattern:

```bash
# Step 1: Create directories and search each category
SEARCH_TERMS=(
  "serve:羽毛球 发球 教学"
  "drive:羽毛球 平抽挡 教学"
  "lob:羽毛球 挑球 教学"
  "block:羽毛球 挡网 教学"
  "serve_return:羽毛球 接发球 教学"
  "transition:羽毛球 过渡球 教学"
)

for term in "${SEARCH_TERMS[@]}"; do
  cat="${term%%:*}"
  query="${term##*:}"
  mkdir -p "raw_videos/$cat"
  yt-dlp --js-runtimes node --flat-playlist --print "%(id)s" \
    "ytsearch5:$query" 2>/dev/null | grep -E "^[a-zA-Z0-9_-]{10,}$" | head -3 \
    > "/tmp/${cat}_vids.txt"
done

# Step 2: Download all found videos in parallel
for term in "${SEARCH_TERMS[@]}"; do
  cat="${term%%:*}"
  while read -r vid; do
    test -n "$vid" || continue
    yt-dlp -f "18" --max-filesize 150M \
      "https://youtube.com/watch?v=$vid" \
      -o "raw_videos/$cat/${cat}_$vid.%(ext)s" &
  done < "/tmp/${cat}_vids.txt"
done
wait
```

This pattern was proven in production: 5 categories x 3 videos each = 15 concurrent downloads completing in ~2 minutes.

### Pitfall 7: Timestamp guesses are often wrong ❌
When cropping English instructional videos (e.g. Badminton Insight), the pure action demo segment is NOT always at 1:30. Always preview frames first. For Chinese 影子羽毛球 (Zhao Jianhua) videos, the structure is:
- 0:00-0:45: 高远球
- 0:45-1:30: 杀球
- 1:30-2:15: 吊球
- 2:15-3:00: 网前
- 3:00-3:45: 步法
- 3:45+: 防守/平抽

### Pitfall 8: Short pure-action clips (e.g. 林丹 9s, 李宗伟 30s) may not need cropping
Some YouTube Shorts/tikTok-style clips are already pure action. Just copy them directly to training_clips/ without ffmpeg processing.

### Pitfall 9: B站搜索替代方案 — yt-dlp 格式探测 + 并行下载
B站视频搜索后，可用 `search.bilibili.com` 的 web 搜索获取 BV 号，然后逐个用 yt-dlp --cookies-from-browser 下载。如果 B站下载失败或格式不可用（如 format ID 302xx 不存在），备选方案:
- YouTube 中文教学频道（李宇轩教练、包建邦羽毛球、洁宝羽毛球）  
- 直接用浏览器截图搜索结果页并告知用户可用内容
- **并行下载策略**: 多个 yt-dlp 进程同时跑，每个 30-60s，前端等待结果。实测 6 个并行下载平均完成 5 个（成功率 83%）。
- 下载成功的文件统一在 `raw_videos/{skill_id}.mp4`，裁剪后放到 `data/training_animations/{skill_id}_demo.mp4`

### Pitfall 10: YouTube 下载的格式锁定
yt-dlp 对 YouTube 使用 `-f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]"` 可以成功下载 720p MP4。短片段（<30s）下载后通常不需要裁剪，但长视频（60s+ 教学）需要浏览找到纯动作段落后裁剪。

### Pitfall 11: 多技能合集视频的裁剪策略
有些教学视频是合集（如陈金羽毛球 吊球教学 4分钟，包含多个分解步骤+多人对抗示范）。对这类视频:
1. 先用 `ffprobe` 看总时长
2. 然后用 `ffmpeg -ss <time> -t 30` 尝试中间段（不一定一次成功，因为不知道示范在几分几秒）
3. 批量裁剪多个候选段，人肉浏览选最佳
4. 或用浏览器截图查看视频时间轴

### Pitfall 16: 切换语言源的时机 — 失败1次就换

当 B站下载失败（格式不匹配/需要会员/需要登录cookies）时，应果断切换到 YouTube 中文教学频道（刘辉、李宇轩、包建邦、陈金）而非继续尝试 B站。**每条视频只尝试1次，失败就换源。** 不要重试 B站 — cookies/membership 限制不会因重试而消失。实测切换源后的成功率接近 100%。

### Pitfall 22: B站4K视频场景检测超时 — 用`-skip_frame nokey`降采样加速

3840×2160 31分钟视频（如闪跃运动4K杀球，640MB）用标准ffmpeg场景检测会超时。**正确做法是只分析关键帧(I帧)：**

```python
# ✅ 对4K视频：scale + skip_frame nokey 加速~100倍
vf = f"scale=1280:720,select='gt(scene,{SCENE_THRESHOLD})',showinfo"
out = ffmpeg([
    "ffmpeg", "-skip_frame", "nokey", "-i", str(path),
    "-vf", vf,
    "-vsync", "0", "-f", "null", "-"
], 600)  # 4K视频给600s超时
```

**原理：** `-skip_frame nokey` 只解码I帧（关键帧），4K 31分钟视频从~47,000帧降到~1,900帧。场景检测在降采样后的I帧上进行，精度损失可接受。`-vsync 0` 防止帧率转换。

### Pitfall 23: B站4K视频静音检测超时 — 先提取音频再检测

```python
# ✅ 大型视频(>200MB)：先复制音频流到临时文件再检测静音
import tempfile
with tempfile.NamedTemporaryFile(suffix='.aac', delete=False) as tf:
    audio_tmp = tf.name
ffmpeg(["ffmpeg", "-i", str(path), "-vn", "-c", "copy", "-y", audio_tmp], timeout)
out = ffmpeg([
    "ffmpeg", "-i", audio_tmp,
    "-af", f"silencedetect=noise={SILENCE_THRESHOLD}:d={MIN_SILENCE}",
    "-f", "null", "-"
], timeout)
os.unlink(audio_tmp)
```

4K视频640MB的音频解码速度远远快于视频解码。`-vn -c copy` 只提取音频流，静音检测在纯音频上运行，避免视频解码开销。

### Pitfall 24: B站搜索的BVID提取方式 — 浏览器JS比API更可靠

B站API `api.bilibili.com/x/web-interface/search/all/v2` 返回空结果，而浏览器搜索页可以直接用JS提取BV号。在搜索页执行：

```javascript
(() => {
  const links = Array.from(document.querySelectorAll('a[href*="/video/BV"]'));
  return [...new Set(links.map(a => a.href.match(/BV\w+/)?.[0]).filter(Boolean))];
})()
```

然后用 `browser_console` 的 `expression` 参数执行这个JS，直接拿到BVID列表。注意同页面点击搜索结果中的视频链接后，`window.location.href.match(/BV\w+/)` 可直接获取当前页面的BV号。

**已确认可用的B站高质量羽毛球教学视频（横版优先，竖版辅助）：**

| BV号 | 内容 | 画质 | 类别 | 优先级 |
|:-----|:-----|:----:|:----:|:-----:|
| `BV1Ht4y1P7Qs` | 闪跃运动4K颠覆杀球发力认知 | **3840×2160 25fps** 31min | smash | 🏆 |
| `BV1aHweeCEVB` | 李宇轩教练如何轻松杀得尖 | 1920×1080 30fps 15min | smash | 🏆 |
| `BV1Hz4y1A7XQ` | 大G吊球教学(刘辉教练) | 1080×1920 竖版 5min | drop | ✅辅助 |
| `BV1fW411R7oA` | 影子羽毛球高清慢动作(十八)反手后场 | **1280×720 25fps** 4min | clear | ✅ |
| `BV1gs411G7do` | 影子陶菲克反手牛一纪念版 | **1280×720 25fps** 3min | clear/bh | ✅ |
| `BV1g34y1o71S` | 顶尖高手高远球集锦(林丹/谌龙/李炫一) | 1534×1080 30fps 2min | clear | ✅ |
| `BV16G411B7fc` | 刘辉教练左手左腿 | 1080×1920 竖版 5min | clear/辅助 | ✅辅助 |
| `BV1nJtUeYEmP` | 李宇轩后场转身慢 | **1920×1080 60fps** 14min | footwork | 🏆 |
| `BV1X24y1B7v2` | 打球步子越大越接不了球 | **1920×1080 60fps** 30min | footwork | 🏆 |
| `BV11Gt4zTEKs` | 桃田贤斗步伐攻略 | **2880×2160 60fps** 3min | footwork | 🏆 |
| `BV1os411K7es` | 李宗伟步法慢动作分解解析 | **1280×720 30fps** 10min | footwork | ✅ |
| `BV1jt41197as` | 影子赵剑华教科书右手版 | **1280×720 25fps** 5.5min | 基础综合 | ✅ |
| `BV1Et41197bx` | 影子赵剑华教科书左手版 | 852×480 25fps 5.5min | 基础综合/对称 | ✅ |
| `BV1Wb411U71C` | 影子肖杰教科书右手版 | **1280×720 25fps** 8.7min | 基础综合 | ✅ |
| `BV1Wb411U7UL` | 影子肖杰教科书左手版 | **1280×720 25fps** 8.7min | 基础综合/对称 | ✅ |
| `BV1hZ4y1d7Hs` | 闪跃运动反手杀球/高远球简化版 | 1280×720 → 4K可用 | 反手综合 | ✅ |

**关键词搜索策略（已验证有效）：**
- `羽毛球 杀球 教学 慢动作` — 杀球类搜索
- `羽毛球 网前球 教学 慢动作` — 网前类
- `羽毛球 吊球 教学 慢动作` — 吊球类
- `羽毛球 高远球 教学 慢动作` — 高远球类
- `羽毛球 步法 教学 慢动作` — 步法类
- 加上 `横版` 关键词可过滤掉很多竖版手机内容

### Pitfall 25: B站下载后通过Pipeline切割产生训练用的动作片段

B站下载的原始教学视频（含讲解段+动作示范段）不适合直接作为训练数据，需要经过 **场景切割Pipeline** 处理：

1. **场景检测：** 低阈值(0.12)检测镜头切换
2. **静音检测：** 切出纯动作示范段（讲解段有语音）
3. **分类：** 2-45s为动作片段(action_demo)，45-120s为讲解段(talking)
4. **输出：** 每个动作片段 `{video_name}_demo{NNN}_{start}s.mp4`

**Pipeline输出量(已验证)：**
- 闪跃4K杀球(31min) → 555个动作片段
- 李宇轩杀球(15min) → 286个动作片段  
- 李宗伟步法(10min) → 23个动作片段
- 桃田步法(3min) → 17个动作片段
- 5个影子慢动作合集 → 118个动作片段

**横版率评估：** 3840×2160 / 1920×1080 / 1280×720 等 `width ≥ height` 的视频为横版全身可追踪。共13个新视频下完后，横版片段占比 **92%（1,363/1,474）**，总计 **1,887个B站clips**（含首批118+新1,363横版+111竖版辅助）。

### Pitfall 26: 训练技能→演示视频映射 — 技能树跟B站clips的关联方案

Pipeline切割的1,887个B站clips需要映射到21个子技能、51个训练等级。创建 `skill_video_mapping.json` 作为桥接文件：

```json
{
  "categories": [{
    "id": "smash", "name": "杀球", "emoji": "💪",
    "sub_skills": [{
      "id": "smash_stand", "name": "原地杀球", "difficulty": 1,
      "levels": [{
        "level": 1,
        "volume": "挥拍30次+击球20次",
        "video_clips": [{
          "src": "bilibili/4K杀球视频目录/demo*.mp4",
          "source": "闪跃运动4K杀球",
          "res": "3840×2160@25fps",
          "best_for": "杀球全身发力链条"
        }]
      }]
    }]
  }]
}
```

API端提供三个端点：
```python
GET /api/training/video-mapping              # 全量映射表
GET /api/training/skill-video/{skill_id}?level=N  # 单技能最佳视频
/clips/...                                    # 静态视频文件
GET /skeletons/...                            # 骨架JSON文件
```

小程序端 `training.js` 的 `openDetail()` 加入 `_loadDemoVideo(skillId, level)` 异步加载，WXML用 `<video>` 播放B站clips。后端用FastAPI `StaticFiles` 挂载clips和skeletons目录。

### Pitfall 27: FastAPI `StaticFiles` 重复挂载报错 — 用`try/except`兜底

```python
try:
    app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="action_clips")
except Exception as e:
    print(f"⚠️ clips挂载失败: {e}")
```

当`name`参数重复时（如多个模块分别挂载），FastAPI会抛出异常。所有`mount`调用都应用`try/except`包裹，并打印警告而非让进程退出。特别是标注系统在`webapp.py`中动态挂载（`name="action_clips"`），启动时目录不一定存在。

### Pitfall 14: First-time GitHub push requires user-provided token

When the local project has no remote configured AND `gh auth status` fails:

1. **Do not try to automate token-less setup** — GitHub API requires authentication for repo creation
2. **Ask the user directly** for a GitHub Personal Access Token (classic) with `repo` scope
3. Once received, set it up:
   ```bash
   # Option A: gh auth login (preferred)
   echo "$TOKEN" | gh auth login --with-token

   # Option B: embedded in remote URL (works with git push)
   git remote add origin https://$GH_USER:$TOKEN@github.com/$GH_USER/$REPO_NAME.git
   git push -u origin main
   ```
4. If the remote repo doesn't exist yet, create it first:
   ```bash
   # With gh (after auth)
   gh repo create $REPO_NAME --source . --public --push

   # Without gh
   curl -s -X POST -H "Authorization: token $TOKEN" \
     https://api.github.com/user/repos \
     -d '{"name": "'"$REPO_NAME"'", "private": false}'
   git remote add origin https://$TOKEN@github.com/$GH_USER/$REPO_NAME.git
   git push -u origin main
   ```

### Pitfall 15: Large-scale parallel video acquisition — pipeline for data labeling

When collecting videos for a labeling system (not just training demos), the strategy changes from "find a few good tutorial videos" to "mass-download and batch-annotate":

**Strategy: reuse + download. 7-step process:**

1. **Catalog the target.** List all categories and their current count vs target (e.g. 15+/category).
2. **Reuse existing clips.** Training animation libraries (`training_animations/`) contain pre-clipped technique demos. Copy matching ones to `raw_videos/{category}/` with filename dedup.
3. **Identify gap categories.** After reuse, compute which categories still need more.
4. **Multi-threaded download.** Run 3-5 parallel yt-dlp processes, each targeting a different category. Use `terminal(background=true)` for each:
   ```bash
   yt-dlp --socket-timeout 20 --max-filesize 80M \
     "ytsearchN:羽毛球 <technique> 教学 [慢动作]" \
     -o "raw_videos/{category}/{category}_%(id)s.%(ext)s"
   ```
5. **Clean partials.** Background downloads interrupted by timeout leave `.part` files. Clean them before counting: `find raw_videos -name '*.part' -delete`.
6. **Deduplicate by video ID.** yt-dlp may download audio+video separately. Count unique IDs (11-12 char alphanumeric after `_`) not files.
7. **Verify target reached.** Each category should hit 15+ unique videos before starting annotation.

**Known failure modes with parallel yt-dlp:**
- **Timeout on large files (e.g. `--max-filesize 50M` still fails for 3+ min downloads).** Raise to 80M and use `--socket-timeout 15-20`.
- **Format not available with `-f`.** Some YouTube videos don't have the requested format. Drop `-f` entirely and rely on `--max-filesize`.
- **Chinese/western keyword differences.** "羽毛球 杀球 教学" and "badminton smash slow motion" return different video pools. Use both if one pool is thin.
- **Background process exits without output.** Check with `process action=poll session_id=...` — if status=exited, check log output. If status=running, wait.
- **Partial downloads.** Kill background processes that run > 5 min — the download likely stalled on a large file that exceeds the timeout.

**After collection, batch-annotate immediately:** Run `batch_annotate.py` while downloads continue for other categories (parallel work). The annotation pipeline doesn't depend on all categories being full. Processing rate on M1 Pro: ~3-4 videos/min.

### Pitfall 17: `.gitignore` 全量 `*.mp4` 规则会排除训练视频 ⚠️

If your `.gitignore` has a blanket `*.mp4` rule (common pattern for ignoring test media files), the training animation MP4s in `data/training_animations/` will be silently **excluded from version control**. Neither `git add` nor `git commit` will include them.

**Fix:** Add a negation rule in `.gitignore`:

```gitignore
# Keep the general rule for test/temp files
*.mp4
*.avi
*.mov

# But explicitly include the production training animations
!data/training_animations/*.mp4
```

**Verify with:**
```bash
git check-ignore -v data/training_animations/clear_fh_demo.mp4
# Should show the negation rule (prefixed with !), not the general *.mp4 rule
```

The negation line must appear **after** the general `*.mp4` rule in the file (git processes `.gitignore` rules top-to-bottom, last match wins).

### 16-Category Video Sourcing Priority Guide

When you need to expand from the base 7 categories (high_clear/smash/drop/net/footwork/defense/feints) to cover all 23 categories (127 sub-skills), use this priority-based approach:

**Priority tiers for sourcing:**

| Tier | Categories | Sub-skills | Strategy |
|:----:|:-----------|:----------:|:---------|
| 🟢 **P0** | serve, drive, lob, block, serve_return, transition | 27 | Video of basic actions is abundant on YouTube/B站. Search by action name directly. |
| 🟡 **P1** | spin, special (behind/crotch/dive), combination | 14 | Moderate scarcity. May need to combine multiple sources. |
| 🔵 **P2** | pacing, tactics (positioning/rally), tactics_pattern, conditioning, singles, doubles | 30 | Most are multi-shot concepts, not single actions. Search for training drills. |
| ⚪ **P3** | flexibility (stretch/protect/recovery) | 4 | Not camera-detectable — skip annotation, use text-based guidance instead. |

**Search keywords for P0 categories (Chinese + English):**

| Category | Chinese Keywords | English Keywords |
|:---------|:----------------|:-----------------|
| 🚀 发球 | `羽毛球 发球 慢动作 教学`, `正手发球/反手发网前` | `badminton serve slow motion`, `short serve / flick serve` |
| ⚡ 平抽挡 | `羽毛球 平抽 防守 慢动作`, `正反手平抽` | `badminton drive slow motion`, `forehand/backhand drive` |
| 🔝 挑球 | `羽毛球 挑球 慢动作`, `正手挑球/反手挑球` | `badminton lift slow motion`, `forehand/backhand lift` |
| 🖐️ 挡网 | `羽毛球 挡网 慢动作`, `正手挡网/反手挡网` | `badminton block slow motion`, `net block` |
| 🔄 接发球 | `羽毛球 接发球 技术`, `接发球推压/推后场` | `badminton service return`, `receive serve` |
| 🌉 过渡球 | `羽毛球 过渡球 中场`, `被动过渡` | `badminton transition shot`, `midcourt transition` |

**For P0 categories: aim for 15+ videos per category (like the base 7).**
**For P1-P2: 5-10 videos per category is sufficient for initial annotations.**

**Search B站 first (1 attempt only), fail fast to YouTube Chinese content.** See Pitfall 18 for the full fallback strategy. Do not retry B站 — the cookie/membership barrier won't change on retry.

## Reference Files

- `references/wechat-video-delivery.md` — WeChat video delivery specifics and known platform bugs
- `references/video-sourcing-comparison.md` — Comparison of B站 vs YouTube vs archive.org sourcing
- `references/chinese-player-sources.md` — Specific Chinese pro player video sources
- `references/mimicmotion-deployment.md` — MimicMotion pose-guided video generation (action migration from B站 pro skeleton to user selfie)
- `references/youtube-batch-sourcing.md` — **Batch sourcing workflow**: finding 8-10 合集 tutorials, parallel yt-dlp download, ffmpeg batch-slicing into 51 individual clips. Proven with Badminton Insight tutorials yielding 63 clips in ~15 min.
- `references/video-cropping-transcript-preservation.md` — Cropping videos while preserving subtitle/transcript text for richer annotation metadata, plus 360° motion generation data strategy

- `wechat-miniprogram-testing` — For UAT of training pages in the mini-program
- `systematic-debugging` — For debugging animation rendering issues
