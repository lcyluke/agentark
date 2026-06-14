---
name: badminton-coach-ai
description: Build or extend a badminton motion-analysis AI coach — pose estimation, stroke detection, footwork analysis, pro-comparison scoring, video scraping, LLM coaching critique, amateur training system (23 categories × 127 sub-skills × 3 levels = 381 training modules), video-based exam scoring, massage library (6 body parts × 3 levels), doubles analysis (multi-person pose tracking, formation/rotation/tactic scoring), and professional service marketplace (coaches + massage therapists + scheduling). Use when the user wants sports video analysis (badminton specifically), automatic technique diagnosis, training plan generation, training animation generation, massage/wellness content, or wants to iterate on the existing project at ~/Desktop/2026AIAPP/workspace/badminton-coach-ai.
---

# Badminton Coach AI

End-to-end pipeline: video → pose estimation → stroke detection → technique
diagnosis → footwork analysis → pro comparison → LLM coaching critique →
annotated output video.

Project location: `/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai`

**⚠️ PROJECT LOCATION — no dual paths.**
There is ONLY ONE canonical project directory: `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`.

A stale empty shell exists at `~/workspace/badminton-coach-ai/` (intentionally cleared). If you find yourself in that directory, immediately `cd` to the real one. If you see a process running from the stale path, kill it and restart from the correct location. The stale path will NOT be repopulated — do not write new code there.

The `~/workspace/` link was an earlier convention. All development now happens under `~/Desktop/2026AIAPP/workspace/`. Never create new files or modules in `~/workspace/badminton-coach-ai/`.

**Brand name:** 羽球宝AI搭子 (NOT 羽迹, NOT 羽毛球AI教练 — this is the actual WeChat mini-program registered name used for 备案.)

## Action classification system (23 categories, 127 sub-skills, 381 training modules)

The project defines a **comprehensive 19-category classification** stored in `skill_definitions_full.py` and dynamically merged into `amateur_training.py`:

### Original 7 categories (51 sub-skills) ✅
| ID | Name | Sub-skills |
|:---|:-----|:----------:|
| high_clear | 🏸 高远球 | 5 |
| smash | 💪 杀球 | 7 |
| drop | 🔄 吊球 | 6 |
| net | 🎯 网前球 | 8 |
| footwork | 🦶 步法 | 5 |
| defense | 🛡️ 防守 | 5 |
| feints | 🎭 假动作 | 15 |

### Extended 12 categories (57 sub-skills) — in `skill_definitions_full.py`
| ID | Name | Sub-skills |
|:---|:-----|:----------:|
| serve | 🚀 发球 | 4 |
| drive | ⚡ 平抽挡 | 4 |
| lob | 🔝 挑球 | 5 |
| block | 🖐️ 挡网 | 4 |
| spin | 🌀 旋转球技术 | 4 |
| combination | 🔗 组合技术 | 5 |
| pacing | 🎵 节奏控制 | 4 |
| serve_return | 🔄 接发球 | 5 |
| tactics | 🧠 战术意识 | 5 |
| conditioning | 🏋️ 体能训练 | 5 |
| singles | 🏃 单打专项 | 6 |
| doubles | 👥 双打专项 | 6 |

### Additional 4 categories (19 sub-skills) — in `skill_definitions_full.py`
| ID | Name | Sub-skills |
|:---|:-----|:----------:|
| transition | 🌉 过渡球 | 5 |
| tactics_pattern | 👟 球路组织 | 5 |
| flexibility | 🧘 柔韧恢复 | 4 |
| special | 🎪 特殊技术 | 5 |

Total: **23 categories · 127 sub-skills · each × 3 levels = 381 training modules**

**Implementation:** `EXTENDED_CATEGORIES` and `EXTENDED_SKILL_BANK` are defined in `skill_definitions_full.py` (~6,500 lines). `amateur_training.py` imports them and merges via `CATEGORIES_BANK.update(EXTENDED_CATEGORIES) / SKILL_BANK.update(EXTENDED_SKILL_BANK)`. The training API at `GET /api/training/categories` automatically returns all 23 categories with no additional routing changes.

Any code that hardcodes "7 categories" or "51 sub-skills" (descriptions, docs, frontend references) is now outdated. When the user asks about the skill system, report 23/127/381.

## When to use

- User wants to analyze badminton (or similar racket sport) technique from video
- Iterate/extend the existing badminton-coach-ai project
- Build sports motion analysis with MediaPipe Pose
- **User asks about the 三等级付费系统** (free/amateur/pro tiers, booking, assessment history — see references/backend-api-routes.md for the API route map)
- **User asks for PRD or product requirements** for the badminton coach app — see references/prd.md in the skill dir
- **User says "持续迭代", "持续开发", or asks for multi-sprint development** — this is a continuous iteration project with 5h/week budget, single-developer, self-funded. See the "Continuous iteration mode" section below for the session-resume checklist and sprint cadence.

## 🎯 商业化核心判断（此技能的重中之重）

**老卢已验证的付费价值逻辑（2026-06-02）：**
1. ❌ MimicMotion生成的"你做标准动作"视频——视觉炫酷但**不含球拍、球、分解教学**，不是付费功能
2. ✅ **上传自己视频→AI比对职业标准→逐帧标出10关节角度差→中文纠错话术→7天训练计划**——这是真正的付费功能
3. ✅ **连续练习追踪+关卡解锁（L1→L2→L3）+ 连续打卡🔥激励**——这是用户留存和付费转化引擎

**开发优先级：** 比对引擎 > 训练追踪 > 激励系统 > 动作演示视频。MimicMotion是锦上添花，不是核心。

## 产品体验（迭代方向）

用户路径：
```
mimic页（一键生成） → practice页（带着练+追进度） → compare页（上传自己动作vs标准）
    |                       |                          |
  上传照片+选7类动作    看拆解演示(4阶段)        上传自己打球视频
  一键生成21个演示视频  今日目标3组×15次          vs 职业标准骨架
                        记录→解锁L1→L2→L3       DTW对齐→10关节角度差
                        连续打卡🔥               中文纠错+7天计划

进阶路径（P0.7）：
  compare页 → dual页（双路视频对比） → 教练预约 → 按摩预约
                  |                    |            |
           正面+侧面双视频        入驻+审核        入驻+审核
           6项3D增强指标         预约+管理        预约+管理
           对称性+姿态+发力链
```

## Architecture (modules under badminton_coach/)

