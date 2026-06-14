---
name: sports-video-labeling-system
description: Build a multi-Agent automated labeling pipeline for sports technique videos — collect, crop, skeleton-trace, annotate with 28-dimensional biomechanical metrics, quality-check, train ML models, and serve amateur/pro dual-tier evaluation reports. Use when you need to bootstrap a training dataset for sports motion analysis from public video sources (B站/YouTube) rather than manual coach labeling.
version: 3.0.0
platforms: [macos, linux]
metadata:
  hermes:
    tags: [labeling, annotation, sports, video, mediapipe, dataset, ml-training]
    related_skills: [pose-video-analysis, training-animation-generation]
---

# Sports Video Labeling System

Bootstrapping a **training dataset for sports motion AI** by automating video collection, MediaPipe skeleton extraction, and 28-dimensional biomechanical annotation, plus serving amateur (8-dim) and professional (28-dim) evaluation reports — replacing expensive manual coach labeling with multi-Agent pipelines.

**Core insight:** Labeling is the asymmetric-competition moat. Manual coach labeling costs ¥5-10 per sample and scales linearly with budget. Automated AI labeling costs ¥0 per sample and scales with compute. This skill captures the architecture, annotation schema (16-base + 12-extended), ML model path, pro/amateur dual-tier evaluators, and pitfalls.

---

## Architecture (6-Agent Pipeline + 2 Evaluators + API Server + DTW Correction Engine)

```
Agent 1: collector v2  →  Agent 2: detector v2  →  Agent 3: skeleton/RTMPose
  (dual-track: amateur   (frame-diff motion     (MediaPipe Pose OR
   + professional,        peak detection +       RTMPose-m 133FPS,
   manifest dedup)       clip extraction)        15 keypoints → NPY)
                            ↓
              Agent 4: annotation_engine (28-dim core)
              Agent 5: annotation_extensions (+12 dims)
                            ↓
              Agent 6: quality_checker (cross-validation)
                            ↓
                    标注数据集 → Phase 1-4 ML models
                            ↓
              ┌───────────────┴───────────────┐
              │                               │
     AmateurEvaluator                  ProEvaluator
     (8合成指标, ¥29/月)              (28维+基准+伤病+战术, ¥399/次)
              │                               │
              └───────────────┬───────────────┘
                              ↓
                    ┌─────────┴──────────┐
                    │                    │
              api_server.py       DTW Correction
         (FastAPI async upload   (joint-level deviation
          → task polling)         → coaching language)
```

| Agent | File | Role | Input | Output |
|:------|:-----|:-----|:------|:-------|
| **1** | `collector_agent.py` v2 | 数据采集 | 关键词/JSON配置 | 原始视频+manifest JSON (双轨amateur/pro) |
| **2** | `detector_agent.py` v2 | 动作检测+裁剪 | 原始视频 | 动作片段MP4+元数据 |
| **3a** | `skeleton_agent.py` | 骨骼追踪 (MediaPipe) | 动作片段MP4 | 逐帧关键点NPY |
| **3b** | `rtmpose_extractor.py` | 骨骼追踪 (RTMPose) | 动作片段MP4 | 逐帧17→15关键点NPY (精度+30%) |
| **4** | `annotation_engine.py` | 28维标注引擎 | 骨骼NPY | 28维标注JSON |
| **5** | `annotation_extensions.py` | 扩展指标 | 骨骼NPY | +12维扩展指标 |
| **6** | `quality_checker.py` | 质量审核 | 标注JSON | 质量评分+异常标记 |
| **E1** | `amateur_evaluator.py` | 业余8维评估 | 标注JSON | E1-E8评分+等级 |
| **E2** | `pro_evaluator.py` | 专业28维报告 | 标注JSON | 6章诊断报告 |
| **C** | `dtw_correction_engine.py` | 关节纠错 | 用户骨骼+基准NPY | 逐关节偏差+中文话术 |
| **API** | `api_server.py` | 异步上传服务 | video multipart | task_id → polling result |

### Orchestration Scripts

| Script | Purpose |
|:-------|:--------|
| `scripts/amateur_pipeline.py` | Phase 1全流程: collect→detect→annotate→report |
| `scripts/pipeline.py` | 原版专业视频流水线 |
| `scripts/qr_generator.py` | 球馆二维码生成 (8预设深圳球馆) |
| `scripts/batch_annotate.py` | 批量标注已有视频 |
| `scripts/train_phase1.py` | RandomForest训练 |
| `scripts/train_phase2.py` | GBDT+Ensemble训练 (172条→76.1%) |
| `scripts/train_stgcn.py` | ST-GCN训练 (失败: 45.7%, 数据不足) |
| `scripts/train_joint_tcn.py` | JointTCN训练 (失败: 5.7%, 数据不足) |
| `scripts/gat_tcn_trainer.py` | GAT+TCN训练 (MPS crash, 架构就绪) |
| `scripts/build_features.py` | 标注文本→34维特征矩阵 |
| `scripts/build_benchmarks.py` | 自动构建DTW基准 (8动作类型) |
| `scripts/parse_features.py` | 正则解析28维标注文本 |

---

## 28-Dimensional Annotation Schema (16-base + 12-extended)

**Design principle:** The same 28-dim engine powers all three pricing tiers. The amateur evaluator (AmateurEvaluator) downsamples 28 dims into 8 intuitive "E scores" (E1发力效果~E8动作一致性). The professional evaluator (ProEvaluator) exposes all 28 dims with L7 benchmark comparisons, injury risk scoring, motion economics, tactical analysis, and training plans.

### Part 1: 16-Base Dimensions (A1-A6, P1-P5, B1-B2)

These are the original 16 dims — direct joint angles, power mechanics, and body parts from MediaPipe skeleton data.

### 1. Basic metadata (3 dimensions)

| ID | Dimension | Type | Range | Method |
|:--:|:----------|:----:|:-----:|:-------|
| M1 | **Action type** | enum | 7-11 categories | Video title + skeleton trajectory classification |
| M2 | **Sub-skill ID** | enum | 50+ skills | Training system mapping |
| M3 | **Grade level** | int | L1-L9 | Rule-engine scoring |

### 2. Joint angles (6 dimensions) — Direct from MediaPipe

| ID | Dimension | Points | Reference values (badminton) |
|:--:|:----------|:------:|:-----------------------------|
| A1 | **Elbow angle** | shoulder→elbow→wrist | Backswing 160-175°, impact 145-165°, follow-through 30-60° |
| A2 | **Shoulder angle** | elbow→shoulder→hip | Max open 110-130°, impact 120-150° |
| A3 | **Knee angle** | hip→knee→ankle | Standing 170-180°, lunge 110-140°, jump crouch 70-90° |
| A4 | **Hip angle** | shoulder→hip→knee | Standing 170-180°, low stance 100-130° |
| A5 | **Waist twist** | shoulder-line vs hip-line angle difference | ±30° typical, signed for rotation direction |
| A6 | **Wrist angle** | elbow→wrist→finger approximation | 0° default without hand landmarks |

**Key implementation detail — NaN handling:**

MediaPipe output contains NaN for undetected frames (person leaves frame, occlusion, awkward angle). Without proper NaN filtering, every downstream metric (explosive power, jump height, relaxation) silently collapses to zero or garbage:

```python
# WRONG — includes NaN in diff/derivative calculations
# velocities = np.linalg.norm(np.diff(wrist_pos, axis=0), axis=1)

# RIGHT — filter NaN before computing derivatives
valid = ~np.any(np.isnan(wrist_pos), axis=1)
if np.sum(valid) < 5: return default_value
wrist_valid = wrist_pos[valid]
velocities = np.linalg.norm(np.diff(wrist_valid, axis=0), axis=1)
```

### 3. Biomechanical power metrics (5 dimensions) — Trajectory inference

These require correct parameter tuning against normalized coordinate space:

| ID | Dimension | Range | Algorithm |
|:--:|:----------|:-----:|:----------|
| P1 | **Power timing** | [0-1]×4 | Angular velocity peak detection per joint. Order: lower_body → core → upper_arm → wrist. Output is normalized frame indices. |
| P2 | **Explosive power** | 0-100 | Wrist acceleration maximum in normalized coordinates. Key: max_accel in normalized space ≈ 0.1-1.0; score = max_accel × 15. |
| P3 | **Relaxation score** | 0-100 | Jerk (d³p/dt³) of wrist trajectory during backswing phase. Lower jerk = smoother = more relaxed. mean_jerk ≈ 0.01-0.2; score = clamp(100 - mean_jerk×500). |
| P4 | **Jump height** | 0-60cm | Hip center Y-coordinate baseline vs peak, with torso-pixel→cm ratio. Must distinguish real jumps from weight-shift. |
| P5 | **Chain efficiency** | 0-100 | Timing correctness (60%) + energy transfer (40%) across 5-joint chain. |

**Key tuning guide — normalized coordinate scaling:**

MediaPipe's `PoseLandmarker` outputs normalized coordinates (0-1 range). All power metrics operate in this space and need scaling factors calibrated per sport:

