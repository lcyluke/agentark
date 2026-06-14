# Tier System API Reference (Luke's 羽球宝AI搭子)

## Three-Tier Model

| Tier | Name | Price | Duration |
|:----:|:----|:----:|:--------|
| free | 免费版 | ¥0 | 30 days unlimited assessments |
| amateur | 业余版 | ¥29 | monthly subscription |
| pro | 专业版 | ¥399 | per-booking |

## Free Tier Rules
- 30-day free period (changed from 90 days per user request)
- Unlimited assessments during free period
- After expiry: upgrade required to continue

## API Endpoints

### GET /api/tiers/info
Returns full feature comparison for all 3 tiers. Each tier has a `features` array with `{ok: bool, text: string}`.

### POST /api/payment/create {tier, method}
Creates a mock payment order. Returns `order_id, amount, qrcode_url, pay_url`.
- In dev mode: user confirms via modal, then calls `/api/payment/confirm`
- In production: returns real WeChat Pay URL / QR code

### POST /api/payment/confirm {tier}
Activates the tier. For amateur: adds 30 days to tier_expires. For pro: increments pro_bookings_used.

### Invite System
- **GET /api/invite/code** — Returns user's invite code (auto-creates if missing, format: `YPB<userid_hex><random>`)
- **POST /api/invite/redeem {code}** — Redeemer enters code; inviter gets 14d amateur, redeemer gets 7d amateur
- Mutual usage prevention: cannot use own invite code
- Once used: invite_code is marked claimed=1, invitee_id set

### Photos & Certificates
- **POST /api/photos/save {photo_type, file_path, grade, score, assess_count}** — Record a photo metadata entry
- **GET /api/photos/list?photo_type=** — List photos (filter by type: assessment/levelup/milestone)
- **POST /api/certificate/generate** — Generate cert; accepts optional {grade, score} body, or uses latest assessment
- **GET /api/certificate/list** — List all user certificates sorted by date desc

## Database Tables

### user_tiers
```sql
CREATE TABLE user_tiers(
    user_id INTEGER PRIMARY KEY,
    tier TEXT DEFAULT 'free',
    free_start INTEGER,
    free_expires INTEGER,
    tier_start INTEGER,
    tier_expires INTEGER,
    pro_bookings_used INTEGER DEFAULT 0,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### invitations
```sql
CREATE TABLE invitations(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inviter_id INTEGER NOT NULL,
    invitee_id INTEGER,
    invite_code TEXT UNIQUE NOT NULL,
    reward_days INTEGER DEFAULT 14,
    claimed INTEGER DEFAULT 0,
    created_at INTEGER,
    claimed_at INTEGER,
    FOREIGN KEY(inviter_id) REFERENCES users(id)
);
```

### certificates
```sql
CREATE TABLE certificates(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    grade TEXT,
    score REAL,
    cert_id TEXT UNIQUE,
    issued_at INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

### user_photos
```sql
CREATE TABLE user_photos(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    photo_type TEXT DEFAULT 'assessment',
    file_path TEXT,
    grade TEXT,
    score REAL,
    assess_count INTEGER DEFAULT 0,
    created_at INTEGER,
    FOREIGN KEY(user_id) REFERENCES users(id)
);
```

## Frontend Pages

| Page | Route | Key Behaviors |
|:----|:------|:-------------|
| payment | /pages/payment/payment | Tier comparison list from `/api/tiers/info`, method selector (wechat/alipay), mock pay button, success state |
| certificate | /pages/certificate/certificate | Certificate cards with grade, score, cert ID, share to timeline |
| photos | /pages/photos/photos | Tab filter (all/assessment/levelup/milestone), grid layout, tap to preview |
| profile | /pages/profile/profile | Invite code display+copy, tier info, upgrade button → payment page |

## Dev Mode Payment Flow
In development, there is no actual payment SDK. The flow is:
1. User taps upgrade → navigates to payment page with `?tier=amateur` or `?tier=pro`
2. Payment page calls POST /api/payment/create → shows mock order
3. User taps confirm → modal says "开发模式：模拟付款"
4. On confirm → calls POST /api/payment/confirm → tier activated
5. Show success screen with "返回个人中心" button

For production, replace with real WeChat Pay JSAPI or 扫码支付.

## Known Issues & Pitfalls

### `lastrowid` on connection (Python 3.9)
```python
# BROKEN:
c = connection.execute("INSERT ...")
pid = c.lastrowid  # ❌ AttributeError on py3.9
# FIX:
cur = c.execute("INSERT ...")
pid = cur.lastrowid  # ✅
```

### certificate/generate needs assessment data
The certificate endpoint can either:
1. Pull from the user's `assessments` table (latest record)
2. Accept `{grade, score}` directly in the POST body

If the assess endpoint doesn't save to the assessments table (which happens if the assess endpoint didn't create a logged-in user assessment), option 2 provides a fallback.

### Invite code format
Generated as `YPB{uid:X}{secrets.token_hex(3).upper()}`. This is a dev format — in production, use a proper random code or shortlink.