| Module | Role |
|--------|------|
| `pose_estimator.py` | MediaPipe PoseLandmarker → 33 keypoints/frame as `FramePose` (new v0.10.35 API) |
| `stroke_analyzer.py` | Wrist-speed peak detection → stroke classify + 4 metrics |
| `footwork_analyzer.py` | split-step, recovery, court coverage, stance height |
| `reference_library.py` | Pro benchmark fingerprints + 0–100 similarity scoring |
| `skill_grader.py` | L1~L7 amateur grade + 6-dim radar profile + per-action scoring |
| `image_assessor.py` | Single-frame photo → pseudo-StrokeEvent → grade (low conf) |
| `coach.py` | Rule report + pro comparison + LLM critique (auto-fallback) |
| `visualizer.py` | Skeleton overlay + stroke annotation video |
| `webapp.py` | FastAPI: /api/assess, /api/doubles (双打角色), /api/full, / (Web UI), includes amateur_training router |
| `auth_api.py` | Auth + 三等级付费系统 (user tiers, bookings, history) |
| `comparison_engine.py` | **Pro逐帧比对引擎** — DTW对齐 + 10关节角度偏差 + 中文纠错话术 + 综合评分A/B/C/D + 7天训练计划 + 侧排比对视频渲染 |
| `amateur_training.py` | Amateur training engine: 7 categories × 51 sub-skills × 3 levels (153 training grades), video exam scoring, massage library API (6 body parts × 3 levels), coach/therapist/scheduling schemas, unlock-chain logic, **doubles skill API** (16 skills × 3 levels), **doubles analyze API** (`/api/doubles/analyze` POST), **training plan API** (`/api/training/plan` GET — AI-generated weekly plan from progress) |
| `doubles_estimator.py` | **Multi-person pose estimator** — MediaPipe Pose Landmarker with `num_poses=4`, auto-assigns A1/A2/B1/B2 player labels by court position (left/right → front/back depth). Returns `DoublesFrame` per frame with `formation`, `court_zones`, `player_assignments` |
| `doubles_analysis.py` | **Doubles match analyzer** — takes a doubles video, outputs: formation stats, rotation events, 8x skill scoring, 6x tactic scoring, 4x coordination scoring, overall score, training advice |
| `token_optimizer.py` | **3-level token compression** to reduce DeepSeek API costs: level 1 = rule-based (zero-dep, ~2ms, 18-25%), level 2 = LLMLingua (50-70%, needs ~500MB model), level 3 = semantic cache (0-100% on hits). See `devops/token-optimization` skill |
| `training_gif.py` | MediaPipe-style skeletal animation GIF generator from hand-authored keyframes — produces practice demo animations (6 skills, 50-134KB each) |
| `comparison_engine.py` | **Pro benchmark comparison engine** (1211 lines) — DTW temporal alignment, 10-joint angle deviation analysis, Chinese correction templates, 7-day training plan generation, overall scoring A/B/C/D, side-by-side skeleton animation rendering. See `references/comparison-engine.md` |
| `dual_video_analyzer.py` | **Dual-camera fusion engine** (420 lines) — front+side video → MediaPipe extraction per view → independent metrics (symmetry/arm trajectory from front, posture/knee/lean from side) → DTW alignment to benchmark per view → 6 fused 3D-enhanced metrics (symmetry, posture, racket-head-speed, kinetic-chain, rotation-quality, overall) → Chinese corrections with view attribution → 7-day training plan. Key design: each view extracts what it sees best; fusion happens at the scoring and correction layer, not the skeleton layer. |
| `training_game.py` | **Game engine** (460 lines) — skill tree DAG with 23-category prerequisite chains, XP/level system, 11 achievement badges (first_clear, streak_3/7/30, skill_master_10/23, xp_1000/10000, category_clear_5/10), daily quest generator (3 random tasks/day, idempotent), auto-check-achievements on call. Layered on top of `training_tracker.py` (uses `get_training_summary()` for progress data). Tables: `user_game`, `achievements`, `daily_quests`, `skill_unlocks` — all in project-root `users.db`. See `references/training-game-system.md`. |
| `defense_assessor.py` | **防守技能评估引擎 (P3)** — 外部视频→MediaPipe→DTW对齐三招benchmark (接杀挡网/低挑/反击)→6维评分→L1-L7等级→达标判定。三招benchmark存于/tmp/badminton_defense/benchmark_*.npy。API: POST /api/defense/assess + GET /api/defense/skills |\n| `defense_animator.py` | **标准防守动画生成器 (P3-②)** — benchmark骨架→1080p骨骼动画视频。OpenCV渲染彩色骨架(橙臂蓝腿) + 自动相位标注(准备/引拍/击球/随挥) + 双向循环播放 + ffmpeg兜底。输出250-430KB MP4。函数: render_animation(skeleton, path, skill_name) → generate_all_defense_animations(dir) → 挂载为 /defense_animations 静态目录。API: GET /api/defense/animations |n| `wechat_pay.py` | **微信支付 API v3 (P1-⑥)** — JSAPI 小程序支付全链路: 创建订单→获取 prepay_id→小程序调起→回调验签→自动升级套餐。双模式：Mock 模式（开发环境零配置）和真实模式（填商户号即切换）。订单表 `orders` + API: `/api/pay/create-order`, `/api/pay/mock-complete`, `/api/pay/orders`, `/api/pay/order/{order_no}`, `/api/pay/callback`。支持 amateur/pro × monthly/annual 四档定价 (¥9.9/¥79/¥29.9/¥199)。 |
| `face_swap.py` | **AI换脸换衣引擎 (P3-③)** — 用户照片+MimicMotion骨架→"自己做标准动作"视频。三模式：stub(本地骨骼动画)、autodl(SSH→AutoDL RTX 4090推理)、local(GPU≥8GB)。autodl模式需环境变量 AUTODL_HOST/PORT/PASS。门控: feature=coach_booking (Pro版)。挂载目录: /defense_animations/avatars/。API: POST /api/avatar/generate + GET /api/avatar/skills。**已验证: stue模式450KB MP4输出，9技能可用，后端121端点全部在线。** |\n| `webapp.py` — 多人评估工具函数 | **多人视频智能选人管线 (P2)**。`_detect_faces_detailed(image_path)` — 返回每个人脸的 `[{bbox, score, proximity: near|mid|far, clarity: clear|blurry|partial, area_pct, lap_var}]`。`_sample_clothing_color(img, face_bbox, h_f, w_f)` — 采样人脸下方躯干区域主导色 → 中文颜色名（红色上衣/蓝色上衣/...）。`_count_faces()` — 保留原简单计数函数。 |

**Three-track training management (P1):** see `references/three-track-training-management.md`.\n\n| `bilibili_catalog.py` | B站教学视频目录: 6专项×3级=18精选视频, 按技能/等级/大类查询, B站URL生成 |\n| `training_manager.py` | 三轨管理引擎: 看示范(推荐+观看追踪), 交作业(上传+评分+历史), 换脸秀(照片+生成+记录), 综合看板 |\n\n**Three-track API endpoints (in webapp.py):**\n\n| Endpoint | Method | Description |\n|:---------|:------:|:------------|\n| `GET /api/training/catalog` | GET | B站视频目录 (skill_id/level/category筛选) |\n| `GET /api/training/catalog/{skill_id}` | GET | 按技能ID查询 |\n| `GET /api/training/recommend` | GET | AI推荐视频 (count=3) |\n| `POST /api/training/watch-log` | POST | 记录观看 {bvid, skill_id, level} |\n| `GET /api/training/watch-history` | GET | 观看历史 |\n| `POST /api/training/submit` | POST | 提交视频作业 |\n| `GET /api/training/submissions` | GET | 作业历史 |\n| `GET /api/training/submission/{id}` | GET | 作业详情+评分 |\n| `POST /api/training/faceswap` | POST | 提交换脸请求 |\n| `GET /api/training/faceswap-history` | GET | 换脸历史 |\n| `GET /api/training/dashboard` | GET | 三轨综合看板 |\n\n**Mini-program page:** `pages/training-manage/` — 三轨Tab切换 (watch/submit/swap), 从 `pages/training/` 的Banner入口进入。\n\n**Comparison engine API endpoints (in webapp.py):**

| Endpoint | Method | Description |
|:---------|:------:|:------------|
| `POST /api/compare` | POST | Upload video → MediaPipe extraction → compare against benchmark → full report |
| `GET /api/compare/from-file` | GET | Direct skeleton file path comparison (dev use) |
| `POST /api/compare/skeleton` | POST | JSON skeleton body comparison |
| `GET /api/compare/benchmarks` | GET | List all 8 available pro benchmarks (smash/clear/drop/net/footwork/feint/def/amateur) |

**P1 商业化 API endpoints (in amateur_training.py router, current):**

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `GET /api/user/plans` | GET | — | 套餐列表 + 定价 |
| `GET /api/user/usage` | GET | Bearer | 用量仪表盘 |
| `POST /api/user/pay` | POST | Bearer | 模拟支付升级套餐 |
| `GET /api/user/gate-check` | GET | Bearer | 检查某功能是否可用 |
| `GET /api/user/popup-state` | GET | Bearer | 轮询弹出提醒状态（到期/配额警告/耗尽 4级） |
| `POST /api/booking/request` | POST | Bearer | 发起竞价预约请求 → 进入竞价池 |
| `GET /api/booking/requests/my` | GET | Bearer | 我的预约请求列表（含竞标数+中标状态） |
| `GET /api/booking/requests/open` | GET | Bearer | 教练端：查看可竞标的开放请求 |
| `POST /api/booking/requests/{id}/bid` | POST | Bearer | 教练对请求出价 |
| `GET /api/booking/requests/{id}/bids` | GET | Bearer | 用户查看竞标列表（智能排序+标签🥇/⭐/💰） |
| `POST /api/booking/requests/{id}/accept` | POST | Bearer | 接受竞标 → 生成正式预约 |
| `POST /api/booking/instant` | POST | Bearer | 即时预约（跳过竞价，兼容原 /api/coach/booking） |
| `POST /api/pay/create-order` | POST | Bearer | 创建微信支付订单 → 返回 prepay 参数 |
| `POST /api/pay/mock-complete` | POST | — | Mock 支付完成（仅开发环境） |
| `GET /api/pay/orders` | GET | Bearer | 用户订单历史 |
| `GET /api/pay/order/{order_no}` | GET | — | 查询单笔订单状态 |
| `POST /api/pay/callback` | POST | — | 微信支付回调端点（需HTTPS+ICP备案） |

