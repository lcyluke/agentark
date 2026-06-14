# FastAPI Integration — V2 Labeling Engine (28-dim direct-from-skeleton)

How to serve the **V2 28-dim annotation pipeline** as a FastAPI endpoint,
plus pitfalls:

1. **NaN → 500 Internal Server Error** (JSON serialization crash)
2. **V2 model structure** (model + scaler + optional feature_names — NOT nested `{grade_model:{model:...}}`)
3. **Global cached models** (5-min TTL via `load_v2_model()` to avoid re-loading on every request)
4. **Manual skeleton quantisation**: Anaconda path pollution demands absolute-venv Python

## Module structure (label_integration.py V2)

```python
badminton_coach/label_integration.py
    ├── _vec3(a,b) / _angle_between(v1,v2)    # vector math helpers
    ├── _calc_joint_angles(lms)                # 10 joint angles from 33 landmarks
    ├── _extract_v2_features_from_landmarks()  # 28-dim from landmark sequence
    ├── load_v2_model(model_name)              # cached pickle load, 5min TTL
    ├── assess_with_annotation(...)             # unified: skeleton→28dim→V2 model
    └── get_annotation_api_endpoint()           # FastAPI router + /api/annotation/models
```

## V2 model structure (different from V1!)

The old model was `{grade_model: {model: ..., data: ...}, explosive_model: {...}, relaxation_model: {...}}`.
The V2 model is flat:

```python
# V2 model pickle structure:
{
    'model': sklearn.Classifier,  # RandomForest/GradientBoosting/Voting
    'scaler': StandardScaler(),    # fitted scaler (must transform before predict!)
    'feature_names': [...]         # 28-dim feature names (optional, only on phase1_randomforest_v2)
}
```

**Do NOT attempt to use old `load_model()` on V2 files — the key structure is incompatible.**

## V2 assess_with_annotation (simplified — no agent import needed)

The V2 version **does not need the annotation_engine** at all. It directly:
1. Runs `SkeletonAgent.process_video()` on the uploaded video
2. Calls `_extract_v2_features_from_landmarks()` to get 28-dim features
3. Builds a numpy feature vector and runs it through V2 models

```python
def assess_with_annotation(video_path, skill_id="unknown",
                           action_type="unknown", use_model=True):
    result = {"skill_id": skill_id, "action_type": action_type, "status": "ok"}
    
    # 1. Skeleton tracking
    from skeleton_agent import SkeletonAgent
    agent = SkeletonAgent()
    landmarks_seq, meta = agent.process_video(video_path)
    if not landmarks_seq or len(landmarks_seq) < 5:
        result["status"] = "insufficient_frames"
        return result
    
    # 2. Extract 28-dim V2 features (direct from landmarks, no annotation_engine)
    v2_features = _extract_v2_features_from_landmarks(landmarks_seq)
    result["v2_features"] = v2_features
    
    # 3. Build feature vector and run models
    FEATURE_NAMES_28 = [...]  # same order as batch_feature_train_v2.py
    X = np.zeros((1, len(FEATURE_NAMES_28)), dtype=np.float32)
    for j, name in enumerate(FEATURE_NAMES_28):
        X[0, j] = v2_features.get(name, 0)
    
    if use_model:
        ens = load_v2_model("phase2_ensemble_v2")  # best model
        if ens:
            X_s = ens['scaler'].transform(X)
            result["model_prediction"]["predicted_grade"] = int(ens['model'].predict(X_s)[0])
    
    return _clean_nan(result)
```

## Model caching pattern (5-min TTL)

Prevents re-loading pickle files on every request while still allowing hot-reload for model updates:

```python
_model_cache = {}
_CACHE_MAX_AGE = 300  # 5 minutes

def load_v2_model(model_name: str) -> Optional[dict]:
    global _model_cache
    cached = _model_cache.get(model_name)
    if cached and (time.time() - cached['loaded_at']) < _CACHE_MAX_AGE:
        return cached['data']
    
    path = os.path.join(MODELS_DIR, f"{model_name}.pkl")
    if not os.path.exists(path): return None
    
    with open(path, 'rb') as f:
        data = pickle.load(f)
    _model_cache[model_name] = {'data': data, 'loaded_at': time.time()}
    return data
```

## 28-dim feature to V2 model feature names mapping

The V2 models expect exactly these 28 features in this order:

