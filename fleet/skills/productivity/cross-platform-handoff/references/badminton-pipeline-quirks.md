# 羽毛球标注系统 — Agent 调用约定

> 项目路径：`~/Desktop/2026AIAPP/badminton-label-system/`

## Agent 参数格式

所有 Agent 使用**位置参数**而非 `--flags`。文档和 README 中建议的 `--flag` 写法是错的。

| Agent | 正确调用 | 错误调用 |
|-------|---------|---------|
| `skeleton_agent.py` | `python3 agents/skeleton_agent.py <video> <output_dir> <video_id>` | `python3 agents/skeleton_agent.py --video X --output Y` |
| `annotation_engine.py` | `python3 agents/annotation_engine.py <npy_path> <meta_path> <action>` | `python3 agents/annotation_engine.py --npy X --output Y --action Z` |
| `detector_agent.py` | `python3 agents/detector_agent.py --video X --action Y` | 正确，这个确实用 `--flag` |
| `amateur_pipeline.py` | `python3 scripts/amateur_pipeline.py --mode report` | `python3 scripts/amateur_pipeline.py --report` ❌ (不是flag，是mode值) |

## MediaPipe 导入容错

detector_agent.py 使用帧差法检测动作，不需要 MediaPipe。但代码在模块顶部尝试了 `from mediapipe.tasks.python import vision` 等导入，在 MediaPipe 版本不匹配时会因 `AttributeError: module 'mediapipe' has no attribute 'solutions'` 崩溃。

修复：把导入包裹在 try/except 中，catch 范围改为 `(ImportError, AttributeError)`：

```python
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    _HAS_MEDIAPIPE = True
except (ImportError, AttributeError):
    _HAS_MEDIAPIPE = False
```

## B站/YouTube 下载

- B站需要登录 cookies 才能下载 ≥480p 视频。360p 以下不需要登录但质量太低不适合标注。
- `yt-dlp --cookies-from-browser chrome` 在 macOS 上可能被 Chrome 保护机制阻止。
- 替代方案：手动导出 cookies.txt 或使用代理。
- 现有 129 个专业教学视频（clear/smash/drop/net/defense/footwork/feints 共7类）已在 `data/raw_videos/` 中，可直接用于检测流水线。

## 检测阈值调优

detector_agent.py 的默认阈值偏宽松（30 个候选帧/视频），调优后：

```python
DETECTION_PARAMS = {
    "motion_threshold": 0.20,      # 提高 → 减少误检
    "min_frames_between_hits": 30, # 增加间隔 → 避免重复
    "clip_before_sec": 2.0,        # 缩短窗口
    "clip_after_sec": 3.0,
}
```

## 完整流水线

```
采集 (collector) → 检测裁剪 (detector) → 骨骼追踪 (skeleton) → 标注 (annotate) → 评估 (evaluate)
       ✅                  ✅                    ✅                ✅              🔲
```

性能：单视频 ~15秒（检测2s + 骨骼10s + 标注3s）。