**DB tables added in P1:**

| Table | Key columns | Purpose |
|:------|:------------|:--------|
| `booking_requests` | user_id, provider_type, booking_date/time, max_budget, status(open/accepted/closed), accepted_bid_id | 竞价预约请求池 |
| `bids` | request_id, provider_id, amount, notes, status(pending/accepted/rejected) | 教练/医师竞标记录 |
| `orders` | order_no, user_id, plan_id, period, amount, status, wx_prepay_id, wx_transaction_id, paid_at | 微信支付订单追踪 |

**Dual-camera comparison API endpoints (in webapp.py):**

| Endpoint | Method | Description |
|:---------|:------:|:------------|
| `POST /api/dual/upload?view=front` | POST | Upload front video → returns `session_id` (5min TTL) |
| `POST /api/dual/upload?view=side&session_id=xxx` | POST | Upload side video for session → triggers fusion analysis, returns full dual report |
| `GET /api/dual/actions` | GET | List 7 supported action types (smash/clear/drop/net/footwork/feint/def) |

**Sequential upload pattern (required by WeChat mini-program `wx.uploadFile` single-file limitation):**
1. `POST /api/dual/upload?view=front&action_type=smash` → user gets `{"session_id": "abc123", ...}`
2. `POST /api/dual/upload?view=side&session_id=abc123&action_type=smash` → user gets full `DualAnalysisResult`
3. In-memory session store with 5-minute TTL auto-cleanup. Invalid/expired `session_id` returns 400.
4. Original `/api/dual/compare` (two files in one POST) was replaced by this two-step pattern because WeChat's `wx.uploadFile` only sends one file per request — do NOT attempt to use `wx.request` with FormData polyfills for multi-file upload; they are unreliable on the mini-program runtime.

**Dual report structure:** `{front: {frames, detection_rate, deviations}, side: {...}, fusion: {overall_score, grade, symmetry_score, posture_score, kinetic_chain, rotation_quality, racket_head_speed, action, benchmark}, corrections: [{joint, view, severity, issue, drill}], training_plan: [{day, phase, tasks}]}`.

**Defense assessment API endpoints (in webapp.py, P3):**

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `POST /api/defense/assess` | POST | Bearer | Upload video → MediaPipe→DTW→6-dim scoring (gated: compare) |
| `GET /api/defense/skills` | GET | — | List 3 defense skills + 7 grades + 6 assessment dims |

**多人视频选人+评估 API (P2, in webapp.py):**

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `POST /api/assess/validate` | POST | — | **增强版** — 多人视频不再截断。2+人脸时返回 `needs_person_select:true` + `people:[{id, face_bbox, proximity, clarity, clothing_color, position, face_crop_path, recommend}]` + `video_path`（视频暂存供后续管线使用）。单人时行为不变。 |
| `POST /api/assess/detect-actions` | POST | — | **动作识别** — 入参 `{video_path, person_id, face_bbox}` → MediaPipe Pose 骨骼追踪选人（鼻尖距人脸检测中心 <40%画幅） → 7类动作启发式分类（杀球/高远球/吊球/网前球/平抽/挑球/步法） → 返回 `{detected_actions, completeness}` |
| `POST /api/assess/cartoon-avatar` | POST | — | **卡通化身** — 入参 `{face_crop_path}` → OpenCV 管线(bilateralFilter×2 + adaptiveThreshold + 色彩量化 + HSV增强) → 返回 `{avatar_path, avatar_url}` |
| `POST /api/assess/evaluate-person` | POST | — | **单人全量评估** — 入参 `{video_path, person_id, selected_actions, face_bbox}` → 调用 `_assess_video` + `_enrich` → 返回 `{assessment, training_plan, injury_prevention, gear, person_id, assessed_actions}`。结束后自动清理临时视频。 |

**完整多人评估流程：** 上传视频 → `validate` 返回人员列表 → 用户选人 → `cartoon-avatar` 生成卡通头像 → `detect-actions` 动作识别清单 → 用户确认动作 → `evaluate-person` 最终评估。

Defense benchmarks live at `/tmp/badminton_defense/benchmark_{defense_block,defense_lob,defense_counter}.npy` (T,33,4). Generated from source video via `build_benchmarks.py` → manual skill_id to time-segment mapping. Defense animation assets served statically at `/defense_animations/` (mounted to `/tmp/badminton_defense/animations/`). See `references/defense-benchmark-pipeline.md` for the full extraction + benchmark + animation pipeline.

**Defense assessment dimensions (6-dim, task-specific):**

| Dim | Weight | What it measures |
|:----|:------:|:-----------------|
| stance_stability | 0.15 | Shoulder Y variance vs benchmark |
| squat_depth | 0.20 | Knee Y depth ratio |
| arm_position | 0.20 | Wrist-to-shoulder Y offset |
| elbow_angle | 0.15 | Elbow flexion angle deviation |
| knee_angle | 0.15 | Knee flexion angle deviation |
| motion_smooth | 0.15 | Wrist acceleration variance |

**Face swap / avatar API endpoints (in webapp.py, P3-③):**

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `POST /api/avatar/generate?skill_id=defense_block&mode=stub` | POST | Bearer | Upload photo → generate face-swapped demo video (gated: coach_booking) |
| `GET /api/avatar/skills` | GET | — | List swappable skills + available modes (stub/autodl/local) |

Avatar videos served from `/defense_animations/avatars/` (mounted to `/tmp/badminton_defense/avatars/`).

**Training game API endpoints (in amateur_training.py router, prefix /api):**

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/training/game/state` | GET | Bearer | Full game state: player(Lv/XP/streak) + skill tree + achievements + daily quests |
| `/api/training/game/skill-tree` | GET | Bearer | Skill tree: 23 categories, 127 skills, per-node lock/unlock/L1/L2/L3 state, prerequisites, progress |
| `/api/training/game/skill-tree/{skill_id}` | GET | Bearer | Single skill unlock check: which prereqs are met/missing, required level |
| `/api/training/game/achievements` | GET | Bearer | Badge list: `all_badges` (earned) + `all_defined` (all 11 with icon/name/desc) + `new_badges` |
| `/api/training/game/quests` | GET | Bearer | Today's 3 random quests (idempotent — same-day calls return same three from DB) |
| `/api/training/game/quest/{quest_id}/complete` | POST | Bearer | Mark quest done → XP reward returned as `{quest, xp_result: {xp_gained, total_xp, level, leveled_up, next_level_xp}}` |

See `references/training-game-system.md` for full game mechanics, XP table, achievement definitions, and import pitfalls.

**Benchmarks** live at `badminton-label-system/data/benchmarks/{action}_L{level}.npy` — 15-landmark format (T, 15, 3) numpy arrays. 8 files available (smash_L6, clear_L5, drop_L6, net_L6, footwork_L5, feint_L5, def_L6, amateur_L6). The comparison engine auto-selects the highest level.

**Architecture:**
1. `load_user_skeleton(json_path)` — parses MediaPipe 33-landmark JSON → 15-keypoint format
2. `load_benchmark(action_type)` — loads the appropriate .npy from benchmarks dir
3. `dtw_align(user_seq, pro_seq)` — angle-based DTW for temporal alignment (more robust than coordinate DTW)
4. `compute_angle_deviation(user_seq, pro_seq, aligned_path)` — per-joint angle comparison with mean/max/std stats
5. `generate_report(deviations, threshold)` — generates Chinese correction advice with severity labels
6. `_compute_overall_score(deviations, corrections)` — weighted scoring (right elbow 0.25 > right shoulder 0.20 > knees 0.15 > waist 0.10 > left side 0.05)
7. `_generate_training_plan(corrections, score)` — 7-day priority-ranked plan
8. `render_comparison_video(user_seq, pro_seq, aligned_path, output_path)` — side-by-side skeleton animation with color-coded bones (green <8°, yellow 8-20°, red >20°)

**Key insight from product validation (2026-06-02):** The user rejected MimicMotion generated videos ("绿色屏幕没有人") and clarified the real product value is **upload-your-own-video → compare → see errors → get training plan**, NOT "see yourself doing the motion". The comparison engine is the core monetizable feature — not the pose-guided video generation.

**Video mapping bridge (badminton-label-system ↔ badminton-coach-ai webapp):**

The two projects are linked at runtime via `badminton-coach-ai/badminton_coach/webapp.py`:

```
_LABEL_SYSTEM = os.path.abspath("../../badminton-label-system")  # 2 directories up from webapp.py
```

This path resolves from `badminton-coach-ai/badminton_coach/webapp.py` → `badminton-label-system/`. It must exist — the webapp reads `skill_video_mapping.json` and mounts `data/processed_videos/` (clips) and `data/skeletons/` (skeleton data) as static files.

**API endpoints for video mapping (all in `webapp.py`):**

| Endpoint | Description | Return |
|:---------|:------------|:-------|
| `GET /api/training/video-mapping` | Full skill→video mapping table | JSON |
| `GET /api/training/skill-video/{skill_id}?level=N` | Best demo video for one skill+level | `{url, resolution, source, best_for}` |
| `GET /clips/...` | Static serving of B站 action clips | MP4 files |
| `GET /skeletons/...` | Static serving of skeleton JSON | JSON files |

The mapping file lives at `~/Desktop/2026AIAPP/badminton-label-system/data/skill_video_mapping.json`. It maps each of the 7×21 sub-skill levels to specific B站 clip paths (globbing patterns like `bilibili/4K视频目录/demo*.mp4`).

**Static mount pattern (safer with try/except):**
```python
try:
    app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="action_clips")