```python
# Normalized coordinate reality:
#   - Wrist max velocity  : ~0.3-0.6 (normalized units/frame)
#   - Wrist max accel     : ~0.1-1.0 
#   - Hip Y range         : ~0.02-0.15 (standing vs jump)
#   - Trajectory jerk     : ~0.01-0.2

# Scaling rules of thumb (initial calibration):
EXPLOSIVE_SCALE = 15           # max_accel * 15 → 0-100
RELAXATION_SCALE = 500         # mean_jerk * 500 subtracted from 100
JUMP_TORSO_CM = 50.0           # torso length in cm for pixel-to-cm
```

**Pitfall — acceleration detection for teaching videos:** Most sports technique/slow-motion videos have much lower accelerations than live play. Explosive power coming out as 2-10 for a teaching video is EXPECTED and normal. Don't try to re-normalize for slow-mo — the score is comparative within the same video type.

### 4. Body part analysis (2 dimensions)

| ID | Dimension | Sub-fields |
|:--:|:----------|:-----------|
| B1 | **Foot** | Landing type (forefoot/flat/heel), weight trajectory heatmap |
| B2 | **Palm/grip** | Palm direction (6 classes), grip tension (0-100 via backswing wrist micro-vibrations) |

### Part 2: 12 Extended Dimensions (A7-A12, P6-P9, B3-B4)

These are the **professional-grade** indicators, added to the base 16 to form a 28-dim engine. Defined in `annotation_extensions.py`. They power the professional evaluator's injury risk detection, L7 benchmark comparison, and tactical analysis.

**Coordinate system criticality:** MediaPipe normalised coordinates have Y increasing downward. All functions that reference "vertical" must use `(0, 1)` not `(0, -1)`. Failures produce 0-value or inverted metric values silently.

#### Joint Angles Extended (A7-A12)

| ID | Metric | Pro Benchmark | Amateur Typical | Code Key |
|:--:|:-------|:-------------:|:---------------|:---------|
| A7 | **Shoulder internal rotation** | 80-120° | 30-60° | `compute_shoulder_internal_rotation()` |
| A8 | **Pelvic tilt** (lateral/anterior/asymmetry) | lateral<5°, asymmetry<10 | 5-15° | `compute_pelvic_tilt()` |
| A9 | **Neck forward tilt** | <10° | 15-25° | `compute_neck_tilt()` |
| A10 | **Ankle dorsiflexion** | 30-45° | <20° | `compute_ankle_dorsiflexion()` |
| A11 | **Forearm pronation/supination** | pronation 60-90° | 20-45° | `compute_forearm_rotation()` |
| A12 | **Non-racket hand height** | height_ratio 0.2-0.5 | <0.2 | `compute_non_racket_hand()` |

**Pitfall — A7 shoulder internal rotation in 2D video:** From a monocular 2D camera view, true 3D shoulder rotation cannot be measured. The workaround approximates it as `arm_elevation_angle × forearm_angle`. This produces reasonable relative scores but is NOT a true biomechanical internal rotation measurement. Document this limitation.

#### Power Mechanics Extended (P6-P9)

| ID | Metric | Pro Benchmark | Code Key |
|:--:|:-------|:-------------:|:---------|
| P6 | **Shoulder rotation speed** | 6-12 rad/s | `compute_shoulder_rotation_speed()` |
| P7 | **Hip rotation speed** | 300-600°/s | `compute_hip_rotation_speed()` |
| P8 | **Power consistency** | >85/100 | `compute_power_consistency()` |
| P9 | **Toe/heel impact ratio** | forefoot landing | `compute_toe_heel_impact()` |

**Pitfall — P7 spin speed from 2D losing phase unwrapping:** `np.unwrap()` can produce massive jumps when hip angles cross 180°/0° boundaries. The fix is to detect >90° frame-to-frame angular changes and clamp rather than unwrap, then use P85 percentile instead of max to exclude single-frame noise.

```python
# Pattern: P85 percentile for speed metrics
sorted_vel = np.sort(ang_vel_deg)
p85_idx = int(len(sorted_vel) * 0.85)
p85_vel = sorted_vel[min(p85_idx, len(sorted_vel)-1)]
return round(float(p85_vel), 1)
```

#### Body Parts Extended (B3-B4)

| ID | Metric | Pro Benchmark | Risk Levels | Code Key |
|:--:|:-------|:-------------:|:------------|:---------|
| B3 | **Bilateral coordination** | >80/100 | — | `compute_bilateral_coordination()` |
| B4 | **Knee valgus (Q-angle)** | <2° | <3°🟢 / 3-8°🟡 / >8°🔴 | `compute_knee_valgus()` |

**Pitfall — B4 knee valgus angle from 2D projection:** True knee valgus is a 3D measurement (tibia deviation from the mechanical axis in the frontal plane). From a single camera view, we approximate it using the perpendicular distance of the knee from the hip→ankle line. This underestimates valgus in some camera angles. The risk categories (<3°/3-8°/>8°) are calibrated conservatively — if the approximate method says "high risk", the true behavior is definitely high risk.

```python
# Knee deviation from hip→ankle line (2D approximation)
ha_vec = ankle - hip
perp_dist = |cross(ha_vec, knee-hip)| / |ha_vec|
valgus_deg = degrees(atan(perp_dist / |ha_vec|))
```

---

## Amateur vs Professional Evaluation Dual-Track

**Design philosophy:** Same 28-dim annotation, different abstraction levels for different user segments.

### Amateur Evaluator (AmateurEvaluator)

**File:** `agents/amateur_evaluator.py`

Converts 28-dim annotation into **8 intuitive dimensions (E1-E8)**, each 0-100 with a label and advice string:

| ID | Dimension | Weight | Data Source |
|:--:|:----------|:------:|:------------|
| E1 | 💪 **发力效果** | 0.15 | P5×0.5 + P2×0.3 + P6(norm)×0.2 |
| E2 | 🎯 **击球精准** | 0.15 | Elbow angle proximity to 165° + shoulder→130° + A12 |
| E3 | 🫳 **动作松弛** | 0.10 | P3 relaxation score (direct) |
| E4 | 🦵 **下肢力量** | 0.15 | Knee angle 70-90° scoring + jump height + A10 |
| E5 | 🏃 **步法速度** | 0.15 | P9 landing type scoring + centroid trajectory |
| E6 | 🧘 **身体控制** | 0.10 | A8 pelvic asymmetry (inverse) + hip angle std |
| E7 | 🔄 **腰部转体** | 0.10 | A5 twist scoring + P7 hip rotation speed |
| E8 | 📊 **动作一致** | 0.10 | P8 power consistency |

**Output format:**
```json
{
  "ratings": {
    "E1": { "score": 62, "label": "良好", "advice": "发力链基本完整..." },
    ...
  },
  "overall": {
    "score": 58.3, "grade": 4, "grade_label": "L4 中级",
    "description": "...", "summary": "..."
  }
}
```

**Price tier:** Free tier (4-dim simplified) / ¥29/month (full 8-dim + category breakdown + training plan).

### Professional Evaluator (ProEvaluator)

**File:** `agents/pro_evaluator.py`

Generates a complete 6-section diagnostic report from the 28-dim annotation:

| Section | Content | Data Source |
|:--------|:--------|:------------|
| **S1** | Full 28-dim raw data with interpretation | Base 16 + Extended 12 |
| **S2** | L7 professional benchmark comparison (14 metrics) | Hardcoded benchmarks for 6 action types |
| **S3** | Injury risk assessment (6 risk factors) | B4, A8, P9, B2, A9, P4 |
| **S4** | Motion economics (Q1-Q3: energy/redundancy/recovery) | Skeleton trajectory + phase analysis |
| **S5** | Tactical analysis (T1-T3: placement/variation/rhythm) | Joint angle variability + timing |
| **S6** | Overall grade + 8-week training plan | Weighted composite |

**L7 benchmarks per action type (built-in):**

| Metric | Clear | Smash | Drop | Net | Lift | Serve |
|:-------|:-----:|:-----:|:----:|:---:|:----:|:-----:|
| chain_efficiency | 88 | 92 | 85 | 82 | 80 | 75 |
| explosive_power | 82 | 95 | 55 | 40 | 50 | 30 |
| shoulder_rotation(rad/s) | 8.5 | 10.5 | 5.5 | 3.0 | 4.0 | 2.0 |
| hip_rotation(°/s) | 450 | 550 | 320 | 200 | 250 | 150 |
| jump_height(cm) | 28 | 45 | 15 | 5 | 3 | 0 |
| consistency | 88 | 82 | 92 | 90 | 88 | 95 |
| shoulder_internal_rot(°) | 75 | 110 | 40 | 20 | 30 | 15 |
| bilateral_coordination | 85 | 80 | 88 | 90 | 85 | 92 |

**Price tier:** ¥399/assessment (single deep diagnosis), ¥599 (with 2-week follow-up).

**Integration pattern:** The evaluators are bridged to FastAPI via `label_integration_v2.py`:

```python
@router.post("/api/assess/amateur")  # 8-dim amateur report
@router.post("/api/assess/pro")      # 28-dim professional report
```

Both endpoints accept video upload and return JSON. The amateur one is suitable for web/mobile clients. The professional one generates enough data for PDF report generation.

---

## Motion Phase Segmentation

Detect 5 phases from elbow angle curve:

```
[Preparation] → [Backswing] → [Impact] → [Follow-through] → [Recovery]
```

**Algorithm:**

```python
def detect_motion_phases(elbow_series, fps):
    velocity = np.abs(np.gradient(elbow_series))
    
    # 1. Preparation end: first frame where velocity exceeds threshold
    active = np.where(velocity > 1.0)[0]
    prep_end = int(active[0]) if len(active) > 0 else len(elbow_series)//8
    
    # 2. Backswing end: elbow angle minimum (max flexion)
    search_start = max(prep_end, n_frames//8)
    min_elbow = int(np.argmin(elbow_series[search_start:]) + search_start)
    
    # 3. Impact: fastest acceleration after minimum
    post_min = elbow_series[min_elbow:]
    post_vel = np.gradient(post_min)
    post_acc = np.gradient(post_vel)
    impact_offset = int(np.argmax(post_acc[:30]))
    impact_idx = min(min_elbow + impact_offset, len(elbow_series)-1)
    
    # 4. Follow-through end: velocity settles
    post_impact = velocity[impact_idx:]
    settled = np.where(post_impact < 0.5)[0]
    follow_end = (settled[0] + impact_idx) if len(settled) > 2 else min(impact_idx+15, len(elbow_series)-1)
```

**Pitfall — amplitude bias in simple min/max detection:** `np.argmin(elbow_series)` finds the global minimum, but if the video starts mid-motion (e.g. player already in backswing), the phase detection is off. Always search from at least frame 10-15% forward.

---

## Quality Checker Design

```python
class QualityChecker:
    def check(self, annotation) -> dict:
        # 1. Completeness — all 16 dims present
        # 2. Physical plausibility — angles in [0,180], jump<120cm, power/relaxation in [0,100]
        # 3. Angle range sanity — elbow mean < 175°, knee not locked
        # 4. Power timing sequence — must be ascending (lower→core→upper→wrist)
        # 5. Domain consistency — "jump" sub-skill without jump detection = warn
        # 6. Statistical outlier detection — z-score > 3σ vs existing same-type annotations
        
        score = 100 - len(issues)*15 - len(warnings)*5
        return {"quality_score": score, "passed": len(issues)==0, ...}
```

---

## ML Model Training (Measured Results, 2026-06-01)

### Phase 1: RandomForest baseline (104 samples, 16-dim) — COMPLETED
```
Model: RandomForest Classifier
Input: 16-dim handcrafted features (6 joint angles + 5 power metrics + 2 body parts + 3 meta)
Output: Grade L3-L6 (4-class)
Samples: 104 (teaching videos, 7 action types)
Accuracy: 71.4% (5-fold CV)
Model: models/phase1_randomforest.pkl (1.1MB)
```

### Phase 2: GBDT + DL comparison (172→276 samples, 360p) — COMPLETED
```
GBDT (GradientBoostingClassifier):
  Input: 34-dim parsed features
  Samples: 172 (L3-L6)
  CV Accuracy: 76.1% (+4.7% over Phase 1)
  Test Accuracy: 91.4% (overfit warning: train_acc=100%)
  Model: models/phase2_gradientboostingclassifier.pkl (1515KB)

ST-GCN: 45.7% — failed (data too small)
GAT+TCN: crashed — MPS incompatibility
JointTCN: 5.7% — failed (data too small)
```

### Phase V2: B站 1,884 samples, 28-dim direct-from-skeleton (2026-06-01) — **COMPLETED 🏆**

**Breakthrough result:** After switching from 360p YouTube data (172 samples) to 1,884 B站 720p/4K skeleton files, accuracy jumped from 76.1% CV to **97.0-97.6% CV** (98.1% test). The key insight was **direct skeleton-to-feature extraction** (compute joint angles + biomechanical metrics on-the-fly from raw MediaPipe landmarks) rather than parsing text-based annotation output.

| Model | Old (360p, 172 samples) | New (B站 v2, 1,884 samples) | Improvement |
|:------|:-----------------------:|:---------------------------:|:-----------:|
| RandomForest | Test 77.1% CV 66.1% | **Test 97.9% CV 97.6%** | +31.5% |
| **GradientBoosting** | Test 91.4% CV 76.1% | **Test 98.1% CV 97.0%** | +20.9% |
| Ensemble (RF+GB) | Test 91.4% | **Test 98.1%** | +6.7% |
| Regression (Explosive Power) | N/A | **R²=1.000** | new |

**Top 5 features (new model):**
1. P2_explosive (29.5%) ← explosion power
2. P6_sh_ir_speed (22.4%) ← shoulder internal rotation speed
3. P7_hip_rot_speed (9.1%) ← hip rotation speed
4. A8_pelvis_std (4.2%) ← pelvic stability
5. B1_foot (3.7%) ← footwork activity

**New model files (v2):**
```
models/phase1_randomforest_v2.pkl    (1.2MB)
models/phase2_gbdt_v2.pkl            (1.3MB)
models/phase2_ensemble_v2.pkl        (5.0MB)
models/phase2_regression_v2.pkl      (14.7MB)
```

**Key change in approach:** The v2 training script (`scripts/batch_feature_train_v2.py`) reads B站 skeleton JSON files directly, computes 28 joint-angle + biomechanical features from raw MediaPipe landmarks in a single pass (no separate `build_features.py` step needed), then trains all models in one pipeline. This eliminates the text-parsing bottleneck and the 172-sample ceiling.

**How to run the v2 pipeline end-to-end:**
```bash
cd ~/Desktop/2026AIAPP/badminton-label-system
# 1. Download B站 videos (via bili_download_v2.py or manually)
# 2. Clip action segments
python3 scripts/bili_clip_pipeline.py
# 3. Skeleton tracking
python3 scripts/skeleton_pipeline.py
# 4. Feature extraction + training (single script!)
python3 scripts/batch_feature_train_v2.py
# 5. Copy models to serving project
cp models/phase*_v2.pkl ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/models/
```

**Data volume milestone:** Crossed from <200 to 1,884 samples — the threshold where deep learning (ST-GCN, GAT+TCN) becomes viable. Next milestone: 5,000+ for self-supervised pretraining.

**Architectural implication:** With 1,884 samples, the old recommendation "GBDT until 500+" is now superseded. Traditional ML still wins at batch inference speed (<1ms per sample), but DL architectures should be re-evaluated at this data scale.

## Clip Quality Audit & Training Data Curation

After collecting and skeleton-tracking B站 clips, always run a quality audit to filter out fragmented clips that degrade model training.

### Duration-based quality filter (proven at 1,887 clips)

Teaching videos (e.g. 李宇轩 杀球教程) are dominated by **short camera-switch fragments** (2-4s) that contain only part of a motion, not a complete action cycle. Pure-action demo videos (影子赵剑华, 闪跃) have naturally longer clips (10-20s).

| Source | Pre-filter | After ≥5s filter | Duration threshold effect |
|:-------|:----------:|:-----------------|:-------------------------|
| Pure action (影子, 闪跃) | 145 | 140 (97%) | Minimal loss |
| Teaching mixed (李宇轩, 刘辉) | 1,742 | 565 (32%) | Removes 68% fragments |
| **Total** | **1,887** | **497 (26%)** | **26% pass rate** |

**Rule of thumb:** For teaching videos, expect only ~1/4 of clips to be usable after filtering.

### training_clips/ directory

After filtering, the clean clips go into `data/training_clips/{skill_id}/`:

```python
# Run after each batch collection:
python3 scripts/filter_training_clips.py
# Output: data/training_clips/clear_fh/ (80 clips) 
#                        clear_bh/ (72 clips)
#                        smash_stand/ (51 clips)
#                        smash_jump/ (40 clips)
#                        footwork_def/ (241 clips)
#                        drop_stand/ (13 clips)
```

Each subdirectory is named by skill ID matching the training system. Clips are hard-linked (not copied) to save space. Minimum clip: 5 seconds, minimum file size: 0.5MB for 720p, 4MB for 4K.

### Training on filtered data

The v2 model (1,884 samples, 98.1% accuracy) was trained on **unfiltered** clips. A model trained on only the 497 high-quality clips plus 145 pure-action clips should achieve even higher accuracy. When adding new training data:

1. Always filter to ≥5s clips first
2. Consider separating pure-action clips as a held-out test set
3. File-size-based filtering is a reasonable proxy when ffprobe is slow for batch operations

See `references/clip-quality-audit-2026-06.md` for the full 1,887-clip audit methodology.

