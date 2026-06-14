# 羽球宝AI搭子 — API Endpoint Reference

Discovered during P0.5 miniprogram API migration session (2026-06-02).
Backend: FastAPI on port 8000, project at `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`.

## Training APIs (P0.5 core)

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/training/categories` | GET | No | 23 categories × 7 groups, sub_skills with levels |
| `/api/training/skills` | GET | No | Flat skill list with levels |
| `/api/training/skills/{skill_id}` | GET | No | Single skill detail |
| `/api/training/sub-skills/{sub_skill_id}` | GET | No | Sub-skill detail |
| `/api/training/progress` | GET | Yes | User's progress on all skills |
| `/api/training/plan` | GET | Yes | AI-generated weekly plan |
| `/api/training/record` | POST | Yes | Record a training set (skill_id, level, sets) |
| `/api/training/video-assess` | POST | Yes | Upload video for assessment |
| `/api/training/video-mapping` | GET | No | Skill → demo video URL mapping |
| `/api/training/skill-video/{skill_id}` | GET | No | Demo video URL for specific skill+level |
| `/api/training/history` | GET | Yes | Exam/assessment history |

## Training v2 APIs (tracking)

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/training/v2/stats` | GET | Yes | streak_days, max_streak, week_sessions, month_sessions, total_skills, total_duration_min, streak_today |
| `/api/training/v2/progress` | GET | Yes | All skill progress |
| `/api/training/v2/record` | POST | Yes | Record with query params: skill_id, level, sets, reps |
| `/api/training/v2/sessions` | GET | Yes | Recent training sessions (date list) |
| `/api/training/v2/skill-breakdown/{skill_id}` | GET | No | Phase-by-phase breakdown: prepare/backswing/hit/follow with key_points, common_errors |
| `/api/training/v2/skill-breakdown` | GET | No | All skills breakdown |
| `/api/training/v2/daily-goals` | GET | Yes | recommended_sets, recommended_reps_per_set, recommended_duration_min |
| `/api/training/v2/level-check` | GET | Yes | Check if level unlock is ready |
| `/api/training/v2/action-clips-config` | GET | No | Action clip generation config |
| `/api/training/v2/skills` | GET | No | Trackable skills list |

## Game/Achievement APIs (bonus beyond P0.5)

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/training/game/state` | GET | Yes | Current game state |
| `/api/training/game/skill-tree` | GET | Yes | Skill tree unlock status |
| `/api/training/game/skill-tree/{skill_id}` | GET | Yes | Single skill node |
| `/api/training/game/quests` | GET | Yes | Daily/weekly quests |
| `/api/training/game/quest/{quest_id}/complete` | POST | Yes | Complete a quest |
| `/api/training/game/achievements` | GET | Yes | Achievement list |

## Massage API

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/massage/library` | GET | No | 6 body parts × 3 levels each |
| `/api/massage/detail` | GET | No | Detail for part+level |
| `/api/massage/log` | POST | Yes | Log a massage session |
| `/api/massage/history` | GET | Yes | Massage history |

## Compare API

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/compare/benchmarks` | GET | No | Available benchmark skeletons (smash/clear/drop/net/footwork/feint/def, levels L5-L6) |
| `/api/compare` | POST | No | Upload video → extract skeleton → compare to benchmark → deviations report |
| `/api/compare/skeleton` | POST | No | Send skeleton JSON directly → compare |
| `/api/compare/from-file` | POST | No | Reference local file for comparison |

## Avatar/Face Swap

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/avatar/generate` | POST | Yes | Upload photo + skill_id → generate face-swapped video (stub/real mode) |
| `/api/avatar/skills` | GET | No | Available skills for face swap |
| `/api/assess/cartoon-avatar` | POST | No | Generate cartoon avatar from photo |

## Key Architecture Notes

- **Monolith structure**: `amateur_training.py` (5,051 lines, 80 functions) contains training, massage, doubles, coach, booking, and game APIs — all behind a single `APIRouter(prefix="/api")`.
- **Tracker**: `training_tracker.py` (1,504 lines, 22 functions) handles v2 tracking APIs, streaks, daily goals, level unlocks.
- **API wrapper**: Frontend uses `utils/api.js` with `request()` (returns `.data` directly, auto-injects Bearer token) and `upload()` (auto-injects token, returns parsed JSON).
- **Auth pattern**: Backend uses `_require_user(authorization: Optional[str])` which raises 401 when token invalid. Frontend `request()` redirects to login on 401.