except Exception as e:
    print(f"⚠️ clips挂载失败: {e}")
```

Backend API route map: see `references/backend-api-routes.md`.
Amateur training system architecture (training engine, massage library, coach schema, API routes, unlock chain): see `references/amateur-training-system.md`.
Check-in API routes: see `references/checkin-api-routes.md` (7 endpoints, all Bearer auth).
DevTools CLI workflow: see `references/wechat-devtools-cli.md`.
WeChat Mini-Program scaffold: see `references/wechat-miniprogram-scaffold.md` (12 pages: login, survey, home, assess, result, training, injury, gear, profile, guide, booking, history).  
Comparison + tracking API route map: see `references/2026-06-02-new-modules.md` (4 new endpoints for compare + 10 for training tracker).  
Skill breakdown (7 categories × 4 phases in Chinese): see `references/2026-06-02-new-modules.md`.  
Doubles analysis system (multi-person pose tracking, formation/rotation/tactic scoring, 16 doubles skills): see `references/doubles-analysis.md`.
Dual-camera fusion system (sequential upload, 6 fused metrics, mini-program pages, test recipe): see `references/dual-camera-system.md`.  
Multi-person video assessment pipeline (validate → person select → cartoon avatar → action detection → focused evaluation): see `references/multi-person-pipeline.md`.
Apex Dashboard kanban integration (task management, batch import, status tracking): see `references/apex-dashboard-integration.md`.
Training game system (skill tree DAG, XP/level, achievements, daily quests, API endpoints, mini-program page): see `references/training-game-system.md`.  
Training plan API (weekly AI-generated plan from progress): see `references/training-plan-api.md`.  
Booking auction system (Uber化竞价: request to bid to smart-rank to accept, P1-④): see `references/booking-auction.md`.  
Payment system (微信支付 API v3 Mock/Real dual-mode, P1-⑥): see `references/payment-system.md`.  
Motion analysis templates (landmark indices, per-technique motion signatures, action segmentation algorithm): see `references/motion-templates.md`.  
Video collection + analysis pipeline (WeChat video to skeleton to segmentation): load the `video-motion-analysis-pipeline` skill.  
Mini-program training page architecture (dual sort, built-in data, progress tracking): see `references/miniprogram-training-page.md`.\nThree-track training management system (B站 catalog, submission pipeline, face swap integration, dashboard): see `references/three-track-training-management.md`.\nTech architecture decision guide: see `references/tech-architecture-decision.md`.

KEY: `auth_api.py` uses `APIRouter(prefix="/api")`, so auth endpoints are
`/api/auth/wechat`, `/api/auth/sms/send`, `/api/auth/sms/login` — NOT
`/api/sms/send` etc. Grep the decorators before calling; guessing cost two 404s.

## Skill grading system (L1~L7)

7-tier amateur scale aligned to 中羽协段位 / D-C-B-A-S / NTRP. Key design:
- 6 dims: swing_power, lower_body, footwork, recovery, balance, consistency
- L3 (中级) hard gate: swing>=45 AND lower>=30 AND footwork>=35, else capped at L2
- consistency is a multiplier (0.75+0.25*c) to prevent single-rally inflation
- image source → low confidence (0.45), video with >=8 strokes → 0.85

### 🎯 Assessment accuracy philosophy (老卢 confirmed 2026-06-02)

羽毛球等级评估不是数学题，没有唯一正确答案。本质是**共识问题**。

> 不要追求"全球最准"，追求"用的人最多"。

**三条路径:**
1. **准确性** — 做双盲验证 (AI vs 3位教练独立打分 → 算MAE)，不吹牛。输出可验证的数字（"与3位国家级教练评分一致性92%"），不是空洞的"最准"。
2. **合适性** — 让用户自己校准。评估结果页加"👍偏高/偏低"反馈按钮，收集500条反馈后按级调整阈值。等级体系从球友共识中长出来。
3. **受欢迎** — 不是优化算法，是优化传播。球友A拿L5发朋友圈 → 球友B看见来测 → 互相比分数 → 裂变。等5000人在用，自然成标准。

**DO NOT** claim "全球最准确" without data. **DO** lead with "深圳X球友在用" + 双盲一致性数字。
**DO NOT** build assessment standards from video titles/topics without actual video data. Video-based assessments must be grounded in real video analysis, not inferred from metadata.

## Setup

```bash
cd /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# MediaPipe 0.10.35+ requires downloading the pose model separately:
curl -L -o pose_landmarker_lite.task \
  "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
```

## Operation

### Start backend

```bash
cd /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai
source venv/bin/activate

# CRITICAL: Kill any stale process on port 8000 first (common resume gotcha)
lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 1

export BADMINTON_SECRET="$(openssl rand -hex 32)"
python3 -c "
import uvicorn
uvicorn.run('badminton_coach.webapp:app', host='127.0.0.1', port=8000, log_level='info')
"
```

### Start backend — CRITICAL: use venv Python, NOT system Python

The project's MediaPipe was built with venv's Python 3.11 + NumPy 1.x.
System Python (e.g. `/opt/anaconda3/bin/python3`) runs NumPy 2.x which crashes
MediaPipe with `ImportError: numpy.core.multiarray failed to import`.

Always start the backend using the VENV python binary directly:

```bash
cd /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai
lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 1
./venv/bin/python3 -m uvicorn badminton_coach.webapp:app --host 0.0.0.0 --port 8000
```

**Do NOT use** `source venv/bin/activate && python3 -c "uvicorn.run(...)"` —
the `python3` inside the `-c` block may resolve to `/opt/anaconda3/bin/python3`
rather than the venv's python, triggering the NumPy version conflict.
Using `./venv/bin/python3 -m uvicorn ...` ensures the venv binary is used
at both the process and the import level.

If you accidentally start with system Python and get "initialization failed"
on `/api/assess`, check the backend logs for `numpy.core.multiarray failed to import`.
Kill the process and restart with `./venv/bin/python3 -m uvicorn ...`.

### Start-of-session health check (resume checklist)

When resuming work on this project after a break (especially when the user says "继续" or starts a new message asking to continue development), run this checklist BEFORE doing anything else:

0. **Canonical directory?** Confirm `pwd` or `cd` to `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`. If you're in `~/workspace/badminton-coach-ai/`, switch immediately — it is a stale empty shell and all real work is in the Desktop path.

1. **Backend alive?** `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/` — if not 200, start it (see above). If port busy, `lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 1` to kill stale process first.
   **CRITICAL: After killing a stale process, verify the new server starts from the right directory.** The old process may be running from `~/workspace/badminton-coach-ai/` (empty shell). Run `ps aux | grep uvicorn | grep -v grep` to see the cwd. If it shows the wrong path, kill it and start from `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`.
2. **DevTools running?** `pgrep -fl wechatwebdevtools` — if no, open with: `/Applications/wechatwebdevtools.app/Contents/MacOS/cli auto --project miniprogram/` (but first quit stale daemon: `cli quit 2>/dev/null; pkill -f wechatwebdevtools 2>/dev/null; sleep 2`)
3. **Git clean?** `git status --short` — uncommitted changes are expected during iteration, but note them for the next commit/tag.
4. **Quick API smoke test:** `curl -s http://127.0.0.1:8000/api/spec | head -c 100`
5. **Survey question count check:** `curl -s http://127.0.0.1:8000/api/survey/questions | python3 -c "import json,sys; d=json.load(sys.stdin); print(len(d['questions']) if isinstance(d,dict) and 'questions' in d else len(d) if isinstance(d,list) else 'warn: unknown format')"` — should be 5. If 1, the router prefix may have changed (auth_api.py uses APIRouter with prefix).
6. **Report status to user** in a compact table: backend ✅/❌, DevTools ✅/❌, git state, API health.

