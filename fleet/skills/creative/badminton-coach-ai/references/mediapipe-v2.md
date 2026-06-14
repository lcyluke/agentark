# MediaPipe API Migration

从 `mp.solutions.pose` 迁移到 `mediapipe.tasks.python.vision.PoseLandmarker`

完整迁移指南见 `badminton-pm` skill 的 `references/mediapipe-migration.md`：
`skill_view(name='badminton-pm', file_path='references/mediapipe-migration.md')`

## 核心差异速查

| 旧API | 新API (0.10.35+) |
|-------|-----------------|
| `mp.solutions.pose.Pose()` | `vision.PoseLandmarker.create_from_options(options)` |
| `pose.process(rgb)` | `detector.detect(mp_img)` |
| `result.pose_landmarks.landmark[i]` | `result.pose_landmarks[0][i]` |
| 模型内置 | 需下载 `.task` 文件 (5.6MB) |
| 单人检测 | 原生多人支持 |

## 需要迁移的文件

- `double_analyzer.py` — 已迁移 ✅
- `pose_estimator.py` — 仍使用旧API ⚠️
- `image_assessor.py` — 仍使用旧API ⚠️
