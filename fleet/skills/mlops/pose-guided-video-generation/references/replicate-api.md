# Pay-per-use API Options for Pose-Guided Video Generation

## Overview

When self-hosting (AutoDL, GPU server) is unreliable, use these third-party APIs instead. All accept: reference image + driving video (rendered skeleton) → output video of person performing the motion.

## Replicate (prunaai/p-video-animate)

**Best for**: Quick prototyping, zero setup

**Model**: `prunaai/p-video-animate` (version `bb85a3375c583d53293a184296791cbaa837f73bcc30ed2b16154e539eb11af0`)

**Input parameters**:
- `image` (string, required): URL to reference photo
- `video` (string, required): URL to driving video (skeleton animation MP4)
- `turbo` (boolean): faster generation, slightly lower quality
- `resolution`: "720p" or "1080p"
- `target_fps`: int (e.g. 8)
- `instruction_prompt`: text prompt for motion guidance
- `seed`: int, optional

**Upload files**:
```bash
curl -X POST -H "Authorization: Bearer $REPLICATE_TOKEN" \
  -F "content=@/path/to/image.jpg" \
  "https://api.replicate.com/v1/files"
# Returns: {"urls":{"get":"https://api.replicate.com/v1/files/...jpg"}}
```

**Call**:
```bash
curl -X POST -H "Authorization: Bearer $REPLICATE_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "version":"bb85a3375c583d53293a184296791cbaa837f73bcc30ed2b16154e539eb11af0",
    "input":{
      "image":"<uploaded_image_url>",
      "video":"<uploaded_video_url>",
      "turbo":true,
      "target_fps":8,
      "resolution":"720p",
      "instruction_prompt":"a person playing badminton"
    }
  }' \
  "https://api.replicate.com/v1/predictions"
```

**Pricing**: ~$0.15-0.25/video (requires billing setup, HTTP 402 if no payment method)

**Gotchas**:
- HTTP 422: wrong version hash or missing required fields
- HTTP 402: account needs billing setup (even with free credits)
- File upload must complete before calling prediction
- China access: Replicate works intermittently from Chinese mainland networks

## HuggingFace Inference API

Not available for pose-guided models as of mid-2026.

## RunPod Serverless (Self-deploy template)

**Best for**: Production in China, predictable pricing

Deploy AnimateAnyone/MagicAnimate as serverless endpoint. Requires one-time Docker image setup. Cost: ~$0.075/video on RTX 4090. Accessible from China without proxy.
