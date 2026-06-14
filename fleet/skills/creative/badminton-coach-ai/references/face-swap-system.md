# InsightFace Face Swap System (P3-③) — 羽球宝AI搭子

**Created:** 2026-06-03 · **Updated:** 2026-06-03 (E2E verified)
**Files:** `badminton_coach/face_swap.py` (~540 lines)
**API endpoints:** `POST /api/avatar/generate`, `GET /api/avatar/skills`
**Dependencies:** insightface 1.0.1, onnxruntime, onnxruntime-silicon (macOS), onnxruntime-gpu (AutoDL)

---

## Architecture

```
User photo → FaceSwapper (singleton, auto-detect CUDA/CPU)
           ├── Mode 1: InsightFace direct detection → pixel-perfect face swap
           └── Mode 2: Skeleton-guided face paste → fallback for low-res
```

**Single-image performance (verified 2026-06-03):**
- M1 Pro CPU: ~1.5s/image, ~1 fps video
- RTX 4090 D CUDA (estimated): ~50ms/image, ~20 fps video

**Verified E2E test results:**
- `GET /api/avatar/skills` — returns 9 skills ✅
- `POST /api/avatar/generate?skill_id=smash_stand&mode=stub` — upload photo → 431KB 4-view skeleton MP4 ✅
- DevTools compile — no errors ✅
- Backend (121 endpoints) — all online ✅

## Two-phase video swap

The `swap_video()` method supports two parallel modes:

### Mode 1: InsightFace detection (primary)
1. Detect face per frame (re-detect every `face_detect_every_n` frames for speed)
2. Use `inswapper_128` ONNX model to perform pixel-perfect replacement
3. Handles varying lighting, pose angles (within ~45° of front)
4. **REQUIRES ~80x80px+ face region** — below that, detection fails

### Mode 2: Skeleton-guided paste (fallback)
When Mode 1 fails (face too small, occlusion):
1. Use MediaPipe 33-landmark skeleton data to locate nose/ears/mouth
2. Compute face bounding box from keypoints (2x radius)
3. Resize user's face crop + alpha-blend with 0.7 opacity

## Critical finding (2026-06-03)

**MimicMotion output (576p) face region is ~24x24 pixels** — too small for InsightFace detection. The skeleton fallback pastes the face at correct position but at very low resolution. The visual impact is marginal on the combined training video.

**True value of InsightFace lies elsewhere:**

| Use case | Resolution | Face size | Works? | Product value |
|:---------|:----------:|:---------:|:------:|:-------------:|
| User selfie + avatar card | ~1280px face | 300x400px | ✅ Perfect | Social sharing 🔥 |
| User training video (720p+ compare page) | 720-1080p | 80-200px | ✅ Great | Core paid feature 🔥 |
| MimicMotion 576p output | 576p | ~24px | ❌ Too small | Not recommended |
| MimicMotion 720p output (future) | 720p | ~50px | ✅ Maybe | Upgrade path |

## Product strategy

The face swap feature is gated behind `feature="coach_booking"` (Pro tier, ¥29.9/month). Three operating modes:

| Mode | Description | When to use |
|:-----|:------------|:------------|
| `stub` | Local skeleton animation, no real face swap | Development, demo |
| `autodl` | SSH to AutoDL → MimicMotion inference → face swap | Production (requires `AUTODL_HOST`+`PORT`+`PASS` env vars) |
| `local` | Local GPU (≥8GB VRAM) | Self-hosted, offline |

Currently `autodl=False` and `local=False` — only stub is active until AutoDL is turned on.

## Available skills (9)

```python
AVAILABLE_SKILLS = [
    {"id": "smash_stand", "name": "原地杀球", "icon": "🔨"},
    {"id": "smash_jump",  "name": "跳杀", "icon": "🦅"},
    {"id": "clear_fh",    "name": "正手高远球", "icon": "🏸"},
    {"id": "clear_bh",    "name": "反手高远球", "icon": "🔄"},
    {"id": "drop_stand",  "name": "原地吊球", "icon": "🪶"},
    {"id": "net_front",   "name": "网前球", "icon": "🎯"},
    {"id": "footwork_def", "name": "防守步法", "icon": "🏃"},
    {"id": "defense",     "name": "防守反击", "icon": "🛡️"},
    {"id": "serve_fh",    "name": "正手发球", "icon": "✋"},
]
```

## Skeleton auto-find

`_find_skeleton(skill_id)` scans `badminton-label-system/data/skeletons/bilibili/` (1,884 files) by keyword mapping. Caches results in `_SKEL_CACHE` to avoid re-scanning.

## Installation

```bash
pip install insightface onnxruntime
# macOS (Apple Silicon):
# pip install insightface onnxruntime-silicon
#   ⚠️ CoreML provider has a shape-rank bug with buffalo_l detection — use CPUExecutionProvider only

# Model files auto-download on first use:
#   ~/.insightface/models/buffalo_l/  (275MB, face detection + recognition)
#   ~/.insightface/models/inswapper_128.onnx  (529MB, face swap)
# Manual download (if auto-download fails with SSL errors):
# curl -L -o ~/.insightface/models/buffalo_l.zip "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
# unzip -q -d ~/.insightface/models/buffalo_l/ ~/.insightface/models/buffalo_l.zip
# curl -L -o ~/.insightface/models/inswapper_128.onnx \
#   "https://github.com/deepinsight/insightface/releases/download/v0.7/inswapper_128.onnx"
```

## Verified test

```python
from badminton_coach.face_swap import FaceSwapper
swapper = FaceSwapper()

# Single image:
out = "swap.jpg"
img = cv2.imread("user.jpg")
src = cv2.imread("photo.jpg")
src_faces = swapper._detect_face(src)
result = swapper.swap_face(img, src_faces[0])
cv2.imwrite(out, result)

# Video with skeleton fallback:
result = swapper.swap_video("input.mp4", "photo.jpg", "output.mp4",
                            skeleton_path="data.json", max_frames=20)

# Generate skeleton demo (no AutoDL needed):
from badminton_coach.face_swap import generate_face_swap
result = generate_face_swap("photo.jpg", "smash_stand", "output.mp4", mode="stub")
print(result)  # {"ok": True, "video_url": "...", "message": "..."}
```

## Common pitfalls

1. **numpy version conflict**: onnxruntime-silicon requires numpy<2. System Python on macOS 15 may have numpy 2.x. Fix: `pip3 install 'numpy<2' --force-reinstall`. Note: opencv-python 4.13 requires numpy>=2 and will show incompatibility warnings — they are non-fatal; both InsightFace and OpenCV work with numpy 1.26.4.

2. **Buffalo_l download fails with SSL errors**: The built-in downloader in `insightface` uses requests/urllib3 which may hit `[SSL: BLOCK_CIPHER_PAD_IS_WRONG]` on certain networks. Fix: use `curl -L` to download manually (see Installation section above).

3. **Image load fails silently**: `cv2.imread()` returns `None` for corrupted or unsupported files. Always check `img is not None` before passing to `app.get()`.
