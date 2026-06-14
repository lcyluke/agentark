---
name: prd-writing
description: "Write Product Requirements Documents (PRD) for software products. Covers user personas, pain points, use cases, monetization strategy, user flows, and go-to-market planning. For MVP-stage B2C products with constrained resources (solo dev, bootstrapped, 5h/week)."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [prd, product-requirements, product-management, mvp, strategy, go-to-market]
    related_skills: [writing-plans, spike, plan]
---

# PRD Writing

Use this skill when the user asks you to write a **Product Requirements Document** — a structured document defining what to build, for whom, and why. This is NOT a technical implementation plan (use `writing-plans` for that) or a UI design spec — it's the product-facing blueprint.

Also load for: sports-app features with progressive unlock paths (train → exam → unlock pro), multi-tier monetization strategy (free/amateur/pro), and service marketplace design (assessors, coaches, therapists).

## When to load

- User says "write a需求说明书 / PRD / 产品需求文档"
- User asks to define user personas, target audience, pain points
- User asks about pricing tiers, monetization, business model
- User asks about go-to-market or user acquisition strategy
- User needs to "画出用户流程图" or "定义产品功能"

## Document structure

A complete PRD has these chapters. Present them as emoji-sectioned markdown with tables for comparison data:

### 1. 产品概述 (Product Overview)

| Section | Content |
|---------|---------|
| One-liner | What the product does in one sentence |
| 三阶段路线 | P0 MVP → P1 Commercial → P2 Ecosystem |
| 核心价值主张 | Table: 对用户 vs 对平台 |

### 2. 用户群体分析 (User Personas)

Create 4-6 personas with a table:

| 画像 | 特征 | 痛点 | 付费意愿 |
|------|------|------|:--------:|
| 🎯 Name | demographics, behavior | what hurts | low/med/high |

Then a **user pyramid** (hierarchical stratification):

```
      🔷 Power users (5%)     ¥399/tier
    🔷 🔷 Active (15%)       ¥29/month
  🔷 🔷 🔷 Free (50%)       3-month trial
🔷 🔷 🔷 🔷 Visitors (30%)  word-of-mouth
```

Include TAM/SAM/SOM estimates if the user has market data.

### 3. 用户痛点与使用场景 (Pain Points & Scenarios)

List 5 core pain points as a table:

| # | Pain | User quote | Severity |
|:-:|------|-----------|:--------:|
| 1 | ... | "..." | 🔴/🟡 |

Write **4-5 concrete use scenarios** as narrative stories. Each scenario should:
- Set the scene (time, place, characters)
- Walk through the user's action sequence
- Show the product response at each step
- End with an outcome that drives engagement or monetization

### 4. 获客策略 (Acquisition)

User acquisition funnel diagram (ASCII):

```
曝光 → 扫码 → 拍照 → 出结果 → 分享 → 注册 → 付费
```

Acquisition channel table:

| 渠道 | 优先级 | 策略 | 获客成本 |
|:----|:------:|------|:--------:|
| ① Own channel | 🥇 P0 | ... | ¥0 (owned) |

**Cold-start plan:** week-by-week granularity for month 1:

| 周次 | 动作 | 预期效果 |
|:----|:-----|:--------|

### 5. 注册与引导流程 (Onboarding)

Flow chart (ASCII):

```
首次打开 → 微信授权 → 标签选择 → 引导第一次评估 → 拍照 → 出结果 → 分享
```

**最小字段原则:** list every registration field, mark required vs optional, state why it's needed and how it's collected. If a field can be skipped until monetization, skip it.

New user guidance table:

| Step | Interaction | Copy |
|:----|:-----------|:-----|

### 6. 付费体系 (Monetization)

Tier comparison table:

| Dimension | 🆓 Free (90-day) | 💎 Hobbyist ¥29/mo | 👑 Pro ¥399/session |
|:----------|:----------------:|:------------------:|:------------------:|
| Feature A | ✅ | ✅ | ✅ |
| Feature B | ⬜ limited | ✅ | ✅ |

Pricing logic (show the math):
```
Free → trial, goal is habit + data
¥29 → one bubble tea, extremely low barrier
¥399 → vs ¥500 private lesson, clear value
Evaluator take-home: ¥319 (80%), platform: ¥80 (20%)
```

Conversion strategy:

| Phase | Trigger | Target rate |
|:------|:--------|:-----------:|
| Day 85 | "5 days left" popup | 30% click-through |

### 7. 多级付费体系 (Multi-Tier Monetization)

When the product has multiple paid tiers with different feature depths (e.g. sports training where each tier unlocks a different training modality):

#### Sports tier progression pattern

```
免费  →  免费体验期  →  AI-only评估
  |
业余版  →  月费/年费  →  AI评估 + 自助训练 + 自助按摩内容
  |
专业版  →  按次付费  →  AI评估 + 训练 + 真人教练 + 真人按摩师 + 双裸眼视频分析
```

Each tier should provide a **clearly differentiated value**:
- **免费**: just enough to demonstrate value (AI assessment, limited history)
- **业余版**: self-service depth (training animations, massage library, full history)
- **专业版**: human service (booking a real coach/therapist, multi-camera analysis)

Key principle: **each tier's new features must require completing the PREVIOUS tier's training**. E.g., to unlock professional coach booking, you must pass all amateur training exams. This creates a natural upgrade path and prevents users from skipping straight to the most expensive tier without seeing the intermediate value.

#### Conversion funnel design

Include numeric projections at each stage:

| Stage | Conv. rate | Users/mo |
|:------|:----------:|:--------:|
| Visitor → Register | 40% | 3000 |
| Free → Amateur | 15% | 360 |
| Amateur → Pro exam pass | 30% | 108 |
| Pro → Pro service | 10% | 36 |

