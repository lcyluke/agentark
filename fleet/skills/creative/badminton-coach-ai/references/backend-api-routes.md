# Backend API route map & startup/verify workflow

The FastAPI backend (`badminton_coach/webapp.py` + `auth_api.py`) is the server
the WeChat mini-program talks to. This is the verified route map and the
correct way to start + smoke-test it.

**Project path:** `/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai`  

## ⚠️ Route prefix gotcha (cost two 404s)

`auth_api.py` mounts its router with `APIRouter(prefix="/api")` and the route
decorators ALSO include their own sub-path. So the full path is the prefix
PLUS the decorator path. Do NOT guess — grep the actual decorators:

```bash
grep -rEn "@(app|router)\.(get|post|put|patch)\(" /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/badminton_coach/
grep -rn "APIRouter\(|include_router|prefix" /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/badminton_coach/
```

## Verified route map (current build — includes 三等级付费系统)

### Core Pages & Assessment
| Method | Full path | Purpose |
|--------|-----------|---------|
| GET  | `/` | Web UI (HTMLResponse) |
| GET  | `/api/spec` | Assessment spec — L1-L7 tiers with criteria |
| POST | `/api/assess` | Image → grade + stroke + radar |
| POST | `/api/doubles?mode=single|double` | Doubles role diagnosis + share card HTML |
| POST | `/api/full` | Full pipeline: assess + training + injury + gear |

### Auth (auth_api.py — APIRouter prefix="/api")
| Method | Full path | Purpose |
|--------|-----------|---------|
| POST | `/api/auth/wechat` | WeChat one-tap login (Mock openid if no WECHAT_APPID) |
| POST | `/api/auth/sms/send` | Send SMS code (returns `dev_code` when SMS_PROVIDER empty) |
| POST | `/api/auth/sms/login` | Phone+code login → returns `token` |
| GET  | `/api/survey/questions` | 5-question pain-point survey |
| POST | `/api/survey/submit` | Submit survey answers (Bearer auth required) |
| POST | `/api/me/assessment` | Save an assessment record |
| GET  | `/api/stats` | Ops dashboard (users/wechat_users/sms_users/surveyed/assessments) |
| GET  | `/api/me` | Current user (Bearer token) |

### 三等级付费系统 (auth_api.py)
| Method | Full path | Purpose |
|--------|-----------|---------|
| GET  | `/api/user/profile` | User info + tier info (remaining days, pro bookings) |
| POST | `/api/user/survey` | Mark survey as complete (`survey_complete: true`) |
| POST | `/api/user/tier/upgrade` | Upgrade tier: `{tier: "amateur"|"pro"}` |
| GET  | `/api/user/history` | Assessment history + grade curve (current/best/trend) |
| POST | `/api/user/tier/check` | `{can_assess: bool, reason, remaining_days}` |
| POST | `/api/booking/create` | Create booking: `{mode, venue, date, time, notes}` |
| GET  | `/api/booking/list?status=all|pending|confirmed|completed` | List user's bookings |

### User Tier Database Schema
```sql
CREATE TABLE IF NOT EXISTS user_tiers(
    user_id INTEGER PRIMARY KEY,
    tier TEXT DEFAULT 'free',         -- 'free' | 'amateur' | 'pro'
    free_start INTEGER,
    free_expires INTEGER,             -- 90 days after free_start
    tier_start INTEGER,
    tier_expires INTEGER,
    pro_bookings_used INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```
Auto-created on new user registration in both `auth_wechat()` and `sms_login()`.

