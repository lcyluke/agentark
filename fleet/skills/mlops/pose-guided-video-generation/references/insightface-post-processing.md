# InsightFace Post-Processing Pipeline

Integration notes for adding face-swap as a post-processing step after MimicMotion video generation.

## When to use

After MimicMotion generates a video of a person (using the skeleton + reference photo), run InsightFace's `inswapper_128` ONNX model per-frame to swap the face with the user's own photo. This produces a **more accurate** face swap than MimicMotion's implicit identity preservation (which can produce a generic face rather than the user's exact face).

## Resolution boundary

| Output resolution | Face size (approximate) | InsightFace detection | Recommendation |
|:-----------------|:-----------------------:|:---------------------:|:--------------|
| 576×1024 | ~24×24 px | ❌ Fails | Skip InsightFace |
| 720×1280 | ~50×50 px | ⚠️ Marginal | Try with fallback |
| 1080×1920 | ~100×100 px | ✅ Reliable | Always use |

MimicMotion's default output is 576p. To get higher resolution, increase the `height`/`width` parameters passed to the pipeline (note: this increases VRAM usage — 720p requires ~16GB, 1080p requires 24GB+).

## Dual-mode strategy

The `FaceSwapper.swap_video()` method implements a two-mode strategy:

1. **Primary**: InsightFace face detection → `inswapper_128` ONNX inference per frame
   - Accurate pixel-level alignment, skin tone blending, edge matching
   - Requires face to be large enough for detection
   - Re-detects face every N frames (configurable via `face_detect_every_n`)

2. **Fallback**: Skeleton-guided face paste
   - Uses MediaPipe 33-landmark keypoints (nose 0, ears 7/8, mouth 9/10) to locate face
   - Computes bounding box from keypoint spread × 1.5 radius
   - Crops user face from source photo, resizes to target, alpha-blends (0.7 user / 0.3 target)
   - Lower quality than Mode 1 but always works when skeleton data is available

## Prerequisites

```bash
pip install insightface onnxruntime
# For CUDA acceleration: pip install onnxruntime-gpu
# For Apple Silicon: pip install onnxruntime-silicon
#   ⚠️ CoreML provider has shape-rank bug with buffalo_l detection on Apple Silicon
#   Use providers=['CPUExecutionProvider'] instead of ['CoreMLExecutionProvider', 'CPUExecutionProvider']
```

Model files auto-download on first use (~800MB total):
- `~/.insightface/models/buffalo_l/` — face detection + 68-landmark detector + recognition (275MB)
- `~/.insightface/models/inswapper_128.onnx` — face swap model (529MB)

## Verbatim integration into autodl_batch.py

After MimicMotion generates the video + skeleton breakdown composes the combined video, add this as Step 5:

```python
from badminton_coach.face_swap import FaceSwapper
swapper = FaceSwapper()
result = swapper.swap_video(
    "combined_train_video.mp4",
    "user_photo.jpg",
    "output_swapped.mp4",
    skeleton_path="skeleton_data.json",
    max_frames=72,
    show_progress=False,
)
```

## AutoDL deployment (verified 2026-06-03)

On AutoDL inside China, InsightFace models must be downloaded from GitHub:

```bash
# buffalo_l (5 ONNX files, 275MB)
mkdir -p ~/.insightface/models
cd ~/.insightface/models
curl -L --retry 3 -o buffalo_l.zip \
  "https://github.com/deepinsight/insightface/releases/download/v0.7/buffalo_l.zip"
unzip -q buffalo_l.zip -d buffalo_l/

# inswapper_128 (529MB — this file downloads slowly from AutoDL, ~2-3 min)
curl -L --retry 3 -o inswapper_128.onnx \
  "https://github.com/deepinsight/insightface/releases/download/v0.7/inswapper_128.onnx"
```

