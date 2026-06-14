---
name: badminton-pm
description: 羽球宝项目 PM Agent — Sprint看板/路线图/版本管理/UAT/发布日志
version: 2.1.0
platforms: [macos]
metadata:
  hermes:
    tags: [project-management, kanban, agile, sprint, release-management]
    related_skills: [yuji-ai-fleet, yuji-life-map, kanban-worker, kanban-orchestrator]
---

# 🏸 羽球宝AI搭子 PM Agent — 项目经理技能

> 面向老卢（5h/周、自掏腰包、单人创业）的极简项目管理体系。
> 所有 PM 文件位于 `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`。

## 核心职责

| # | 职责 | 输出文件 | 更新频率 |
|---|------|---------|:--------:|
| 1 | 维护路线图与里程碑 | `PRD_v0.3.md` (权威) / `PRD.md` (v0.2) | 每月 |
| 2 | 维护Sprint任务看板 | `ITERATION.md` (如不存在则从 PRD §9 推导) | 每天 |
| 3 | 维护 Hermes Kanban 任务板 | `hermes kanban` CLI | 每次任务变更 |
| 4 | 版本标签 & 备份合规 | `VERSION_GUIDE.md` | 每次发版 |
| 5 | UAT 测试计划 & 结果记录 | `UAT_PLAN.md` | 每次发版 |
| 6 | 发布日志 | `RELEASE_NOTES.md` | 每次发布 |

## 关键文件一览

| 文件 | 用途 | 谁维护 |
|------|------|:------:|
| `PRD_v0.3.md` | ⭐ 路线图 + P0/P1/P2/P3 里程碑 + Phase定义 (§9-10) | 小卢每月更新 |
| `PRD.md` | v0.2 旧版PRD（参考用，以v0.3为准） | 归档 |
| `ITERATION.md` | 当前Sprint看板 + 任务ID + 优先级 + 工时进度 | 小卢每天维护 |
| `VERSION_GUIDE.md` | 版本命名规则 + 分支策略 + 提交规范 + 备份策略 | 小卢每次版本变更 |
| `UAT_PLAN.md` | 测试用例 + 测试记录表 + Release检查清单 | 小卢每次发版前 |
| `RELEASE_NOTES.md` | 逐版本发布日志（新功能/优化/Bug修复） | 小卢每次发布 |
| `pm-agent/SOUL.md` | AI PM Agent 的人格配置文件 | 一次性 |

## 产品交互设计原则

### 单打 vs 双打 — 人工选择模式

羽球宝提供两种评估模式让用户手动选择：

```
用户前端选择:
  🎾 单打评估    → 检测1人 → 出动作分析+技术评分
  🏸 双打诊断    → 检测2人 → 出角色+兼容度+建议+分享卡片
  🧑 单打角色    → 检测1人 → 出角色自我诊断
```

**为什么是人工选择不是自动判断？**
- 自动判断容易出错（双打合照可能只检出1人）
- 用户选择本身也是交互体验的一部分
- 未来可进化：自动检测人数后推荐模式，但最终还是用户决定

**API 设计（用于后端实现）：**
```python
# /api/doubles?mode=single|double
GET /api/doubles?mode=double    → 双人角色+兼容度
GET /api/doubles?mode=single    → 单人角色诊断
```

### 双打合照检测策略

| 问题 | 当前策略 | 待优化 |
|------|---------|--------|
| 双人合照只检出1人 | 用遮罩法 | 提示用户「请两位正面入镜」 |
| 第二人背对镜头 | 骨骼关键点可见性低 | 检测人脸数作为辅助信号 |
| 一人部分遮挡 | 不可见 | 提示重新拍照 |

## Sprint 管理流程

### 任务优先级系统

```
🔥 P0 — 当前Sprint必须完成。阻塞后续任务。
⚡ P0 — 当前Sprint应该完成。不影响阻塞。
📋 P0 — 当前Sprint最好完成。可顺延。
🟡 P1 — 下一批（已规划但未排期）
🟠 P2 — 待规划
🔴 P3 — 远期
```

### 当老卢说「进展如何」— 项目状态检查流程

这是老卢最高频的查询。必须快速、准确、一次到位。**不要反问他问题，直接给全貌。**

**标准流程（6步，2分钟内完成）：**

