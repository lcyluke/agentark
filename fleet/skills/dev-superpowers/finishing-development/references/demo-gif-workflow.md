# Demo GIF Workflow — Terminal Recording for GitHub README

## Problem
GitHub READMEs do NOT support `<video>` tags. MP4 files >~3MB are rejected with "Sorry, we can't show files that are this big."

## Solution: asciinema → GIF

### Install tools
```bash
brew install agg          # asciinema GIF generator (~9MB)
# asciinema typically already installed via pip/conda
```

### Record
```bash
asciinema rec demo.cast -c "bash scripts/demo.sh"
```

### Convert to GIF
```bash
# --cols 70 --rows 28: fits GitHub README width
# --font-size 14: readable
# --speed 1.2: slightly faster than real-time
agg --cols 70 --rows 28 --font-size 14 --speed 1.2 demo.cast demo.gif
```

Target output: 100-500KB GIF is ideal. 9.8MB MP4 becomes 180KB GIF.

### Embed in README
```markdown
<p align="center">
  <img src="demo.gif" alt="Demo" width="100%">
</p>
```

## Alternative: Clickable Logo → Video
If GIF is too large, use a clickable logo that links to the video file:
```markdown
<p align="center">
  <a href="https://github.com/user/repo/blob/main/demo.mp4">
    <img src="logo.png" alt="▶ Watch Demo" width="400">
  </a>
  <br><b>▶ Click the logo to watch demo</b>
</p>
```

## Pitfalls
- **MP4 too large (9.8MB)**: GitHub rejects inline viewing. Compress with ffmpeg first: `ffmpeg -i input.mp4 -c:v libx264 -crf 30 -preset fast -c:a aac -b:a 64k output.mp4`
- **GIF too large (>5MB)**: Reduce `--cols`, lower `--font-size`, or speed up `--speed`
- **agg not in npm**: Install via brew, not npm (`brew install agg`). npm package `@asciinema/agg` may 404.
