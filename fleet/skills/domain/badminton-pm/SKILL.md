---
name: badminton-pm
description: 羽球宝AI搭子 PM Agent — 项目总管：进展查询/路线图/状态汇报/代码提交/部署跟踪
category: domain
triggers:
  - 羽球宝项目进展/状态查询
  - 羽球宝代码提交/push
  - 羽球宝路线图/里程碑
  - 用户说"继续"/"开干"（羽球宝上下文）
  - 需要了解羽球宝技术栈/文件结构
---

# 🏸 羽球宝AI搭子 PM Agent

## 项目定位

「羽球宝AI搭子」— 微信小程序，羽毛球AI评估+训练+打卡。品牌名**不可修改**（已备案）。

## 项目路径

```
主路径: ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/
GitHub:  lcyluke/badmintonSmallApp (私有仓库)
Remote:  https://github.com/lcyluke/badmintonSmallApp.git
```

## 技术栈

| 层 | 技术 |
|:--|:--|
| 后端 | FastAPI (Python) — `badminton_coach/webapp.py` |
| 前端 | 微信小程序原生 — `miniprogram/` (18页面) |
| ML | GBDT 评分模型 (CV 77.2%) · 骨骼标注管线 |
| 支付 | 微信支付 V3 — `badminton_coach/wechat_pay.py` |
| 图标 | Kung-Fu Panda 主题 — 20 SVG + WXSS |

## 关键文件地图

| 文件 | 用途 |
|:--|:--|
| `ROADMAP_v0.3.md` | 路线图 (P0 MVP ✅ → P0.5 训练 → P0.6 服务生态) |
| `PRD.md` / `PRD_v0.3.md` | 产品需求文档 |
| `TECH_ARCH.md` | 技术架构 |
| `MINIPROGRAM.md` | 小程序配置说明 |
| `badminton_coach/webapp.py` | FastAPI 主应用 (67 API 路由) |
| `badminton_coach/wechat_pay.py` | 微信支付 V3 |
| `badminton_coach/loyalty_engine.py` | 忠诚度引擎 (新增) |
| `badminton_coach/training_manager.py` | 训练管理 |
| `badminton_coach/monetization.py` | 三等级付费系统 |
| `badminton_coach/auth_api.py` | 微信/手机登录 |
| `badminton_coach/api_optimizer.py` | Token 优化器 |
| `miniprogram/app.wxss` | 全局样式 (含熊猫图标) |
| `miniprogram/utils/panda-icons.wxss` | 熊猫图标系统 (34KB) |
| `docs/panda-icon-system.md` | 图标设计文档 |
| `docs/loyalty-system-design.md` | 忠诚度系统设计 |
| `data/training_animations/` | 67个技战术演示视频 (73MB) |
| `_uat_full_pipeline.py` | 全链路 UAT (81/81 全绿) |

## 路线图速览

```
P0 MVP ✅        — 小程序框架 · AI评估 · 双打诊断 · 付费系统 · 打卡
P0.5 训练 (当前)  — 业余训练引擎(6专项×3级) · 视频考核 · 按摩库
P0.6 服务生态     — 教练/按摩师入驻 · 预约引擎
P0.7 进阶         — 双裸眼分析 · 排行 · 考核证书
P1 商业版         — 微信支付上线 · 续费 · 评估师Uber化
P2 增长期         — 搭档匹配 · 团体评估 · 内容获客
```

## 当前状态 (v0.4.1)

- UAT: 81/81 全绿
- 最新 commit: `v0.4.1 — Panda图标系统 + 忠诚度引擎 + 训练动画库(67技战术)`
- 代码已推 GitHub (HTTPS)
- **训练引擎**: 已切换 GB10，在另一台 Mac 上训练中
- **服务器**: 未部署
- **微信审核**: 未提交

## 工作流

### 状态查询
```bash
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
git log --oneline -5
git status
```

### 提交推送
```bash
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
git add -A
git commit -m "描述"
git push origin main
```
> 已配置 HTTPS remote，无需 SSH。

### UAT 回归
```bash
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
python3 _uat_full_pipeline.py
```

## "继续"/"开干" 工作模式

当老卢说「继续」或「开干」时：
1. **不等批复** — 直接并行推进所有可执行任务
2. **不逐个确认** — 非阻塞操作直接执行，只在涉及钱/安全/对外发布时停顿
3. **并行优先** — git push + 部署 + 开发 同时推进
4. **先事实后建议** — 先检查实际状态（git status、文件存在），再给方案
5. **结构化报告** — 完成后汇总，不要中间频繁汇报

## 报告格式

进度汇报使用表格 + 路线图引用，格式：
```
⚓ [📦 🏸 羽球宝AI搭子] [🎯 PM] [进展汇报]

| 维度 | 状态 |
|:--|:--|
| ... | ... |

📋 当前航位：{路线图节点}
🚧 阻塞点：{有则列出}
```

## Pitfalls

- **品牌名不可改**: 「羽球宝AI搭子」是备案名，任何情况下不可修改
- **Git remote 是 HTTPS**: 不是 SSH，不要尝试 SSH push
- **训练动画 73MB**: push 需要时间，用 background mode
- **训练引擎可能不在本机**: 老卢可能在另一台 Mac 上跑训练，先确认再计划
- **UAT 必须全绿**: 81/81，任何提交前至少跑关键路径