Note: GitHub.com is accessible from AutoDL (unlike HuggingFace which is blocked). Downloads are at ~3-4 MB/s with curl. The final directory should have:
```
~/.insightface/models/
├── buffalo_l/
│   ├── 1k3d68.onnx (137MB)
│   ├── 2d106det.onnx (5MB)
│   ├── det_10g.onnx (16MB)
│   ├── genderage.onnx (1.3MB)
│   └── w600k_r50.onnx (166MB)
└── inswapper_128.onnx (529MB)
```

## Performance on AutoDL (CPU-only, no CUDAExecutionProvider)

On AutoDL with onnxruntime (CUDA 13.2 is too new — CUDA 13.x. CUDAExecutionProvider not available):
- Face detection (buffalo_l): ~0.1s/frame
- Face swap (inswapper_128): ~0.6s/frame
- Video 72 frames: ~50s total (detection cached every 5 frames)

## numpy<2 confirmed compatible

The `numpy<2` fix was verified (2026-06-03): after `pip3 install 'numpy<2' --force-reinstall`, onnxruntime 1.19.x loads successfully. OpenCV 4.13.0 emits a warning about `numpy>=2` requirement but works fine functionally. The warning is cosmetic.

- InsightFace `inswapper_128` is trained on front-facing faces — extreme angles (>60° from camera) produce poor results
- The skeleton fallback paste does NOT match skin tone or face orientation — the user may notice the pasted face doesn't match the body's lighting
- Face swap currently does NOT modify clothing, hair color, or body shape
- **onnxruntime + numpy 2 incompatibility**: `onnxruntime` 1.19.2+ and insightface require `numpy<2`. If the environment has numpy 2.x (`numpy 2.0.2`), onnxruntime crashes at import with `AttributeError: _ARRAY_API not found / ImportError: numpy.core.multiarray failed to import`. Fix: `pip install 'numpy<2' --force-reinstall`. Note: this may break other packages like OpenCV 4.13+ which require `numpy>=2` — test after the downgrade.
- **CoreML on Apple Silicon**: Use `CPUExecutionProvider` only, not `CoreMLExecutionProvider`, for both buffalo_l and inswapper_128. CoreML's ONNX runtime has a shape rank bug (`({1,1,1,800,1}) vs ({3200,1})`) on Apple Silicon M1 Pro.

## Troubleshooting: InsightFace detects 0 faces

If `app.get(img)` returns 0 faces on photos that clearly contain faces:

1. **`det_size` not sticking after `prepare()`**: `app.prepare(ctx_id=0, det_size=(320, 320))` sets `app.det_model.input_size` but it may not persist across calls. After `prepare()`, override:
   ```python
   app = FaceAnalysis(name='buffalo_l', providers=['CPUExecutionProvider'])
   app.prepare(ctx_id=0, det_size=(320, 320))
   app.det_model.input_size = (320, 320)  # explicit override
   app.det_thresh = 0.5
   ```

2. **Face too small for default det_size**: For 1707×1280 photos with a person, face may be ~60×80px — detectable at det_size=320, missed at det_size=640 (downsampled too much). For small faces try det_size=(224, 224).

3. **`.get()` returns 0 on second+ calls** (rare singleton race): If first call works but subsequent calls return 0 on the same image, this is a non-deterministic singleton state issue. Call `.get()` with `max_num=1` to limit search space.

4. **MimicMotion 576p output has ~24×24 pixel faces** — below detection threshold. Use skeleton-guided fallback only. Upgrade to 720p+ for real swaps.

## Apple Silicon CoreML bug

When using `onnxruntime-silicon` with `CoreMLExecutionProvider`, buffalo_l's `det_10g.onnx` crashes:
```
CoreML static output shape ({1,1,1,800,1}) and inferred shape ({3200,1}) have different ranks.
```

**Fix:** Use `providers=['CPUExecutionProvider']` for BOTH `FaceAnalysis` AND `get_model('inswapper_128.onnx')` on Apple Silicon. Detection model (5MB ONNX) runs fine on CPU in ~0.6s. Swapper model (529MB) takes ~1.5s/image on CPU. Do NOT mix providers — `['CoreMLExecutionProvider', 'CPUExecutionProvider']` causes CoreML compilation failure before CPU fallback.