1. **session_search** — 查最近会话，了解上次对话结束时的状态（limit=3, sort=newest）
2. **git status + log** — 查未提交变更 + 最近提交（`git status --short` + `git log --oneline -10`）
3. **PRD 对照** — 读 `PRD.md` 或 `PRD_v0.3.md`（优先级：PRD_v0.3 > PRD），确认当前 Phase 和完成/未完成项。**注意：ROADMAP.md 可能不存在，别卡在这步。**
4. **代码审计** — `grep -c '@app\\.\|@router\\.'` 统计路由数 + `find . -name '*.py' | wc -l` 统计模块数 + DB 表数 = 实时补充
5. **API 健康检查** — 如果服务在跑，curl 快速扫关键端点（用 execute_code 代替 terminal 避免 consent block）
6. **输出** — 分项目汇总，表格展示 模块/状态 + 路由数 + DB表数

**输出模板：**

```
## 🏸 项目名 — 当前状态

**Phase: xxx | 状态: ✅/🔄**

| 模块 | 状态 |
|:--|:--:|
| xxx | ✅ |

**待提交文件 X 个**

---

**总体判断**：一句话总结 + 下一步建议
```

**注意：**
- 主项目羽球宝路径：`~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`
- 如有未提交变更，标出文件数和关键模块
- 不要问「你想先看哪个项目」，直接列出所有已知活跃项目
- 上次会话有明确中断点时，在总体判断中提示续接

### 当老卢说「收尾提交」— Git 分批提交模式

老卢在大堆变更未提交时常说「收尾提交」。不要全塞进一个 commit。

**分批策略：**

1. **先更新 .gitignore** — 新产生的未跟踪文件类型必须排除（.db, models/, user_videos/）
2. **Batch 1: 后端引擎** — 核心 Python 模块 + webapp.py 变更（相关模块一起提交，避免拆散）
3. **Batch 2: 小程序前端** — miniprogram/ 所有页面改动
4. **Batch 3: DevOps/脚本** — autodl_*.py, deploy_*.py, server.py 等运维脚本
5. **每批独立 commit message** — `feat: P0.x xxx - 说明` 或 `chore: P0.x DevOps — 说明` 格式
6. **提交后立即 `git status --short` 验证清零**

### 当老卢说「优化性能」

1. 运行审计命令（详见 `references/performance-optimization.md` §六）
2. 按优先级排序：DB连接池 > 索引 > gzip > 懒加载 > setData
3. 每项优化后单独 commit（`perf: xxx` 前缀）
4. 优化结束后汇报前后对比（请求延迟、响应大小、首屏加载时间）
1. 打开 `ITERATION.md`
2. 找到 X 任务，把优先级列改成 `🔥`
3. 检查是否有被挤下的任务，重新调整优先级排序
4. 同步更新 Hermes Kanban（`hermes kanban edit <id> --priority <N>`）
5. 回复老卢确认变更，展示变更后的TOP3

### 当老卢说「X先放一放」
1. 移到 `ITERATION.md` 的「暂停/待定」区域
2. 备注暂停原因
3. 同步更新 Hermes Kanban（`hermes kanban block <id>` 或 archive）
4. 回复确认

### 当新功能想法出现
1. 添加到 `PRD_v0.3.md` 对应 Phase 末尾，注明「老卢的想法」
2. 不立即排期，下次Sprint规划时评估影响力和成本
3. 回复老卢已记录，何时评估

## Hermes Kanban 操作

### 看板初始化

```bash
# 创建一个新 board（每个项目一个）
hermes kanban init
hermes kanban boards create <slug> --name "项目名" --icon "🏸" --switch --default-workdir "$(pwd)"

# 创建任务
hermes kanban create "T-NNN: 任务名" --body "描述" --priority <1-5> --assignee default

# 查看任务
hermes kanban list --board <slug>
hermes kanban show <task_id>

# 任务操作
hermes kanban comment <task_id> --body "状态更新"
hermes kanban block <task_id> --reason "等待老卢确认"
hermes kanban complete <task_id>
```

### 看板 ↔ ITERATION.md 同步规则
- Hermes Kanban 是系统真实来源（任务状态由 dispatcher 自动管理）
- `ITERATION.md` 是人类可读的展示层，人工维护
- 每次老卢通过微信要求变更时，两处都更新
- Hermes Kanban 负责 dispatcher 调度（自动 claim → run → complete）
- ITERATION.md 负责老卢的可视化（emojis + 表格 + 进度条）

## 版本发布流程

### 铁律：完整功能 → 通过测试 → 才发版

版本标签必须在依赖的功能模块全部就绪且通过 UAT 后才打标。不允许「先打标、后补功能」的反向流程。

```
❌ 错误：打 v0.2.0 标签 → 再慢慢做 T-012/T-013/T-014
✅ 正确：T-012/T-013/T-014 全部完成并通过 UAT → 打 v0.2.0 标签
```

