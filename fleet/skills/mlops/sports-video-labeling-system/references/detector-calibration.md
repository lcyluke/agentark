# detector_agent.py 阈值校准记录

## 校准过程

### Round 1 (初始值)
```
motion_threshold: 0.15
min_frames_between_hits: 20
clip_before_sec: 3.0, clip_after_sec: 4.0
min_clip_frames: 90, max_clip_frames: 450
```
结果: 1个10MB业余视频 → 30个片段 (太多, 大量误检)

### Round 2 (收紧)
```
motion_threshold: 0.20 (↑提高阈值)
min_frames_between_hits: 30 (↑增加间隔)
clip_before_sec: 2.0, clip_after_sec: 3.0 (↓缩短窗口)
min_clip_frames: 60, max_clip_frames: 300 (↓缩小时长)
```
结果: 130视频 → 172片段 (平均1.3/视频), 3-8个/视频 ✓

### 关键洞察

1. 帧差法对昏暗视频敏感, motion_threshold < 0.18 会产生大量噪音
2. B站教学视频 (有讲解的画外音片段) 需要更高的 min_frames_between_hits
3. 业余对打视频的动作密度高, 需要用 max_clip_frames 限制
4. 专业慢动作教学片段的片段数最少 (1-3个/视频)

### 按视频类型的推荐阈值

| 视频类型 | motion_threshold | min_interval | 预期片段数 |
|:---------|:----------------:|:------------:|:--------:|
| 业余对打 (业余) | 0.18 | 25 | 5-12 |
| 教学讲解 (专业) | 0.22 | 30 | 2-5 |
| 慢动作示范 (专业) | 0.25 | 40 | 1-3 |
| 比赛集锦 (混合) | 0.20 | 20 | 8-15 |
