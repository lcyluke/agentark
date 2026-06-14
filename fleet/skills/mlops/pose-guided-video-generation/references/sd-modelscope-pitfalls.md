# SD 1.5 ModelScope Download Pitfalls (AutoDL China, 2026-06-03)

## The Problem

ModelScope downloads from inside China (AutoDL) frequently leave SD 1.5 UNet safetensors **corrupted** — the file has full size (1.48GB, 686 tensors) but `safetensors.torch.load_file()` raises `Error while deserializing header: incomplete metadata, file not fully covered`. The file's header metadata doesn't cover all bytes, meaning the tail of the file is random data scraped from the temp dir.

## Root Cause

`snapshot_download` manages large files (>500MB) poorly from AutoDL's relay. It writes to `._____temp/` and moves to final dir on completion, but if interrupted even briefly, the final file in the snapshot directory is a broken copy of a partially-downloaded temp file. The temp file itself may be correct (>1.4GB) but the strategic copy is wrong.

## Symptom

```python
from diffusers import UNet2DConditionModel
# FAILS with:
# OSError: Unable to load weights from checkpoint file for 'unet/diffusion_pytorch_model.safetensors'
```

The file passes `struct.unpack` checks but `safetensors.torch.load_file()` catches it.

## Fix

```bash
# 1. Delete the corrupted file
rm -f /path/to/SD1.5/unet/diffusion_pytorch_model.safetensors

# 2. Manually copy from temp (which has the correct version)
cp /path/to/SD1.5/._____temp/AI-ModelScope/stable-diffusion-v1-5/unet/diffusion_pytorch_model.safetensors \
   /path/to/SD1.5/unet/diffusion_pytorch_model.safetensors

# 3. Verify
python3 -c "
import json, struct
with open('/path/to/SD1.5/unet/diffusion_pytorch_model.safetensors', 'rb') as f:
    h = struct.unpack('<Q', f.read(8))[0]
    content = f.read(h)
    data = json.loads(content)
    tensors = [k for k in data if k != '__metadata__']
    print(f'VALID: {len(tensors)} tensors')
"
```

Expected output: `VALID: 686 tensors`

## Prevention

For future downloads, prefer `model_file_download()` for each individual large file rather than `snapshot_download()`. Monitor the `._____temp/` directory size (should match expected ~1.4GB for UNet). If it stops growing for >3 minutes, cancel and retry.

## Tokenizer Fix

ModelScope's SD 1.5 download also misses vocab.json for the tokenizer. Generate it:
```python
from transformers import CLIPTokenizer
CLIPTokenizer.from_pretrained("openai/clip-vit-large-patch14").save_pretrained("./tokenizer")
```

## Component-by-Component Pipeline Build

When `from_pretrained()` fails due to model_index config, build from components:

```python
from diffusers import UNet2DConditionModel, AutoencoderKL, DDIMScheduler
from transformers import CLIPTextModel, CLIPTokenizer
from diffusers import StableDiffusionPipeline
import torch

unet = UNet2DConditionModel.from_config(f"{path}/unet")
unet.load_state_dict(safetensors.torch.load_file(f"{path}/unet/diffusion_pytorch_model.safetensors"), strict=False)

vae = AutoencoderKL.from_pretrained(f"{path}/vae")
text_encoder = CLIPTextModel.from_pretrained(f"{path}/text_encoder")
tokenizer = CLIPTokenizer.from_pretrained(f"{path}/tokenizer")
scheduler = DDIMScheduler.from_pretrained(f"{path}/scheduler")

pipe = StableDiffusionPipeline(
    vae=vae, text_encoder=text_encoder, tokenizer=tokenizer,
    unet=unet, scheduler=scheduler, safety_checker=None,
    feature_extractor=None, requires_safety_checker=False,
)
pipe = pipe.to("cuda", dtype=torch.float16)
```
