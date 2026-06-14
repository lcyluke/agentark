# Batch Generation Caveats (MimicMotion on AutoDL)

Collected during a 25-video batch run on AutoDL RTX 4090 D (2026-06-03).

## Verify `sys.path` capitalization

The MimicMotion repo lives at `/root/autodl-tmp/MimicMotion/` on AutoDL. The `mimicmotion/` package is a **subdirectory** of that, NOT the root:

```python
sys.path.insert(0, "/root/autodl-tmp/MimicMotion")   # ✓ correct
sys.path.insert(0, "/root/autodl-tmp/mimicmotion")    # ✗ wrong — ModuleNotFoundError
```

A wrong path delays your batch by 30s+ because the script hangs during model loading before crashing with `ModuleNotFoundError`.

## Always pass `device=` to every `pipeline()` call

`MimicMotionPipeline.__call__` expects `device=torch.device("cuda")` as a kwarg. Without it:

1. **First video** works (pipeline auto-detects CUDA on first call)
2. **Second video** crashes with `ValueError: Expected a cuda device, but got: cpu`

```python
# ✓ Correct — every call:
result = pipeline(
    image=img, image_pose=pt, num_frames=len(pf),
    height=576, width=1024, num_inference_steps=25,
    max_guidance_scale=2.0, tile_size=24, tile_overlap=4,
    decode_chunk_size=8,
    device=torch.device("cuda"),          # ← REQUIRED
)
```

```python
# ✗ Wrong — crashes on 2nd+ video:
# pipeline.to(torch.device("cuda"))  — crashes: property '_execution_device' has no setter
```

This is different from standard diffusers pipelines where `pipe.to(device)` works fine.

### Kill stale infer_server before batch

If `infer_server.py` (FastAPI server) was left running, it holds ~19GB VRAM of cached model weights. The batch script tries to load the same model again and gets OOM even though there's technically 24GB VRAM — the old process holds 19GB, leaving only 5GB for the new one.

```bash
kill $(pgrep -f infer_server.py) 2>/dev/null
sleep 2
python3 -c 'import torch; torch.cuda.empty_cache()'
nvidia-smi --query-gpu=memory.used --format=csv,noheader
# Verify < 500MB before starting batch
```

### Syntax warning: `0.3or` → Python 3.12 invalid decimal literal

The batch script uses compact expressions like `vis[i]<0.3or(p[0]<0and p[1]<0):continue` which produce `SyntaxWarning: invalid decimal literal` on Python 3.12+. This doesn't crash but floods the log with warnings. Fix before launch:

```bash
sed -i 's/0.3or/0.3 or/g; s/0and/0 and/g' autodl_batch.py
# Then launch with -W ignore to suppress any remaining:
nohup /path/to/python3 -W ignore autodl_batch.py > output/batch.log 2>&1 &
```

## InsightFace CPU-only on AutoDL

`onnxruntime-gpu` does NOT support CUDA 13.2 (NVIDIA driver 595.58.03). Available providers are only `AzureExecutionProvider, CPUExecutionProvider`. InsightFace runs at ~600ms/frame on CPU.

25 videos × 72 frames × 600ms = ~30 minutes just for face-swap post-processing. Wrap Step 5 in a try/except that silently falls through:

```python
try:
    from badminton_coach.face_swap import FaceSwapper
    swapper = FaceSwapper()
    # ... swap ...
except Exception as e:
    _l(f"  ⚠ {sk_id}: InsightFace skipped ({e})")
```

Or skip InsightFace entirely during batch and run it separately on the final combined videos that have verified output quality.

Expected timing (RTX 4090 D, 10 inference steps):

| Step | Time per video | 25 videos |
|:-----|:--------------:|:---------:|
| MimicMotion inference (10 steps) | ~180s | ~75 min |
| 4-view skeleton breakdown | ~2s | ~50s |
| Side-by-side composite | ~1s | ~25s |
| **Total per video** | **~183s** | **~77 min** |
| InsightFace (if CUDA available) | ~3s | ~75s |

The batch generates 3 files per skill: `output/demo/{skill}.mp4` (MimicMotion-only), `output/skel_breakdown/{skill}.mp4` (skeleton-only), `output/train/{skill}.mp4` (combined side-by-side).

## Post-generation: encoding fix for macOS playback

The `cv2.VideoWriter(*"mp4v")` on AutoDL (Linux headless) produces `mpeg4`-encoded MP4s that appear as green/unplayable on macOS QuickTime. The file has correct size and duration but all pixels render green.

**Fix: re-encode to h264 on the local machine after download:**

```bash
mkdir -p train_h264
for f in train/*.mp4; do
  name=$(basename "$f")
  ffmpeg -y -i "$f" \
    -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
    "train_h264/$name"
done
```

This produces playable 4-5MB files (vs 7-8MB mpeg4).

### Brightness fix: skeleton side is too dark

The 4-view skeleton breakdown (`breakdown_renderer.py`) renders on a dark background (`color=15`/RGB `#0f0f0f`). On the combined 1920×1080 training video, the skeleton quadrants average only **16 luminance** (out of 255) — virtually invisible on most monitors. The right-side MimicMotion face-swapped video averages **101 luminance** (visible but dim).

