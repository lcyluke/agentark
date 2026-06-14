# 多人视频智能选人 + 动作识别管线

## 概览

解决"上传1分钟视频有2个人，AI不知道该评估谁"的问题。四个新增API端点串成完整流程。

## 流程

```
上传视频 → POST /api/assess/validate
  ↓ needs_person_select: true
  ↓ people: [{id, face_bbox, proximity, clarity, clothing_color, face_crop_path, recommend}]
  ↓ video_path 保存供后续使用
选人 → 用户点击人员卡片
  ↓
POST /api/assess/cartoon-avatar {face_crop_path}
  ↓ 返回 avatar_url
POST /api/assess/detect-actions {video_path, person_id, face_bbox}
  ↓ MediaPipe Pose → 选人（鼻距 <40%画幅） → 动作分类
  ↓ detected_actions: [{action, name, frame_range, confidence}]
  ↓ completeness: {detected_count, missing, is_complete, message}
确认动作 → 用户勾选要评估的动作
  ↓
POST /api/assess/evaluate-person {video_path, person_id, selected_actions, face_bbox}
  ↓ _assess_video + _enrich
  ↓ 完整评估报告
```

## 人员属性检测

### 远近判断 (proximity)
基于人脸 bbox 面积占画面百分比：
- `>8%` → `near` （近景·清晰）
- `3%-8%` → `mid` （中景）
- `<3%` → `far` （远景·模糊）

### 清晰度判断 (clarity)
基于人脸 ROI 的 Laplacian 方差：
- `>500` → `clear` （清晰）
- `150-500` → `blurry` （轻微模糊）
- `<150` → `partial` （不清晰）

### 穿着颜色
采样人脸下方躯干区域（bbox 下 0.2-3倍高度），取中位色映射中文名：
红色、蓝色、绿色、黑色、白色、棕色、黄色、紫色、灰色、橙色 → `"红色上衣"`

### 推荐标记
`recommend: true` 当且仅当 `proximity == "near" && clarity == "clear"`

## 动作识别启发式规则

7类动作，基于10帧滑动窗口的骨骼运动特征：

| 动作 | 手腕运动 (wrist_y) | 髋部运动 (hip_drop) | 肩部旋转 | 阈值 |
|:--|:--|:--|:--|:--|
| 杀球 smash | 快速向下 | 轻微下沉 | — | wrist_motion < -8, hip_drop > 2 |
| 高远球 clear | 向上伸展 | — | 小 | wrist_motion > 10, shoulder_rot < 3 |
| 吊球 drop | 轻柔向下 | 几乎不动 | — | -5 < wrist_motion < -1, hip_drop < 1 |
| 网前球 net_shot | 几乎不动 | 明显下沉(前倾) | — | abs(wrist_motion) < 3, hip_drop > 4 |
| 平抽 drive | 水平挥动 | — | 明显 | abs(wrist_motion) < 6, shoulder_rot > 5 |
| 挑球 lift | 向上轻挑 | — | — | 3 < wrist_motion < 12 |
| 步法 footwork | 几乎不动 | 大幅横移 | — | hip_drop > 5, abs(wrist_motion) < 2 |

### 骨骼选人逻辑
逐帧比对鼻尖坐标与人脸检测框中心的欧氏距离，超过 `max(w, h) * 0.4` 的骨骼视为非目标人员，丢弃。

### 置信度
`confidence = min(0.95, 0.5 + len(detected_frames) / 50)`

### 完备性判断
- 侦测到 5+ 种动作 → `is_complete: true`
- 侦测到 3-4 种 → 提示缺失动作
- 侦测到 <3 种 → 建议重录

## 卡通化身生成

OpenCV 管线（无 ML 依赖）：
1. `bilateralFilter(img, 9, 75, 75)` — 保边平滑
2. `adaptiveThreshold(gray, 255, MEAN_C, THRESH_BINARY, 9, 9)` — 边缘提取
3. `bilateralFilter(smooth, 9, 150, 150)` — 色彩量化
4. `bitwise_and(color, edges_colored)` — 边缘+色彩融合
5. HSV S+30 V+10 → 提亮增饱和

输出保存为 `<UPLOAD_DIR>/cartoon_<uuid>.jpg`，返回相对路径 + URL。

## 前端交互要点

- 人员卡片显示：人脸裁剪图 + 远近标签 + 清晰度 + 穿着 + 位置 + 推荐星标
- "这是我" / "这是球友" 切换：选球友时提示"每周3次免费为他人测评"
- 动作确认页：卡通头像 + 动作清单(checkbox) + 完备性警告 + "全选/取消全选" + "开始评估(N种动作)"
- 卡通头像绑定：`wx.setStorageSync('cartoonAvatar', url)`，可用于登录页头像和报告水印
