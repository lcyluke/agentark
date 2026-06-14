# Hermes Agent Dashboard 竞品参考（2026-06）

## 直接竞品

| 项目 | Stars | 架构 | UI评分 | 特色 |
|---|---|---|---|---|
| EKKOLearnAI/hermes-web-ui | 7,363 | Vue3+NaiveUI+Koa2 BFF | 8.5 | 最完整Web方案，BFF架构 |
| itq5/OpenClaw-Admin | 802 | Vue3+NaiveUI+双网关代理 | 7.5 | OpenClaw+Hermes双网关 |
| xaspx/hermes-control-interface | 753 | Vanilla JS+Express单体 | 7.0 | RBAC+CSP安全设计 |
| awizemann/scarf | 597 | SwiftUI原生，零服务端 | 9.0 | 原生体验最佳，仅Apple |
| lotsoftick/hermes_client | 221 | React+MUI+CLI驱动 | 7.0 | 14套主题，极简 |

## 顶级设计参考

| 项目 | Stars | 设计系统 | 借鉴点 |
|---|---|---|---|
| langflow-ai/langflow | 149K | React19+Tailwind+shadcn/ui | HSL变量+弹性动画+group-hover |
| langgenius/dify | 144K | Next.js+Tailwind+ECharts | 语义化Token+渐变背景+字体层次 |
| open-webui/open-webui | 140K | Svelte+SvelteKit+SVG图表 | 自研图表+可拖拽侧边栏+极简KPI |

## Apex差异化优势

- 14视图全功能覆盖（竞品最多8视图）
- 项目立项审批+模块架构+Agent弹窗（独有）
- SKILL进化引擎+模块市场（独有）
- Pipeline 7阶段流水线（独有）
- 40+ REST API端点

## 待优化

- P1: 组件统一性（对标NaiveUI token系统）
- P1: 操作按钮hover显现（减少视觉噪音）
- P1: 渐变背景替代纯色（更有层次感）
- P2: 响应式PWA
- P2: WebSocket实时推送替代15s轮询
