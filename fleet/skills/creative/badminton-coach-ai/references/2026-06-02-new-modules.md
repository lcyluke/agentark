# 2026-06-02 新增模块

## comparison_engine.py (1,211行)
逐帧比对引擎 — 用户骨架 vs 职业标准骨架对比

| 函数 | 说明 |
|------|------|
| `load_benchmark(action_type)` | 加载对应最高等级的职业标准骨架 |
| `load_user_skeleton(json_path)` | 解析媒体Pipe骨架 JSON |
| `dtw_align(user_seq, pro_seq)` | DTW 时间对齐（解决节奏差异） |
| `compute_angle_deviation(user, pro, aligned)` | 10关节角度偏差分析 |
| `generate_report(deviation_data)` | 中文纠错话术生成 |
| `compare_full(user_json, action_type)` | 完整流程: 加载→对齐→偏差→评分→报告 |
| `render_comparison_video(user, pro, aligned, output)` | 侧排对比骨骼动画 MP4 |

API路径：`/api/compare` / `/api/compare/skeleton` / `/api/compare/from-file` / `/api/compare/benchmarks`

## training_tracker.py (1,355行)
训练追踪引擎 — 记录、统计、技能拆解、关卡解锁

| 函数 | 说明 |
|------|------|
| `record_training(skill_id, level, sets, reps)` | 记录训练+更新连胜天数 |
| `get_training_summary()` | 聚合统计（总数/连续/本月/各类） |
| `check_level_unlock(skill_id, level, total_reps)` | L1→L2需要30次，L2→L3需要100次 |
| `get_daily_goals(skill_id, level)` | 基于进度的每日推荐训练量 |
| `get_skill_breakdown(skill_id)` | 4阶段拆解（准备/引拍/击球/随挥） |

**4阶段拆解数据**：7大类别（high_clear/smash/drop/net/footwork/defense/feints）各包含：
- 准备阶段：架拍/站位/握拍细节 + 关键要点
- 引拍阶段：蓄力/转体/引拍轨迹 + 关键要点 + 常见错误
- 击球阶段：发力/击球点/拍面控制 + 关键要点 + 常见错误
- 随挥阶段：收拍/回中/重心转移 + 关键要点

API路径（前缀`/api/training/v2`）：/skills /stats /record /progress /sessions /level-check /daily-goals /skill-breakdown/{id} /skill-breakdown /action-clips-config

## Route prefix 冲突注意
- `amateur_training.py` 使用 `APIRouter(prefix="/api")`，routes 如 `/training/skills`
- `training_tracker.py` 使用 `APIRouter(prefix="/api/training/v2")`，routes 如 `/v2/skills`
- `auth_api.py` 使用 `APIRouter(prefix="/api")`，routes 如 `/auth/wechat`
- 当两个 router 有重叠前缀时，FastAPI 按 include_router 顺序匹配，第一个匹配的优先
- 新加到 `webapp.py` 的 router 必须放在冲突路由的后面（或使用不同前缀）
