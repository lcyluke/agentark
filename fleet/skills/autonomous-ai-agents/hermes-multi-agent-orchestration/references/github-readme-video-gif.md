# GitHub README Video/GIF Embedding Pattern

## Problem

GitHub README does NOT support `<video>` tags. Attempting to embed a `.mp4` via `<video src="...">` renders nothing.

Also: files larger than ~10MB fail with "Sorry about that, but we can't show files that are this big right now."

## Solution: Convert MP4 to Animated GIF

GIFs play inline in GitHub README without any click required.

### Step 1: Compress MP4 (if needed)

```bash
# Compress to reasonable size before GIF conversion
ffmpeg -y -i input.mp4 -c:v libx264 -crf 30 -preset fast \
  -c:a aac -b:a 64k -movflags +faststart output.mp4
```

### Step 2: Convert to GIF with good quality

```bash
# 720px, 15fps, optimized palette — good balance of size vs quality
ffmpeg -y -i input.mp4 \
  -vf "fps=15,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
  -loop 0 output.gif
```

Parameters:
- `fps=15`: 15 frames/sec (smooth enough for screen recording)
- `scale=720:-1`: 720px wide, maintain aspect ratio
- `stats_mode=diff`: Better palette for screen recordings (lots of static areas)
- `dither=bayer`: Bayer dithering for smooth gradients at small size

### Step 3: Embed in README

```markdown
<p align="center">
  <img src="demo.gif" alt="Demo" width="100%">
</p>
```

### Size Guidelines

| Resolution | FPS | Typical Size | Quality |
|-----------|-----|-------------|---------|
| 480px | 10fps | ~1.4MB | Acceptable |
| 720px | 15fps | ~3MB | Good |
| 720px | 20fps | ~6MB | Excellent |
| 1080px | 15fps | ~8MB | Best (may approach limit) |

Target ≤5MB for fast loading; GitHub handles up to ~10MB.

### Common Pitfalls

- **Don't use `<video>` tag** — GitHub strips it. Must use `<img>` with .gif.
- **Don't link a .mp4 file expecting inline playback** — GitHub doesn't embed video files in README.
- **Don't put the GIF ABOVE the logo/title** — demo shows best below the title and language toggle, above the tagline.
- **Keep the logo separate** — don't replace the static logo with the GIF. Logo at top, GIF in its own section.
