# 双打分析系统

## 文件结构

```
badminton_coach/
├── doubles_estimator.py    # 多人骨骼追踪 (DoublesPoseEstimator)
└── doubles_analysis.py     # 双打分析引擎 (DoublesAnalyzer)

amateur_training.py 内:
├── DOUBLES_SKILLS_BANK     # 16项双打技能 × 3级
├── DOUBLES_TRAINING_ADVICE  # 8类训练建议 (low/mid/high)
├── GET /api/doubles/skills # 返回技能体系
├── POST /api/doubles/analyze # 上传视频分析
└── GET /api/doubles/progress # 双打进度 (需auth)
```

## 双打分析引擎原理

### 1. 多人骨骼追踪 (doubles_estimator.py)

- 使用 MediaPipe Pose Landmarker 的 `num_poses=4` 选项
- 每帧检测场上最多4人
- 自动球员分配策略:
  - 按 x 坐标分左右半场 → A队(左) / B队(右)
  - 每队内按 y 坐标分前后 → A1(后场主攻) / A2(网前)  
- 队形分类: attack(前后) / defense(左右平行) / transition(轮转中) / mixed(不规则)

### 2. 双打技术评分 (doubles_analysis.py)

| 维度 | 评分方法 |
|:----|:---------|
| 平抽快挡 | 手腕关节高频变动 + 中前场活动比例 |
| 网前扑压 | 网前(0.35<y<0.5)区域帧占比 |
| 推球分球 | 手腕运动量 |
| 发接发 | 前3秒帧占比 |
| 后场进攻 | attack队形占比 |
| 防守挑球 | defense队形占比 |

### 3. 战术意识评分

| 维度 | 评分方法 |
|:----|:---------|
| 进攻站位意识 | attack队形占比 |
| 防守站位意识 | defense队形占比 |
| 轮转时机 | 轮转频率(合理:1-3次/分钟) |
| 连续进攻 | 最长attack连续帧数 |
| 攻防转换 | 轮转事件总数 |

### 4. 搭档配合评分

| 维度 | 评分方法 |
|:----|:---------|
| 场区覆盖 | 4个场区覆盖数 |
| 补位默契 | 3-4人稳定检测帧占比 |
| 球路分配 | 前后场活动均衡度 |
| 沟通暗示 | 轮转频率(≈沟通频率) |

## API 使用

```bash
# 获取双打技能体系
curl http://localhost:8000/api/doubles/skills

# 分析双打视频
curl -X POST http://localhost:8000/api/doubles/analyze \
  -F "file=@match_clip.mp4"

# 双打进度 (需Bearer token)
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/doubles/progress
```

## 16项双打技能体系

### 双打技术 (7项)
1. 正手平抽 (flat_drive_fh)
2. 反手平抽 (flat_drive_bh)
3. 网前扑压 (net_kill)
4. 推球分球 (push_split)
5. 发接发 (serve_receive)
6. 接发球 (serve_receive_return)
7. 中场拦截 (mid_block)

### 轮转与站位 (4项)
8. 前后轮转 (rotation_front_back)
9. 左右补位 (rotation_side)
10. 防守站位 (defense_position)
11. 进攻站位 (attack_position)

### 战术意识 (3项)
12. 空档攻击 (tactic_gap_attack)
13. 连续进攻 (tactic_continuous)
14. 攻防转换 (tactic_transition)

### 搭档配合 (2项)
15. 场区覆盖 (coordination_cover)
16. 配合沟通 (coordination_communication)

## 已知限制

1. MediaPipe Pose Landmarker 在广角/多人在同一画面重叠时可能丢失部分人体
2. 球员自动分配基于简单的位置假设（左=队A, 右=队B），换边/复杂走位可能误判
3. 战术评分基于位置统计，无法理解球路意图 — 需要结合 shuttlecock tracking 才能精确
4. 视频越短（<30s）统计越不准确，建议上传60s+比赛片段
