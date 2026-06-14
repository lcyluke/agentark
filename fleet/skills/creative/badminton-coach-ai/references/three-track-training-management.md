# 三轨训练管理系统

羽球宝AI搭子训练模块的核心架构 — 将用户训练拆为三条独立轨道，每条轨道独立的数据源和交互模式。

## 架构总览

```
训练管理
├── 轨道1: 📺 看示范 (Watch)
│   ├── B站公开教学视频目录 (6专项×3级=18个精选视频)
│   ├── AI推荐引擎 (根据观看历史推荐进级视频)
│   └── 观看追踪 (watch_log表，记录完成/时长)
│
├── 轨道2: 📤 交作业 (Submit)  
│   ├── 录视频/选视频 → 上传 → AI评分
│   ├── 关联 evaluate-person / assess 评估管线
│   └── 作业历史 + 6维×3招评分追踪
│
└── 轨道3: 🎭 换脸秀 (Face Swap)
    ├── 上传正面照 → 选技能 → AI生成"我做标准动作"视频
    ├── MimicMotion骨架驱动 + ComfyUI换脸
    └── Pro版专属功能 (feature=coach_booking门控)
```

## 后端模块

### bilibili_catalog.py — B站视频目录

数据类：`BilibiliVideo` — bvid, title, author, duration, skill_id, level, category, description, key_moments

函数接口：
- `get_all_videos()` → List[dict] — 18个精选视频
- `get_video_by_skill_level(skill_id, level)` → Optional[dict] — 精确匹配
- `get_catalog_summary()` → dict — 按大类分组统计
- `build_bvid_url(bvid)` → str — `https://www.bilibili.com/video/{bvid}`
- `build_embed_url(bvid)` → str — B站播放器嵌入URL
- `export_catalog()` → 导出到 `data/bilibili_catalog.json`

6大技能类目，每类L1/L2/L3三级，共18个视频。UP主均为知名教练（李宇轩/陈金/BIG/羽球小达人/林丹教学）。

### training_manager.py — 三轨管理引擎

数据库表（SQLite，路径 `data/training_manager.db`）：
- `watch_log` — 观看记录 (user_id, bvid, skill_id, level, watched_at, completed)
- `submission` — 作业提交 (user_id, skill_id, level, video_path, status, ai_score, dimension_scores)
- `face_swap_log` — 换脸记录 (user_id, target_skill_id, source_photo, output_video, status)
- `training_task` — 训练计划 (user_id, skill_id, level, track, planned_date, completed)

核心函数：
- `recommend_training_videos(user_id, count=3)` — AI推荐：看过L1 → 推荐L2；未看过 → 推荐同级
- `log_watch(user_id, bvid, skill_id, level)` — 记录观看
- `submit_training_video(user_id, skill_id, level, video_path)` — 提交作业
- `get_submission_detail(submission_id)` — 作业详情+评分
- `request_face_swap(user_id, target_skill_id, source_photo)` — 提交换脸
- `get_training_dashboard(user_id)` — 三轨总览看板

### API端点 (webapp.py)

轨道1: 看示范
| Endpoint | Method | Description |
|:---------|:------:|:------------|
| `/api/training/catalog` | GET | B站视频目录 (支持 skill_id/level/category 筛选) |
| `/api/training/catalog/{skill_id}` | GET | 按技能ID获取视频 |
| `/api/training/recommend` | GET | AI推荐训练视频 |
| `/api/training/watch-log` | POST | 记录观看 |
| `/api/training/watch-history` | GET | 观看历史 |

轨道2: 交作业
| Endpoint | Method | Description |
|:---------|:------:|:------------|
| `/api/training/submit` | POST | 提交训练视频作业 |
| `/api/training/submissions` | GET | 作业列表 |
| `/api/training/submission/{id}` | GET | 作业详情 |
| `/api/training/submission/{id}/score` | POST | 更新AI评分 (异步回调) |

轨道3: 换脸秀
| Endpoint | Method | Description |
|:---------|:------:|:------------|
| `/api/training/faceswap` | POST | 提交换脸请求 |
| `/api/training/faceswap-history` | GET | 换脸历史 |
| `/api/training/faceswap/{id}/result` | POST | 更新换脸结果 |

综合
| `/api/training/dashboard` | GET | 三轨总览看板 |

## 小程序前端

页面路径: `miniprogram/pages/training-manage/`

三轨Tab切换: `activeTrack ∈ {watch, submit, swap}`

- **看示范Tab**: 推荐区(横向scroll) + 分类筛选(filter-bar) + 等级筛选(level-chips) + 视频列表 → 点击跳转B站
- **交作业Tab**: 录视频(wx.chooseMedia camera) + 从相册选 + 选择技能 → 上传 → 作业历史列表
- **换脸秀Tab**: 选技能 + 上传正面照 → 生成按钮 → 历史记录

从 training 页进入: `goTrainingManage()` → `wx.navigateTo('/pages/training-manage/training-manage')`

## 与已有系统的关系

- **训练管理页** 是独立子页面，从 training 页的Banner入口进入
- 交作业评分**复用** `/api/assess/evaluate-person` 评估管线
- 换脸**复用** `face_swap.py` 的 `/api/avatar/generate` 端点
- B站视频目录**独立于** `badminton-label-system` 的 `skill_video_mapping.json` (那是动作clips路径，这里是教学视频)
- 三轨系统有自己的 `training_manager.db`，不依赖项目根 `users.db`
