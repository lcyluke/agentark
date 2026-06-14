# Training Game System (P0.7-⑨)

`training_game.py` — 460-line game engine layered on top of `training_tracker.py` and `amateur_training.py`.

## Database tables (auto-created at import time)

| Table | Purpose |
|:------|:--------|
| `user_game` | XP and player level |
| `achievements` | Earned badge records |
| `daily_quests` | Today's random tasks |
| `skill_unlocks` | Skill unlock event log |

All use the same `users.db` at project root (`/path/to/badminton-coach-ai/users.db`).

## Skill tree DAG

23 categories × 127 skills with prerequisite chains. Defined in `SKILL_PREREQUISITES`:

- **Base skills** (no prereqs): high_clear, smash, drop, net, footwork, serve, drive, lob — always unlocked
- **Advanced skills**: require L1 passes on prerequisite skills (e.g. `feints` needs `smash` + `drop` L1)
- **Expert skills**: require L2 passes (e.g. `tactics` needs `pacing` L2 or `combination` L2)

Unlock thresholds per `CATEGORY_UNLOCK_REQUIREMENTS` — some need N-of-M prereqs passed.

## XP system

| Action | XP |
|:-------|:--:|
| Practice skill quest | 50 |
| Footwork quest | 40 |
| Complete 3 sets | 60 |
| Video assessment | 80 |
| Massage log | 30 |

Level thresholds: L1=100, L2=250, L3=450, ... (`_xp_for_level(level)` = `level*100 + (level-1)*50`)

## 11 Achievement badges

- `first_clear` — any skill L1 ≥ 60
- `first_A` — any skill ≥ 85
- `streak_3/7/30` — consecutive day streak
- `skill_master_10/23` — N skills at L2
- `xp_1000/10000`
- `category_clear_5/10` — all skills in N categories pass L1

Auto-checked on `check_achievements()` call.

## API endpoints (in `amateur_training.py` router)

| Endpoint | Method | Auth | Description |
|:---------|:------:|:----:|:------------|
| `/api/training/game/state` | GET | Bearer | Full game state (player + tree + achievements + quests) |
| `/api/training/game/skill-tree` | GET | Bearer | Skill tree with unlock states and progress |
| `/api/training/game/skill-tree/{skill_id}` | GET | Bearer | Single skill unlock check |
| `/api/training/game/achievements` | GET | Bearer | All badges (earned + defined) |
| `/api/training/game/quests` | GET | Bearer | Today's daily quests (auto-generated if none exist) |
| `/api/training/game/quest/{quest_id}/complete` | POST | Bearer | Mark quest done → XP reward |

## Daily quest implementation detail

3 random quests generated per day from `DAILY_QUEST_TEMPLATES`. Idempotent — calling `generate_daily_quests()` multiple times on the same day returns the same three (from DB, not re-generated). The `{skill}` placeholder is replaced with a random Chinese skill name at generation time.

## Import pitfalls

- `training_game.py` **must import from `training_tracker.py`** for progress data: use `get_training_summary(user_id)` — it returns `{user_stats, progress, recent_sessions}`. Do NOT import `get_user_progress` or `get_user_stats` directly (they don't exist as standalone exports).
- Database path: `_DB = Path(__file__).resolve().parent.parent / "users.db"` — the actual `users.db` is at the project root, NOT in the `data/` subdirectory.
- Tables auto-create at module import time via `_auto_init()` — no explicit `init_game_tables()` call needed in `webapp.py`.

## Mini-program page

`pages/game/` — 4 files (game.json, game.wxml, game.wxss, game.js)

Features:
- Player card (level badge + XP progress bar + streak counter 🔥)
- Daily quest list (tap to complete → XP reward toast)
- Category skill tree (horizontal scroll, expand/collapse per category, dot indicators for lock/L1/L2/L3 state)
- Achievement badge wall (grayscale if locked, color if earned)

Entry points:
- Training page top banner (`goGame` → `wx.navigateTo`)
- Registered in `app.json` as `pages/game/game`
