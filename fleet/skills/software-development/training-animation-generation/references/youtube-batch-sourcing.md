# yt-dlp Batch Video Sourcing for Training Clips

This reference documents the proven workflow for sourcing ~51 training video clips
from YouTube tutorials, used to supplement the羽球宝AI搭子 training system.

## Source Video Selection Criteria

| Property | Target |
|:---------|:-------|
| Duration | 5-15 min (covers multiple skills) |
| Content | Pure action demonstration + slow-motion replay |
| Speaker | Minimal talking, no lecture segments |
| Resolution | ≥720p |
| Channel | Badminton Insight, Tobias Wadenka, or pro-player channels |

## Resource Planning

For 51 skills:
- 9 tutorial videos × ~8 min avg = ~72 min raw footage
- 51 slices × 25s avg = ~21 min total output
- 8-9 parallel downloads
- ~15 min total processing time (download + slice + verify)

## yt-dlp Best-practice Flags

```bash
# Reliable YouTube 720p download:
yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  -o "raw_videos/%(title).50s_%(id)s.mp4" "URL"

# Score-based search (picks best from results):
yt-dlp "ytsearch1:badminton forehand clear tutorial" -f "best[height<=720]" \
  -o "raw_videos/clear_tutorial.mp4"
```

## Parallel Execution

Run 4-9 downloads simultaneously. Expected behavior:
- Each ~20-30MB file takes ~30-60s on typical connections
- 15-20% of downloads hit SSL/EOF errors on last few KB — retry once
- All 9 downloads finish within ~90s with 4 parallel workers
- Don't use shell `&` inside terminal(background=true) — use one background process per download

## Common Failure Modes

| Symptom | Cause | Fix |
|:--------|:------|:----|
| `Video unavailable` | Region-locked or deleted | Swap to yt-search alternative |
| `Got error: [SSL: DECRYPTION_FAILED_OR_BAD_RECORD_MAC]` | Intermittent YouTube CDN | Retry, resolves 90% of the time |
| `HTTP Error 403` | Rate-limited | Wait 30s, retry with --sleep-interval 5 |
| `No supported JavaScript runtime` | Missing deno/node | Ignore — video still downloads; add `--compat-options no-js` if format issues |
| `Got error: 540672 bytes read, 6914 more expected` | Partial download | Retry, usually completes on second attempt |

## Batch ffmpeg Slicing Script Template

```bash
#!/bin/bash
# slice_videos.sh — batch-切片教程视频到单技能片段

SLICE() {
  local input=$1 start=$2 duration=$3 output=$4
  if [ -f "raw_videos/$input.mp4" ]; then
    local size=$(stat -f%z "raw_videos/$input.mp4" 2>/dev/null)
    [ "$size" -le 100000 ] && return
    ffmpeg -y -ss "$start" -t "$duration" -i "raw_videos/$input.mp4" \
      -vf "scale=640:-2:flags=lanczos,fps=24" -c:v libx264 -crf 26 -preset fast -an \
      "data/training_animations/${output}_demo.mp4" 2>/dev/null
    local out_sz=$(stat -f%z "data/training_animations/${output}_demo.mp4" 2>/dev/null)
    [ "$out_sz" -gt 10000 ] && echo "✅ $output" || echo "❌ $output"
  fi
}

# Verify source files
for f in clear_tutorial smash_tutorial; do
  dur=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "raw_videos/$f.mp4")
  echo "$f: ${dur%.*}s"
done

# Slice calls — timestamps will need adjustment per video
SLICE clear_tutorial 60 30 clear_fh
# ...add all other slice calls here...
```

## Second-round Slicing

When the first-round timestamps miss some segments (e.g. "too short" or "blank"):
1. Adjust start time by ±30s
2. Re-run only the failed slices
3. No need to redownload — the raw file is already there

## Video Delivery Stats (Production)

| Metric | Value |
|:-------|:------|
| Single Skills | 51/51 ✅ |
| Doubles Skills | 7 dedicated + 9 reusable |
| Total Clips | 63 |
| Size Range | 265KB - 1.5MB |
| Total Size | ~60MB |
| Format | MP4 H.264, 640px, 24fps, no audio |
| Serve Method | Static mount at `/training_animations/` |
| URL Pattern | `http://host:8000/training_animations/{skill_id}_demo.mp4` |
