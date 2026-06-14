# Defense Benchmark Pipeline

How to extract standard badminton defense benchmarks from an external video,
build the 6-dimension scorer, render skeleton animations, and wire face swap.

## Full Pipeline (session-tested 2026-06-02)

### Phase 1: External Video → Benchmarks

```
1. User sends video via WeChat
   → arrives at ~/.hermes/cache/documents/doc_<hash>_video.mp4
   → HEVC 720p vertical, ~3MB/min, playable directly

2. Extract skeleton: PoseEstimator().process_video(path)
   → returns List[FramePose], each with .landmarks (33,4) numpy array
   → 89% detection rate typical for close-up single-person videos
   → Landmark access: lm[16][1] for right wrist Y (NOT lm[16].y)

3. Identify motion segments by time:
   - Or wrist-Y based: look for low wrist_y (arm raised) and high knee_y (squat)
   - Segment into 5-15s chunks per skill
   - Use ffmpeg for key frame extraction: ffmpeg -y -ss $t -i video -vframes 1

4. Save benchmark: np.save(f'benchmark_{skill_id}.npy', seq)
   → shape (T, 33, 4), subsampled to ~50 frames
   → store at /tmp/badminton_defense/benchmark_<skill_id>.npy
```

### Phase 2: Build Assessor

```
1. defense_assessor.py defines:
   - DEFENSE_SKILLS dict: skill metadata + benchmark path
   - GRADE_THRESHOLDS: 7 tiers (L1 0→L7 90)
   - ASSESS_DIMS: 6 dims with weights

2. Core function: assess_defense(skeleton, skill_id) → dict
   - load_benchmark → DTW alignment (hip+wrist+shoulder 3-feature)
   - 6-dim scoring per aligned pair
   - weighted total → L1-L7 grade

3. CRITICAL: all return values must use Python native types
   - float(val), int(val), bool(val) for every numpy scalar
   - Error: "Object of type bool_ is not JSON serializable"
```

### Phase 3: Render Standard Animations

```
1. defense_animator.py functions:
   - render_animation(skeleton, path, skill_name) → single mp4
   - generate_all_defense_animations(dir) → all 4 mp4s

2. Render parameters:
   - 1920x1080, 30fps, dark blue background
   - Right arm: orange, Left arm: light orange
   - Right leg: blue, Left leg: light blue
   - Auto phase detection from wrist Y extrema
   - Dual loop (forward+reverse) for seamless playback

3. Output: 250-430KB per skill, 421KB combined
   - Static mount: /defense_animations → /tmp/badminton_defense/animations
   - API: GET /api/defense/animations → skill list + animation_urls
```

### Phase 4: Face Swap

```
1. face_swap.py generates "user doing standard motion" videos

2. Three modes:
   - stub: returns standard skeleton animation (dev mode, no GPU)
   - autodl: SSH to AutoDL RTX 4090 D → MimicMotion inference
   - local: macOS MPS/GPU (often crashes on FP16, use autodl)

3. MimicMotion rendering format:
   - Skeleton frames: 576x1024 black background with colored bones
   - JSON format: {"fps":8, "frames":[{"lms":[[x,y],...]}]}
   - Force 48 frames for consistent inference

4. AutoDL connection: AUTODL_HOST/PORT/PASS env vars
   - MimicMotion verified: 10 steps, 17s, 8.8GB VRAM on RTX 4090 D

5. Gate: _check_feature_gate(request, "coach_booking")
   - Free: blocked (402)
   - Pro: allowed (5 uses/month)
```

### API Endpoints

| Endpoint | Gate | Description |
|:---------|:----:|:------------|
| POST /api/defense/assess?skill=all | compare | Video→DTW→6-dim→L1-L7 |
| GET /api/defense/skills | -- | 3 skills + 7 grades + 6 dims |
| GET /api/defense/animations | -- | Animation URLs per skill |
| POST /api/avatar/generate | coach_booking | Photo→face-swapped video |
| GET /api/avatar/skills | -- | Available skills + modes |

### Pitfalls

- **Numpy JSON**: Return dicts must use Python scalars only (float/int/bool cast)
- **First frame**: Frame 0 often has no detection -- skip it in metrics
- **Landmark access**: `f.landmarks[16][1]` NOT `f.landmarks[16].y`
- **Xiaohongshu**: Fully blocked (300012). User sends videos via WeChat.
- **DB migration**: New tables need manual CREATE TABLE IF NOT EXISTS
- **Venv pip**: Use `./venv/bin/python3 -m pip install` not `./venv/bin/pip`
