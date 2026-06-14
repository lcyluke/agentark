# AutoDL MimicMotion 部署检查单

从零到推理的全流程，按此顺序执行。每条已验证过。

## 环境

- **实例**: Ubuntu 22.04, Python 3.12.3 (conda), RTX 4090 D 24GB
- **路径**: 所有文件放 `/root/autodl-tmp/MimicMotion/`（50GB fast storage）
- **Shell**: `/root/miniconda3/bin/python3`（`python3` 不在 PATH）

## 1. 依赖安装

```bash
/root/miniconda3/bin/pip3 install "diffusers[torch]==0.30.3" "huggingface-hub==0.25.2" \
  "transformers==4.46.3" accelerate opencv-python-headless "imageio[ffmpeg]" \
  einops decord modelscope fastapi uvicorn python-multipart httpx -q
```

验证: `/root/miniconda3/bin/pip3 list | grep -E 'diffusers|huggingface|transformers|fastapi|modelscope'`

## 2. 源码上传

从本地（不在 China、可连 GitHub）打包上传:

```bash
# 本地
cd /path/to/MimicMotion
tar czf - mimicmotion/ | sshpass -p 'PASS' ssh -p PORT root@HOST \
  "cd /root/autodl-tmp/MimicMotion && tar xzf -"
```

验证: `/root/miniconda3/bin/python3 -c "import sys; sys.path.insert(0,'/root/autodl-tmp/MimicMotion'); from mimicmotion.utils.loader import MimicMotionModel; print('OK')"`

## 3. 模型下载

### 3a. SVD base (gated, ModelScope)

```bash
/root/miniconda3/bin/python3 -c "
from modelscope.hub.file_download import model_file_download
import os
base = '/root/autodl-tmp/MimicMotion/models/svd_base'
files = [
    'vae/diffusion_pytorch_model.safetensors',
    'image_encoder/model.safetensors',
    'image_encoder/model.fp16.safetensors',
    'unet/diffusion_pytorch_model.fp16.safetensors',
]
for f in files:
    print(f'Downloading {f}...', flush=True)
    model_file_download('stabilityai/stable-video-diffusion-img2vid-xt-1-1', f, cache_dir=base, revision='master')
    print(f'DONE {f}', flush=True)
"
```

预计 35 分钟，单文件 5-8 分钟。

### 3b. MimicMotion 权重 (open, hf-mirror)

```bash
curl -L -k --retry 5 --retry-delay 10 \
  -o /root/autodl-tmp/MimicMotion/models/mimicmotion_weights/MimicMotion_1-1.pth \
  'https://hf-mirror.com/tencent/MimicMotion/resolve/main/MimicMotion_1-1.pth'
```

预计 20 分钟（2.3MB/s）。如果 SSL 失败，用 `-k` 重试。如果彻底不行，从本地 `cat | ssh` 上传（~20 分钟）。

### 3c. Config 文件上传

ModelScope 不下 config JSON。从本地打包上传:

```bash
# 本地
cd /path/to/models/svd_base
tar czf - *.json */config.json */preprocessor_config.json scheduler/ | \
  sshpass -p 'PASS' ssh -p PORT root@HOST \
  "cd /root/autodl-tmp/MimicMotion/models/svd_base/stabilityai/stable-video-diffusion-img2vid-xt-1-1 && tar xzf -"
```

## 4. VAE fp16 修复

```bash
cd /root/autodl-tmp/MimicMotion/models/svd_base/stabilityai/stable-video-diffusion-img2vid-xt-1-1
cp vae/diffusion_pytorch_model.safetensors vae/diffusion_pytorch_model.fp16.safetensors
```

## 5. 验证模型完整性

```bash
find /root/autodl-tmp/MimicMotion/models -name '*.safetensors' -o -name '*.pth' | while read f; do
  echo "$(ls -lh "$f" | awk '{print $5}') $f"
done
find /root/autodl-tmp/MimicMotion/models/svd_base -name '*.json' | wc -l  # 应 ≥6
```

## 6. 启动推理服务

```bash
screen -dmS infer bash -c '/root/miniconda3/bin/python3 /root/autodl-tmp/MimicMotion/infer_server.py 2>&1 | tee /tmp/infer.log'
```

等 40 秒加载模型（4.5GB VRAM），然后验证:

```bash
tail -3 /tmp/infer.log  # 应显示 "Ready. VRAM: 4.5GB"
```

## 7. SSH 隧道 + 健康检查

```bash
# 本地
sshpass -p 'PASS' ssh -N -L 8765:localhost:8765 -p PORT root@HOST &
sleep 2
curl http://localhost:8765/health  # → {"ok":true,"vram_gb":4.5}
```

