# 羽球宝后端模块清单

> 最后更新: 2026-06-09 | P1 阶段

## 核心引擎

| 模块 | 行数 | Phase | 职责 |
|:--|:--|:--|:--|
| `webapp.py` | 1,888 | P0 | FastAPI 主入口，路由注册中枢 |
| `auth_api.py` | ~600 | P0 | 用户认证 + tier管理 + token |
| `image_assessor.py` | ~500 | P0 | AI拍照评估 (6维 L1-L7) |
| `double_analyzer.py` | ~400 | P0 | 双打角色诊断 |
| `comparison_engine.py` | ~400 | P0 | 动作比对 (用户vs职业) |
| `pose_estimator.py` | ~300 | P0 | MediaPipe 骨骼提取 |

## P0.5 训练系统

| 模块 | 行数 | Phase | 职责 |
|:--|:--|:--|:--|
| `amateur_training.py` | 5,051 | P0.5 | 业余训练引擎+教练+按摩师+预约 |
| `training_tracker.py` | ~200 | P0.5 | 训练追踪+技能拆解+关卡解锁 |
| `matching.py` | ~300 | P0.5 | 球友匹配算法 |

## P0.6 生态

| 模块 | 行数 | Phase | 职责 |
|:--|:--|:--|:--|
| `checkin.py` | 351 | P0.6 | 场馆打卡 (7 API) |
| `venue_db.py` | 155 | P0.6 | 球馆数据库 (326家深圳球馆) |

## P0.7 进阶

| 模块 | 行数 | Phase | 职责 |
|:--|:--|:--|:--|
| `dual_video_analyzer.py` | ~500 | P0.7 | 双裸眼视频分析 |
| `ranking_engine.py` | ~200 | P0.7 | 多维排行榜 + 段位 |
| `billing.py` | 156 | P0.7 | 专业按摩计费 (三档+夜间+上门+退款) |

## P1 商业

| 模块 | 行数 | Phase | 职责 |
|:--|:--|:--|:--|
| `assessor_system.py` | 600 | P1 | 评估师Uber (入驻/匹配/接单/评分/分成) |
| `monetization.py` | 392 | P1 | 付费墙 + 配额 + 支付处理 |
| `wechat_pay.py` | ~200 | P1 | 微信支付封装 (mock模式) |

## P3 AI研发

| 模块 | 行数 | Phase | 职责 |
|:--|:--|:--|:--|
| `defense_assessor.py` | ~200 | P3 | 防守技能评估引擎 |
| `defense_animator.py` | ~100 | P3 | 防守动画生成 |

## API 总览

- **总路由数**: 110+ (webapp 28 + amateur_training 64 + auth ~10 + 各模块)
- **数据库**: SQLite (`users.db`), 自动备份到 `backups/`
- **服务端口**: `localhost:8000` (uvicorn --reload)
