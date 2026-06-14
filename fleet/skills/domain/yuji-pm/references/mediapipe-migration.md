# MediaPipe 0.10.x API 迁移指南

> 羽迹项目使用的 MediaPipe 0.10.35 已移除旧版 `mp.solutions.pose` API。所有使用旧API的模块必须迁移到新的 `PoseLandmarker`。

## 旧API (0.8.x ~ 0.9.x)

```python
import mediapipe as mp

with mp.solutions.pose.Pose(
    static_image_mode=True,
    model_complexity=1,
    min_detection_confidence=0.4,
) as pose:
    result = pose.process(rgb)
    if result.pose_landmarks:
        landmarks = result.pose_landmarks.landmark
        # landmarks is a list of 33 NormalizedLandmark
```

## 新API (0.10.x)

```python
import cv2
import mediapipe as mp
from mediapipe.tasks.python import vision
from mediapipe.tasks.python.core.base_options import BaseOptions

# 下载模型文件（约5.6MB）
# curl -L -o pose_landmarker_lite.task \
#   https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task

options = vision.PoseLandmarkerOptions(
    base_options=BaseOptions(model_asset_path="pose_landmarker_lite.task"),
    running_mode=vision.RunningMode.IMAGE,
    min_pose_detection_confidence=0.4,
)
detector = vision.PoseLandmarker.create_from_options(options)

# 需要构建 mp.Image 对象
mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=cv2.cvtColor(img, cv2.COLOR_BGR2RGB))
result = detector.detect(mp_img)

# 直接访问 pose_landmarks（列表，每项33个关键点）
for landmarks in result.pose_landmarks:
    # landmarks[0] = nose, landmarks[11] = left_shoulder, landmarks[12] = right_shoulder ...
    nose_y = landmarks[0].y
    rwrist_y = landmarks[16].y
    lwrist_y = landmarks[15].y
```

## 关键区别

| 维度 | 旧API | 新API |
|------|-------|-------|
| 模型 | 内置（无下载） | 需下载 `.task` 文件 |
| 输入 | `cv2 RGB` 数组 | `mp.Image` 对象 |
| 关键点访问 | `result.pose_landmarks.landmark[i]` | `result.pose_landmarks[person_idx][i]` |
| 多人检测 | 需手动遮罩+重试 | 原生支持多人（受 `min_pose_detection_confidence` 控制） |
| 可视化 | `mp.solutions.drawing_utils` | `vision.PoseLandmarksConnections` + `drawing_utils` |
| 性能 | 较快 | 略慢（需模型加载） |

## 多人检测优化技巧

```python
# 原生检测时第二人被遮挡/远距离时可能漏检
# 优化策略：先检测，若人数不够则遮罩第一人区域再检测
detector = vision.PoseLandmarker.create_from_options(options)
result = detector.detect(mp_img)

# 若只有1人但有2人脸，尝试遮罩
if len(result.pose_landmarks) == 1:
    h, w = img.shape[:2]
    lm0 = result.pose_landmarks[0]
    xs = [lm.x * w for lm in lm0]
    ys = [lm.y * h for lm in lm0]
    x1 = max(0, int(min(xs)) - int(w*0.1))
    x2 = min(w, int(max(xs)) + int(w*0.1))
    y1 = max(0, int(min(ys)) - int(h*0.15))
    y2 = min(h, int(max(ys)) + int(h*0.15))
    masked = img_rgb.copy()
    masked[y1:y2, x1:x2] = (0, 0, 0)
    result2 = detector.detect(
        mp.Image(image_format=mp.ImageFormat.SRGB, data=masked)
    )
```

## 人脸检测辅助（OpenCV内置，无需下载）

```python
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
)
gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
faces = face_cascade.detectMultiScale(gray, 1.1, 4)
# 返回 [(x, y, w, h), ...]
```

## 动作分析核心指标

| 指标 | 计算方式 | 意义 |
|------|---------|------|
| 手臂伸展度 | 肩-肘-腕夹角 / 180° | 0~1，越高越好 |
| 屈膝度 | clip((180 - 髋-膝-踝夹角) / 70, 0, 1) | 0~1，越高=蹲得越深 |
| 持拍手 | 比较左右腕y坐标，更小者为持拍手 | 判断用户是左/右手 |
| 击球点高度 | 1.0 - 持拍腕y坐标 | 0~1，越高=击球点越高 |
| 转体程度 | atan2(|肩高差|, |肩宽差|) / 60° | 0~1，越高=侧身越充分 |
| 身体前倾 | 1 - atan2(|髋肩y差|, |髋肩x差|) / 90° | 0~1，越高=前倾越大 |