## 8. 测试推理

```bash
# 准备测试请求
python3 -c "
import json, base64
from PIL import Image
# 生成测试照片
img = Image.new('RGB', (1024, 576), (30, 30, 60))
img.save('/tmp/test.jpg')
with open('/tmp/test.jpg', 'rb') as f:
    b64 = base64.b64encode(f.read()).decode()
# 生成骨架 JSON (使用项目的 benchmark)
import numpy as np
skel = np.load('/tmp/badminton_defense/benchmark_defense_block.npy')
frames = []
for i in range(min(len(skel), 48)):
    lms = [[float(skel[i,j,0]), float(skel[i,j,1])] for j in range(33)]
    frames.append({'lms': lms})
with open('/tmp/test_request.json', 'w') as f:
    json.dump({'photo_b64': b64, 'skeleton': {'frames': frames}, 'num_steps': 10, 'num_frames': 48}, f)
"

curl -s -X POST http://localhost:8765/infer \
  -H "Content-Type: application/json" \
  -d @/tmp/test_request.json \
  -o /tmp/test_result.mp4 \
  --max-time 180

ls -lh /tmp/test_result.mp4  # 应生成 ~6-8MB mp4
```

预计 42 秒（48 帧 × 10 步 on RTX 4090D）。

## 排错

| 错误 | 原因 | 修复 |
|:--|:--|:--|
| `ModuleNotFoundError: No module named 'mimicmotion'` | sys.path 未包含 mimicmotion/ 的父目录 | 检查 `ls -d /root/autodl-tmp/MimicMotion/mimicmotion/`，确认 `sys.path.insert(0, "/root/autodl-tmp/MimicMotion")` |
| `OSError: no file named diffusion_pytorch_model.fp16.bin found` | VAE 缺 fp16 版本 | `cp vae/diffusion_pytorch_model.safetensors vae/diffusion_pytorch_model.fp16.safetensors` |
| `SyntaxError: illegal target for annotation` | 导入了 `mimicmotion.models.*` (404 stub) | 只导入 `mimicmotion.utils.loader` 和 `mimicmotion.pipelines.*` |
| 视频是绿色画面 | cv2.VideoWriter 在 headless Linux 上坏掉 | 用 `imageio.get_writer(codec='libx264')` |
| `pipeline.to(device)` crash | MimicMotionPipeline 不是 diffusers pipeline | 不调 `.to()`，传 `device=device` 到 `pipeline()` |
| SSH 连接超时 | 下载占着中继带宽 | 等 download screen 完成，期间不连新 SSH |

## 服务重启 (AutoDL 实例过期/重启后)

AutoDL 实例重启后，SSH 隧道和推理服务都会掉。按此顺序快速恢复：

### 1. 确认实例存活

```bash
sshpass -p 'PASS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p PORT root@HOST \
  "echo 'ALIVE' && nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader"
```
应返回 `ALIVE` + GPU 信息。如果超时，实例可能已过期需重新启动。

### 2. 检查推理服务

```bash
sshpass -p 'PASS' ssh ... "ps aux | grep infer_server | grep -v grep"
```

如果无输出 → 服务未运行，跳到步骤 3。如果有 PID → 服务活着但需验证。

### 3. 启动推理服务（使用绝对路径！）

⚠️ **`nohup python3` 会报 `No such file or directory`** — nohup 环境 PATH 极简。必须用绝对路径。

```bash
sshpass -p 'PASS' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=15 -p PORT root@HOST \
  "cd /root/autodl-tmp/MimicMotion && nohup /root/miniconda3/bin/python infer_server.py > /tmp/mimic_server.log 2>&1 &"
```

加载需 ~20 秒。验证:

```bash
# 等 15-20s 后
sshpass -p 'PASS' ssh ... "tail -5 /tmp/mimic_server.log"
# 应显示: "Ready. VRAM: 4.5GB" + "Application startup complete"
```

### 4. 建立本地 SSH 隧道

```bash
sshpass -p 'PASS' ssh -o StrictHostKeyChecking=no -o ServerAliveInterval=30 \
  -o ServerAliveCountMax=3 -N -L 8765:localhost:8765 -p PORT root@HOST &
```

### 5. 健康检查

```bash
sleep 3 && curl -s http://127.0.0.1:8765/health
# → {"ok":true,"vram_gb":4.5}
```

### 6. 更新本地 tunnel 脚本 PID

```bash
# 更新 /tmp/autodl_tunnel.pid 或重启 tunnel 脚本
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
bash scripts/autodl_tunnel.sh stop
bash scripts/autodl_tunnel.sh start
```

全程恢复时间: ~30 秒（20s 模型加载 + 10s 其余操作）。
