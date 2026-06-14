# P1-⑥ 微信支付系统

## Module: `badminton_coach/wechat_pay.py`

Dual-mode: **Mock** (dev, zero-config) → **Real** (production, 3 env vars).

## Architecture

```
POST /api/user/pay → create_order() → Mock: mock_complete_payment() → process_payment()
                                    → Real: 返回prepay参数 → 小程序wx.requestPayment
                                                                 → 微信回调 /api/pay/callback
                                                                 → verify_callback_signature()
                                                                 → process_callback() → process_payment()
```

## Mock mode (default)

When `WECHAT_PAY_MCHID` is unset:
- `IS_REAL = False`
- `create_order()` sets `status='mock_pending'` and returns mock prepay params
- `/api/user/pay` auto-completes: create → mock_complete → upgrade (backward compatible)
- `/api/pay/mock-complete` can be called manually for testing

## Real mode

Set 3 env vars to switch:
```bash
export WECHAT_PAY_MCHID=1234567890
export WECHAT_PAY_API_V3_KEY=your_api_v3_key
export WECHAT_PAY_SERIAL_NO=证书序列号
```

Also requires:
- `badminton_coach/certs/apiclient_key.pem` — merchant private key
- HTTPS callback URL (needs ICP备案) — set via `WECHAT_PAY_NOTIFY_URL`

When `IS_REAL=True`:
- `create_order()` calls WeChat Pay API v3 JSAPI endpoint
- Returns `prepay_params` for `wx.requestPayment`
- Callback at `/api/pay/callback` verifies signature + processes upgrade

## DB: `orders` table

```sql
orders: id, order_no(unique), user_id, plan_id, period, amount,
  status(pending/mock_pending/paid/failed/expired),
  wx_prepay_id, wx_transaction_id, created_at, paid_at, expired_at
```

Order numbers format: `YQB{YYYYMMDDHHmmss}{6-digit-random}`

## Pricing

| plan_id | period | amount |
|:--------|:-------|-------:|
| amateur | monthly | ¥9.9 |
| amateur | annual | ¥79 |
| pro | monthly | ¥29.9 |
| pro | annual | ¥199 |

## Endpoints

| Endpoint | Auth | Purpose |
|:---------|:----:|:--------|
| `POST /api/pay/create-order` | Bearer | Create order → prepay params |
| `POST /api/pay/mock-complete` | — | Mock complete (dev only) |
| `GET /api/pay/orders` | Bearer | Order history |
| `GET /api/pay/order/{order_no}` | — | Query single order |
| `POST /api/pay/callback` | — | WeChat callback (HTTPS) |

## Integration with popup

`/api/user/popup-state` carries payment context in the popup payload:
```json
{
  "popup": {
    "type": "quota_exhausted",
    "plans": [{"id":"amateur","price":9.9,...}, {"id":"pro","price":29.9,...}],
    "recommended_plan": "amateur",
    "pay_endpoint": "/api/user/pay",
    "pay_params": ["plan_id", "period"]
  }
}
```

Frontend renders plans → user picks → `POST /api/user/pay` with `plan_id` + `period`.