#### Pricing logic section

Show the unit economics:

``` 
业余版 ¥29/月 = 一杯奶茶钱
专业版 ¥399/次 = 对比私教课¥500/节，超值
评估师到手 ¥319 (80%)，平台抽成 ¥80 (20%)

评估师日接3单 = ¥957/天
评估师月接15单 = ¥4,785/月 (兼职)
```

### 8. 预约与在线选择 (Booking Flow)

UI flow as ASCII diagrams. Show the user selecting a tier → choosing assessment type → picking date/time → selecting venue → confirming payment.

Include the **evaluator onboarding flow** if applicable (registration → credential verification → setting service range → accepting orders → payment).

### 8. 业务规则 (Business Rules)

Rules table:

| Rule | Description |
|:----|:------------|
| Free trial | 90 calendar days from registration |
| Evaluator radius | Only venues they selected |

### 9. KPI (Key Metrics)

**北极星指标 (North Star):** one metric that captures the core value loop.

Core metrics table:

| 指标 | 基准线 | 目标值 |
|:----|:-----:|:-----:|
| Conversion rate | — | ≥10% |

User lifecycle:

```
Acquisition(¥0) → Free trial(¥0) → Hobbyist(¥29/mo) → Pro(¥399) → Evaluator(20% cut)
```

### 10. 产品路线图 (Roadmap)

P0/P1/P2 phases, each with a table:

| Feature | Priority | Status |
|:--------|:--------:|:------:|
| Core feature | 🔴 P0 | ✅/⏳/📝 |

### 11. 风险与对策 (Risk Assessment)

| Risk | Probability | Impact | Mitigation |
|:----|:-----------:|:------:|:----------|
| ... | low/med/high | low/med/high | ... |

## Writing principles

### Brand & IP integrity during multi-workspace work

**CRITICAL RULE: Never rename, rebrand, or replace a project that has an existing domain/app registration/ICP备案.**

When working in a scratch (experimental) workspace and developing features under a new brand name (e.g., "羽迹"), then merging back into the real project:

1. **Preserve the original project name everywhere.** The app label in `app.json` (`navigationBarTitleText`), the `app.title` in `webapp.py/FastAPI`, page `<title>` tags, copyright footers, and any brand copy in the HTML/CSS frontend must all keep the **original registered name**.

2. **Before merging:** audit brand references in the new code (`grep -r "新品牌名" scratch/`) and replace every instance with the original name before copying files over.

3. **Never overwrite the real project directory.** The real project is at `~/Desktop/2026AIAPP/...` or wherever the user keeps it. The scratch workspace is at `~/workspace/...`. Always merge by **copying new files + patching existing ones** in the real project — never `cp -r scratch/ real/`.

4. **The user's registered name is authoritative.** Even if the PRD or concept uses a different working name, the code/assets must use the registered name. The user will say "不能用羽迹了，备案用之前名" — treat this as a hard constraint, not a suggestion.

5. **Documentation can use the working name** internally (PRD, roadmap, internal notes), but **code and UI must use the registered brand**. When pushing docs to Notion, the page titles can remain conceptual; the actual deployment code cannot.

### User preference: structured, compact, actionable

This user (老卢) communicates via WeChat and prefers:
- **Emoji-sectioned chapters** with `#` headings (🏸, 🎯, 🆓, 💎, 👑, etc.)
- **Tables** for comparison data — never prose paragraphs for side-by-side analysis
- **ASCII flow charts** for user journeys (avoid image-based diagrams)
- **Concrete numbers** — avoid vague statements like "a lot of users"; use "300万球友, 0.1%渗透=3000人"
- **Risk-first thinking** — lead with "泼冷水再给路径" (cold water first, then path forward)
- **Bite-sized actions** — end with "下一步做什么" (what to do next)

### Keep it real

- **Monetization must be realistic for the user's constraints.** This user: solo dev, 5h/week, bootstrapped, no team, no payment self-operation. Don't propose VCs, full-time hires, national expansion, or self-operated payment.
- **Cost sections must include actual ¥ amounts.** Don't write "cheap" — write "≈55元/年".
- **Timeline must respect 5h/week.** A task that says "build this in 1 week" means 5 total hours of work.
- **Reference existing assets** — if the user already has a venue database or social accounts, build the GTM plan around them.

### Output

Save to `.md` file in the project directory (or user-specified location). Offer to sync to Notion afterward using the `notion` skill with curl fallback (the `ntn` CLI may not be installed).

### Notion sync pattern (when user asks to push docs)

```bash
# 1. Create a parent page under a known parent (e.g. "深圳羽球地图")
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "parent": {"page_id": "KNOWN_PARENT_ID"},
    "icon": {"emoji": "🏸"},
    "properties": {
      "title": [{"text": {"content": "📂 Section Title"}}]
    }
  }'

# 2. Create sub-pages with full markdown body
curl -s -X POST "https://api.notion.com/v1/pages" \
  -H "Authorization: Bearer $NOTION_API_KEY" \
  -H "Notion-Version: 2025-09-03" \
  -d '{
    "parent": {"page_id": "PARENT_PAGE_ID"},
    "icon": {"emoji": "📄"},
    "properties": {
      "title": [{"text": {"content": "📋 Document Title"}}]
    },
    "markdown": "ESCAPED_FILE_CONTENT"
  }'

# The markdown field accepts normal markdown — tables, links, code blocks all work.
# For multi-file sync: loop over documents, read each file, json-escape content, POST.
# Key: the parent page AND the sub-pages must all be Shared with the integration in Notion UI.
```
