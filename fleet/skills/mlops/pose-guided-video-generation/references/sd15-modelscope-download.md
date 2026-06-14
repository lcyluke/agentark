# SD 1.5 从 ModelScope 下载 — 实战经验 (2026-06-03)

## 核心问题

在 AutoDL 上从 ModelScope 下载 SD 1.5 最大的坑是：

**`snapshot_download()` 会在 >2GB 文件时 hang 死** — 进度条停在某个百分比不动了，5分钟以上无任何进展。必须 Ctrl+C 取消，用 `file_download()` 逐个下载。

## 需要下载的文件清单

SD 1.5 (`AI-ModelScope/stable-diffusion-v1-5`) 总共约 2.1GB，含以下文件：

| 文件 | 大小 | 下载方式 |
|:-----|:----:|:--------|
| `unet/diffusion_pytorch_model.safetensors` | 1.4GB | **file_download** (snapshot会hang) |
| `vae/diffusion_pytorch_model.safetensors` | 320MB | file_download OK |
| `text_encoder/model.safetensors` | 470MB | file_download OK |
| `safety_checker/model.safetensors` | ~200MB | file_download OK |
| config files (约10个 .json) | 几KB | file_download OK |

注意：ModelScope 的 `AI-ModelScope/stable-diffusion-v1-5` 不包含 `tokenizer/vocab.json`，需要从 `tokenizer/merges.txt` 重建。

## 下载脚本 (已验证可行)

```python
from modelscope.hub.file_download import model_file_download
import os

SD = "AI-ModelScope/stable-diffusion-v1-5"
CACHE = "/root/autodl-tmp/models"  # 会下载到 CACHE/AI-ModelScope/stable-diffusion-v1-5/

# 先建目录
os.makedirs(f"{CACHE}/AI-ModelScope/stable-diffusion-v1-5/unet", exist_ok=True)
os.makedirs(f"{CACHE}/AI-ModelScope/stable-diffusion-v1-5/vae", exist_ok=True)
os.makedirs(f"{CACHE}/AI-ModelScope/stable-diffusion-v1-5/text_encoder", exist_ok=True)
os.makedirs(f"{CACHE}/AI-ModelScope/stable-diffusion-v1-5/tokenizer", exist_ok=True)
os.makedirs(f"{CACHE}/AI-ModelScope/stable-diffusion-v1-5/scheduler", exist_ok=True)
os.makedirs(f"{CACHE}/AI-ModelScope/stable-diffusion-v1-5/feature_extractor", exist_ok=True)
os.makedirs(f"{CACHE}/AI-ModelScope/stable-diffusion-v1-5/safety_checker", exist_ok=True)

# 下载所有文件
files = [
    "model_index.json",
    "unet/config.json", "unet/diffusion_pytorch_model.safetensors",
    "vae/config.json", "vae/diffusion_pytorch_model.safetensors",
    "text_encoder/config.json", "text_encoder/model.safetensors",
    "tokenizer/merges.txt", "tokenizer/special_tokens_map.json", "tokenizer/tokenizer_config.json",
    "scheduler/scheduler_config.json",
    "feature_extractor/preprocessor_config.json",
    "safety_checker/model.safetensors",
]

for f in files:
    print(f"Downloading {f}...")
    path = model_file_download(SD, f, cache_dir=CACHE, revision="master")
    size = os.path.getsize(path) // (1024*1024)
    print(f"  OK ({size}MB)" if size > 0 else "  OK")
```

## Tokenizer 修复

ModelScope 下载的 SD 1.5 缺少 `tokenizer/vocab.json`。`from_pretrained()` 会报：
```
TypeError: expected str, bytes or os.PathLike object, not NoneType
```

修复方法：从 `merges.txt` 重建 vocab.json

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

## Variant 修复

如果 `model_index.json` 里有 `"variant": "fp16"`，要用完整精度的 `.safetensors` 时，确认没有下载半精度的 `.fp16.safetensors`。最简单做法：删掉 `model_index.json` 里的 `"variant"` 键。

## 加载验证

```python
from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained(
    "/path/to/stable-diffusion-v1-5",
    torch_dtype=torch.float16, safety_checker=None
)
pipe = pipe.to("cuda")
# 如果 OK → model loaded
```

## 速度

- 从 AutoDL 到 ModelScope 下载速度: ~3-4 MB/s
- UNet (1.4GB) 约 6-8 分钟
- VAE (320MB) 约 1-2 分钟
- text_encoder (470MB) 约 2-3 分钟
- 总共约 12-15 分钟

## 备用方案: 使用已有的 base 环境

AutoDL 的 base 环境 (conda) 已经预装了：
- torch 2.5.1+cu124
- diffusers 0.30.3
- transformers 4.46.3
- opencv-python

缺失的包（需要安装）：
```bash
pip install imageio[pyav] decord opencv-python-headless einops modelscope
```
