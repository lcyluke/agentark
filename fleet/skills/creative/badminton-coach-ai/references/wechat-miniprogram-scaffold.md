# WeChat Mini-Program Scaffold (12 pages)

Current state: fully built 12-page mini-program at `miniprogram/`.

```
miniprogram/
├── app.js / app.json / app.wxss    # Global config, dark theme (#0f1f33)
├── pages/
│   ├── login/        ─→ WeChat one-tap auth (wx.login + code exchange)
│   ├── survey/       ─→ 5-question on-boarding survey (level, freq, needs, injury, willingness-to-pay)
│   ├── home/         ─→ Landing page: grade badge + entry buttons
│   ├── assess/       ─→ Assessment: tier selection (free/amateur/pro) + upload photo/video
│   ├── result/       ─→ Grade (L1-L7) + 6-dim radar + strengths/weaknesses + tips
│   ├── training/     ─→ Personalized training plan from AI assessment
│   ├── injury/       ─→ Injury prevention + recovery tips
│   ├── gear/         ─→ Equipment recommendations (search link only, no real payments)
│   ├── profile/      ─→ User info + tier status + upgrade button + booking management
│   ├── guide/        ─→ How-to-use guide for app
│   ├── booking/      ─→ Book a pro assessor (time/venue selection)
│   └── history/      ─→ Assessment history + grade curve chart
├── utils/
│   └── api.js        ─→ wx.request wrappers for all 20+ backend endpoints
├── project.config.json
└── sitemap.json
```

## Tab bar (3 tabs)
- 首页 (home)
- 评估 (assess)
- 我的 (profile)

## API contract

| Mini-program action | Backend endpoint |
|-------------------|-----------------|
| 单打评估 | `POST /api/assess` (file body) |
| 双打角色诊断 | `POST /api/doubles?mode=single\|double` |
| 全量评估 | `POST /api/full` (assess + training + injury + gear) |
| 微信登录 | `POST /api/auth/wechat` |
| 调研题 | `GET /api/survey/questions` |
| 用户信息 | `GET /api/user/profile` |
| 等级检查 | `POST /api/user/tier/check` |
| 升级套餐 | `POST /api/user/tier/upgrade` |
| 评估历史 | `GET /api/user/history` |
| 预约创建 | `POST /api/booking/create` |
| 预约列表 | `GET /api/booking/list?status=all` |

## Key devtools constraints

- `project.config.json` must set `"miniprogramRoot": "miniprogram/"` if `app.json` lives in a subdirectory
- `"enhance": false` + `"libVersion": "2.33.0"` in `project.config.json` to avoid babel/runtime packaging bugs (the `module '@babel/runtime/helpers/typeof.js' is not defined` error). Note: `libVersion: "3.4.0"` (the default for newer devtools) ALSO triggers this bug.
- DevTools → 详情 → 本地设置 → ☑ 不校验合法域名 for HTTP dev backend
- `wx.uploadFile` name param must match FastAPI `UploadFile = File(...)` arg name

## AppID
Real AppID: `wxdad7cddb0cfa785e` (羽球宝AI搭子). Set in `project.config.json`.