### Phase 3: Full pipeline architecture — BUILT
### Phase 3: Full pipeline architecture + DTW correction — BUILT
```
Components ready, awaiting 500+ samples for DL upgrade:
  ✅ RTMPose extractor (agents/rtmpose_extractor.py) — +30% accuracy over MediaPipe
  ✅ DTW correction engine (agents/dtw_correction_engine.py) — 8 benchmarks, Chinese coaching text
  ✅ 8 action benchmarks (data/benchmarks/) — best L5-L6 samples per type
  ✅ Feature builder (scripts/build_features.py) — 276→172→34 dims (superseded by batch_feature_train_v2.py)
  ✅ GAT+TCN architecture designed but MPS-crashed (scripts/gat_tcn_trainer.py)
  ✅ UAT full pipeline: 61/61 tests pass (dual 35 + pipeline 26)
  ✅ Mini-program DevTools integration (webapp.py patched with /api/v1/* routes)
```

**Full results:** See `references/phase2-3-training-results.md` for measured model numbers, DL architecture failure details, DTW correction design, UAT coverage, and B站 download limitations. For the complete model architecture recommendation (LLM vs traditional ML vs specialized models for each pipeline stage), see `references/model-architecture-comparison.md` — covers DeepSeek/Gemini/Qwen vs RTMPose/VideoMAE/CoSTFormer, measured GBDT 76.1% vs failed DL attempts, and the multi-stage pipeline design rationale. For the v2 breakthrough results (1,884 samples, 98.1% accuracy), see `references/v2-batch-feature-train-2026-06-01.md`. For the skill-to-video mapping and miniprogram integration pattern, see `references/skill-video-miniprogram-integration.md`. For the V2 FastAPI integration pattern (28-dim direct-from-skeleton assess_with_annotation, V2 model structure, 5-min cache), see `references/fastapi-integration-pattern.md`.

**Key architectural decision:** At <200 samples, traditional ML (GBDT 76.1%) >> deep learning (ST-GCN 45.7%, JointTCN 5.7%, GAT+TCN crash). **At 1,884 samples, GBDT achieves 98.1% test accuracy** with 28 direct-from-skeleton features — this is the production model. DL architectures (ST-GCN etc.) should be re-tested at this scale; the 45.7% failure was a data-volume issue, not an architecture issue.

### DTW Joint Correction Engine

New component (`agents/dtw_correction_engine.py`): aligns user skeleton to benchmark via Dynamic Time Warping, then computes per-joint angle deviations and maps them to coaching language templates:

```
User skeleton → DTW align to L5-L7 benchmark → per-joint deviation → correction text
```

Key design:
- 10 evaluation joints with correction templates in Chinese
- Severity levels: 🟢 <12° / 🟡 12-20° / 🔴 >20°
- Benchmarks built from best-available samples per action type (8 types built)
- Nan-safe path handling for DTW edge cases

---

## Project Directory Structure

```
sports-labeling-system/
├── agents/
│   ├── collector_agent.py      # Agent 1 v2: dual-track采集 (amateur+professional)
│   ├── detector_agent.py       # Agent 2 v2: 帧差法动作检测+片段裁剪
│   ├── skeleton_agent.py       # Agent 3: 骨骼追踪 (MediaPipe)
│   ├── annotation_engine.py    # Agent 4: 28维标注引擎 (846行)
│   ├── annotation_extensions.py # 12维扩展指标 (960行)
│   ├── amateur_evaluator.py    # 业余8维评估器 (300行)
│   ├── pro_evaluator.py        # 专业28维报告 (1655行)
│   └── quality_checker.py      # Agent 6: 质量审核 (310行)
├── scripts/
│   ├── amateur_pipeline.py     # Phase 1全流程: collect→detect→annotate→report
│   ├── pipeline.py             # 原版专业视频流水线
│   ├── qr_generator.py         # 球馆二维码生成器 (8预设深圳球馆)
│   ├── batch_annotate.py       # 批量标注
│   └── train_phase1.py         # RandomForest训练
├── api_server.py               # FastAPI异步标注服务 (/api/v1/*)
├── docs/
│   ├── PRD_产品方案.md
│   ├── ANNOTATION_SCHEMA.md    # 28维标准+计算代码
│   ├── EVALUATION_SYSTEM_WHITEPAPER.md
│   ├── CLASSIFICATION_23CATS_v2.md
│   ├── TASK_ROADMAP.md         # 全宇宙最强路线图 (104→10000+)
│   └── API_SPEC_UPLOAD.md      # 小程序上传API规范
├── data/
│   ├── raw_videos/{amateur,professional}/{category}/
│   ├── clips/                  # 裁剪后的动作片段
│   ├── annotations/{skill_id}.json
│   ├── skeleton_features/{id}.npy
│   ├── video_manifest.json     # 视频指纹+元数据索引
│   ├── user_uploads/           # 用户上传视频
│   └── venue_qrcodes/          # 球馆二维码+manifest
├── models/
│   └── phase1_randomforest.pkl
└── templates/
    └── annotation_template.json
```

### Phase 1 Roadmap (TASK_ROADMAP.md)

Four-phase progression toward "world's best" badminton evaluation:

| Phase | Samples | Model | Accuracy | Timeline |
|:------|:-------:|:------|:--------:|:---------|
| Phase 1 | 104→500 | RandomForest→ST-GCN | 71%→80% | 1-2 months |
| Phase 2 | 500→2,000 | ST-GCN + TSN | 80%→88% | 3-5 months |
| Phase 3 | 2,000→5,000 | VideoMAE + BadmintonFormer | 88%→92% | 6-12 months |
| Phase 4 | 5,000→10,000+ | BadmintonFormer (self-supervised pretrain) | 92%+ | 12+ months |

Key Phase 1 deliverables (completed): collector v2, detector v2, amateur_pipeline, api_server, qr_generator, API spec, roadmap doc.

See `references/fastapi-integration-pattern.md` for the V2 FastAPI integration pattern — 28-dim direct-from-skeleton assess_with_annotation, V2 model structure (flat model+scaler vs old nested), 5-min model cache, deployment workflow, and failure modes.

See `references/badminton-pipeline-deployment.md` for the badminton-specific deployment instance (project paths, calibrated thresholds, agent inventory, environment notes, data stats). Absorbed from `badminton-labeling-pipeline` skill.
See `references/phase2-3-training-results.md` for the measured Phase 2 GBDT/ST-GCN comparison, Phase 3 GAT+TCN architecture, DTW correction engine benchmarks, and B站 download limitations.
See `references/mediapipe-global-timestamp.md` for the global timestamp accumulator technique (critical for batch processing 1,000+ clips — avoids 71min of per-clip landmarker init).
See `references/p0-video-collection-pipeline.md` for a complete P0 walkthrough (21 videos → 1,417 action clips via v2 scene+silence detection → MediaPipe skeletal tracking).
See `references/bili-v2-batch-download-2026-06-01.md` for the 13-video multi-category B站 batch download record (smash/drop/clear/footwork, including 4K/60fps sources) — a concrete example of the v2 downloader in action.
See `references/clip-quality-audit-2026-06.md` for a full 1,887-clip quality audit, teaching-vs-pure-action breakdown, the `data/training_clips/` filtering strategy (→497 high-quality clips), and the MimicMotion deployment attempt (model download failure route diagnostics).

### Detector MediaPipe import resilience

The detector v2 (`detector_agent.py`) uses OpenCV frame-diff motion detection as the primary method, with MediaPipe as an optional enhancement. The import must be defensive because MediaPipe can raise `AttributeError` (not just `ImportError`) when some submodules are unavailable:

```python
# RIGHT — catches both ImportError and AttributeError:
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    _HAS_MEDIAPIPE = True
except (ImportError, AttributeError):
    mp = None; mp_pose = None; _HAS_MEDIAPIPE = False
```

### Apple Silicon MPS deep learning — operations that trigger crashes

When training PyTorch models on Apple Silicon (M1/M2/M3 with `torch.device("mps")`), certain tensor operations trigger MPS-specific memory format errors. These are NOT code bugs — they're MPS backend limitations:

**Known crash patterns:**

1. **`softmax` after broadcast expansion** — `tensor.unsqueeze() + broadcast → softmax` triggers `RuntimeError: Invalid memory format ChannelsLast3d`. The MPS backend cannot handle softmax on tensors that went through unsqueeze+broadcast in the same forward pass.

2. **`einsum` with >3 tensors** — `torch.einsum("nhdvt,nhvut->nhdut", ...)` on MPS produces dimension mismatches when tensors exceed MPS internal block alignment.

3. **`matmul` with heavily reshaped tensors** — MPS `matmul` with `unsqueeze()` on both operands produces dimension errors absent on CUDA/CPU.

**Mitigations (in priority order):**

1. Use `torch.device("cpu")` for training <1000 samples — negligible overhead, guaranteed stability.
2. Replace `einsum` with explicit `matmul` + `permute` + `reshape` chains.
3. Avoid `unsqueeze()` near `softmax()` — reshape into a stable shape beforehand.
4. Setting `PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.0` limits memory but doesn't fix softmax/einsum bugs.

**GBDT (traditional ML) is the correct choice at <500 samples anyway**, so MPS issues are only relevant when data crosses the DL threshold.

### NaN in skeleton NPYs from MediaPipe

