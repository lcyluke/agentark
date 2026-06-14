# GitHub README Demo Video → GIF Pattern

GitHub README does NOT support `<video>` tags. They are silently stripped. Workarounds:

## Option A: MP4 → GIF Conversion (Best for short demos)

```bash
# High quality: 720px, 15fps, diff palette
ffmpeg -y -i demo.mp4 \
  -vf "fps=15,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
  -loop 0 demo.gif

# Smaller: 480px, 10fps
ffmpeg -y -i demo.mp4 \
  -vf "fps=10,scale=480:-1:flags=lanczos,split[s0][s1];[s0]palettegen[p];[s1][p]paletteuse" \
  -loop 0 demo.gif
```

Then embed in README:
```html
<p align="center">
  <img src="demo.gif" alt="Demo" width="100%">
</p>
```

Target 2-5MB for acceptable GitHub load time. 720p/15fps typically yields 3-4MB for a 30-second clip.

## Option B: Clickable Link (Fallback)

```html
<a href="https://github.com/user/repo/blob/main/demo.mp4">
  <img src="logo.png" alt="▶ Watch Demo" width="400">
</a>
```

GitHub serves raw MP4 with proper Content-Type — clicking opens in browser's native player.

## Option C: Hosted Video (YouTube/etc.)

Not recommended for README — GitHub strips `<iframe>`. Use a badge link instead.

## Pitfalls

- **`<video>` tag**: Does not render on GitHub. Silently stripped. Don't use it.
- **File over 10MB**: GitHub shows "Sorry, we can't show files that are this big." Compress below 5MB.
- **GIF quality vs size**: `palettegen=stats_mode=diff` + `dither=bayer:bayer_scale=5` gives the best quality/size ratio.
- **Standalone logo**: If you have both a logo and a demo GIF, put the logo FIRST, then the GIF below. Don't make the logo clickable for the video — it confuses users.
