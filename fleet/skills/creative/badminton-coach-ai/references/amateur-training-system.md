# Amateur Training System — Technical Architecture

Added in PRD v0.3 / P0.5 sprint. This system sits alongside the core assessment pipeline and extends the app from "just assess" to "assess → train → pass exam → unlock pro".

## Files

| File | Role |
|------|------|
| `badminton_coach/amateur_training.py` | Skill definitions (6×3), training API routes, massage library API, coach/therapist/scheduling schema, video assessment scoring |
| `badminton_coach/training_gif.py` | Skeletal animation GIF generator from keyframe definitions |
| `data/training_animations/*.gif` | Generated GIFs (6 files, 50-134KB each, auto-loop) |

## Skill Definitions (6 skills × 3 levels)

Defined as a dict `SKILL_BANK` in `amateur_training.py`:

| Key | Name | Levels |
|-----|------|--------|
| `high_clear` | 高远球 | 3 (初级→中级→高级) |
| `smash` | 杀球 | 3 |
| `drop` | 吊球 | 3 |
| `footwork` | 步法 | 3 |
| `defense` | 防守 | 3 |
| `net` | 网前球 | 3 |

Each level defines:
- `title`, `volume` (e.g. "3组×20次"), `rest_sec`
- `key_points` (list of text strings)
- `common_mistakes` (list), `pass_score` (60/65/70 for lv1/2/3)
- `grade_base` (e.g. "L1-L3", "L3-L5", "L5-L7")

## Skeletal Animation GIF Generation

### How it works

1. Each stroke type has hand-authored keyframes — 3-5 critical poses per animation
2. Between keyframes, linear interpolation produces smooth motion
3. Each frame renders: background → bone connections → joint circles → text labels → progress bar
4. PIL converts frame sequence to GIF with `loop=0` (infinite)

### Keyframe design

Keyframes are defined in `_STROKE_KEYFRAMES` as `{frame_idx: {landmark_idx: (x, y)}}` where x,y are normalized [0,1] coordinates in MediaPipe convention (y-down).

Example (simplified, from `high_clear`):
```
frame 0:  resting pose (arms half-raised)
frame 5:  winding up (elbow back, torso rotated)
frame 10: contact point (arm fully extended upward)
frame 15: follow-through (arm coming down)
frame 20: recovery (back to rest)
```

### Adding a new animation

```python
from badminton_coach.training_gif import TrainingGifGenerator
gen = TrainingGifGenerator()
path = gen.generate_gif("new_skill", "new_skill.gif")  # 80ms per frame default
```

Or for a specific level duration:
```python
path = gen.generate_for_level("smash", level=2, duration_ms=100)
```

### SVG/Image alternatives

If GIF quality is insufficient (banding, large size), consider:
- **APNG** — better compression, wider color range, but Safari-only on iOS/macOS
- **MP4 looped video** — `ffmpeg -i frames/%04d.png -vf "setpts=2.0*PTS" -loop 1 out.mp4`
- **Lottie JSON** — vector animation via airbnb's Lottie, but requires SDK integration

## Video Exam Scoring

`assess_training_video()` in `amateur_training.py`:

1. Video uploaded → saved to `data/training_videos/`
2. MediaPipe PoseEstimator processes video → `List[FramePose]`
3. StrokeAnalyzer detects stroke events → `List[StrokeEvent]`
4. ReferenceLibrary compares against pro benchmarks → `ComparisonResult.overall_score`
5. If no strokes detected → fallback to `_fallback_pose_score()` (average frame-by-frame metric)
6. Score >= pass_score → pass. Score recorded + progress updated.

**Pass thresholds:**
- Level 1 (初级): ≥60
- Level 2 (中级): ≥65
- Level 3 (高级): ≥70

## Massage Library

6 body parts × 3 levels = 18 entries:

| Part | Level 1 (15s) | Level 2 (30s) | Level 3 (60s) |
|------|:-------------:|:-------------:|:-------------:|
| shoulder | 肩后侧拉伸 | 冈下肌网球按揉 | YTWL完整流程 |
| elbow | 伸腕肌群拉伸 | 前臂滚轴卷绳 | 深层横向松解 |
| wrist | 腕屈伸拉伸 | 握力球训练 | TFCC康复操 |
| waist | 猫式伸展 | 梨状肌拉伸 | 核心稳定训练 |
| knee | 股四头肌拉伸 | 髌骨带松动 | 臀部肌群激活 |
| ankle | 踝关节绕环 | 小腿滚揉放松 | 平衡板训练 |

Each entry has: `title`, `duration`, `steps` (list), `benefit`, `gif_ref`.

## Database Tables

Added by `init_training_tables()`:

```sql
training_progress(user_id, skill_id, level, completed_sets, total_sets, passed, last_practice_at, primary_score)
assessment_videos(id, user_id, skill_id, level, video_path, ai_score, passed, detail_json, created_at)
massage_logs(id, user_id, part, level, completed, created_at)
coaches(id, user_id, name, phone, level, cert_info, rating, price, available_hours, created_at, status)
massage_therapists(id, user_id, name, phone, level, cert_info, rating, price_local_30, price_full_60, price_deep_90, available_hours, city, districts, created_at, status)
appointments(id, user_id, provider_type, provider_id, service_type, booking_date, booking_time, duration_minutes, venue, address, status, amount, payment_status, notes, created_at)
```

## API Routes

All prefixed `/api`:

| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/training/skills` | List all skills + levels |
| GET | `/api/training/skills/{id}?level=N` | Skill detail for a specific level |
| GET | `/api/training/progress` | User's training progress (Bearer) |
| POST | `/api/training/record` | Record completed sets (form) |
| POST | `/api/training/video-assess` | Upload exam video + AI score (multipart) |
| GET | `/api/training/history` | Exam history |
| GET | `/api/massage/library` | List massage body parts + levels |
| GET | `/api/massage/detail?part=N&level=N` | Massage steps for a specific part+level |
| POST | `/api/massage/log` | Record massage completion |
| GET | `/api/massage/history` | List massage history |

## Unlock Chain

```
业余版 user
  → complete sets in amateur_training
  → pass video exam (score >= threshold)
  → training_progress.passed = 1 for that skill+level
  → when ALL 6 skills have ALL 3 levels passed
    → all_lv3_passed = true
    → pro_training_unlocked = true
    → user can access professional coach booking
```

Checked by `check_training_unlock(uid)` — returns per-skill progress and unlock status.

## Regenerating GIFs after keyframe edits

```bash
cd /Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai
./venv/bin/python3 -c "
from badminton_coach.training_gif import TrainingGifGenerator
gen = TrainingGifGenerator()
results = gen.generate_all()
for k, v in results.items():
    import os
    print(f'{k}: {os.path.getsize(v)//1024}KB -> {v}')
"
```
