# ⚡ Apex Sprint 001 — 舰队首航
>
> **Sprint**: 001 | **周期**: 2026-06-19 → 2026-06-25 (7天)
> **PM**: PM_Lu (project-manager)
> **舰队**: 老卢舰队 · Mac-A Origin
> **版本目标**: v0.2.0 → v0.3.0-alpha

---

## 🎯 Sprint Goal

完成 Apex 多Agent操作系统的 **核心闭环**：Agent创建 → 任务执行 → 自愈 → 进化 → 看板可视。让 `apex run` 从 Demo 级升级为可生产使用的 Alpha 版本。

## 📊 KPI

| KPI | 现状 | 目标 |
|-----|------|------|
| 单元测试覆盖率 | ~15% | ≥60% |
| Agent自愈成功率 | 未实现 | ≥80% |
| CLI命令可用数 | 18个声明 | 18个全可用 |
| Web Dashboard | 骨架 | 功能完整 |
| 知识图谱共享 | TODO | 原型可用 |
| Token预算银行 | 未实现 | 原型可用 |

---

## 📋 任务清单 (5 Agent × 3 Tasks = 15 Tasks)

### 🏛️ architect (架构师)
| ID | 任务 | 优先级 | 估时 | 状态 |
|----|------|--------|------|------|
| APX-001 | 审计现有代码架构，输出架构评审报告 | P0 | 2h | todo |
| APX-002 | 设计 Skill Evolution 引擎架构（替代 _auto_learn TODO） | P0 | 4h | todo |
| APX-003 | 设计跨项目知识图谱共享协议 | P1 | 3h | todo |

### ⚙️ backend-dev (后端开发)
| ID | 任务 | 优先级 | 估时 | 状态 |
|----|------|--------|------|------|
| APX-004 | 实现 Token Budget Bank 核心路由逻辑 | P0 | 4h | todo |
| APX-005 | 修复 CLI 18条命令的连通性（apex run/debate/swarm等） | P0 | 3h | todo |
| APX-006 | 实现 Self-Healing 三振出局机制（重试→换模型→简化→通知） | P1 | 4h | todo |

### 💻 frontend-dev (前端开发)
| ID | 任务 | 优先级 | 估时 | 状态 |
|----|------|--------|------|------|
| APX-007 | 完善 Web Dashboard — Agent实时状态面板 | P0 | 4h | todo |
| APX-008 | 实现项目舰队可视化（Org Chart + 任务流） | P1 | 3h | todo |
| APX-009 | 搭建前端组件测试框架（Playwright） | P1 | 2h | todo |

### 🔧 devops (运维)
| ID | 任务 | 优先级 | 估时 | 状态 |
|----|------|--------|------|------|
| APX-010 | 搭建 CI/CD Pipeline（lint → test → build） | P0 | 3h | todo |
| APX-011 | 配置多环境部署（dev/staging/prod 配置文件） | P1 | 2h | todo |
| APX-012 | 集成 PyPI 自动发布流水线 | P2 | 2h | todo |

### 🧪 qa-engineer (测试)
| ID | 任务 | 优先级 | 估时 | 状态 |
|----|------|--------|------|------|
| APX-013 | 编写核心模块单元测试（runtime/profile/providers） | P0 | 4h | todo |
| APX-014 | 设计集成测试场景矩阵（6种编排模式） | P1 | 3h | todo |
| APX-015 | 建立质量门控标准 + 覆盖率CI卡点 | P1 | 2h | todo |

---

## 🗺️ 依赖关系

```
APX-001 (架构审计) ──→ APX-002 (进化引擎设计)
                   ──→ APX-005 (CLI修复参考)
                   
APX-005 (CLI修复) ──→ APX-013 (单元测试可依赖CLI接口)

APX-007 (Dashboard) ──→ APX-008 (舰队可视化依赖Dashboard框架)

APX-010 (CI/CD) ──→ APX-015 (质量门控需CI集成)
```

---

## ⚠️ 风险登记

| # | 风险 | 概率 | 影响 | 缓解方案 |
|---|------|------|------|----------|
| R1 | DeepSeek API限流影响开发 | 中 | 高 | 配置 fallback model |
| R2 | 架构审计发现重大重构需求 | 中 | 高 | 评估范围，Sprint 2才做大重构 |
| R3 | 测试环境搭建阻塞 | 低 | 中 | DevOps优先搭建CI |

---

## 📅 Daily Standup

- **时间**: 每日 09:00 GMT+8
- **形式**: PM_Lu 巡检各Agent → 更新Kanban → 报告师父
- **升级**: 阻塞>2h → 立即通知师父

---

## ✅ Definition of Done

- [ ] 代码通过 lint + 测试
- [ ] PR 经架构师或PM审查
- [ ] 相关文档更新
- [ ] Kanban卡移至 done 列

---

> ⚓ 航向: v0.3.0-alpha | 司令: PM_Lu | 舰队: 5 Agent 全员就绪