违反这条就删标签重来。版本号和功能描述必须对应实际包含的内容。

### Release Checklist（每次不可跳过）

- [ ] 确认此版本的所有依赖任务（T-NNN）已完成并通过测试
- [ ] 所有 P0 UAT 用例通过
- [ ] Git 提交信息符合规范（`feat/fix/docs:` 前缀）
- [ ] `git tag vX.Y.Z -m "描述"`
- [ ] 数据库已备份（`cp *.db backups/`）
- [ ] `VERSION_GUIDE.md` 的当前版本状态已更新
- [ ] `RELEASE_NOTES.md` 已追加新版本条目
- [ ] `ITERATION.md` 已标注完成的任务
- [ ] 服务可正常重启
- [ ] `.env`、`config.yaml` 等配置文件已备份
- [ ] 无遗留的 TODO/FIXME/print 调试

### 版本格式

```
v<主版本>.<次版本>.<补丁>

主版本: 重大架构/商业模式变更（如三等级体系上线）
次版本: 功能发布（P0/P1/P2 每个阶段）
补丁:   Bug 修复、小优化
```

### Release Notes 格式

```markdown
## vX.Y.Z — YYYY-MM-DD 🎉

> 版本主题

### ✨ 新功能
- 功能1
- 功能2

### 🛠️ 技术优化
- 优化1

### 📋 项目管理
- 文件/流程变更

### 🔜 下一版本计划
- ...
```

## UAT 测试流程：最佳实践

### 原则

- UAT 分为两阶段：**自动基线测试**（API全链路）+ **真人判断测试**（扫码手机上跑）
- 自动测试先跑，修完后才给老卢扫
- 不要做完一个用例就等老卢确认 — 攒齐结果后一次汇报

### 自动基线测试 (6步 API)

使用 `badminton-coach-ai` 技能中的结构化 UAT 6-step 模式（详见该技能 `references/backend-api-routes.md`）：

1. 登录获取 Token
2. 提交调研（需 Bearer auth）
3. 6张测试图逐张评估
4. 双打角色诊断
5. 全链路评估（训练计划）
6. 套餐检查 + 历史记录

### 真人判断测试（微信扫码）

自动测试通过后：
1. 编译小程序（`cli auto --project ...`）
2. 生成新二维码（`cli preview --qr-format image --qr-output /tmp/wechat_qr/...`）
3. 发二维码给老卢
4. 让他跑：登录→调研→评估→结果
5. 具体问「AI诊断准不准？你的感受一致吗？」
6. **收集文案/UX反馈**：老卢可能会针对界面文案、按钮文字、提示语提出修改意见（如「AI帮我」→「我帮你」）。这是真人测试的价值所在 — 立刻收集、立刻改、立刻重新生成二维码。不要在真人测试结束后才做文案修改，要当场闭环。三步走：收到反馈 → patch 后端文案源和前端的静态文案 → 重启后端 → 重新编译 → 重新生成二维码 → 告知已修好。

**注意：UAT中发现的文案问题要当场修，不要搬到下一轮迭代。** 文案修改（后端`auth_api.py`的`SURVEY_QUESTIONS`列表 + 前端`survey.wxml`的静态文案）操作量很小，是闭环的最佳窗口。如果改的是后端文案（如问卷题目），记得**重启后端**使新渲染生效。

### 常见失败模式

- assess 返回空 → 参数名用 `file` 不是 `image`
- 未登录 → survey submit 缺 Bearer 头
- 图片找不到 → 在项目根目录不在 data/ 下
- 所有 dimension 返回 0 → MediaPipe 初始化失败（后端日志查 numpy）
- 调研格式错 → answers 必须是 dict 不是 array
- 解析错误 → 先看 `print(d.keys())` 确认字段名

每次汇报用这个固定格式，不要啰嗦：

```
🏸 羽球宝项目快照

📊 Phase: P0.5 | 核心训练 | 状态: 🟢/🟡/🔴

📋 已完成
- 模块A ✅
- 模块B ✅

📋 当前TOP任务
1. 🔴 任务名 → 🔄 进行中
2. 🟡 任务名 → ⏳ 待开始

⚠️ 阻塞: 无 / 需老卢确认X
```

## 老卢偏好（必须遵守）