First-frame skeleton NPYs can contain NaN values (`np.nan` in the float32 array). This causes:
- `min()/max()` returns NaN → downstream range checks fail
- `np.gradient()` propagates NaN to velocity/acceleration metrics → all zeros
- JSON serialization of NaN → `ValueError: Out of range float values`

**Fix:** Always check `np.isnan(sample).any()` on first load, and use `np.nan_to_num(sample, nan=0.0)` to zero-fill. Track `nan_count` in metadata so quality checks can flag low-confidence frames.

### Skeleton agent argument convention

The skeleton agent uses **positional arguments**, not `--flags`:

```bash
# CORRECT:
python agents/skeleton_agent.py <video_path> <output_dir> <video_id>

# WRONG (parses --video literally as the video path):
python agents/skeleton_agent.py --video path.mp4 --output path.npy
```

### Pipeline manifest sync

The `amateur_pipeline.py` report mode reads from an internal counter, not from `video_manifest.json`. After collector downloads, the report may show `已采集: 0` even though videos exist on disk and are recorded in the manifest. Fix: read manifest counts directly in report mode.

### v2 Scene + Silence Detection (precision extraction)

The old approach used a single ffmpeg scene detection threshold (0.35), which treated entire tutorial segments as single clips — a 695s video produced 1 clip. The v2 method combines **low-threshold scene detection (0.15)** with **audio silence detection** to split instructional videos into precise "talking" vs "pure action demonstration" segments. Result: 147 clips → 1,417 clips (9.6× improvement).

**Algorithm:**
```python
# Step 1: Scene boundaries at low threshold
scenes = detect_scenes(video, threshold=0.15)  # catches talking↔demo transitions

# Step 2: Silence boundaries
silence_starts, silence_ends = detect_silence(video, noise="-30dB", min_silence=0.5s)

# Step 3: Merge all boundaries, remove tiny gaps (<3s)
boundaries = set(scenes) | set(silence_starts) | set(silence_ends) | {0.0, duration}
merged = remove_tiny_gaps(sorted(boundaries), min_gap=3.0)

# Step 4: Classify each segment
for start, end in segments:
    seg_type = classify(duration=end-start):
        if 3s ≤ duration ≤ 60s  → action_demo  ✓ extract
        if 60s < duration ≤ 180s → talking      💬 save for transcript context
        if duration < 3s          → too_short    ✗ skip
        if duration > 180s        → oversized    ✗ skip
```

**ffplay silence detection command:**
```bash
ffmpeg -i video.mp4 -af "silencedetect=noise=-30dB:d=0.5" -f null - 2>&1 | grep -E "silence_(start|end)"
```

**Pitfall — background-process concurrent writes:** When running 3+ parallel yt-dlp downloads writing to the same parent directory, their outputs can interleave in the terminal log. Use separate subdirectories per category (`raw_videos/{category}/`) so downloads don't conflict, and always verify with a final `find` count before trusting the download log output.

**Pitfall — Whisper transcript files not found:** When running whisper via `python3 -m whisper`, the output JSON is saved to the CWD (current working directory), NOT to `--output_dir` if that path doesn't exist or is wrong. Always use absolute paths for `--output_dir` and verify the output directory exists before running. Better yet, extract audio first (first 300s, mono 16kHz) and transcribe that — it's 10× faster and avoids the CWD issue:
```bash
ffmpeg -y -i input.mp4 -t 300 -vn -ar 16000 -ac 1 preview.wav
python3 -m whisper preview.wav --model tiny --language zh --output_dir /abs/path/transcripts
rm preview.wav
```

**Pitfall — Whisper + numpy≥2 crash:** `openai-whisper` depends on `numba` which is incompatible with `numpy≥2.0`. If the environment has numpy 2.x, whisper will crash with `numpy.core.multiarray failed to import`. Fix:
```bash
pip install "numpy<2"
```
Check with `python3 -c "import whisper; print(whisper.__version__)"` before running the batch.

### ffmpeg scene detection on 4K/60fps video — keyframe mode

**Problem:** ffmpeg scene detection (`select='gt(scene,0.12)',showinfo`) on a 3840×2160 31-minute video times out after 300s even with `scale=1280:720` downsampling. The full decode+filter requires processing ~47,000 frames at 4K resolution.

**Fix — keyframe-only detection (`-skip_frame nokey`):**

```bash
# BEFORE (times out on 4K):
ffmpeg -i input.mp4 -vf "scale=1280:720,select='gt(scene,0.12)',showinfo" -vsync vfr -f null -

# AFTER (100x faster, same accuracy for scene boundaries):
ffmpeg -skip_frame nokey -i input.mp4 -vf "select='gt(scene,0.12)',showinfo" -vsync 0 -f null -
```

`-skip_frame nokey` decodes only I-frames (keyframes), typically 1/25 of total frames. For scene detection this is **equally accurate** because scene changes always insert a keyframe. The `-vsync 0` prevents frame duplication from the sparse input.

**Important:** `-skip_frame nokey` must come BEFORE `-i`, not after. The correct position is:
```bash
ffmpeg -skip_frame nokey -i input.mp4 -vf "..."
```
Putting it after `-i` silently ignores it.

For 4K video, combine with `scale`:
```bash
ffmpeg -skip_frame nokey -i 4K_video.mp4 -vf "scale=1280:720,select='gt(scene,0.12)',showinfo" -vsync 0 -f null -
```

Tested on: 3840×2160 31min (47,000 frames) → <30s vs 300s+ timeout.

### ffmpeg silence detection timeout on 4K/large video

**Problem:** `silencedetect` also times out on 640MB 4K videos at the default 120s timeout, because ffmpeg decodes the entire video stream even though silence detection only needs audio.

**Fix — extract audio first (no video decode):**

```bash
# BEFORE (decodes video + audio, can timeout on 4K):
ffmpeg -i 4K_video.mp4 -af "silencedetect=noise=-30dB:d=0.3" -f null -

# AFTER (extract audio only, ~5s even for 4K):
ffmpeg -i 4K_video.mp4 -vn -c copy audio_tmp.aac
ffmpeg -i audio_tmp.aac -af "silencedetect=noise=-30dB:d=0.3" -f null -
rm audio_tmp.aac
```

The `-vn -c copy` extracts the audio stream without any video decoding. For videos >200MB, always use this two-step approach. For smaller videos, the single-pass works fine.

---

## Pitfalls

### Mini-program WXML: JS expressions are forbidden in templates

WeChat mini-program WXML templates do NOT support JavaScript expressions inside `{{ }}` interpolation — only data references. This means `new Date()`, `.filter()`, `.map()`, `.find()`, ternary operators with function calls, and regex matching all crash at compile time:

```html
<!-- ❌ CRASHES: "Bad value: unexpected token" -->
<view>{{new Date(c.issued_at * 1000).toLocaleDateString()}}</view>

<!-- ✅ CORRECT: pre-compute in JS, bind as data -->
<!-- In JS: cert.issued_date = new Date(cert.issued_at*1000).toLocaleDateString() -->
<view>{{c.issued_date}}</view>
```

**Fix pattern:** In the Page's `.js` file, after fetching data from the API, map over the array and pre-compute any derived values before calling `setData()`. Use `...spread` to keep original fields while adding computed ones.

### Detector threshold calibration — false-positive avalanche at low thresholds

The detector v2's initial parameters (`motion_threshold=0.15`, `min_frames_between_hits=20`) caused **26 false-positive action clips from a single 10MB amateur video** (should produce 3-8 clips). This happens because low motion thresholds detect every weight-shift and walking step as a "hit".

**Calibrated parameters** (set in `detector_agent.py` `DETECTION_PARAMS` dict):
```python
DETECTION_PARAMS = {
    "motion_threshold": 0.20,      # +33% stricter (was 0.15)
    "min_frames_between_hits": 30, # +50% wider spacing (was 20)
    "clip_before_sec": 2.0,        # shorter lead-in (was 3.0)
    "clip_after_sec": 3.0,         # shorter follow-through (was 4.0)
    "min_clip_frames": 60,         # 2s minimum
    "max_clip_frames": 300,        # 10s maximum
}
```

**Validation:** After the first detector run, spot-check 3-5 clips from different categories. If >50% of clips from amateur videos look like "person walking" or "person adjusting grip" rather than actual strokes, increase `motion_threshold` by 0.05 and re-run. True badminton strokes produce distinct frame-diff spikes that survive higher thresholds.

MediaPipe outputs coordinates normalized to [0,1]. All velocity/acceleration/jerk metrics need scaling factors calibrated against REAL data, not guessed.

**The correct approach:** Run the pipeline on 5-10 videos first, print raw intermediate values (velocity magnitudes, jerk values, hip Y ranges), THEN set scaling factors. Do NOT guess scaling factors and then wonder why all scores are 0 or 100.

```python
# Debug output to print BEFORE scaling:
print(f"Max acceleration in normalized space: {max_accel:.6f}")
print(f"Mean jerk: {mean_jerk:.6f}")
print(f"Hip Y range: {hip_y_range:.4f}")
```

