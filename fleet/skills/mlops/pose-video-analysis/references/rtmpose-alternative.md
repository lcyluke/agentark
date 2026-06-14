# RTMPose — High-Accuracy Pose Estimation Alternative to MediaPipe

## Why RTMPose over MediaPipe

| Metric | MediaPipe Pose | RTMPose-m | Delta |
|:-------|:--------------|:----------|:-----:|
| COCO mAP | ~58% | **75.8%** | +30% |
| FPS (ONNX) | ~30 | **133** | 4.4× |
| Keypoints | 33 (full body) | 17 (COCO) → map to 15 badminton | — |
| Model size | ~6MB (.tflite) | ~50MB (.pth) | larger |
| Deployment | TFLite / MediaPipe Task API | ONNX / OpenMMLab mmpose | — |

## Installation

```bash
pip install mmpose mmdet mmengine openmim
mim download mmpose --config rtmpose-m_8xb256-420e_body8-256x192 --dest models/rtmpose
```

## COCO → Badminton Keypoint Mapping

```python
# COCO 17: nose(0), L_eye, R_eye, L_ear, R_ear, L_shoulder, R_shoulder,
#           L_elbow, R_elbow, L_wrist, R_wrist, L_hip, R_hip,
#           L_knee, R_knee, L_ankle, R_ankle
# Badminton 15: same minus eyes
COCO_TO_BADMINTON = [0, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16]
```

## Usage Pattern

```python
from mmpose.apis import init_model, inference_topdown

model = init_model("rtmpose-m_config.py", "rtmpose-m.pth", device="cpu")
results = inference_topdown(model, image, bboxes=[bbox])

# Map to badminton 15 keypoints
kpts_17 = results[0].pred_instances.keypoints[0].cpu().numpy()
kpts_15 = kpts_17[COCO_TO_BADMINTON]  # (15, 3): x, y, confidence
```

## When to Use

- **Use MediaPipe** for: quick prototyping, mobile/edge, single-person near shot
- **Use RTMPose** for: higher accuracy needed, server-side batch processing, multi-person scenes, serving as input to downstream ML models (GAT+TCN, VideoMAE)

## Integration Pattern

The `rtmpose_extractor.py` agent produces the same NPY format as `skeleton_agent.py` (T×15×3), making it a drop-in replacement in the pipeline.
