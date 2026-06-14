# SD 1.5 + ControlNet Pipeline (Alternative to MagicAnimate)

Used when MagicAnimate's custom magic-animate specific weights (appearance_encoder, temporal unet) fail to download from ModelScope. Falls back to standard diffusers components that are available on ModelScope.

## Architecture

```
Reference photo → img2img ControlNet pipeline (逐帧, no temporal consistency)
Pose sequence → ControlNet OpenPose (骨骼引导)
```

**Key limitation**: This generates each frame independently — no temporal attention. Expect flickering. Only use as a fallback.

## Required Models (from ModelScope)

| Model | ModelScope ID | Critical Files | Size | 
|-------|:-------------|:---------------|:----:|
| SD 1.5 | `AI-ModelScope/stable-diffusion-v1-5` | `unet/diffusion_pytorch_model.safetensors` | 1.4GB |
| ControlNet OpenPose | `iic/control_v11p_sd15_openpose` | Full model | ~1.5GB |

## Known Failure Patterns (AutoDL 2026-06-03)

### 1. ModelScope `snapshot_download` Hangs

`snapshot_download("AI-ModelScope/stable-diffusion-v1-5")` hangs on files >1GB. ALWAYS use `file_download()` for individual files:

```python
from modelscope.hub.file_download import model_file_download

# OK — downloads one file at a time (works for 1.4GB UNet)
model_file_download("AI-ModelScope/stable-diffusion-v1-5", 
    "unet/diffusion_pytorch_model.safetensors",
    cache_dir="/root/autodl-tmp/models", revision="master")

# HANGS — do NOT use for any model with >500MB files:
# from modelscope.hub.snapshot_download import snapshot_download
# snapshot_download("AI-ModelScope/stable-diffusion-v1-5", ...)  # HANGS on UNet
```

### 2. UNet Safetensors File Corruption

After download, the UNet file may appear valid (`ffprobe` shows 454MB or 1.4GB) but has `incomplete metadata, file not fully covered`. This happens when a previous download goes to a cache temp dir and gets partially moved.

**Diagnosis:**
```python
from safetensors import safe_open
with safe_open("unet/diffusion_pytorch_model.safetensors", framework="pt") as f:
    keys = f.keys()   # ← raises "incomplete metadata" if corrupted
```

**Fix:** Delete the file and re-download fresh:
```bash
rm -f unet/diffusion_pytorch_model.safetensors
rm -rf /root/autodl-tmp/models/._____temp/
```

If ModelScope keeps downloading the wrong version (it may pull a 454MB combined file instead of the 1.4GB component), manually copy from the temp directory after download completes:
```bash
cp /root/autodl-tmp/models/._____temp/AI-ModelScope/stable-diffusion-v1-5/unet/diffusion_pytorch_model.safetensors \
   /root/autodl-tmp/models/AI-ModelScope/stable-diffusion-v1-5/unet/diffusion_pytorch_model.safetensors
```

### 3. Missing `tokenizer/vocab.json`

ModelScope does NOT download `tokenizer/vocab.json` for SD 1.5. The tokenizer directory will contain `merges.txt`, `special_tokens_map.json`, `tokenizer_config.json` but NOT `vocab.json`. This causes:

```
TypeError: expected str, bytes or os.PathLike object, not NoneType
```

**Fix:** Reconstruct `vocab.json` from `merges.txt`:
```python
import json
with open("tokenizer/merges.txt") as f:
    lines = f.readlines()
merges = [l.strip().split() for l in lines[1:] if l.strip()]
vocab = {}
for i in range(256):
    vocab[chr(i)] = i
vocab["<|startoftext|>"] = 49406
vocab["<|endoftext|>"] = 49407
for i, pair in enumerate(merges[:49152]):
    vocab["".join(pair)] = i + 256
with open("tokenizer/vocab.json", "w") as f:
    json.dump(vocab, f, ensure_ascii=False)
```

### 4. Model `variant` Mismatch

If `model_index.json` contains `"variant": "fp16"`, the pipeline tries to load `diffusion_pytorch_model.fp16.safetensors` which doesn't exist for full-precision downloads.

**Fix:** Remove the variant key from `model_index.json`.

## ControlNet from ModelScope

`iic/control_v11p_sd15_openpose` downloads cleanly via `snapshot_download` (all files are small). The critical issue is that ModelScope places it at:
```
$cache_dir/iic/control_v11p_sd15_openpose/
```
But when loading with `ControlNetModel.from_pretrained()`, you need to point to that exact path. It's NOT under a `models/` subdirectory.

## Complete Pipeline Code

```python
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel
import torch, numpy as np
from PIL import Image

SD_PATH = "/root/autodl-tmp/models/AI-ModelScope/stable-diffusion-v1-5"
CN_PATH = "/root/autodl-tmp/models/iic/control_v11p_sd15_openpose"

controlnet = ControlNetModel.from_pretrained(CN_PATH, torch_dtype=torch.float16)
pipe = StableDiffusionControlNetPipeline.from_pretrained(
    SD_PATH, controlnet=controlnet, torch_dtype=torch.float16,
    safety_checker=None, requires_safety_checker=False,
)
pipe = pipe.to("cuda")
pipe.enable_xformers_memory_efficient_attention()
pipe.enable_vae_slicing()

# For each frame:
with torch.autocast("cuda"):
    result = pipe(
        prompt="a person playing badminton",
        image=ref_img,           # the reference photo (img2img)
        control_image=pose_img,  # skeleton render (ControlNet)
        num_inference_steps=20,
        strength=0.8,            # how much to preserve reference
        generator=torch.Generator("cuda").manual_seed(frame_idx),
    )
```
