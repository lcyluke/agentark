# Video Cropping with Transcript Preservation

## Why

When cropping instructional videos into pure-action clips for the annotation pipeline, the original video's **讲解文字**（narrative/transcript/commentary）is valuable training context. The 28-dim annotation captures biomechanical metrics from the skeleton, but the verbal description tells the model what the coach considers important about the technique.

Annotated clips where the **associated transcript** is preserved allow future models to:
- Learn why a specific motion is correct/incorrect
- Associate biomechanical metrics with coaching terminology
- Generate text descriptions of technique from video analysis (text-to-motion → motion-to-text cycle)

## Technique

### Option A: Separate transcript per clip (preferred)

When using yt-dlp, download subtitles alongside video. After cropping, extract the subtitle segment corresponding to each clip:

```bash
# Step 1: Download video with subtitles
yt-dlp --write-auto-subs --sub-langs "zh-Hans,zh-CN,en" \
  -o "raw_videos/%(id)s.%(ext)s" "<URL>"

# Step 2: Convert subtitles to SRT
ffmpeg -i "raw_videos/<id>.zh-Hans.vtt" "raw_videos/<id>.srt" 2>/dev/null || true

# Step 3: Crop video
ffmpeg -ss 00:01:30 -t 25 -i "raw_videos/<id>.mp4" \
  -c copy "clips/<skill_id>.mp4"

# Step 4: Extract matching subtitle segment
ffmpeg -ss 00:01:30 -t 25 -i "raw_videos/<id>.srt" \
  -c copy -y "clips/<skill_id>.srt" 2>/dev/null
```

### Option B: Manual transcript via filename

When subtitles are unavailable, annotate the clip filename with a brief description:

```
clear_fh_demo_正手高远_转体充分_击球点最高.mp4
```

This embeds the key coaching point directly in the filename. The pipeline's metadata extractor can parse the `_分隔` parts.

### Option C: JSON metadata sidecar

For the labeling pipeline, each clip can have a `{clip_id}_meta.json` sidecar:

```json
{
  "source_video": "https://youtube.com/watch?v=xxx",
  "source_title": "羽毛球正手高远球教学 - 李宇轩",
  "clip_range_sec": [90, 115],
  "transcript": "击球的时候手臂要完全伸直，击球点在身体前上方最高点",
  "skill_id": "clear_fh",
  "skill_name": "正手高远球",
  "coach_name": "李宇轩"
}
```

### Format compatibility

| Format | Diffcult to crop | Easy to crop | Has timestamps |
|:-------|:----------------:|:------------:|:--------------:|
| .srt | No | Yes | Yes |
| .vtt (WebVTT) | No | ffmpeg -c copy | Yes |
| .ass/.ssa | Needs re-encoding | Complex | Yes |
| YouTube auto-subs (.vtt) | Downloads via yt-dlp --write-auto-subs | Yes | Yes |
| B站 CC subtitles (.json) | Yes — embedded in video | No | Yes |

## 360° Motion Generation Goal

The ultimate goal of the labeling system is to train a model capable of **generating 360° badminton motion from any viewpoint** — including the player, racket, and shuttlecock.

Video collection strategy should account for this downstream requirement:

- **Multi-angle is better than single-angle.** Collecting videos from multiple camera angles (front, side, back, overhead) allows the future motion generation model to learn 3D structure.
- **Racket tip tracking.** Standard MediaPipe Pose doesn't track the racket. For motion generation, you'll need:
  - MediaPipe Hands (for grip position)
  - Custom racket detection (color tracking, or a fine-tuned object detector)
  - Ball/shuttlecock detection (object detection fine-tuned on shuttlecocks)
- **Camera angle diversity.** Chinese coaches tend to film from the side (teaching) or overhead (match analysis). YouTube tutorials often use 45° behind. Collect both.

For the current 7+16 category expansion, prioritize the **side/45° angle** instructional videos — they give the best view of full-body joint angles for MediaPipe. Multi-angle can be a Phase 3 addition when motion generation becomes the active goal.
