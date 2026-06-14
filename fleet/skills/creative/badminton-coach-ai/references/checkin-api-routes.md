# Check-in API Routes (羽迹打卡系统)

All under `APIRouter(prefix="/api")`. All endpoints require Bearer token auth via `authorization` header.

## Core Routes

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/checkin` | Create a check-in. Multipart form: type, venue_name, notes, mood, companions, photos[] | Bearer |
| GET | `/api/checkins` | List check-ins. Query: type, offset, limit. Default 20 per page | Bearer |
| GET | `/api/checkins/timeline` | Timeline grouped by day. Query: year, month | Bearer |
| GET | `/api/checkins/map` | Map markers: venues aggregated by venue_id with count + last_time | Bearer |
| GET | `/api/checkins/stats` | Stats: total, this_month, streak_days, venues_visited, by_type | Bearer |
| GET | `/api/checkin/photo/{fname}` | Serve uploaded check-in photo | Public |

## Venue Search

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| GET | `/api/venues/search` | Search 326 venues. Query: q (keyword), lat, lng, radius_km | Bearer |

## Content Validation

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/assess` | Upload image/video → content validation → L1-L7 grade | Bearer |
| POST | `/api/full` | Full assessment with all action types | Bearer |

Content validator (`content_validator.py`) runs BEFORE assessment. Returns 400 with `INVALID_CONTENT` code if:
- No person detected
- Non-badminton sport detected (table tennis, basketball, etc.)
- Image too dark/blurry/blank

## Supporting Routes

| Method | Path | Description | Auth |
|--------|------|-------------|------|
| POST | `/api/recognize` | Upload photo → identify venue name from 326 DB | Bearer |
| GET | `/api/share-card/weekly` | Generate weekly HTML share card | Bearer |
| POST | `/api/invite/code` | Get/generate my invite code | Bearer |
| POST | `/api/invite/redeem` | Redeem a friend's invite code | Bearer |
| GET | `/api/invite/friends` | List my friends | Bearer |
| GET | `/api/invite/stats` | Invitation statistics | Bearer |
| GET | `/api/goals` | List life goals (filter: category, status) | Bearer |
| POST | `/api/goals` | Create a life goal | Bearer |
| PUT | `/api/goals/{id}` | Update goal progress | Bearer |
| DELETE | `/api/goals/{id}` | Soft-delete goal (sets status=abandoned) | Bearer |
| GET | `/api/goals/progress` | Goal completion stats | Bearer |
| GET | `/api/discount/rules` | Group discount tier rules | Bearer |
| GET | `/api/discount/status` | Current platform discount status | Bearer |
| GET | `/api/dashboard/overview` | Overview stats | Bearer |
| GET | `/api/dashboard/trends` | 7-day check-in trend | Bearer |
| GET | `/api/dashboard/hot-venues` | Top 10 venues by check-in count | Bearer |
| GET | `/api/dashboard/type-distribution` | Check-in type pie chart data | Bearer |