### Action phase detection failure modes

The 5-phase motion detection relies on elbow angle curve shape. Three common failure modes:

1. **Video starts mid-action** → `np.argmin` picks a global min from the first frame. Fix: skip first 10-15% of frames.
2. **Slow-motion video** → velocity is half what it would be at normal speed. Fix: apply FPS-aware normalization, not fixed thresholds.
3. **No clear impact event** (e.g. footwork-only video) → no acceleration spike → `impact_frame` falls behind. Fix: for non-stroke actions, use hip-velocity peaks instead.

### NaN propagation kills metrics silently

MediaPipe returns NaN for any frame where the person isn't detected (brief occlusion, person exits frame edge). If you compute `np.diff()` on an array with NaN, the `gradient()` propagates NaN to the entire result. Always clean NaN before derivative computation.

### Phase 1 model with <50 samples

With fewer than 50 samples, the RandomForest cross-validation accuracy is unstable (±15-20%). The model is still useful for:
- **Feature importance analysis** (which joint angles matter most)
- **Baseline for future comparison**
- **Predicting "within 1 grade level"** rather than exact level

Don't claim "model is trained and accurate" at 23 samples. Say "model has learned feature patterns, needs 5x more data for stable accuracy."

See `references/training-milestones.md` for the full training history across sample counts (23→104 samples, 60.0%→71.4%).
See `references/large-scale-collection.md` for a complete walkthrough of the 25→107 video acquisition + batch annotation cycle.

### Patching the model into the serving project

After each retraining cycle, copy the model and restart the backend:
```bash
cp models/phase1_randomforest.pkl ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/models/
# Then restart badminton-coach-ai backend
```

---

## Data Volume → Model Quality (Measured)

| Samples | Model | Accuracy | Date | Notes |
|:-------:|:------|:--------:|:-----|:------|
| 104 | RandomForest (16dim) | 71.4% CV | Phase 1 | 7 action types, teaching videos only |
| 172 | GBDT (34dim) | **76.1% CV** | Phase 2 | 34 parsed features, 172 usable samples |
| 174 | ST-GCN (skeleton) | 45.7% | Phase 2.5 | 1.7M params → overfit at small scale |
| 174 | GAT+TCN (skeleton) | CRASH | Phase 2.5 | MPS `ChannelsLast3d` incompatibility |
| 171 | JointTCN (skeleton) | 5.7% | Phase 2.5 | Loss=NaN, class imbalance |
| 500 (target) | GBDT + GAT+TCN | ~82-85% | Phase 3 | Requires amateur data pipeline or miniapp uploads |
| 2,000 (target) | PoseC3D + CoSTFormer | ~88% | Phase 4 | Multi-angle data needed |
| 5,000+ (target) | BadmintonFormer pre-train | 92%+ | Phase 5 | Self-supervised on unlabeled video pool |

**Key insight:** At <200 samples, traditional ML (GBDT 76.1%) >> deep learning (ST-GCN 45.7%, JointTCN 5.7%). Three architectures, one conclusion: DL needs 500+ samples. GBDT is the production model until data volume crosses that threshold.

## B站视频采集与质量评估

### B站视频发现流程 (Browser→BVID→yt-dlp)

当需要从B站补充特定类别视频时，使用以下流程：

**Step 1: Browser搜索目标类别（因B站搜索API返回数据有限）**
```python
# 用browser工具直接搜索B站，从搜索结果中提取BVID
browser_navigate("https://search.bilibili.com/all?keyword=羽毛球+杀球+教学+慢动作&order=click")
browser_console('(()=>{...return BVIDs})()')  # 从页面提取所有BV号
```

**Step 2: API验证视频质量**
```bash
# 用B站公开API检查时长和标题（匿名访问，无需cookie）
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=BVxxx" | python3 -c "
import json,sys; d=json.load(sys.stdin)
if d['code']==0: print(d['data']['title'], d['data']['duration'])
"
```

**Step 3: 检查画质（选择1280×720+的视频）**
- 优先选择竖屏(720×1280) vs 横屏(1280×720)：横屏更适合全身骨骼追踪
- 闪跃运动频道提供3840×2160 4K视频，骨骼追踪率可达99.8%
- 影子传说频道(Shadow SlowMo)提供1280×720教科书级慢动作

**Step 4: 批量下载**
```bash
yt-dlp --cookies data/bilibili_cookies.txt -f "bestvideo[height<=2160]+bestaudio" \
  -o "data/raw_videos/{category}/%(title).50s_{bvid}.%(ext)s" \
  --merge-output-format mp4 "https://www.bilibili.com/video/{BVID}"
```

**Step 5: Pipeline提取动作片段 → 骨骼追踪**
```bash
python3 scripts/bili_clip_pipeline.py     # 场景+静音检测→切出动作clip
python3 scripts/skeleton_pipeline.py       # MediaPipe Pose骨骼追踪
```

### 已验证的B站优质羽毛球教学频道

| 频道 | 画质 | 内容 | 骨骼追踪质量 |
|:-----|:----:|:-----|:-----------:|
| **闪跃运动** (Flash Sports) | **3840×2160** 🏆 | 反手/杀球教学 | **99.8%** 🔥 |
| **影子传说** (Shadow SlowMo) | 1280×720 ✅ | 赵剑华/肖杰教科书式慢动作 | 93-99% ✅ |
| **大G羽毛球** (刘辉教练授权) | 1280×720/竖版 | 杀球/吊球/高远球系统课 | 需筛选横版 |
| **李宇轩教练** | 1920×1080@60fps | 杀球/步法/发力系统课 | 讲解夹杂动作，需切分 |
| **腿腿羽毛球** | 竖版 | 短小精悍慢动作片段 | 宜作为补充 |
| **汤老师羽毛球** | 待检查 | 网前/搓球慢动作 | 待评估 |

**新发现的高画质来源（2026-06-01）：**
- **桃田贤斗贴地飞行** (BV11Gt4zTEKs) — 2880×2160 @60fps，步法/脚部细节顶级
- **李宗伟步法解析** (BV1os411K7es) — 1280×720，10分钟完整步法示范
- **李宇轩30分钟步法课** (BV1X24y1B7v2) — 1920×1080 @60fps
- **闪跃4K杀球发力** (BV1Ht4y1P7Qs) — 3840×2160，31分钟杀球系统教学
- **正手高远球纯净版** (BV1xj411t7hN) — 纯动作示范，零讲解，适合骨骼追踪

### 画质对骨骼追踪的实证影响

实测对比（同Pipeline、同MediaPipe模型）：

| 分辨率 | 人体占比 | 追踪率 | 关节定位精度 | 适用性 |
|:------:|:--------:|:------:|:-----------:|:------:|
| 360×640 (YouTube) | ~120px | 98.0% | ±15° | 勉强可用 |
| **1280×720 (B站)** | ~300px | 93-99% | **≤5°** ✅ | 模型训练级 |
| **3840×2160 (4K)** | ~500px | **99.8%** 🔥 | **≤2°** 🏆 | 基准级 |

**结论：同一个Pipeline，从360p升级到720p，关节精度提升3倍（±15°→≤5°）。**
——建议所有模型训练用B站720p/4K数据，旧360p仅用作对比基线。

### B站Cookie提取（关键坑）

B站cookie在macOS上**不能**用 `--cookies-from-browser chrome` 自动提取：
- SESSDATA/DedeUserID/bili_jct 是 Chrome 的 HttpOnly 加密 cookie
- yt-dlp 和 browser-cookie3 都无法解密
- **唯一可靠方法：** 装"Get cookies.txt LOCALLY"扩展 → 打开B站 → 点击导出 → 保存为 `data/bilibili_cookies.txt`
- 验证cookie有效性后，有效期一般6个月

验证cookie是否有效：
```bash
curl -s -b cookies.txt "https://api.bilibili.com/x/web-interface/nav" | python3 -c "import json,sys; d=json.load(sys.stdin); print('OK' if d.get('data',{}).get('isLogin') else 'NO')"
```

### B站批量下载模式对比

**v1 — 单类别按需下载**
```bash
# 适合补一个类别
yt-dlp --cookies cookies.txt -f "bestvideo[height<=2160]+bestaudio" \
  -o "data/raw_videos/{category}/%(title).50s_{BVID}.%(ext)s" \
  --merge-output-format mp4 "https://www.bilibili.com/video/{BVID}"
```

**v2 — 多类别批量下载器**
创建批量下载脚本时，用元组列表定义下载队列：`(BVID, category_subdir)`。适合一次性补全多个缺失类别：

```python
DOWNLOAD_LIST = [
    # === 杀球 (smash) ===
    ("BV1Ht4y1P7Qs", "smash"),   # 闪跃4K 31min
    ("BV1aHweeCEVB", "smash"),   # 李宇轩杀球 14min
    # === 吊球 (drop) ===
    ("BV1Hz4y1A7XQ", "drop"),    # 大G吊球 5min
    # === 高远球 (clear) ===
    ("BV1xj411t7hN", "clear"),   # 正手高远球纯净版
    ...
]
```

