# Phase 1 Model Training Milestones

## Accuracy vs Sample Count (实测数据)

| Samples | Algorithm | Accuracy | MAE | Date |
|:-------:|:---------:|:--------:|:---:|:----|
| 23 | RandomForest | 60.0% | 0.40 | 2026-05-30 |
| 104 | GBDT (GradientBoosting) | **71.4%** | 0.38 | 2026-05-31 |

**Key findings:**

1. **GBDT consistently outperforms RandomForest** on this 18D feature set (6 joints × 3 stats). GBDT test accuracy was 71.4% vs RF's 61.9% at 104 samples. Always train both and pick the better one.
2. **Feature importance (104 samples, top 6):** `elbow_mean > elbow_range > knee_mean > knee_range > hip_std > elbow_std`. The elbow is by far the most discriminative joint for grade classification.
3. **Regression models (power/relaxation) remain unreliable** at this sample size (R² ~30%). They need 500+ samples to become useful. For now, report them as "estimated" with explicit caveat.
4. **Grade distribution at 104 samples:** L4 (25), L5 (62), L6 (17) — heavily skewed to mid-range because teaching videos show intermediate-to-advanced players. Beginner (L1-L3) and elite (L7-L9) are absent. This means the classifier is only valid for L4-L6 range.

## Retraining procedure

```bash
cd ~/Desktop/2026AIAPP/badminton-label-system
cp models/phase1_randomforest.pkl ~/Desktop/2026AIAPP/workspace/badminton-coach-ai/models/
```

Then restart the badminton-coach-ai backend for the new model to take effect:

```bash
lsof -ti:8000 | xargs kill -9 2>/dev/null; sleep 1
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
./venv/bin/python3 -m uvicorn badminton_coach.webapp:app --host 0.0.0.0 --port 8000
```

## Current bottleneck

The 18D feature space (mean/std/range of 6 joints) captures static posture differences but NOT motion quality. To get past 75%, the system needs:
- Feature engineering improvements (e.g. velocity-based features)
- More samples in underrepresented grades (L1-L3, L7-L9)
- Moving to Phase 2 (LSTM on skeleton sequences) when 2000+ samples exist
