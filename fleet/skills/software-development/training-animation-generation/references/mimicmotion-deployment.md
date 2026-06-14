# MimicMotion Pose-Guided Video Generation for Badminton

Deploy [Tencent MimicMotion](https://github.com/Tencent/MimicMotion) for action migration: take a user's selfie + a B站 pro skeleton sequence → generate video of the user performing the same badminton stroke.

## Architecture

```
用户照片 (selfie.jpg) ─┐
                        ├──→ MimicMotionPipeline ──→ 🎬 output.mp4
B站骨骼JSON (MediaPipe) ─┘
       ↓
  run_mimic.py: render_mediapipe_skel()
       → 33 MediaPipe landmarks → 576×1024 skeleton image sequence
       → MimicMotion (SVD + PoseNet) → user doing the stroke
```

## Model Weights Required (total ~8GB)

| Model | Source | Size | Gated? |
|-------|--------|------|--------|
| SVD base | `stabilityai/stable-video-diffusion-img2vid-xt-1-1` | ~5GB | ✅ Auto (need license agreement) |
| MimicMotion finetune | `tencent/MimicMotion` (MimicMotion_1-1.pth) | ~3GB | ❌ Open |

## Installation

```bash
cd ~/Desktop/2026AIAPP/MimicMotion

# Dependencies
pip install diffusers omegaconf torch torchvision opencv-python pillow imageio

# Source code (23 files from GitHub raw)
# Already cloned to ~/Desktop/2026AIAPP/MimicMotion/
```

## Running Inference

```bash
# Prerequisites: 5GB+ free RAM/VRAM, model weights downloaded
python3 run_mimic.py \
  --ref_img selfie.jpg \        # User portrait/selfie
  --skill smash_stand \          # Skill ID (or --skel path/to/skel.json)
  --steps 25 \                   # 15-50, higher = better quality
  --guidance 2.0 \               # 1.0-3.0
  --stride 2 \                   # Larger = faster movement
  --device mps                   # mps (Apple), cuda, cpu
```

## Our Advantages

- **3,446 skeleton JSONs already extracted** (876,715 frames, 97.8% tracking rate)
- MediaPipe 33-landmark format → MimicMotion's DWPose format via `render_mediapipe_skel()`
- 497 high-quality clips (≥5s, avg 10-15s) in `data/training_clips/`

## Memory Constraints

| Device | Specs | Feasibility |
|--------|-------|-------------|
| M1 Pro 16GB | MPS 14GB shared | ⚠️ Tight (SVD alone uses ~4GB unet) |
| RTX 4090 24GB | CUDA | ✅ Comfortable |
| RTX 3090 24GB | CUDA | ✅ Comfortable |
| T4 16GB (cloud) | CUDA | ✅ Works with fp16 |

On M1, try: `--steps 15`, `decode_chunk_size 4`, `tile_size 14` to reduce memory.
