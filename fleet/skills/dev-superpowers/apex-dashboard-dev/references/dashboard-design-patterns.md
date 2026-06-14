# 顶级 Dashboard 设计精华

> 源码级分析: Dify(144K⭐) + Langflow(149K⭐) + OpenWebUI(140K⭐)

## Top 6 设计模式（按落地优先级）

### 1. 渐变背景替代纯色（Dify）
```css
/* 纯色 → 渐变: 卡片有微妙的品牌色倾向 */
background: linear-gradient(135deg, var(--bg2), color-mix(in srgb, var(--teal) 3%, var(--bg2)));
```

### 2. 操作按钮 hover 显现（Langflow/OpenWebUI）
```css
.card-actions { opacity: 0; transition: opacity .15s; }
.card:hover .card-actions { opacity: 1; }
```

### 3. 侧边栏折叠双态（三者共性）
```css
.side.collapsed { width: 56px; }
.side.collapsed .nav span { max-width: 0; opacity: 0; overflow: hidden; }
```

### 4. 语义化设计 Token 体系（Dify）
- 颜色不直接用 `gray-500`，封装为 `--color-components-{element}-{state}`
- 图表配色建立类型常量（green/orange/blue），每个绑定 lineColor + areaFillGradient

### 5. 0.5px 分割线（Dify）
```css
border: 0.5px solid var(--line);
/* 比 1px 更精致，配合渐变分割线更有层次 */
```

### 6. 四层字体层次系统（Dify）
```
system-xs-semibold-uppercase → 状态标签
system-sm-medium → 导航项
system-md-regular → 正文
title-2xl-semi-bold → 标题
```

## 跨项目通用精华

| 维度 | Dify | Langflow | OpenWebUI |
|------|------|---------|-----------|
| 侧边栏 | 216px/56px双态 | 280px固定 | 220-480px可调 |
| 卡片圆角 | rounded-xl(12px) | rounded-lg(8px) | rounded-2xl(16px) |
| 核心动画 | transition-all 200ms | cubic-bezier弹性 | slide 250ms |
| 配色体系 | 语义色类型映射 | HSL vars(shadcn/ui) | Tailwind原生色板 |
| 状态反馈 | hover显现操作按钮 | group-hover显现 | hover显现 |

## Apex 已对齐项

✅ CSS变量体系(12类token) ✅ 亮暗主题 `[data-theme]` ✅ fade过渡动画 ✅ 侧边栏230px ✅ Tabler Icons全站 ✅ 暗色渐变背景 ✅ 三字体组合

## 待对齐项

| 优先级 | 改进 | 来源 |
|--------|------|------|
| P1 | card操作按钮hover显现 | Langflow |
| P1 | 渐变背景替代纯色 | Dify |
| P2 | 侧边栏折叠按钮 | 三者共性 |
| P2 | 0.5px分割线 | Dify |
| P2 | sidebar宽度可拖拽 | OpenWebUI |
