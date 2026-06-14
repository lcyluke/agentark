# Content Validation System

## Purpose
Prevent non-badminton content from being assessed with L1-L7 grades. Users uploading food photos, table tennis, basketball, or blank images should get friendly error messages, not fake skill grades.

## Architecture
`content_validator.py` runs as a pre-assessment gate inside `/api/assess` and `/api/full` endpoints (in `webapp.py`). The assessment is only reached if the gate passes.

## Validation Pipeline (image)

1. **Quality check**: brightness (>30 avg), sharpness (Laplacian var >15), non-blank (std dev >5)
2. **Non-badminton sport detection**: HSV color histogram + heuristic rules:
   - Table tennis: dark blue + white edges
   - Basketball: >15% orange pixels
   - Tennis: green + white lines
   - Football, swimming: color-based detection
3. **Human detection**: MediaPipe Pose (reuses `pose_estimator.py`)
4. **Stroke feature analysis** (at least 2 of 3):
   - Wrist/elbow above shoulder (raised-arm hitting posture)
   - Arm extension angle (three-point angle)
   - Asymmetric arms (racket hand vs non-racket hand)

## Validation Pipeline (video)

- Sample first 10 frames + 5 middle frames
- >30% frames with stroke features → valid, high confidence
- No person detected → INVALID_CONTENT
- Person but no stroke → warning

## Error Messages

| Code | Scenario | User-facing message |
|------|----------|-------------------|
| INVALID_CONTENT | No person detected | 🤔 没看到人呢，请拍一张包含打球人物的照片 |
| INVALID_CONTENT | Other sport detected | 🏓 这看起来不是羽毛球运动哦 |
| INVALID_CONTENT | Too dark/blurry | 📸 图片有点模糊，请在光线充足的地方重新拍摄 |
| content_warning | Low confidence | 击球动作不明显，评估结果仅供参考 |

## Integration

- `webapp.py`: inserted as first check in `_assess_image()` and `_assess_video()`
- `miniprogram/pages/assess/`: displays friendly error cards with retry button
- The frontend parses both HTTP 400 `INVALID_CONTENT` responses and `content_warning` fields in successful assessments
