# Alternative: API-Based Pose-Guided Video Generation

When self-hosting (MimicMotion, MagicAnimate, SD+ControlNet) fails or takes too long, pay-per-use API services are a viable alternative for generating demo/training videos.

## Options Comparison

| Service | Cost per 10s video | China Access | Effort | Quality |
|---------|:------------------:|:------------:|:------:|:-------:|
| **Replicate** (`animate-anyone`) | ~$0.25 | Needs proxy | Zero | Good |
| **Fal.ai** | ~$0.20 | Medium | Low | Good |
| **RunPod** (serverless deploy) | ~$0.075 | ✅ Yes | Medium | Good |
| **Alibaba PAI-EAS** (deploy) | ~¥0.8/video | ✅ Native | Medium | Good |

## Input Format

All APIs require: **source reference image** + **driving video** (a skeleton render video from your keypoint data).

You CANNOT send raw keypoint JSON — you must first render the skeleton into a video:

```python
import cv2, numpy as np, imageio

# Render MediaPipe landmarks → skeleton video
BONES = [(11,12),(11,13),(13,15),(12,14),(14,16),(11,23),(12,24),(23,24),...]
frames = []
for landmark_set in landmarks_list:
    canvas = np.zeros((576, 576, 3), dtype=np.uint8)
    for i1, i2 in BONES:
        if ...:  # visibility check
            cv2.line(canvas, p1, p2, (100,200,255), 3)
    frames.append(canvas)

# Save as 5-10 second MP4
writer = imageio.get_writer("driving_skel.mp4", fps=8, codec='libx264')
for f in frames:
    writer.append_data(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
writer.close()
```

## Replicate API (Quickest for Prototyping)

```bash
# Set up
export REPLICATE_API_TOKEN="r8_..."

# Call animate-anyone
curl -s -X POST \
  -H "Authorization: Token $REPLICATE_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input": {
      "source_image": "data:image/jpeg;base64,...",
      "driving_video": "data:video/mp4;base64,...",
      "width": 512,
      "height": 768,
      "num_steps": 25
    }
  }' \
  "https://api.replicate.com/v1/models/yisol/animate-anyone/predictions"
```

**From China**: Replicate is semi-blocked. Use a Cloudflare Worker or direct proxy. HuggingFace is accessible from China and may work for certain Spaces that wrap these models.

## RunPod (Best for China Production)

1. Find a MagicAnimate template in RunPod serverless
2. Deploy as a Docker endpoint
3. Call via HTTP (no proxy needed)
4. Cost: ~$0.075 per 10s video

## When to Use API vs Self-Host

| Situation | Go With |
|:----------|:--------|
| Prototype, need first result today | Replicate/Fal.ai | 
| Production in China, <100 videos/month | RunPod serverless |
| Production in China, 100+ videos/month | Alibaba PAI-EAS |
| Need full control, model fine-tuning | Self-host on AutoDL |