**Fix: apply a brightness+contrast filter during re-encode:**

```bash
ffmpeg -y -i "input.mp4" \
  -vf "eq=brightness=0.15:contrast=1.2:saturation=1.1" \
  -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
  "output.mp4"
```

This lifts the skeleton quadrants from 16→37 luminance and the face-swapped side from 101→137, making both clearly visible. The `breakdown_renderer.py` should ideally use a lighter background (e.g. `color=40` or `#282828`) in future versions to avoid needing post-processing.

### Demo videos are h264, train are mpeg4

The `autodl_batch.py` script uses **imageio** (which uses libx264) for demo videos and **cv2.VideoWriter** (which uses mpeg4) for training composites. To get playable output on macOS, either:
- Change the batch script's composite step to use imageio instead of cv2, OR
- Accept the encoding mismatch and re-encode post-download (as above).

## Skeleton file selection from B站 directory

When preparing data/skeletons/ for a batch, you have 1884 JSON files in ~18 subdirectories. One skill needs one skeleton file. Use keyword matching + frame count heuristics:

```python
# 1. Define skill→keyword map (3-4 keywords per skill, highest-scoring wins)
SKILL_KEYWORDS = {
    'smash_stand': ['4K', '杀球', '发力', 'BV1Ht'],
    'clear_fh': ['高远球', '林丹', '正手', 'BV1g3'],
    'clear_bh': ['反手', '陶菲克', 'BV1gs'],
    'drop_fh': ['吊球', '刘辉', 'BV1Hz'],
    'fw_full': ['李宗伟', '步法', 'BV1os'],
    'net_rub': ['搓球', '网前'],
    # ... etc for 25 skills
}

# 2. Score: each keyword match = 3 points
# 3. Target frame count: 40-100 frames (closest to 72)
# 4. Fallback: if no keyword match, pick any file with 40-100 frames
```

Typical B站 skeleton directories and their content:
- `4K颠覆你的杀球发力认知...` (554 files) — smash variations
- `顶尖高手高远球慢动作...` (8 large files, 153-858 frames) — clears
- `吊球又高又慢怎么办...` (15 files, 243-1590 frames) — drops/net shots  
- `李宗伟-步法慢动作...` (22 files, 38-1163 frames) — footwork
- `陶菲克反手...` (14 files, 109-882 frames) — backhand
- `李宇轩教练...` (202-581 files each) — large diagnostic corpus

Most clips are too long (200+ frames). Pick the file whose frame count is closest to 72, or sample using stride=2-4 in the batch script.

| Step | Time per video | 25 videos |
|:-----|:--------------:|:---------:|
| MimicMotion inference (10 steps) | ~180s | ~75 min |
| 4-view skeleton breakdown | ~2s | ~50s |
| Side-by-side composite | ~1s | ~25s |
| **Total per video** | **~183s** | **~77 min** |
| InsightFace (if CUDA available) | ~3s | ~75s |

The batch generates 3 files per skill: `output/demo/{skill}.mp4` (MimicMotion-only), `output/skel_breakdown/{skill}.mp4` (skeleton-only), `output/train/{skill}.mp4` (combined side-by-side).

## Post-generation: encoding fix for macOS playback

The `cv2.VideoWriter(*"mp4v")` on AutoDL (Linux headless) produces `mpeg4`-encoded MP4s that appear as green/unplayable on macOS QuickTime. The file has correct size and duration but all pixels render green.

**Fix: re-encode to h264 on the local machine after download:**

```bash
mkdir -p train_h264
for f in train/*.mp4; do
  name=$(basename "$f")
  ffmpeg -y -i "$f" \
    -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
    "train_h264/$name"
done
```

This produces playable 4-5MB files (vs 7-8MB mpeg4).

### Brightness fix: skeleton side is too dark

The 4-view skeleton breakdown (`breakdown_renderer.py`) renders on a dark background (`color=15`/RGB `#0f0f0f`). On the combined 1920×1080 training video, the skeleton quadrants average only **16 luminance** (out of 255) — virtually invisible on most monitors. The right-side MimicMotion face-swapped video averages **101 luminance** (visible but dim).

**Fix: apply a brightness+contrast filter during re-encode:**

```bash
ffmpeg -y -i "input.mp4" \
  -vf "eq=brightness=0.15:contrast=1.2:saturation=1.1" \
  -c:v libx264 -preset fast -crf 23 -pix_fmt yuv420p \
  "output.mp4"
```

This lifts the skeleton quadrants from 16→37 luminance and the face-swapped side from 101→137, making both clearly visible. The `breakdown_renderer.py` should ideally use a lighter background (e.g. `color=40` or `#282828`) in future versions to avoid needing post-processing.

### Demo videos are h264, train are mpeg4

The `autodl_batch.py` script uses **imageio** (which uses libx264) for demo videos and **cv2.VideoWriter** (which uses mpeg4) for training composites. To get playable output on macOS, either:
- Change the batch script's composite step to use imageio instead of cv2, OR
- Accept the encoding mismatch and re-encode post-download (as above).
