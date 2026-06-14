# MimicMotion from China (AutoDL) — Verified Recipe

## Instance: connect.bjb2.seetacloud.com:32581 | root | RTX 4090 D (24GB) | Ubuntu 22.04

## Network reality from inside China (verified 2026-06-01)

| Resource | Open models | Gated models | Speed |
|----------|:-----------:|:------------:|:-----:|
| HuggingFace direct | ❌ Blocked (CloudFront) | ❌ Blocked | — |
| `hf-mirror.com` curl | ✅ Works | ❌ 401 even with Bearer token | ~1-3 MB/s |
| ModelScope `modelscope.cn` | ✅ Works | ✅ Works | ~3-4 MB/s |
| `huggingface_hub` Python lib | ❌ Blocked | ❌ Blocked | — |
| GitHub.com git clone | ❌ Blocked | N/A | — |
| GitHub via `ghproxy.com` | ❌ Blocked (DNS) | N/A | — |

## Dependency version matrix (fragile!)

Starting from AutoDL defaults (torch 2.5.1+cu124, torchvision 0.20.1+cu124):

```bash
# WITHOUT xformers (keep torch 2.5.1):
pip install "diffusers[torch]==0.30.3" "huggingface-hub==0.25.2" "transformers==4.46.3" \
  accelerate opencv-python-headless "imageio[ffmpeg]" einops decord modelscope -q
pip install "torchvision==0.19.1" -q

# WITH xformers (downgrades torch to 2.4.1):
pip install xformers==0.0.28  # auto-downgrades torch
pip install "diffusers[torch]==0.27.2" "huggingface-hub==0.24.7" -q
```

## File transfer patterns

### RELIABLE (use these):
```bash
# Small files (<100KB): pipe through cat | ssh
cat local_script.py | sshpass -p 'PWD' ssh -p PORT root@HOST \
  "cat > /remote/path/target.py"

# Code tarballs (50KB-1MB): tar and pipe
tar czf /tmp/code.tar.gz dir1/ dir2/
cat /tmp/code.tar.gz | sshpass -p 'PWD' ssh -p PORT root@HOST \
  "cd /remote/path && tar xzf -"

# Large files (>1MB): nohup + curl on the server is faster than uploading
```

### UNRELIABLE (avoid):
- SCP through AutoDL relay — times out on files >500KB
- Base64-encoded scripts via echo — gets corrupted by shell interpretation

### Long-running processes:
```bash
# Use nohup (screen dies on AutoDL restart):
nohup python3 -u script.py > output/run.log 2>&1 &
# Check: tail -f output/run.log

# For process isolation:
sshpass -p 'PWD' ssh -p PORT root@HOST \
  "cd /project && nohup python3 -u run.py > out.log 2>&1 & echo PID=$!"
```

## Green-screen video fix

When `cv2.VideoWriter(*"mp4v")` produces a video that plays as a solid green rectangle:

```bash
# The fix: use imageio with libx264 instead
pip install "imageio[ffmpeg]"
python3 -c "
import imageio
w = imageio.get_writer('output.mp4', fps=8, codec='libx264', quality=8)
w.append_data(numpy_frame)  # RGB numpy array (H, W, 3)
w.close()
"
```

OpenCV's mp4v codec on AutoDL/headless Linux produces broken MP4 that macOS QuickTime and VLC decode as green. imageio + libx264 always works.

## Model download time estimates (RTX 4090 D, ~3 MB/s avg)

| File | Size | Est. Time |
|------|:----:|:---------:|
| MimicMotion_1-1.pth | 2.9 GB | ~15 min |
| SVD unet fp16 | 2.84 GB | ~15 min |
| SVD image_encoder fp32 | 2.35 GB | ~12 min |
| SVD image_encoder fp16 | 1.18 GB | ~6 min |
| SVD vae fp32 | 373 MB | ~2 min |
| SVD vae fp16 | 187 MB | ~1 min |
| All 16 files | ~10.5 GB | ~50 min |

## Inference benchmark (RTX 4090 D, 24GB VRAM)

| Frames | Steps | Time | Peak VRAM | Output |
|:------:|:-----:|:----:|:---------:|:------:|
| 12 | 10 | 17s | 8.8 GB | 468 KB |
| 72 | 25 | 3m34s | 17.6 GB | 3.8 MB |
| 72 | 25 | ~4m | 17.6 GB | ~4 MB |

## Known failure modes

1. **`_execution_device` crash**: `AttributeError: property '_execution_device' of 'MimicMotionPipeline' object has no setter`. Fix: pass `device=torch.device("cuda")` as a kwarg to `pipeline.__call__()`. Do NOT call `pipeline.to(device)`.

2. **`IndexError: list index out of range` in tiling**: `tile_size` (default 16) must be <= `num_frames`. For short clips (12 frames), set `tile_size=12, tile_overlap=0`.

3. **`SyntaxError: illegal target for annotation (404: Not Found)`**: You imported from `mimicmotion.models.*`. Those files contain only the text "404: Not Found". Import from `mimicmotion.modules.*` instead.

4. **Green-screen video**: You used `cv2.VideoWriter`. Switch to `imageio.get_writer(..., codec='libx264')`.

5. **Python3 not found**: AutoDL's default shell doesn't have `/root/miniconda3/bin` on PATH. Use full path or `source /root/miniconda3/bin/activate`.

6. **Pip install hangs on large packages**: AutoDL uses Aliyun mirror which is slow for 797MB packages like torch. Allow 5-10 minutes — it's not frozen, just slow.