关键注意事项：
- 使用 `%(title).50s_{BVID}.%(ext)s` 命名模板确保唯一可追溯
- 每个类别写入独立子目录 `raw_videos/{category}/`
- 先通过 `curl -s "https://api.bilibili.com/x/web-interface/view?bvid=$BV"` 匿名验证标题和时长
- 用 `-f "bestvideo[height<=2160]+bestaudio/best[height<=2160]"` 获取最高画质
- 4K视频文件可达640MB以上，注意磁盘空间

使用 `%(title).50s_{bvid}.%(ext)s` 模式确保文件名的唯一性和可追溯性：
- `.50s` 截断长标题
- BVID确保唯一可回溯
- yt-dlp自动选择最佳格式 + 合并

### 多数据源融合策略

当新旧数据来源分辨率不同时：
1. **旧360p数据保留** — 已跑完骨骼追踪（1,562 clips / 366,277帧）
2. **720p+4K数据覆盖同类别** — 骨骼追踪后提取特征替换旧数据
3. **特征级融合** — 低分辨率数据标注时加置信度权重
4. **训练时按分辨率分组Cross-validation** — 确保模型不过拟合低分数据

### Batch processing: B站720p+4K data into existing pipeline

The skeleton pipeline automatically picks up new clips via `_progress.json`:
```bash
# 1. Download B站 videos into raw_videos/bilibili/
# 2. Clip them with bili_clip_pipeline.py
# 3. Rerun skeleton_pipeline.py — it detects new clips not yet in _progress.json
python3 scripts/bili_clip_pipeline.py     # → data/processed_videos/bilibili/
python3 scripts/skeleton_pipeline.py       # → data/skeletons/bilibili/
# 4. Extract features
python3 scripts/build_features.py
# 5. Retrain model
python3 scripts/train_phase1.py
```

### Prioritising B站 sources

Order of priority when looking for badminton technique videos:
1. B站 横屏 1280×720+ 慢动作/教学视频 → best for model training
2. B站 竖屏 Video (手机版) → usable for skeleton but footwork obscured
3. YouTube Chinese content → fallback when B站 has gaps
4. Pre-existing training animation library → fastest (zero download time)

### 类别覆盖追踪表

```
类别         360p(旧)    720p B站    4K B站    状态
─────────────────────────────────────────────────────
反手(smash_fh)  ❌        ❌         ✅(闪跃)  需补充720p
杀球(smash)     ❌        🆕         🆕        进行中
吊球(drop)      ❌        🆕         ❌        进行中
高远球(clear)   ❌        🆕         ❌        进行中
步法(footwork)  ❌        🆕         ❌        进行中
网前(net)       ❌        ❌         ❌        下一批
```

可复用脚本：
- `scripts/bili_batch_download.py` — 批量下载器模板（填入BVID即可）
- `scripts/bili_clip_pipeline.py` — B站视频场景切割Pipeline

## Data Collection Strategy (yt-dlp batch)

### Dual-track: amateur vs professional sources

The collector v2 (`collector_agent.py`) supports two data tracks with separate keyword templates:

**Amateur keywords (Chinese):** 业余羽毛球比赛, 球友对打, 爱好者实战, 俱乐部比赛, 深圳业余羽毛球, 初学者动作

**Amateur keywords (English):** amateur badminton match, recreational play, beginner practice, club game

**Professional keywords** — mapped per action type (clear_fh, smash_jump, drop_fh, etc.) with Chinese + English pairs in `PROFESSIONAL_KEYWORDS` dict.

### Collector v2 features

- **Manifest-based dedup:** SHA256 fingerprint of first 1MB per video → `data/video_manifest.json`
- **Data label tracking:** Each video tagged `amateur` or `professional`
- **Batch mode:** `--batch config.json` with per-task source/count/keywords
- **Stats:** `--stats` shows breakdown by data_label

### Motion-based detection (detector v2)

Uses **frame-difference motion scoring** (no MediaPipe needed for detection pass):

1. Sample every 3rd frame, compute normalized diff vs prev frame
2. Find peaks above μ + 1.5σ → hit candidates
3. Confirm local maxima within ±5 frame window
4. Extract clips: hit_frame − 3s to hit_frame + 4s

**Parameters:** `motion_threshold=0.15`, `min_frames_between_hits=20`, `clip_before_sec=3.0`, `clip_after_sec=4.0`

### Full pipeline orchestration

```bash
cd ~/Desktop/2026AIAPP/badminton-label-system

# Single command: collect → detect → annotate → report
python scripts/amateur_pipeline.py --mode full --count 10

# Step-by-step:
python scripts/amateur_pipeline.py --mode collect --count 20
python scripts/amateur_pipeline.py --mode detect
python scripts/amateur_pipeline.py --mode annotate
python scripts/amateur_pipeline.py --report
```

### Source mix: reuse + download

Best strategy for reaching 15+ videos per category in minimal time:

1. **Reuse existing demo clips first** — training animation libraries (`training_animations/`) contain pre-clipped technique demos. Copy them to `raw_videos/{category}/` (check filename dedup).
2. **Download supplementary videos** — use yt-dlp with Chinese keywords targeting teaching/slow-motion content. Categories sorted by urgency.

### yt-dlp batch downloading patterns

```bash
# Base command pattern for Chinese badminton teaching videos:
yt-dlp --socket-timeout 20 --max-filesize 80M \
  "ytsearchN:羽毛球 <technique> 教学 [慢动作]" \
  -o "category/keyword_%(id)s.%(ext)s"
```

**Known failure modes:**

- **Format not available.** YouTube may not offer `best[height>=480]` for all matched videos. Drop the `-f` flag entirely to let yt-dlp pick the default format. The `--max-filesize` alone is sufficient control.
- **Timeout.** Some searches/sources are slow. Use `--socket-timeout 15-20` and run as background processes with `terminal(background=true, notify_on_complete=true)`.
- **Chinese keywords return Taiwan/cantonese results.** That's fine — the accents are irrelevant for skeleton analysis.
- **`.part` files accumulate.** Background downloads interrupted by timeout leave partial files. Always clean them before counting: `find raw_videos -name '*.part' -delete`.
- **Multiple formats per video.** yt-dlp may download audio+video separately (`f251.webm` + `f313.webm`). Deduplicate by extracting the video ID (11-12 char alphanumeric after `_`) rather than counting files. Use `grep -v '\.part$'` to exclude partials, then group by ID.

### Batch size calibration

With 30-120 min per category (search + download + deduplicate), a 7-category collection cycle completes in 2-4 hours. Run multiple categories in parallel (each as a `background=true` terminal process), up to 5 concurrent — yt-dlp connection pooling handles it.

### China network limitations (critical)

- **B站 downloads require authentication.** Free formats (360p+) return "format not available" without login.
- **B站 cookie auto-extraction fails on macOS:** `yt-dlp --cookies-from-browser chrome` extracts 3344 cookies but does NOT extract SESSDATA/DedeUserID/bili_jct (login-critical cookies). These are Chrome's encrypted HttpOnly cookies that neither yt-dlp nor browser-cookie3 can decrypt. The only reliable method is manual export via the "Get cookies.txt LOCALLY" Chrome extension — open B站, click extension, save, then `yt-dlp --cookies /path/to/cookies.txt ...`.
- **YouTube Chinese content as fallback:** When B站 fails, YouTube with Chinese search keywords works. Validated channels: 刘辉羽毛球 (Liu Hui), 影子羽毛球, 肖杰, 李玲蔚. Use `ytsearch10:羽毛球 <action> 教学 中文` or direct channel URLs. YouTube format 18 (360p, ~5-30MB per 5-min video) works without auth.
- **YouTube is blocked in China.** From Chinese ISPs without VPN, searches timeout. Only use YouTube fallback from a non-China server or VPN-connected machine.
- **`yt-dlp` search keyword language matters.** `ytsearch:业余羽毛球` searches YouTube (blocked). Use explicit B站 URLs or `--cookies` for B站 sources.
- **`.part` files accumulate.** Interrupted/timeout downloads leave 0-byte `.part` and `.ytdl` files. Always clean before counting: `find raw_videos -name '*.part' -o -name '*.ytdl' -delete`.

## Batch Annotation

### PYTHONPATH pitfall (critical)

The `batch_annotate.py` script imports agents from `agents/`:
```python
sys.path.insert(0, os.path.join(PROJECT_ROOT, "agents"))
from skeleton_agent import SkeletonAgent
```

**If run with the wrong Python interpreter, it crashes.** Two root causes:

1. **System Python (conda/anaconda).** Anaconda's Python 3.12 ships matplotlib 3.10+ which has an `ImportError: initialization failed` from `from matplotlib._path import ...`. This is a pre-existing conda environment bug — it happens because Anaconda's matplotlib was compiled against a different numpy ABI than the one on disk.  
   **Fix: use the venv Python from `workspace/badminton-coach-ai/venv/bin/python3`**, which has the correct mediapipe + numpy version pair.