### Continuous iteration mode (5h/week · single dev · self-funded)

When the user says "持续迭代", "持续开发", "继续", or initiates a session asking to resume development, follow this sprint cadence:

1. **Session resume**: run the health check checklist above. Report compact status.
2. **Prioritize**: the user's implicit preferences (confirmed across sessions) are: fix known bugs > UI/UX fixes > backend features > deployment > new capabilities. Never propose new features if there are known bugs.
3. **Produce increments**: every session should produce at least one working increment. No session is "just planning" unless the user explicitly asks for it.
4. **Version bumps**: `v0.1` → `v0.2` → ... → `v0.6` (deploy+release). Tag each version with `git tag -a v0.X.0 -m "..."` after passing UAT.
5. **UAT before tag**: run the 12-step smoke test (see `references/backend-api-routes.md`) covering changed endpoints. If all pass, tag.
6. **Notify on version**: when a version is tagged and backend restarted, tell the user "v0.X ready. Summary: <3 bullets>". Offer to compile DevTools for manual testing.
7. **Backlog tracking**: keep sprint items in todo() — max 3 active items. Move completed to memory as a "latest version v0.X" note, not full task logs.

## CRITICAL PITFALLS (learned the hard way)

### MediaPipe & AI Pipeline

2. **`FramePose.point()` must return xyz, not xy only.** `pose_estimator.py`'s `point()` returns landmarks with `return lm[:2]` (xy only). But `stroke_analyzer.py`'s `_foot_stance()` accesses `la[2] - ra[2]` (z-axis for front/back foot detection), causing `IndexError: index 2 is out of bounds for axis 0 with size 2` on every video assessment. **Fix: change to `return lm[:3]`.** The landmarks array has shape (33, 4) — x, y, z, visibility. Returning only xy breaks any consumer that reads z. This bug manifests as HTTP 500 on `POST /api/assess` with error `index 2 is out of bounds for axis 0 with size 2`. The fix doesn't affect consumers that only use [0] and [1] (xy). Already fixed in the codebase.

   **Debug tip:** When all videos return the same `IndexError: index 2 is out of bounds for axis 0 with size 2` error, grep for `point(` calls that access index [2] and check the `point()` return shape. The fix is a one-line change in `pose_estimator.py`.

3. **Training animation video vs phone video — same MediaPipe, different source.** Training demo clips from B站/YouTube are typically 480-1080p streaming recordings. Phone-shot videos are HEVC 720p 30fps. MediaPipe's PoseLandmarker processes both identically — no transcoding needed. The differences that affect assessment quality are clip length (see above) and camera angle (side profile vs front-facing phone selfie).

2. **MediaPipe 0.10.35+ dropped `mp.solutions` API.** The `mp.solutions.pose.Pose` API is REMOVED in MediaPipe 0.10.35+. Migrate to `mediapipe.tasks.python.vision.PoseLandmarker` with a downloaded `.task` model file. Full migration guide:

   **Download the model:**
   ```bash
   curl -L -o pose_landmarker_lite.task \
     "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/latest/pose_landmarker_lite.task"
   ```

   **Old code (removed):**
   ```python
   with mp.solutions.pose.Pose(static_image_mode=True, model_complexity=1) as pose:
       res = pose.process(rgb)
       lm = res.pose_landmarks.landmark  # 33 landmarks
   ```

   **New code (PoseLandmarker):**
   ```python
   from mediapipe.tasks.python import vision
   from mediapipe.tasks.python.core.base_options import BaseOptions
   
   options = vision.PoseLandmarkerOptions(
       base_options=BaseOptions(model_asset_path="pose_landmarker_lite.task"),
       running_mode=vision.RunningMode.IMAGE,  # or .VIDEO
       min_pose_detection_confidence=0.4,
   )
   detector = vision.PoseLandmarker.create_from_options(options)
   mp_img = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)
   result = detector.detect(mp_img)
   lm = result.pose_landmarks[0]  # list of persons, each with 33 landmarks
   lm[0].x  # or use the old accessor pattern
   ```

   **Key differences:**
   - Model file: `.task` (5.6MB), not built-in
   - Input: `mp.Image`, not raw numpy/rgb
   - No `with` context manager — create `detector` once, reuse
   - Keypoints: `result.pose_landmarks[person_idx][kpt_idx]` not `result.pose_landmarks.landmark[kpt_idx]`
   - No `.visibility` field on landmarks — set to `1.0` by default
   - For video: `running_mode=vision.RunningMode.VIDEO`, use `detector.detect_for_video(mp_img, timestamp_ms)` with timestamp in milliseconds
   - Multi-person: returns all detected people as list; also add `num_poses=N` to options to set max
   - Single-person photos still mostly work, but partially occluded second people are often missed — use the "遮罩法" (mask out first person region and re-detect) to recover

   **Files that needed migration in this project (all done):**
   - `double_analyzer.py` — `_detect_two_people()` and `_get_detector()`
   - `pose_estimator.py` — `PoseEstimator._lazy_init()` and `process_video()`
   - `image_assessor.py` — `_frame_from_image()`
   - `webapp.py` — `_assess_image()` (standalone copy for the doubles tab)

2. **MediaPipe Pose is SINGLE-PERSON, CLOSE-UP only.** Wide-angle broadcast / multi-player gym footage gives near-zero detection and garbage metrics. For broadcast footage you need YOLOv8-pose (multi-person) — that's an upgrade path, not a bug.

3. **YouTube is fully bot-walled.** `player_client: [android, ios, web]` alone does NOT bypass it. Use archive.org for real badminton footage: `curl -s "https://archive.org/advancedsearch.php?q=badminton+AND+mediatype:movies&fl[]=identifier&fl[]=title&rows=8&output=json"`

4. **Stroke peak detection**: use adaptive "global threshold + local prominence" (peak >= 2x local median). Already implemented in stroke_analyzer.py — don't regress it.

5. **Quick pipeline-validation video without user footage.** Intel-iot-devkit has a directly-downloadable clip: `curl -sL -o test_human.mp4 "https://github.com/intel-iot-devkit/sample-videos/raw/master/person-bicycle-car-detection.mp4"`. Proves pose detection fires on real humans. Synthetic stick-figure video from `cli demo` will NEVER be detected by MediaPipe (0 frames hit) — that is expected, demo only validates video read/write plumbing.

### Phone Video Assessment

Phone-shot videos (iPhone HEVC 720p/1080p, 30fps, `.mp4`) work natively with MediaPipe — **no transcoding needed**. MediaPipe's `PoseLandmarker` processes HEVC frames correctly. Verified with landscape mode phone videos as short as 1.8s.

**Limitation: very short videos (<10s) give poor evaluation.** A 1.8-7s clip typically captures only 1-3 strokes, yielding L2 (初级) with ~33/100 score and low confidence. The AI can't assess consistency, footwork recovery, or transition patterns from such short clips. For meaningful evaluation, the user should upload 30s+ rally clips with multiple strokes and court movement. The resume checklist's quick smoke test (`curl -s /api/spec`) works fine with short clips to verify the pipeline fires, but don't report the actual grade to the user as meaningful.

Phone-sourced videos arrive via WeChat as `.mp4` (HEVC) 720p files in `~/.hermes/cache/documents/` with filenames like `doc_<hash>_video.mp4`. They are true MP4 files (`ISO Media, MP4 v2`) — curl's `-F "file=@..."` uploads them directly to the API with no issues.

### FastAPI Backend