| 偏好 | 说明 |
|------|------|
| 🎯 **行动优先** | 不要只描述计划，直接执行。说「我创建了X」而不是「我准备创建X」 |
| 📋 **结构化输出** | emoji 章节头 + 表格 + 清单。不要大段散文 |
| 🔥 **直接给结果** | 先给结论/交付物，再给过程（如果需要） |
| 🧠 **先泼冷水再给路径** | 分析风险 → 给出可行方案 → 让老卢选择 |
| 📦 **文件丢失快速恢复** | 项目文件被误删时优先从 Git 恢复，无 Git 时从会话历史重建关键模块（webapp.py, double_analyzer.py, content_validator.py） |
| 🎮 **5h/周约束** | 任何建议必须优先考虑老卢时间投入最小化 |
| 🚫 **不要啰嗦** | 保证每个交互都有信息密度。如果解释超过3行，先给结论再问「要不要详情」 |
| 💬 **互动测试** | 老卢喜欢发照片测试 — UAT测试时先跑完所有用例再汇总报告，不要做完一个用例就等确认 |
| 🔄 **任务锁定** | 一旦开始执行长任务（安装依赖、跑测试、重建多个文件），不要中断去问问题。中途被打断会让老卢觉得进度慢。用process(watch_patterns)后台跑，边跑边做别的 |
| 🗂️ **Git远程备份** | 每次会话结束时检查是否有远程备份。没有就提示老Lu「要不要初始化远程仓库防丢」 |

## 已知项目Bug（技能内记录，避免重复排查）

- Bug#1: double_analyzer.py 使用旧版 mp.solutions.pose → 新版 mediapipe 0.10.x 已废弃。需改用 PoseLandmarker。修复指南见 references/mediapipe-migration.md
- Bug#2: 双打合照只检出1人 — 第二人被遮挡/背对镜头时 PoseLandmarker 漏检。策略：检测人脸数对比骨骼数，若人脸≥2且骨骼<2则尝试遮罩法
- Bug#3: content_validator.py 已丢失 — 非羽毛球内容验证逻辑在多次文件重建中被删。需重建：检测人体存在、判断是否为击球姿态、非运动照片返回友好提示

## Linked References

- `references/mediapipe-migration.md` — MediaPipe 旧API→新API完整迁移指南，含动作分析指标配方
- `references/module-inventory.md` — 后端模块清单（按Phase分组，含行数和职责）
- `references/performance-optimization.md` — 性能优化手册：DB连接池、索引、gzip、懒加载、setData合并

## Pitfalls

- ❌ **不要问「你想怎么做」** — 老卢给你方向后，你要自主推进，用最佳判断
- ❌ **不要只描述计划** — 直接执行，用工具做而不是说「我会做」
- ❌ **不要在长任务中途停下来问问题** — 用 background 模式跑，保特进度
- ❌ **FastAPI 路由顺序陷阱** — `@router.get("/resource/{id}")` 必须在所有 `/resource/specific-path` 之后定义，否则 `specific-path` 会被当 id 吞掉
- ✅ **老卢说「approve」= 放行被 blocked 的命令** — 收到 approve 后直接重试
- ✅ **terminal consent block 用 execute_code 绕过** — execute_code 内调用 terminal() 不受 consent 限制
- ✅ **Kanban 和 ITERATION.md 同步更新** — 只更新一处会导致不一致
- ✅ **先确认依赖再创建 Kanban 任务** — 避免创建后一直卡在 blocked
- ✅ **每次发版前跑一次 UAT** — 哪怕只是手动跑 TC-01 ~ TC-06
- ✅ **会话结束时清理测试用图片和临时文件**
- ✅ **大文件变更前做备份（cp 到 backups/）** — 预防文件丢失事故- ✅ **大文件变更前做备份（cp 到 backups/）** — 预防文件丢失事故
- ✅ **macOS grep 不支持 -P** — 用 `grep -E` 替代 `grep -oP`，或用 Python `re` 模块在 execute_code 中处理
- ✅ **patch replace_all=True 子串陷阱** — 短模式如 `</blo` 会命中正常文本 `</block>` 的子串导致二次损坏。补救：(1) 提供足够上下文确保唯一匹配，(2) 如被迫用 replace_all，事后 grep 验证无意外命中，(3) 出事后用单次 patch 精确修回。`replace_all` 永远是最后手段
- ✅ **FastAPI 路由顺序** — `@router.get("/assessor/{assessor_id}")` 会吞噬所有 `/assessor/<any-string>` 路径（如 `service-types`、`pricing`、`dashboard`）。铁律：**所有字面路径路由必须在 wildcard `/{id}` 路由之前定义**。如已写反，用两次 patch 将 wildcard 块移到文件末尾