### Booking Table Schema
```sql
CREATE TABLE IF NOT EXISTS bookings(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    assessor_id INTEGER DEFAULT 0,
    mode TEXT DEFAULT 'single',
    venue TEXT,
    booking_date TEXT,
    booking_time TEXT,
    status TEXT DEFAULT 'pending',
    notes TEXT,
    created_at INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### Tier Rules
- `free`: 90-day trial from signup.
- `amateur`: ¥29/month. 30-day expiry.
- `pro`: ¥399/session. Increments `pro_bookings_used`.
- `/api/user/tier/check` returns `can_assess: false` + reason when expired.

Auth uses `Authorization: Bearer <token>` header for all protected endpoints.

## Start the backend

```bash
cd /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai
export BADMINTON_SECRET="$(openssl rand -hex 32)"
python3 -m uvicorn badminton_coach.webapp:app --host 127.0.0.1 --port 8000 --log-level info
```

Or using the module's main block:
```bash
python3 -m badminton_coach.webapp
```

## Full smoke test (12 checks — verifies everything end-to-end)

⚠️ **IMPORTANT: The `/api/assess` endpoint uses `file` as the form field name** (matching `def assess(file: UploadFile = File(...))`). Using `image` instead produces `422: Field required`. This is NOT the same as most other file-upload APIs.

```bash
# 1. Homepage
curl -s -o /dev/null -w "Home: %{http_code}\n" http://127.0.0.1:8000/

# 2. Spec
curl -s -o /dev/null -w "Spec: %{http_code}\n" http://127.0.0.1:8000/api/spec

# 3. Mock login
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/wechat \
  -H "Content-Type: application/json" \
  -d '{"code":"test123"}' | python3 -c "import json,sys; print(json.load(sys.stdin)['token'])")

# 4. User profile + tier
curl -s http://127.0.0.1:8000/api/user/profile -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Tier: {d[\"tier\"][\"tier\"]}, Days: {d[\"tier\"][\"free_remaining_days\"]}')"

# 5. Tier check
curl -s -X POST http://127.0.0.1:8000/api/user/tier/check -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Can assess: {d[\"can_assess\"]}')"

# 6. Upgrade to amateur
curl -s -X POST http://127.0.0.1:8000/api/user/tier/upgrade -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"tier":"amateur"}' \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Tier: {d[\"tier\"]}')"

# 7. Assessment history
curl -s http://127.0.0.1:8000/api/user/history -H "Authorization: Bearer $TOKEN"

# 8. Create booking
curl -s -X POST http://127.0.0.1:8000/api/booking/create -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"mode":"single","venue":"深圳湾体育中心","date":"2025-06-15","time":"14:00-15:00","notes":"test"}'

