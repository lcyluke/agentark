# AnimateAnyone / Moore-AnimateAnyone Weight Download (2026-06-04 Session)

## Repo: `patrolli/AnimateAnyone` (4 files)

| File | Verified Size | SHA (quick verify) |
|:----|:-------------:|:-------------------|
| `denoising_unet.pth` | 3.2 GB | ZIP/torch save, 3.2 GB exact |
| `motion_module.pth` | 441 MB | OK |
| `pose_guider.pth` | 4.1 MB | OK |
| `reference_unet.pth` | 1.2 GB | OK |

All from: `https://huggingface.co/patrolli/AnimateAnyone/resolve/main/{filename}`

## Repo: `lambdalabs/sd-image-variations-diffusers` (2 files)

| File | Verified Size | Note |
|:----|:-------------:|:-----|
| `image_encoder/config.json` | 703 B | CLIPVisionModelWithProjection, 1024 hidden dim, 24 layers, patch_size=14 |
| `image_encoder/pytorch_model.bin` | **1.22 GB** | ZIP archive (torch save), 395 entries, EOCD valid |

Both from subfolder `image_encoder/`:
`https://huggingface.co/lambdalabs/sd-image-variations-diffusers/resolve/main/image_encoder/{filename}`

## ⚠️ CRITICAL: Cross-Repo Dependency

DO NOT try to fetch `image_encoder/pytorch_model.bin` from `patrolli/AnimateAnyone` — it returns **HTTP 404**.
The Moore-AnimateAnyone `tools/download_weights.py` script is the canonical source of truth for which repo each file belongs to.

## Download Verification Method

After downloading a torch `.bin` file, verify completeness by checking if it's a valid ZIP:

```python
import zipfile
try:
    with zipfile.ZipFile(path) as z:
        names = z.namelist()
        total = sum(z.getinfo(n).compress_size for n in names)
        print(f"Valid — {len(names)} entries, {total/1e9:.2f} GB")
except zipfile.BadZipFile:
    print("INCOMPLETE — truncated download")
```

This works because PyTorch `.bin` files are internally ZIP archives (torch.save format).

## ⚠️ HF HEAD Request Pitfall

`curl -sI` on HuggingFace model files returns **Content-Length: 117** for Git LFS pointers, NOT the real file size.
The actual file (`image_encoder/pytorch_model.bin`) is 1.22 GB even though the HEAD response says 117 bytes.
**Always download and check actual file size, don't trust HEAD response Content-Length.**

## Download Command (Mac, HF works directly)

```bash
# AnimateAnyone weights (4 files)
BASE="https://huggingface.co/patrolli/AnimateAnyone/resolve/main"
curl -L -C - --retry 5 --retry-delay 15 --connect-timeout 30 -o /tmp/denoising_unet.pth "$BASE/denoising_unet.pth"
curl -L -C - --retry 5 --retry-delay 15 --connect-timeout 30 -o /tmp/motion_module.pth "$BASE/motion_module.pth"
curl -L -C - --retry 5 --retry-delay 15 --connect-timeout 30 -o /tmp/pose_guider.pth "$BASE/pose_guider.pth"
curl -L -C - --retry 5 --retry-delay 15 --connect-timeout 30 -o /tmp/reference_unet.pth "$BASE/reference_unet.pth"

# Image encoder (DIFFERENT REPO!)
mkdir -p /tmp/image_encoder
IE="https://huggingface.co/lambdalabs/sd-image-variations-diffusers/resolve/main/image_encoder"
curl -fsSL -o /tmp/image_encoder/config.json "$IE/config.json"
curl -fsSL -C - --retry 5 --retry-delay 15 --connect-timeout 30 \
  -o /tmp/image_encoder/pytorch_model.bin "$IE/pytorch_model.bin"
```
