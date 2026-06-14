# 2026-05-30 — Badminton Coach AI 版本管理 + 备份体系搭建

## 背景

`badminton-coach-ai` 项目原先在 `/Users/Mac/workspace/badminton-coach-ai/`（scratch workspace），经历 GC 后部分前端文件丢失。发现主项目实际位于 `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`（持久目录），包含完整的 17 个核心模块（3,207 LOC）和微信小程序全量页面。

## 本次操作记录

### B1: Git 版本管理
- **工作路径**: `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`
- **项目**: 17 个 Python 模块 + 微信小程序页面 + reference_db + HTML 工具页面
- **首次 commit**: `5432ae5` — 72 files, 5,649 insertions
- **.gitignore**: 排除了 `venv/`, `users.db`, `backups/`, `__pycache__`, `*.mp4` 等
- **有无 git remote?** 无。当前仅本地仓库。

### B2: 备份脚本
- **文件**: `daily_backup.sh` — 备份 users.db（SQLite 一致性快照）
- **压缩**: `YYYY-MM-DD_HHMMSS.db.gz` 时间戳文件名
- **保留**: 30 天自动轮转
- **cron**: Hermes cronjob `22ed3110b7a0` — 每天凌晨 3:00 (Asia/Shanghai)，安静执行

### B3: 双路径发现
- **Scratch workspace** (`/Users/Mac/workspace/badminton-coach-ai/`): 包含 `double_analyzer.py`（双人角色诊断）、新版 `skill_grader.py`、新版 `stroke_analyzer.py`、UAT 测试脚本 `_uat_test.py` —— 这些尚未合并到主项目
- **主项目** (`~/Desktop/2026AIAPP/...`): 完整 17 模块，但缺少 `double_analyzer.py`

### 用户决策
- **版本策略**: 完整功能 → 通过测试 → 才发版。不先打标再补功能
- **数据安全**: 任何涉及文件删除、重建、恢复的操作，必须先经用户授权，且确认有备份恢复机制才执行

## 后续待办
- [ ] 将 `double_analyzer.py` + 新版 skill_grader + 新版 stroke_analyzer 从 scratch 合并到主项目（需授权）
- [ ] webapp 已启动（uvicorn port 8000，返回 200 OK）可继续 UAT
  
## 关键路径
```
~/Desktop/2026AIAPP/workspace/badminton-coach-ai/  # 主项目（git init ✅, daily backup ✅）
└── daily_backup.sh                                  # 备份脚本
└── backups/                                         # 备份目录（保留30天）
└── badminton_coach/                                 # 17个Python模块
└── .git/                                            # 本地git仓库（无remote）

/Users/Mac/workspace/badminton-coach-ai/             # scratch workspace（含未合并的UAT文件）
└── double_analyzer.py                               # 双人角色诊断（17KB）
└── skill_grader.py                                  # 新版（25KB vs 主项目 254行）
└── stroke_analyzer.py                               # 新版（17KB vs 主项目 194行）
└── _uat_test.py                                     # UAT测试脚本TC-01~TC-04
```
