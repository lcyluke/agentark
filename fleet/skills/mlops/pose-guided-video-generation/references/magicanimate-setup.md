# MagicAnimate Setup for Badminton AI Coach

## Why MagicAnimate Over MimicMotion

| Factor | MagicAnimate | MimicMotion |
|--------|:------------:|:-----------:|
| ReferenceNet (identity preservation) | Yes | No |
| Output reliability | Generates actual humans | Produces skeleton renders unless meticulously tuned |
| VRAM | ~8GB | ~8.5GB |
| Speed (RTX 4090, 48 frames) | ~12s (~4fps) | ~180s (~0.4fps) |
| License | Apache 2.0 | MIT |
| ModelScope download | `zcxu-eric/magic-animate` | `tencent/MimicMotion` from hf-mirror |

## Architecture

Reference photo -> AppearanceEncoder (ReferenceNet) -> UNet3D (temporal) -> Video
Pose sequence -> ControlNet (OpenPose) -> UNet3D (temporal) -> Video

## Required Models (from ModelScope)

| Model | From | Files | Total Size |
|-------|:----|:------|:----------:|
| SD 1.5 | `AI-ModelScope/stable-diffusion-v1-5` | unet/vae/text_encoder/tokenizer + configs | ~2.1GB |
| ControlNet OpenPose | `iic/control_v11p_sd15_openpose` | Full ControlNet | ~1.5GB |
| Appearance Encoder | `zcxu-eric/magic-animate` | `appearance_encoder.pth` | ~1.3GB |
| Denoising UNet (temporal) | `zcxu-eric/magic-animate` | `denoising_unet.pth` | ~3.1GB |

## CRITICAL: ModelScope snapshot_download Limitation

`snapshot_download` can HANG on files >2GB (verified on AutoDL 2026-06-03). Always use `file_download()` for individual large files. DO NOT use `snapshot_download` for SD 1.5 (hangs on unet/diffusion_pytorch_model.safetensors at 1.4GB).

## Step 1: SD 1.5 (download files individually)

```
mkdir -p AI-ModelScope/stable-diffusion-v1-5/unet
mkdir -p AI-ModelScope/stable-diffusion-v1-5/vae
mkdir -p AI-ModelScope/stable-diffusion-v1-5/text_encoder
mkdir -p AI-ModelScope/stable-diffusion-v1-5/tokenizer
mkdir -p AI-ModelScope/stable-diffusion-v1-5/scheduler
mkdir -p AI-ModelScope/stable-diffusion-v1-5/feature_extractor
mkdir -p AI-ModelScope/stable-diffusion-v1-5/safety_checker
```

```python
from modelscope.hub.file_download import model_file_download
SD = "AI-ModelScope/stable-diffusion-v1-5"
CACHE = "/root/autodl-tmp/models"

# Config files first
for f in [
    "model_index.json", "unet/config.json", "vae/config.json",
    "vae/diffusion_pytorch_model.safetensors",
    "text_encoder/config.json", "text_encoder/model.safetensors",
    "tokenizer/merges.txt", "tokenizer/special_tokens_map.json",
    "tokenizer/tokenizer_config.json",
    "scheduler/scheduler_config.json",
    "feature_extractor/preprocessor_config.json",
]:
    path = model_file_download(SD, f, cache_dir=CACHE, revision="master")

# UNet (1.4GB, 5-10min download)
path = model_file_download(SD, "unet/diffusion_pytorch_model.safetensors",
    cache_dir=CACHE, revision="master")

# safety_checker (optional)
model_file_download(SD, "safety_checker/model.safetensors", cache_dir=CACHE, revision="master")
```

### Token file fix

ModelScope doesn't download `tokenizer/vocab.json`. Create from merges.txt:

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

### Variant fix

If model_index.json has "variant": "fp16", remove it (the downloaded files are full-precision).

## Step 2: ControlNet OpenPose

```python
from modelscope.hub.snapshot_download import snapshot_download
model_dir = snapshot_download("iic/control_v11p_sd15_openpose",
    cache_dir="/root/autodl-tmp/models", revision="master")
```

ControlNet files are smaller -- snapshot_download works fine.

## Step 3: MagicAnimate Weights

```python
from modelscope.hub.file_download import model_file_download
for fname in ["appearance_encoder.pth", "denoising_unet.pth"]:
    path = model_file_download("zcxu-eric/magic-animate", fname,
        local_dir="/root/autodl-tmp/magic-animate/pretrained_weights",
        revision="master")
```

## MediaPipe -> OpenPose Keypoint Mapping

```python
MEDIAPIPE_TO_OPENPOSE = [
    (0,0), (4,1), (1,2), (5,3), (2,4),   # face
    (11,5), (12,6),                       # shoulders
    (13,7), (14,8),                       # elbows
    (15,9), (16,10),                      # wrists
    (23,11), (24,12),                     # hips
    (25,13), (26,14),                     # knees
    (27,15), (28,16),                     # ankles
    (29,17), (30,18),                     # heels
    (31,19), (32,20),                     # feet
]
```

## Environment Setup on AutoDL

```bash
# Use base env (diffusers 0.30.3 already installed)
pip install imageio[pyav] decord opencv-python-headless einops modelscope

# Alternative: dedicated conda env
conda create -y -n magicanimate python=3.10
conda install -y -n magicanimate pytorch torchvision pytorch-cuda=12.1 -c pytorch -c nvidia

# Clone from local (GitHub blocked from AutoDL):
#   git clone --depth 1 https://github.com/magic-research/magic-animate.git
#   tar czf core.tar.gz magicanimate/ configs/ requirements.txt --exclude='*.pth'
#   cat core.tar.gz | ssh ... "cat > /remote/magic.tar.gz && tar xzf -"
```

## Inference Structure

```python
from magicanimate.pipelines.pipeline_animation import AnimationPipeline
from magicanimate.models.unet import UNet3DConditionModel
from magicanimate.models.controlnet import ControlNetModel
from magicanimate.models.appearance_encoder import AppearanceEncoder

pipe = AnimationPipeline.from_pretrained("runwayml/stable-diffusion-v1-5", torch_dtype=torch.float16)
pipe.controlnet = ControlNetModel.from_pretrained("/path/controlnet", subfolder="controlnet", torch_dtype=torch.float16)
pipe.appearance_encoder = AppearanceEncoder.from_pretrained("/path/weights", subfolder="appearance_encoder", torch_dtype=torch.float16)
pipe.unet = UNet3DConditionModel.from_pretrained("/path/weights", subfolder="denoising_unet", torch_dtype=torch.float16)
pipe = pipe.to("cuda")
pipe.enable_xformers_memory_efficient_attention()

result = pipe(ref_image=ref_img, pose_images=pose_frames, width=512, height=768,
    num_inference_steps=25, guidance_scale=7.5,
    generator=torch.Generator("cuda").manual_seed(42))
```

## Pitfalls

1. **GitHub blocked from AutoDL.** Clone locally, tar core dir, upload via cat|ssh.
2. **ModelScope snapshot_download hangs on files >2GB.** Use file_download() individually.
3. **model_index.json may have "variant": "fp16"** that causes load failures. Remove that key.
4. **SD 1.5 tokenizer/vocab.json missing** from ModelScope. Reconstruct from merges.txt.
5. **SSH rate-limited** on AutoDL relay. Wait 3-5s between commands. Use screen for long ops.
6. **cat|ssh unreliable for >10MB** through AutoDL. Use SCP for large files, or split the tar.
7. **conda activate inside screen broken.** Use full paths: /root/miniconda3/envs/magicanimate/bin/python3