10. **FastAPI Header(None) + GET query params = 422.** When same endpoint has BOTH query params AND `authorization: str = Header(None)`, FastAPI's `Header()` inject triggers the `query` location for `authorization`, producing 422 on every request. Fix: use `request: Request` and extract manually: `request.headers.get("Authorization") or request.headers.get("authorization")`. This is REQUIRED for all GET endpoints with query params that need auth. POST endpoints with `Form()` params are safe — `Form()` pins the data source, so `Header(None)` works there.

11. **venue_db.py CSV path fallback chain.** `VENUE_CSV` env var → hardcoded `~/Desktop/2026AIAPP/shenzhen-badminton/data/venues.csv` → `../data/venues.csv`. If running from a subdirectory the paths may miss. Set `export VENUE_CSV=/absolute/path/venues.csv` to override. The module caches after first load — if the file moves, clear the cache or restart.

### WeChat Mini-Program

12. **WeChat mini-program structure**: lives at `miniprogram/` with **25 pages**: login, survey, home, assess, result, training, injury, gear, profile, guide, booking, history, payment, certificate, photos, matching, venue, daily, compare, practice, mimic, coaches, dual (双路视频对比), camera (双角度录制引导), game (训练闯关). All registered in `app.json`.

12a. **Production deployment prerequisites (user must do themselves):** (a) register at mp.weixin.qq.com → get AppID/AppSecret; (b) get ICP-备案 HTTPS domain for backend; (c) sign up for SMS provider. Backend has Mock fallback — works in devtools without real credentials. Production deploy bottleneck is ICP 备案 (7-15 days) — file it FIRST since it gates HTTPS whitelist.

12b. **DevTools auto-open with real AppID.** The CLI open command works reliably when a real AppID is set in `project.config.json`:
   ```bash
   /Applications/wechatwebdevtools.app/Contents/MacOS/cli auto --project <miniprogram_dir>
   ```
   Without a real AppID, `open` fails with "AppID 不合法". The `auto` command starts the IDE, loads the project, and starts automation mode. User's actual AppID: `wxdad7cddb0cfa785e` (羽球宝AI搭子).

13. **No real payments**: gear recommendation is search-URL jumps only. Real 微信支付 requires business license — explicitly OUT OF SCOPE.

14. **WeChat mini-program API error handling — `e.message` is often undefined.** WeChat's request utility returns `{msg: "...", code: ...}` NOT JavaScript `Error` instances. Fix:
    ```javascript
    } catch (e) { this.setData({ err: e.message || e.msg || '请求失败' }); }
    ```
    Fix api.js request wrapper too:
    ```javascript
    if (res.statusCode >= 400) return reject(new Error(
      (res.data && (res.data.detail || res.data.msg || res.data.error)) || '请求失败'
    ));
    ```

14a. **WXML inline arrow functions in event handlers break mini-program compilation.** `bindinput="e=>venue=e.detail.value"` compiles as `Bad value with message: unexpected '>'`. Replace with named JS methods: `bindinput="onVenueInput"` + define `onVenueInput(e)` in the Page() object. This is separate from the WXML `{{}}` expression ES6 restriction.

14b. **uvicorn `--reload` doubles memory → OOM kill (exit 137).** With MediaPipe + OpenCV + FastAPI's full import graph loaded, `--reload` runs a second watcher process that can spike memory past system limits. Use plain `uvicorn ...` without `--reload` for background processes. Restart manually after code changes.

15. **WeChat mini-program login — WeChat-only (no SMS).** Files: `pages/login/login.wxml` (single button), `pages/login/login.js` (only `loginWechat` + `_afterLogin`). `app.js` `apiBase` must be `http://43.139.191.202` (HTTP before ICP 备案, HTTPS after). DevTools: details → local settings → ☑ 不校验合法域名.

16. **WeChat devtools `@babel/runtime` / enhance mode packaging bug.** Error: `module '@babel/runtime/helpers/typeof.js' is not defined` at `login.js:4`. Fix in `project.config.json`: `"libVersion": "2.33.0"`, `"enhance": false`, remove `lazyCodeLoading` from root. In `app.json`: remove `lazyCodeLoading` from JSON root. DevTools → details → 本地设置 → 基础库选 2.33.0 (not gray 3.16.1). Close devtools, `rm -rf ~/Library/Application\ Support/WechatDevtools/*/Default/`, reopen and recompile.

17. **WeChat mini-program 备案 (Tencent platform).** Just AppID + AppSecret (no APK MD5, no APK needed). APK signing MD5 is only for Android APK distribution — irrelevant for WeChat mini-program.

18. **WeChat devtools "app.json is not found in project root".** Devtools reads the `project.config.json` from the `--project <dir>` passed to the CLI. If that dir has a `project.config.json` with `miniprogramRoot` pointing to a subdirectory, DevTools looks for `app.json` under the subdirectory. **If using `--project` pointing directly at the miniprogram directory, do NOT include `miniprogramRoot`** — it produces "请检查 project.config.json 是否存在及是否有效 (code 19)". Use one of these patterns:
    - Pattern A (recommended for CLI): `--project ./miniprogram` with `project.config.json` at `./miniprogram/project.config.json`, no `miniprogramRoot` field.
    - Pattern B (recommended for GUI): root `project.config.json` with `"miniprogramRoot": "miniprogram/"`, then open the ROOT dir in the IDE.

19. **WeChat devtools CLI port must be manually enabled once.** CLI commands fail with "IDE service port disabled" until user opens DevTools → Settings → Security Settings → enables Service Port. Requires WeChat scan confirmation. One-time setup; persists across restarts.

20. **WeChat mini-program training page loads B站 clips for demo video.** The training detail modal (pages/training/training.js) calls GET /api/training/skill-video/{skill_id}?level=N to get the best B站-sourced action clip. The <video> tag src is {{API}}{{demoVideo.url}} — API must be exposed via data: { API: API }. Three loading states: loading → metadata display (source, resolution, skeleton status) → empty fallback ("暂无示范视频，Pipeline采集中"). The API is served from the badminton-label-system project via FastAPI StaticFiles mounts on /clips/ and skill-video-mapping endpoint.

21. **WeChat `wx.uploadFile` = single file only.** Cannot upload two files in one request. For multi-file endpoints, use a **sequential upload pattern**: first upload returns a `session_id`, second upload includes that ID to trigger processing. Server stores temp files in memory with a short TTL (5 minutes). Do NOT attempt `wx.request` with DIY FormData — the mini-program runtime does not reliably support it. The `/api/dual/upload` API follows this pattern: `?view=front` → session_id → `?view=side&session_id=xxx` → report. Mini-program page: `pages/dual/dual.js` — calls `wx.uploadFile` twice sequentially, passing `session_id` from the first response into the second call's query params.

22. **Cross-page data passing: `app.globalData`.** When one page processes data and navigates to another, `wx.navigateTo` does not carry a payload. Use `app.globalData._<key>` as a temporary bridge: write before `navigateTo`, read in the target page's `onLoad`, then delete immediately to prevent stale state on back-navigation. Example: `camera.js` writes `app.globalData._dualResult = result` before `wx.navigateTo({url: '/pages/dual/dual'})`; `dual.js` reads it in `onLoad` and deletes it. Always delete after reading — if the user navigates back and forth, stale globalData causes the results page to show old data.

23. **WeChat native camera: `wx.chooseMedia` with `sourceType: ['camera']`.** The mini-program does NOT support `<camera>` component-based custom recording UI for production (it renders behind other elements and has poor frame access). Use `wx.chooseMedia` to open the system camera directly — it supports `maxDuration` (seconds), `camera: 'back'|'front'`, and returns a temp file path. The 3-2-1 countdown is done in JS before calling `wx.chooseMedia` — the system camera UI itself has no countdown API. Pattern in `pages/camera/camera.js`: `setInterval` countdown → `wx.chooseMedia({sourceType:['camera'], maxDuration:10})` → temp file path → preview in `<video>` tag.

### Landmark Access & Motion Analysis

