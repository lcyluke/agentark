# 羽球宝AI搭子 · 微信小程序 UX 模式

> 设计日期: 2026-06-01 | 版本: v0.4

## 5-Tab 结构

| Tab | 页面 | 核心功能 | 用户问题 |
|:----|:-----|:---------|:---------|
| 首页 | `pages/home/home` | 个人仪表盘+快捷入口 | "从哪开始？" |
| 技能测评 | `pages/assess/assess` | 三级套餐+上传+等待动画 | "我什么水平？" |
| 模拟训练 | `pages/training/training` | 进度环+51项技能+AI周计划 | "怎么练能涨？" |
| 按摩预防 | `pages/injury/injury` | 风险雷达+5部位+热身恢复 | "怎么不受伤？" |
| 我的 | `pages/profile/profile` | 套餐/证书/支付 | "管理账户" |

## 首页设计 (个人仪表盘)

### 布局
```
[头像(可点击上传靓照)]  嗨，老卢 👋  免费版
─────────────────────────────
  (L4)      (35%)     (75)
 技能等级   训练完成    健康度     ← 三指标环
─────────────────────────────
 🏸 技能测评   🎯 模拟训练
 🩹 按摩预防   🛡️ 护具推荐        ← 四宫格
─────────────────────────────
 🤝匹配球友  🗺️球馆地图
 ✅打卡目标  ⬆️升级套餐          ← 快捷操作
```

### 数据来源
- **技能等级**: 从 `lastResult` localStorage 读取最近评估的 grade_label
- **训练完成**: 从 trainingCats localStorage 统计 passed/total
- **健康度**: 从 lastResult injury_prevention 反向计算（100 - high_risk_count × 25）

## 技能测评页 (assess)

### 三级套餐卡
- 免费快速测评（默认选中）
- 业余版 ¥29/月（点选跳转升级页）
- 专业版 ¥399/次（点选跳转升级页）

### 上传流程
1. `chooseVideo()` 调 `wx.chooseMedia` → 上传到 `/api/full`
2. 加载态：5步动画（上传→检测→骨骼→标注→评估），每0.8s推进
3. 完成后 400ms → `redirectTo result`

### 拍摄指南弹窗
- 触发: 点「💬 查看详细」
- 内容: 视频要求、图片要求、动作完整性、拍摄角度（🥇侧后45°/🥈正侧90°/🥉正后方）、常见问题（过短/逆光/多人/局部）、小技巧
- 实现: `showGuideModal` data字段控制弹窗显隐，底部上滑式 modal

## 模拟训练页 (training)

### 关键模式
- **内置离线数据**: BUILTIN_CATEGORIES 包含 7 类 ≈15 个 sub_skill，API 不可用时兜底
- **进度环**: conic-gradient CSS 实现（需 --pct CSS 变量）
- **技能分类折叠**: `open` 字段控制展开/收起，箭头旋转动画
- **详情弹窗**: 底部上滑 modal，含视频+L1-L3等级切换+关键要点+常见错误+记录按钮
- **记录训练**: API + 本地双写，按钮即时响应

### API 端点
- `GET /api/training/categories` — 技能分类列表
- `GET /api/training/progress` — 用户进度
- `GET /api/training/plan` — AI 周计划
- `POST /api/training/record` — 记录训练

## 按摩预防页 (injury/massage)

### 风险雷达
- 从 lastResult.injury_prevention 提取 personalized_plans
- 按部位显示风险条（绿/黄/红）+ 百分比
- 无评估数据时显示「去测评」引导

### 5 部位内容
每个部位 (肩/膝/腕/背/踝) 包含 4 步：
1. 🔥 赛前热身（5分钟）
2. 💪 预防强化训练
3. 🧘 赛后拉伸（30秒×2）
4. 👐 自我按摩（2分钟/部位）

### 通用指南
- 打球前 10 分钟流程（慢跑→动态拉伸→专项→关节→轻打）
- 打球后 15 分钟流程（慢走→静态拉伸→泡沫轴→冰敷→补水）
- 7 种常见伤病自查清单（网球肘、肩袖、跳跃膝等）

## 新增子页面

### 匹配球友 (matching)
- 显示我的等级+位置偏好+常去区域
- 模拟匹配列表（Mock数据，4条）
- 发布约球按钮（需先完成测评）
- 打招呼功能（开发中占位）

### 球馆地图 (venue)
- 8 个深圳预设球馆数据
- 搜索 + 区域筛选（福田/南山/罗湖/宝安/龙华/龙岗）
- 每条含名称/片区/地址/特色标签
- 导航按钮调 `wx.openLocation`
- 预约按钮跳 `booking` 页

### 打卡目标 (daily)
- 连续打卡天数环形展示
- 今日训练清单（4项可勾选：热身/基础动作/步法/拉伸）
- 打卡按钮 → 本地持久化（streak/week/month 计数）
- 日历视图（当月打卡日期高亮绿色，今天橙色边框）
- 训练统计（技能数/累计小时/级别进度）

## app.json 配置
```json
{
  "pages": [..., "pages/matching/matching", "pages/venue/venue", "pages/daily/daily"],
  "tabBar": {
    "list": [
      {"pagePath": "pages/home/home", "text": "首页"},
      {"pagePath": "pages/assess/assess", "text": "技能测评"},
      {"pagePath": "pages/training/training", "text": "模拟训练"},
      {"pagePath": "pages/injury/injury", "text": "按摩预防"},
      {"pagePath": "pages/profile/profile", "text": "我的"}
    ]
  }
}
```

## 关键坑

### WXML 禁止 JS 表达式
```
❌ {{new Date(c.issued_at * 1000).toLocaleDateString()}}
✅ JS 中预计算 c.issued_date，WXML 中 {{c.issued_date}}
```

### 首页导航类型
- Tab 页（技能测评/模拟训练/按摩预防）→ `wx.switchTab`
- 子页（匹配/球馆/打卡/护具/指南）→ `wx.navigateTo`
- 非 Tab 页误用 switchTab 会静默失败
