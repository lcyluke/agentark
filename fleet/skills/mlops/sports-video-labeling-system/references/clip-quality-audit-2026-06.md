# B站Clip质量审计 + MimicMotion模型部署尝试 (2026-06-01)

## 1,887个B站clip质量审计

### 源分类与质量

| 源 | clip数 | 平均时长 | <5s | ≥8s | 画质 |
|:--|:------:|:--------:|:---:|:---:|:----:|
| 影子赵剑华/肖杰(纯动作) | 110 | 14s | 5 | 68 | 1280×720@25fps 横版 |
| 闪跃反手4K(纯动作) | 24 | 12s | 0 | 18 | 3840×2160 横版 |
| 陶菲克反手(纯动作) | 14 | 16s | 0 | 12 | 1280×720 |
| **纯动作合计** | **145** | **12.8s** | **5(3%)** | **98(68%)** | |
| 李宇轩杀球(教学) | 581 | 3.3s | 454 | 15 | 1920×1080@30fps |
| 4K杀球教程(教学) | 555 | 3.3s | 407 | 41 | 3840×2160@25fps |
| 李宇轩步法(教学) | 203 | 5.5s | 115 | 39 | 1920×1080@60fps |
| 打球步法(教学) | 244 | 4.5s | 159 | 36 | 1920×1080@60fps |
| 其他教学 | 159 | 6.8s | 42 | 67 | 混合 |
| **教学合计** | **1,742** | **4.2s** | **1,177(68%)** | **198(11%)** | |

**结论：** 纯动作145个clip质量可用，教学类1,742个clip中1,177个（68%）是<5s的碎片，不适用于模型训练或小程序播放。

### 清理后的结果

`data/training_clips/` 目录包含 497 个高质量clip（全部≥5s）：

| 技能 | clip数 | 平均时长 | 原始源 |
|:----|:------:|:--------:|:-------|
| clear_bh | 72 | 15.1s | 影子+陶菲克+闪跃+教学 |
| clear_fh | 80 | 10.1s | 影子赵剑华+顶尖高手 |
| drop_stand | 13 | 10.3s | 大G吊球 |
| footwork_def | 241 | 10.1s | 李宇轩+李宗伟+桃田 |
| smash_jump | 40 | 13.7s | 闪跃4K+影子 |
| smash_stand | 51 | 11.4s | 李宇轩+4K杀球 |

## MimicMotion部署尝试

### 目标
把B站高手的骨骼动作迁移到用户照片上（用户穿球服做同样的动作）

### 进度
- ✅ MimicMotion源码下完（23个源文件，GitHub raw）
- ✅ 推理脚本 `run_mimic.py` 写好（MediaPipe→骨骼渲染→MimicMotion）
- ✅ 依赖全装（diffusers 0.38.0, omegaconf, modelscope）
- ❌ 模型权重下载失败

### 模型下载诊断

| 模型 | 大小 | 来源 | 需要授权？ | 下载状态 |
|:----|:---:|:----|:---------:|:--------:|
| `tencent/MimicMotion` `MimicMotion_1-1.pth` | 3.05GB | HuggingFace | ❌ 公开 (gated:false) | ❌ 被墙 |
| `stabilityai/stable-video-diffusion-img2vid-xt-1-1` | ~5GB | HuggingFace | ✅ 需接受协议 (gated:auto) | ❌ 被墙 |

**试验过的下载方式：**
1. `huggingface-cli download` — 废弃，被`hf`命令取代
2. `hf download` — 进程一直跑但无输出，卡住
3. Python `hf_hub_download()` — `An error happened while trying to locate the file`
4. `huggingface.co` 网页 — 加载正常，但文件托管在 `xethub.hf.co` (AWS S3/CloudFront CDN) → 国内被墙
5. `hf-mirror.com` — 连不上
6. 直接 `curl` 下载链接 `.../resolve/main/...?download=true` — 302到S3后超时
7. `modelscope` — 安装成功但API兼容性有问题

**结论：** HuggingFace网页可达但CDN被墙。需要VPN或海外服务器（如AutoDL GPU实例）。

### 推荐替代方案

**方案A：老卢亲自下载（微信传文件）**
```bash
# 打开这个链接，点download保存到桌面
https://huggingface.co/tencent/MimicMotion/resolve/main/MimicMotion_1-1.pth?download=true
# SVD需要先登录HF + 接受协议
# 然后放回 Mac 的 ~/Desktop/2026AIAPP/MimicMotion/models/
```

**方案B：AutoDL云GPU（¥1.9/时）**
AutoDL的国内服务器可直连HuggingFace，在上面下载+推理，总花费≈¥2-3

### MimicMotion骨骼渲染格式

MimicMotion需要 `draw_pose()` 输出的骨骼图像序列（黑色背景+彩色骨骼线+关节圆点，RGB ndarray），不是DWPose的keypoint坐标。`run_mimic.py` 里的 `render_mediapipe_skel()` 函数把MediaPipe 33 landmarks渲染成这个格式。

关键骨骼映射（MediaPipe→COCO→DWPose兼容）：
```python
# 画出人体13个关键连接线
BONES = [
    (11, 12),  # 双肩
    (11, 13), (13, 15),  # 左臂
    (12, 14), (14, 16),  # 右臂
    (11, 23), (12, 24),  # 躯干两侧
    (23, 24),  # 髋
    (23, 25), (25, 27), (27, 29), (27, 31),  # 左腿
    (24, 26), (26, 28), (28, 30), (28, 32),  # 右腿
    (11, 0), (12, 0),  # 颈到头
]
```