2. **`PYTHONPATH=""` does NOT fix Anaconda pollution.** The Anaconda path is baked into the conda Python binary itself, not in the environment variable. Setting `PYTHONPATH=""` has zero effect. The only reliable fix is to use the **absolute path** to the hermes venv Python:
   ```bash
   /Users/Mac/.hermes/hermes-agent/venv/bin/python3 scripts/batch_whisper.py
   # NOT: python3 scripts/batch_whisper.py  ← may resolve to anaconda python in background processes
   ```

**Diagnosis:**
```bash
# Check which python you're actually getting:
which python3
# If it shows /opt/anaconda3/bin/python3, you're in the wrong environment

# Check if anaconda paths are in sys.path:
python3 -c "import sys; print([p for p in sys.path if 'anaconda' in p])"

# Check mediapipe import path:
python3 -c "import mediapipe; print(mediapipe.__file__)"
# Expected: ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages/mediapipe/
# Bad:      /opt/anaconda3/lib/python3.12/site-packages/mediapipe/
```

**Why background processes hit this:** When you type `python3` in an interactive terminal, the shell resolves to `~/.hermes/hermes-agent/venv/bin/python3` (because that's first in PATH). But `terminal(background=true)` spawns a subprocess whose PATH may resolve differently — `/opt/anaconda3/bin` comes before the venv in the background shell's PATH resolution. This is a **shell init vs subprocess init difference**, not a PATH env var problem.
   
   **Always use absolute venv path for background processes.** `/Users/Mac/.hermes/hermes-agent/venv/bin/python3` bypasses PATH resolution entirely.

3. **`PYTHONPATH=\"\"` does NOT fix Anaconda pollution.** The Anaconda path is baked into the conda Python binary itself, not in the environment variable. Setting `PYTHONPATH=\"\"` has zero effect. The only reliable fix is to use the **absolute path** to the hermes venv Python:

### Batch annotation rate

On Apple M1 Pro, the pipeline processes ~3-4 videos/minute (including MediaPipe initialization + skeletal tracking + annotation + QC). This means ~100 videos takes ~25-30 min.

Expect the first video to be slower (~8-15s) because MediaPipe initializes the XNNPACK delegate on first use. Subsequent videos are 4-6s each.

### Model re-training cycle

After batch annotation, always:
1. Copy the new model to the main project: `cp models/phase1_randomforest.pkl ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/models/`
2. Restart the backend for the new model to take effect
3. Report the before/after accuracy delta

## CRITICAL RULE — NO FILE DELETION WITHOUT PERMISSION

**This overrides any perceived urgency, disk-full situation, or "just helping" instinct. Never delete files without explicit user consent.**

The user (老卢) has a strict zero-tolerance policy on file deletion. NEVER delete any file, cache, Docker artifact, temp file, or project data without explicit permission. This includes: Trash/recycle bin, system caches (brew, pip, Docker), Docker containers/images/networks, temp files and test outputs, project scratch files and build artifacts — any file anywhere for any reason.

If disk space is full: report the amount to the user and ask what to do. Do NOT take cleanup action yourself.

**Asking pattern:**
> "磁盘还剩X GB空间。需要我清理什么吗？" — then wait for explicit instructions.

This is the user's **last trust agreement** (2026-05-30). A third violation means permanent loss of trust. This rule is embedded in MEMORY.md and USER.md and injected every session.

---

## 16-Category Video Sourcing for the Labeling Pipeline

When expanding from 7 base categories to 23 (127 sub-skills), target new-category videos by priority:

### Video Collection Plan (P0-P3)

| Tier | Categories | Sub-skills | Target videos | Strategy |
|:----:|:-----------|:----------:|:------------:|:---------|
| 🟢 **P0** | serve, drive, lob, block, serve_return, transition | 27 | 15+/category | Direct search by action name. YouTube/B站 abundant. |
| 🟡 **P1** | spin, special (behind/crotch/dive), combination | 14 | 5-10/category | Moderate scarcity. May need multiple source combos. |
| 🔵 **P2** | pacing, tactics, tactics_pattern, conditioning, singles, doubles | 30 | 3-5/category | Multi-shot concepts, not single-action. Search drills. |
| ⚪ **P3** | flexibility | 4 | Skip | Not camera-detectable. Use text-based guidance instead. |

### Chinese Search Keywords per P0 Category

| Category | Chinese keywords |
|:---------|:----------------|
| 🚀 发球 | `羽毛球 发球 慢动作 正手发球 反手发网前` |
| ⚡ 平抽挡 | `羽毛球 平抽 防守 正反手平抽 慢动作` |
| 🔝 挑球 | `羽毛球 挑球 正手挑球 反手挑球 慢动作` |
| 🖐️ 挡网 | `羽毛球 挡网 正手挡网 反手挡网 慢动作 教学` |
| 🔄 接发球 | `羽毛球 接发球 技术 推压` |
| 🌉 过渡球 | `羽毛球 过渡球 中场过渡 被动` |

For all P0 categories, search Chinese B站 first, fall back to YouTube Chinese content. Aim for 15+ videos per category to match base-7 coverage.

### Processing pipeline for new categories

```bash
# 1. Collect videos (adjust count per priority tier)
python scripts/amateur_pipeline.py --mode collect --category serve --count 15
python scripts/amateur_pipeline.py --mode collect --category drive --count 15
# ... one per P0 category, run in parallel background processes

# 2. Detect and clip action segments
python scripts/amateur_pipeline.py --mode detect

# 3. Batch annotate all new clips
PYTHONPATH="$PWD/agents:$PYTHONPATH" \
  ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/venv/bin/python3 scripts/batch_annotate.py

# 4. Retrain model with expanded dataset
~/Desktop/2026AIAPP/workspace/badminton-coach-ai/venv/bin/python3 scripts/train_phase1.py

# 5. Copy model to main project and restart
cp models/phase1_randomforest.pkl ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/models/
```
 

```python
import math

def _clean_nan(obj):
    """Recursive NaN/Inf scrubber — CRITICAL: json.dumps crashes on NaN"""
    if isinstance(obj, dict):
        return {k: _clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [_clean_nan(v) for v in obj]
    elif isinstance(obj, float):
        return None if (math.isnan(obj) or math.isinf(obj)) else obj
    return obj
```

Always call `_clean_nan()` as the LAST transform before returning from your API endpoint.

### Critical pitfalls

- **MediaPipe VIDEO mode detectors are single-use.** Creating a `SkeletonAgent` once and reusing it fails silently on the second video. Create fresh per request.
- **Pickle version mismatch crashes silently.** If the RandomForest was trained with sklearn 1.8.0 but served from 1.6.1, predictions may silently be wrong. Pin sklearn or retrain on the serving env.
- **NaN in JSON = 500 Internal Server Error.** FastAPI's response serializer raises `ValueError: Out of range float values are not JSON compliant` if any NaN reaches json.dumps. The traceback points to `starlette/responses.py`, not your code — misleading.
- **curl file upload syntax.** `-F "file=@path.mp4"` (with `@`) sends the file. Without `@`, FastAPI receives a string and returns `422: Expected UploadFile`.
- **First request is slow (8-15s).** MediaPipe initializes XNNPACK delegate on first use. Subsequent requests are 4-6s. Expected.

### Batch annotation (pre-downloaded video pool)

```python
# Import agents directly, don't subprocess
sys.path.insert(0, AGENTS_DIR)
from skeleton_agent import SkeletonAgent
from annotation_engine import AnnotationEngine
from quality_checker import QualityChecker

# Inject source metadata before annotation
meta["skeleton_path"] = npy_path
meta["annotation_id"] = sub_skill_id
meta["source"] = {"platform": "youtube", "title": skill_id, "crop_range_sec": [0, 30]}

# Always add default=str to json.dump for NumPy types
json.dump(ann, f, ensure_ascii=False, default=str)
```

### UAT regression test (6-action smoke)

Pick one video per major action category, assert all return status=ok + non-null grade. Expected ranges for teaching videos: grade L4-L6, explosive power 0.2-9.2, relaxation 66-99, jump height 12-75cm.

Teaching videos produce LOWER explosive power (2-9) than live play (40-80). This is EXPECTED — don't re-normalize for slow-mo.

### Multi-person batch assessment (upgrade-to-pro feature)

Design an endpoint that accepts multiple videos from different people, evaluates each independently, grades them, and automatically recommends upgrading to professional-level assessment (¥399) when a person reaches L6+:

```python
@router.post("/api/annotation/multi-assess")
# Accept List[UploadFile]
# Per-person: annotation engine → grade
# If grade >= 6: pop modal "已达到专业水准！推荐专业版评估"
# Return: {results: [{person, grade, metrics}], upgrade_recommendations: [...]}
```

See `references/fastapi-integration-pattern.md` for the full endpoint design, upgrade logic table, and frontend display pattern (multi-person results grid with per-row upgrade buttons).

## This User's Communication Preferences (老卢)

**Style:** SHORT responses. No justification — just do it. Structured output (tables, emoji, checklists) over prose. Direct answers, not plans.

**Data policy:** CRITICAL RULE above. Never delete anything without explicit permission.