28. **`FramePose.landmarks` is a numpy array, not an object.** Access by INDEX: `lm[16][1]` for right wrist Y, NOT `lm[16].y` (numpy arrays don't have `.y` attributes). The array shape is `(33, 4)` — indices 0-2 are x/y/z, index 3 is visibility. Key landmark indices: 11/12=shoulders, 14=right elbow, 16=right wrist, 26=right knee, 28=right ankle.

29. **Screen coordinates are inverted.** Lower Y value = higher physical position (arm raised). Higher Y = lower (arm down). Knee Y: higher = deeper squat. See `references/motion-templates.md` for per-technique motion signatures and the full landmark reference table.

30. **First frame of video often has no detection.** MediaPipe needs 2-3 frames to initialize. Skip frame 0 when computing detection rate metrics.

32. **Numpy types crash JSON serialization.** `numpy.float64`, `numpy.int64`, `numpy.bool_` are NOT JSON-serializable by Python's stdlib json. When building assessment results (defense_assessor, comparison_engine, etc.), cast EVERY scalar: `float(val)`, `int(val)`, `bool(val)`. Return `round(float(score), 1)` not `round(score, 1)`. The error manifests as `"Object of type bool_ is not JSON serializable"` — search for undecorated numpy scalars in return dicts. Do NOT use `numpy.bool_` anywhere in a dict destined for `JSONResponse`.

33. **RedNote/Xiaohongshu is fully blocked from this environment.** The browser and API return 300012/300031 (IP at risk). Do not attempt to scrape RedNote content. User sends videos via WeChat → files arrive as `~/.hermes/cache/documents/doc_<hash>_video.mp4` (HEVC 720p MP4, playable directly).

### Python Import Pitfalls

31. **DB migration trap: adding new tables to existing `users.db`.** The `_ensure_tables()` block in `amateur_training.py` uses `CREATE TABLE IF NOT EXISTS`, which only fires on first run. If `users.db` already exists (from a previous session), new tables added to the DDL block are **never created**. When adding new tables (`booking_requests`, `bids`, `orders`, etc.), you MUST manually run `sqlite3 users.db "CREATE TABLE IF NOT EXISTS ..."` for each new table, OR delete `users.db` and let it regenerate (loses all user data). The backend will return 500s with cryptic SQLite errors when querying non-existent tables. **Fix**: after adding new DDL, check with `sqlite3 users.db ".schema <table_name>"` — if empty, create manually.

29. **`form.get()` returns `UploadFile | str | int`, not `str`.** FastAPI's `request.form()` method returns a `FormData` dict where every value has the union type `UploadFile | str`. When you need an integer, use `int(form.get("key", 0))` — the cast works at runtime but Pyright will report type errors. These are false positives and safe to ignore.

30. **`coaches` table has no `city`/`districts` columns.** Only `massage_therapists` has those. When writing queries that join across both provider types, `SELECT id FROM coaches WHERE ...` is safe, but `SELECT id, city FROM coaches` will 500.

24. **`training_game.py` must import from `training_tracker.py` via `get_training_summary()`.** There is NO standalone `get_user_progress()` or `get_user_stats()` export. The correct import is `from .training_tracker import get_training_summary` — it returns `{user_stats: {...}, progress: [...], recent_sessions: [...]}`. Extract `progress` and `user_stats` from the dict. Using wrong import names causes `ImportError` / `AttributeError`.

25. **`load_benchmark(action_type)` takes exactly 1 argument.** Do NOT pass a `benchmark_dir` second argument — the function resolves its own path internally from `BENCHMARKS_DIR` in `comparison_engine.py`. Passing two args causes `TypeError`.

26. **`dtw_align(user_seq, pro_seq)` returns only `list[tuple[int,int]]`** — no distance value. Do NOT unpack as `aligned_path, dtw_dist = dtw_align(...)`. The function only returns the alignment path. If you need a distance proxy, compute `sum(abs(u-p) for u,p in aligned_path) / len(aligned_path)` afterwards.

27. **Database path for `training_game.py`**: the actual `users.db` lives at project root (`badminton-coach-ai/users.db`), NOT in `data/`. Set `_DB = Path(__file__).resolve().parent.parent / "users.db"`. Using `data/users.db` causes table-not-found errors at query time.

31. **Popup trigger: `used >= limit - 1` is `True` when `used=0` and `limit=1`.** The quota-warning tier in `api_popup_state()` originally used `u["used"] >= u["limit"] - 1` which triggers for `0 >= 0` (True) when limit=1 (e.g. compare=1/月). Free users with 0 usage got spurious "本月视频对比还剩1次" popups. **Fix: use exact match `u["limit"] > 1 and u["used"] == u["limit"] - 1`** so that only features with ≥2 quota trigger warnings, and only when exactly 1 use remains. The exhausted tier (`used >= limit`) handles the actual depletion separately.

### Tencent Cloud / Server Deployment

20. **TencentOS nginx.conf does not include sites-enabled.** Only `include /etc/nginx/conf.d/*.conf` — no `sites-enabled/` include. Write config to `conf.d/` directly. Remove `default_server` from listen directives (nginx.conf:39 already has one, else "duplicate default server"). Tencent Cloud Security Group (cloud console) is a SEPARATE firewall — open 80/443 there too or external requests are blocked before reaching nginx.

21. **Python 3.11 missing _sqlite3 module on TencentOS.** Causes badminton.service to fail and enter auto-restart loop. Fix:
    ```bash
    yum install -y sqlite-devel
    cd /tmp/Python-3.11.9
    ./configure --enable-optimizations --prefix=/usr/local --with-sqlite3
    make -j$(nproc) && make altinstall
    rm -rf /data/badminton/app/venv
    /usr/local/bin/python3.11 -m venv /data/badminton/app/venv
    /data/badminton/app/venv/bin/pip install -r requirements.txt
    ```

22. **deploy.sh script evolution.** V1: apt-get → "command not found" → detect yum vs apt-get. V2: sudo PATH truncation → python3.11 not found. V3: for-loop hardcoded paths + rm -rf venv + pip force official PyPI. V4: Tencent Cloud pip `/etc/pip.conf` global lock → PIP_CONFIG_FILE override. V5: pip.conf trusted-host two lines → "option already exists" → merge to one line. V6: trusted-host one line + sqlite3 detection + auto-fix compile. V7: mkdir /etc/nginx/sites-available + conf.d write + remove duplicate default_server. Final: includes sqlite-devel, python3.11 hardcoded path, pip.conf override, nginx conf.d write. Re-rsync after each patch; `rm -rf /data/badminton/app/venv` if re-running.

23. **Tencent Cloud pip internal mirror lock.** Tencent Cloud yum repos mirror pip packages with restricted version range (max numpy 1.19.5). Fix: `PIP_CONFIG_FILE=/data/badminton/pip.conf` pointing to `https://pypi.org/simple/` with `trusted-host = pypi.org files.pythonhosted.org` (one line, not two).

24. **Heavy pip installs look frozen but are running.** `-q` hides all output. Check progress with `ls /data/badminton/app/venv/lib/python3.11/site-packages/ | wc -l`. Allow 2-5 min. Always remove `-q` during debugging so progress is visible.

25. **Tencent Cloud SMS real integration.** Module `sms_tencent.py` wired into `_send_sms()` when `SMS_PROVIDER=tencent`. Needs env: TENCENT_SECRET_ID/KEY, SMS_SDK_APPID (1400xxxxxx), SMS_SIGN_NAME, SMS_TEMPLATE_ID. Both signature AND template need Tencent approval.

26. **云片 (Yunpian) SMS — 个人可用的短信平台.** Supports individual registration with ID card auth. `_send_sms()` uses `SMS_PROVIDER=yunpian` to switch. HTTP 400 `code:-62 "无效资质信息"` = developer info not filled in (account settings, takes hours~1 day to verify). Test: `YUNPIAN_APIKEY=xxx SMS_SIGN_NAME=羽球宝 python deploy/test_sms.py <phone>`.

## Verification workflow (always do this)

### Model versions and paths (2026-06-01 update)

The project now has TWO parallel model sets:

| Model | Old (360p) | New v2 (B站 1,884 samples) | Status |
|:------|:----------:|:-------------------------:|:------:|
| RandomForest | `models/phase1_randomforest.pkl` 1.1MB (71.4%) | `models/phase1_randomforest_v2.pkl` 1.2MB (97.9%) | ✅ **v2 deployed** |
| GBDT | `models/phase2_gradientboostingclassifier.pkl` 1.5MB (91.4%) | `models/phase2_gbdt_v2.pkl` 1.3MB (98.1%) | ✅ **v2 deployed** |
| Ensemble | — | `models/phase2_ensemble_v2.pkl` 5.0MB (98.1%) | ✅ |

The v2 models live in the badminton-label-system project at `models/phase*_v2.pkl`. They must be COPIED to the coach project after training:
```bash
cp ~/Desktop/2026AIAPP/badminton-label-system/models/phase*_v2.pkl \
   ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/models/
```

### Video mapping bridge (badminton-label-system ↔ badminton-coach-ai)

The two projects are linked at runtime via `webapp.py` which mounts the label system's clips and skeletons as static files, and serves the skill-video-mapping API:

```python
_LABEL_SYSTEM = os.path.abspath("../../badminton-label-system")
app.mount("/clips", StaticFiles(directory=_LABEL_SYSTEM+"/data/processed_videos"), ...)
app.mount("/skeletons", StaticFiles(directory=_LABEL_SYSTEM+"/data/skeletons"), ...)
```

Key endpoints:
- `GET /api/training/video-mapping` — full table
- `GET /api/training/skill-video/{skill_id}?level=N` — best demo video
- `GET /clips/bilibili/...` — B站 action clips
- `GET /skeletons/bilibili/...` — skeleton JSON files

```bash
source venv/bin/activate
python -m badminton_coach.cli selftest   # synthetic keypoints, no video/net
python -m badminton_coach.cli demo       # synthetic video, full pipeline
# real video:
python -m badminton_coach.cli analyze <video.mp4> --output out.mp4 --no-llm
```

`selftest` synthesizes two stroke trajectories (one clean smash, one flawed)
and asserts stroke detection + footwork + comparison + plan all fire. This is
the fast regression gate — run it after any edit to the analysis engine.

Quick API smoke test (no video needed): upload the 6 test images and compare
results against `references/ai-assessment-test-images.md`. The `lower_body`
dimension should consistently be the lowest across all scorable images.

For a **structured 6-step UAT** that covers login → survey → assess × 6 → doubles →
full pipeline → tier check + history, see the "Structured UAT testing pattern"
section in `references/backend-api-routes.md`. This is the standard regression
test to run before every version tag.

### UAT Run Pattern: auto baseline first, then human judgment

When the user asks to do UAT testing (especially with WeChat mini-programs):

1. **Run the automated UAT smoke test FIRST** (the 6-step pattern in `references/backend-api-routes.md`). This gives you a baseline: login → survey → assess × 6 → doubles → full → tier check.
2. **Parse and interpret the results into a human-readable table** — grade per image, strengths/weaknesses per dimension, doubles role, training plan summary.
3. **Compile the mini-program AND generate a phone-scan preview QR** in one shot using the DevTools CLI workflow below. Send the QR to the user via `MEDIA:`.
4. **Present the user with specific questions**: "扫这个码在手机上跑一遍登录→评估，看看AI诊断准不准？尤其图4说你'站着扣杀'挥拍57分但下肢仅14分，这个符合你的感觉吗？"
5. **If automated tests identified any actual bugs** (not just parser errors), fix them BEFORE asking the user to scan. Don't make the user find bugs you could have caught automatically.
6. **On user feedback** — if they confirm the diagnosis matches their real experience, that's PASS. If they disagree, note the delta as product feedback for model improvement.
7. **Collect UX/copy feedback on the spot** — the user may flag awkward wording (e.g. "AI帮我" → "我帮你"). Fix it immediately: patch `auth_api.py`'s `SURVEY_QUESTIONS` list for backend-served text AND `survey.wxml`'s static text → restart backend → recompile → regenerate preview QR. Don't defer copy fixes to the next sprint — they take 2 minutes and closing the loop in the same session builds trust.

**Key insight**: the automated UAT catches regression bugs (server crash, 422, 500, missing endpoints, wrong field names). The human UAT catches model quality issues (wrong grade, irrelevant training plan) AND UX/copy issues (awkward wording, confusing UI text). Both are needed, but run automated first so the user only does the high-value judgment work.

### DevTools CLI compile-preview workflow

After backend is up and any code changes made, compile and generate a phone-scan preview:

```bash
CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
PROJ="/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/miniprogram"
mkdir -p /tmp/wechat_qr

# 1. Clean restart (quit stale session first)
"$CLI" quit 2>/dev/null
pkill -f wechatwebdevtools 2>/dev/null
sleep 3  # wait for full teardown

# 2. Compile (auto = open + load + compile)
"$CLI" auto --project "$PROJ"

# 3. Generate preview QR — always use --qr-format image + --qr-output
#    The terminal QR code (default) often generates before project is ready.
"$CLI" preview --project "$PROJ" --qr-format image --qr-output /tmp/wechat_qr/preview.png

# 4. Send QR to user
# MEDIA:/tmp/wechat_qr/preview.png
```

**IMPORTANT preview pitfalls:**
- `--qr-format terminal` (default) produces ASCII art that scans poorly. Always use `--qr-format image --qr-output /path`
- If you get error 10 "二维码输出路径无效或不存在", the `--project` path is wrong or project.config.json is invalid
- If you get error 19 "请检查 project.config.json", see pitfall #18 above (miniprogramRoot issue)
- The `auto-preview` subcommand is unreliable — use `auto` + `preview` separately instead
- Preview QR codes expire after ~5-10 minutes. Regenerate if the user can't scan in time
- **Regenerate QR for each UAT round** — don't reuse old QR images. The old QR links to a stale build. Always call `preview --qr-format image --qr-output /tmp/wechat_qr/uat_preview_N.png` for each new round.
- **DevTools log may show `start cli server error: [object Object]`** — this is a DevTools internal IPC error during CLI command-handshake and does NOT mean the compile failed or the project is broken. If the `auto` command printed `✔ auto` and `preview` shows a bundle size table, the build is valid. Ignore this error.

See `references/wechat-devtools-cli.md` for all pitfalls (QR path bug, @babel/enhance mode, miniprogramRoot confusion, stale daemon).

## ✅ Product-validated monetization strategy (updated 2026-06-02)

**三层定价逻辑（老卢确认）：**

| 层级 | 功能 | 门控 | 定价 |
|:--|:--|:--|:--:|
| 🆓 免费 | 多角度**照片**评估 (L1-L7+6维雷达) | assess_per_month=3 | ¥0 |
| ⭐ 业余 | 单招**视频对标** (DTW+逐维纠错) | compare_per_month=10 | ¥9.9/月 |
| 👑 Pro | 全三招对标 + **AI动画生成** (换脸换衣) | compare=999+coach_booking | ¥29.9/月 |

**核心逻辑:**
- 照片评估是**入口** — 降低门槛，拍张照就知道等级
- 视频对标是**核心付费价值** — "你和标准动作差在哪" 才是付费理由（门控 feature=compare）
- AI动画是**终极付费钩子** — "达标解锁 → 看到自己做标准动作" 闭环

**标准动作采集流程:**
```
外部视频(微信/小红书/B站) → MediaPipe骨骼提取 → 
按技术分段(5-15s) → 存为benchmark_{skill}.npy (T,33,4) →
用户上传 → DTW对齐 → 6维偏差 → 等级+纠错
```

**DO NOT** pitch MimicMotion-style demo videos as standalone paid feature.
**DO** lead with "先采集标准动作库 → 你上传视频 → AI告诉你怎么练".
**DO** gate defense assess behind `check_gate(uid, "compare")` so free users are redirected to upgrade.

## Roadmap

- ✅ Dual-camera fusion analysis (P0.7-⑦, commit `ff42198`)
- ✅ Interactive training game system (P0.7-⑨, commit `c7eaa12`)
- ✅ Coach + massage therapist marketplace (P0.6, commits `a99cc39`, `0979269`, `b3369bb`)
- ✅ Uber化预约竞价引擎 (P1-④, commit `94bcb1e`) — booking_requests + bids + smart ranking + accept
- ✅ 免费到期弹窗+支付打通 (P1-⑤⑥, commits `47d8769`, `49a6553`, `6af6a2a`) — popup carries plans/recommended/pay_endpoint; /api/user/pay → order system → Mock秒升 / Real prepay
- ✅ 防守技能评估引擎 (P3, commit `0fdcd62`) — 红书视频→benchmark提取→DTW对齐→6维×3招打分→API+门控。免费=照片评估, 业余=视频对标, Pro=AI动画
- ✅ AI标准动画生成 (P3-②, commit `472ea47`) — benchmark骨架→1080p骨骼动画 + 自动相位标注 + 静态挂载 /defense_animations + API端点 | `defense_animator.py`
- ✅ 换脸换衣系统 (P3-③, commit `5dd0f1f`) — 用户照片→MimicMotion换脸→Pro门控 + stub/autodl双模式 + /api/avatar/generate + /defense_animations/avatars 挂载 | `face_swap.py`