```python
FEATURE_NAMES_28 = [
    # A1-A6 Joint angles (6 mean values)
    'A1_elbow_mean', 'A2_shoulder_mean', 'A3_knee_mean', 'A4_hip_mean',
    'A5_waist_twist_mean', 'A6_wrist_mean',
    # P1 Power timing (4 timing values)
    'P1_timing_0', 'P1_timing_1', 'P1_timing_2', 'P1_timing_3',
    # P2-P5 Power mechanics (4 values)
    'P2_explosive', 'P3_relaxation', 'P4_jump', 'P5_chain',
    # B1-B2 Body parts (3 values)
    'B1_foot', 'B2_palm_dir', 'B2_grip',
    # A7-A12 Extended joints (4 values + 2 stats)
    'A7_sh_ir_mean', 'A8_pelvis_mean', 'A8_pelvis_std', 'A10_ankle_mean',
    'A12_nr_height_mean',
    # P6-P9 Extended power (5 values)
    'P6_sh_ir_speed', 'P7_hip_rot_speed',
    'P8_consistency', 'P9_impact_type', 'P9_impact_force',
    # B3 Coordination (1 value)
    'B3_coordination',
]
```

The `_extract_v2_features_from_landmarks()` function in `label_integration.py` computes each of these from raw MediaPipe landmarks using the same algorithm as `batch_feature_train_v2.py`. The key call order is:

```
landmarks_seq → per-frame calc_joint_angles() → angle_series[] + velocities[]
  → per-feature aggregation (mean, std, peak timing, velocity stats)
  → 28-dim dict → numpy array in FEATURE_NAMES_28 order → scaler.transform → model.predict
```

## V2 model verification endpoint

A `GET /api/annotation/models` endpoint helps debug whether V2 models are available:

```python
@router.get("/models")
async def list_models():
    models = {}
    for name in ["phase1_randomforest_v2", "phase2_gbdt_v2",
                  "phase2_ensemble_v2", "phase2_regression_v2"]:
        path = os.path.join(MODELS_DIR, f"{name}.pkl")
        models[name] = "available" if os.path.exists(path) else "not_found"
    return {"models": models, "features": 28, "feature_names": FEATURE_NAMES_28}
```

## Model deployment workflow

```bash
# After retraining in badminton-label-system:
cp ~/badminton-label-system/models/phase*_v2.pkl \
   ~/workspace/badminton-coach-ai/models/

# Restart backend to clear the 5-min model cache
kill $(lsof -ti:8000) && cd ~/workspace/badminton-coach-ai && \
  ./venv/bin/python3 -m uvicorn badminton_coach.webapp:app --host 0.0.0.0 --port 8000

# Verify
curl -s http://localhost:8000/api/annotation/models
# Expect: phase2_ensemble_v2: "available" (or "loaded")
```

## Failure modes (all encountered in production)

| Symptom | Root cause | Fix |
|:--------|:-----------|:----|
| 2nd+ request returns empty annotation | MediaPipe VIDEO mode detector reused | Create fresh `SkeletonAgent()` per call |
| `ValueError: Out of range float values are not JSON compliant` | NaN from undetected frames | `_clean_nan()` before every return |
| Model predicts L2 on data that clearly justifies L5 | Pickle loaded V1 model format with V2 loader | Check model filename: `_v2.pkl` or `.pkl` |
| curl returns `422: Expected UploadFile, received: <class 'str'>` | `-F "file=path.mp4"` without `@` | Use `-F "file=@path.mp4"` |
| First request takes 12s, subsequent 5s | XNNPACK delegate init + model load on first call | Expected — document in API docs |
| `AttributeError: module 'scipy' has no attribute 'io'` | scipy test mode broke numpy interop | Reinstall scipy: `pip install --force-reinstall scipy` |
| old pickle format raises ValueError for numpy BitGenerator | numpy >2 compat issue | Use hermes-agent venv python3.11, not system anaconda python3.12 |

## UAT smoke test (6-action)

When deploying, test one video per major action category. All should return `status=ok`, grades above L1:

```bash
for skill in smash clear drop net lift serve; do
  result=$(curl -s -X POST http://localhost:8000/api/annotation/assess \
    -F "file=@test_${skill}.mp4" -F "skill_id=${skill}" -F "action_type=${skill}")
  echo "$skill: $(echo "$result" | python3 -c 'import sys,json; d=json.load(sys.stdin); print(f"ok" if d.get("status")=="ok" else f"FAIL: {d.get("status")}")')"
done
```

Teaching videos produce **lower** explosive power (2-9) than live play (40-80). This is EXPECTED — re-normalizing for slow-mo would break live-play scoring.

## V2 model validation

Quick test to verify models load and infer correctly:

```bash
cd ~/workspace/badminton-coach-ai
./venv/bin/python3 -c "
from badminton_coach.label_integration import load_v2_model, FEATURE_NAMES_28
import numpy as np
ens = load_v2_model('phase2_ensemble_v2')
X = np.zeros((1, len(FEATURE_NAMES_28)), dtype=np.float32)
pred = ens['model'].predict(ens['scaler'].transform(X))[0]
print(f'✅ Dummy inference => grade={pred}')
"
```