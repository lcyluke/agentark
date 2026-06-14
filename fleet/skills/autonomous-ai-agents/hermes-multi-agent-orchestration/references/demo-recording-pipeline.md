# Demo Recording Pipeline — asciinema + agg → GIF

## When to use

When adding a terminal demo GIF to a GitHub README to show CLI/TUI output inline.

## Pipeline

```bash
# 1. Write a demo script that shows key features with pauses
#    (use `sleep 1.5` between steps, echo commands in green, output in default)

# 2. Record with asciinema
asciinema rec demo.cast -c "bash scripts/demo.sh"

# 3. Convert to GIF with agg (install: brew install agg)
agg --cols 70 --rows 28 --font-size 14 --speed 1.2 demo.cast demo.gif
```

## Parameters

| Flag | Purpose | Recommended |
|------|---------|-------------|
| `--cols` | Terminal width | 70 |
| `--rows` | Terminal height | 28 |
| `--font-size` | Font pixels | 14 |
| `--speed` | Playback multiplier | 1.2 (slightly faster than real-time) |

## Size Budget

Target: **< 500KB** for GitHub inline playback. 
- 180KB achieved for 7-step 30-second demo at 70×28
- Larger demos: reduce cols/rows or speed up

## Demo Script Structure

```bash
#!/usr/bin/env bash
set -e
pause() { sleep 1.5; }

clear
echo "╔═══ Title ═══╗"
pause

echo "▶ Step 1: ..."
echo "$ command"
# output
pause
```

## Notes

- GitHub README does NOT support `<video>` tags — GIF is the only reliable inline format
- MP4 files >~5MB show "Sorry, we can't show files that are this big"
- Clickable logo → MP4 link pattern also works but requires user click
- Keep demos short (30-60s) — attention spans are short
