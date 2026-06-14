# P1-④ Uber化预约竞价系统

## Flow

```
用户发单 → 进入竞价池(status=open) → 多位教练出价
    → 智能排序(评分×性价比加权) → 标签(🥇最佳性价比/⭐评分最高/💰最低价)
    → 用户选标 → accept → 自动生成正式appointment → 其他bid标记rejected
```

## DB tables

```sql
booking_requests: id, user_id, provider_type, booking_date, booking_time,
  duration_minutes, venue, address, max_budget, status(open/accepted/closed),
  accepted_bid_id, created_at, updated_at

bids: id, request_id, provider_id, provider_type, amount, notes,
  status(pending/accepted/rejected), created_at
```

## Smart ranking (`_smart_rank_bids`)

- `match_score = rating/5.0 * 0.6 + (1 - amount/max_budget) * 0.4`
- Sorted descending by match_score
- Tags: 🥇 top result, ⭐ highest rating (non-top), 💰 lowest price (non-top)

## Key endpoints

| Endpoint | Auth | Role | Purpose |
|:---------|:----:|:----:|:--------|
| `POST /api/booking/request` | Bearer | User | Create auction request |
| `GET /api/booking/requests/my` | Bearer | User | My requests with bid counts |
| `GET /api/booking/requests/open` | Bearer | Coach | View open requests to bid on |
| `POST /api/booking/requests/{id}/bid` | Bearer | Coach | Place bid (one per request) |
| `GET /api/booking/requests/{id}/bids` | Bearer | User | View ranked bids |
| `POST /api/booking/requests/{id}/accept` | Bearer | User | Accept bid → creates appointment |
| `POST /api/booking/instant` | Bearer | User | Skip auction, instant booking |

## Anti-patterns

- `coaches` table has no `city`/`districts` columns. Only `massage_therapists` has them.
- After accepting a bid, the code writes to `appointments` with `status='confirmed'`.
- Duplicate bids blocked: one pending bid per provider per request.
- Gate check: `coach_booking` feature requires Pro tier (402 if denied).