# 9. Assess image — NOTE: field name is `file`, NOT `image`
curl -s -X POST http://127.0.0.1:8000/api/assess \
  -F "file=@/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/test_img_4.jpg" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Grade: {d.get(\"grade_code\")}, Score: {d.get(\"overall_score\")}')"

# 10. Doubles diagnosis
curl -s -X POST "http://127.0.0.1:8000/api/doubles?mode=single" \
  -F "file=@/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/test_img_4.jpg" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Role: {d[\"player_a\"][\"role_cn\"]}')"

# 11. Full enrichment
curl -s -o /dev/null -w "Full: %{http_code}\n" http://127.0.0.1:8000/api/full \
  -X POST -F "file=@/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/test_img_4.jpg"

# 12. List bookings
curl -s "http://127.0.0.1:8000/api/booking/list?status=all" -H "Authorization: Bearer $TOKEN" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f'Bookings: {len(d.get(\"bookings\",[]))}')"
```

## Structured UAT testing pattern (6-step API smoke test)

When running UAT after changes, follow this structured pattern. It catches the most common regressions in one pass:

```bash
cd /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai

# STEP 1: Login + get token
TOKEN=$(curl -s -X POST http://127.0.0.1:8000/api/auth/wechat \
  -H 'Content-Type: application/json' -d '{"code":"uat_test"}' \
  | python3 -c "import json,sys; print(json.load(sys.stdin).get('token',''))")
echo "Token: ${TOKEN:0:20}..."

# STEP 2: Survey submit (requires Bearer auth)
curl -s http://127.0.0.1:8000/api/survey/submit -X POST \
  -H 'Content-Type: application/json' -H "authorization: Bearer $TOKEN" \
  -d '{"answers":{"level":"4","freq":"每周3-5次","pain":"下肢蹬转发力不足","injury":"没有","pay":"30-100元"}}'
# Expected: {"ok":true}

# STEP 3: Assess all 6 test images (tests image_assessor.py + skill_grader.py)
for i in 1 2 3 4 5 6; do
  curl -s http://127.0.0.1:8000/api/assess -X POST \
    -F "file=@test_img_$i.jpg" | python3 -c "
import json,sys; d=json.load(sys.stdin)
print(f'img_$i: {d.get(\"grade_code\",\"?\")} | {d.get(\"overall_score\",\"?\")}分 | {d.get(\"description\",\"?\")[:40]}')"
done

# STEP 4: Doubles role diagnosis
curl -s "http://127.0.0.1:8000/api/doubles?mode=single" \
  -F "file=@test_img_2.jpg" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(d.get('player_a',{}).get('role_cn','?'))"
# Expected: 全场跑动型 / 防守反击型 / 后场重炮型 / 网前雨刮器型

# STEP 5: Full pipeline (training plan)
curl -s http://127.0.0.1:8000/api/full -X POST \
  -F "file=@test_img_3.jpg" \
  | python3 -c "import json,sys; d=json.load(sys.stdin); print(f\"Plan: {d.get('training_plan',{}).get('grade','?')} {d.get('training_plan',{}).get('intensity','?')}\")"

# STEP 6: Tier check + history
curl -s -X POST http://127.0.0.1:8000/api/user/tier/check -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" -d '{"user_id":"uat_test"}'
curl -s "http://127.0.0.1:8000/api/user/history?user_id=uat_test"
```

**Common UAT failure patterns:**
1. **Empty response on assess** → likely wrong form field name (`image` vs `file`). Grep the endpoint: `grep -A5 "async def assess" webapp.py`
2. **"未登录" on survey** → missing `authorization: Bearer` header. Survey submit requires auth.
3. **curl: (26) Failed to open/read local data** → test images not found. They're in project ROOT not `data/`: `ls test_img_*.jpg`
4. **All lower_body scores = 0.0** → MediaPipe initialization failed. Check backend logs for numpy.core.multiarray error.
5. **All dims return 0 + test_img_6 style = "无法评估"** → MediaPipe can't find a person. Backend may have crashed on first request.
6. **Survey question count = 1** → auth_api.py router prefix mismatch. Grep `APIRouter(prefix=` in auth_api.py.
7. **Survey submit returns "Input should be a valid dictionary"** → `answers` field must be a JSON object (`{"key": "val"}`), NOT an array (`[{...}]`). The Pydantic model expects `answers: dict`, not a list. Fix: submit `{"answers": {"level": "4", "freq": "每周3-5次"}}` instead of `{"answers": [{"question_id": "level", "answer": "4"}]}`.
8. **POST /api/user/tier/check with `{user_id: ...}` returns 422** → tier/check reads the user ID from the Bearer token, NOT from the request body. Send `{}` (empty body) with `Authorization: Bearer $TOKEN`. The same applies to `/api/user/history` — it reads user from token, not query param. Do NOT include `user_id` in the body or query string for these endpoints.
9. **All dims return the same static value (e.g. footwork=40, balance=40, recovery=40)** → image_assessor.py is returning default/fallback values for dimensions it can't compute from a single photo. This is expected behavior for image-only assessments — the `swing_power` and `lower_body` are the only dynamically computed dims from images. Consistency defaults to 50. The static dims (footwork/recovery/balance) return the project's configured default (40) because they require video to measure. This is a known limitation, NOT a regression. Documented in image_assessor.py as `_FALLBACK_DIMS`.
10. **parse error: raw is valid JSON but script expects different field names** → the `/api/assess` response schema uses `grade_code`, `grade_name`, `overall_score` (NOT `level`, `score`). Doubles response uses `player_a.role_cn` (NOT `role` directly). Train/pipeline response nests training plan inside `training_plan` as a dict with `grade`, `intensity`, `week_plan`, `summary`. Always use `| python3 -c "import json,sys; d=json.load(sys.stdin); print(d.keys())"` first to discover the actual key structure.
