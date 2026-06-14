# Assessment Test Images — Known Results

All 6 test images live at `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/test_img_{1-6}.jpg`.
Run assessment via: `curl -s -X POST http://127.0.0.1:8000/api/assess -F "file=@test_img_N.jpg"`

⚠️ **CRITICAL: The form field name is `file`, NOT `image`**. Using `-F "image=@..."` produces `422: Field required`.
The endpoint signature is `async def assess(file: UploadFile = File(...))`.

## Results (2026-05-30, verified)

### Photo Assessment (6-dim radar)

| Image | Grade | Score | Strengths | Weaknesses | AI Diagnosis |
|-------|-------|-------|-----------|-------------|-------------|
| 1 | L3 中级 | 37 | 挥拍发力 52 | 下肢蹬转 32, 重心 40, 回中 40 | 转体不足，发力靠手臂 |
| 2 | L2 初级 | 31 | 一致性 50 | 下肢蹬转 16, 挥拍 32, 重心 40 | 击球点偏低+未屈膝+转体不足 |
| 3 | L3 中级 | 37 | 一致性 50 | 下肢蹬转 37, 重心 40, 回中 40 | 转体不足 |
| 4 | L2 初级 | 33 | 挥拍发力 58 | 下肢蹬转 15, 重心 40, 回中 40 | 击球点低+未屈膝 |
| 5 | L2 初级 | 33 | 挥拍发力 54 | 下肢蹬转 29, 重心 40, 回中 40 | 击球点偏后偏低 |
| 6 | — 无法评估 | 0 | — | — | 无人像/角度不对 |

### Doubles Role Diagnosis (via /api/doubles)

| Image | Role | Confidence | Description |
|-------|------|:----------:|------------|
| 2 (single person) | 🔄 全场跑动型 | 70% | 视野开阔衔接好，能前能后能补位，双打万能胶 |

Note: Doubles diagnosis works on single-person photos (returns `solo: true` when only one person detected).

### Full Pipeline — Training Plan (via /api/full)

| Field | Value |
|-------|-------|
| Grade | L3 |
| Intensity | 中 |
| Focus dims | 下肢蹬转, 步法移动, 回中能力 |
| Summary | 当前 L3 级，强度档「中」。本周重点补强：下肢蹬转、步法移动、回中能力。 |
| Week plan | 6 days: 弓步蹬伸+起跳杀球, 后退步法, 重复杀上网, 休息, 步法组合, 放松 |

### Key Findings

1. **Cross-image consistency**: all 5 scorable images show `lower_body` as the weakest dimension (15-37). This is the user's real problem — they stand while smashing because lower-body engagement is missing. The AI correctly identifies this across different poses.
2. **Relative strength**: `swing_power` (51-58) is consistently the highest dimension. The user has arm strength but the kinetic chain is broken (no leg drive → no hip rotation → arm-only swing).
3. **Image limit**: single-frame images produce confidence 0.45 and cannot assess footwork, recovery, or consistency. Best for quick diagnostic snapshots.
4. **Solo mode on doubles**: `/api/doubles?mode=single` with single-person photos returns `solo: true` and diagnoses the visible player's role. True doubles diagnosis requires a photo with 2 players.

## When to regenerate

- After any change to `image_assessor.py` or `skill_grader.py`
- After MediaPipe model upgrade
- Run all 5 scorable images and verify the `lower_body` dimension still correlates (the user's actual problem should produce consistent results)
- After changes to `double_analyzer.py` — verify the role diagnosis still produces Chinese role names
- After changes to the training plan generator in `/api/full` — verify it produces a 6-day week plan
