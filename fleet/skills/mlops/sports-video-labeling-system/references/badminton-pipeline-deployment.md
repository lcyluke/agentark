# Badminton-Specific Labeling Pipeline Deployment

This is the concrete deployment instance of the `sports-video-labeling-system` for badminton. It contains project-specific paths, calibrated thresholds, environment details, and integration notes.

## Project Paths

- **Labeling system**: `~/Desktop/2026AIAPP/badminton-label-system/`
- **Main project**: `~/Desktop/2026AIAPP/workspace/badminton-coach-ai/`

## Quick Start

```bash
cd ~/Desktop/2026AIAPP/badminton-label-system

# View status
python scripts/amateur_pipeline.py --mode report

# Full pipeline (collect→detect→annotate)
python scripts/amateur_pipeline.py --mode full --count 10

# Individual stages
python scripts/amateur_pipeline.py --mode collect --count 20
python scripts/amateur_pipeline.py --mode detect
python scripts/amateur_pipeline.py --mode annotate
```

## Agent Inventory

| Agent | File | Function |
|:------|:-----|:---------|
| collector_agent.py | `agents/` | B站+YouTube collection, amateur/pro dual-track, manifest dedup |
| detector_agent.py | `agents/` | Frame-diff motion detection + clip extraction |
| skeleton_agent.py | `agents/` | MediaPipe Pose skeleton tracking, 15 keypoints → NPY |
| annotation_engine.py | `agents/` | 28-dim annotation (joint+mechanics+body+extended), 846 lines |
| annotation_extensions.py | `agents/` | 12-dim extended metrics (960 lines) |
| amateur_evaluator.py | `agents/` | Amateur 8-dim evaluation (300 lines) |
| pro_evaluator.py | `agents/` | Professional 28-dim report (1655 lines) |
| quality_checker.py | `agents/` | Basic quality check (310 lines) |

## Orchestration Scripts

| Script | Purpose |
|:-----|:-----|
| `scripts/amateur_pipeline.py` | Amateur full-pipeline orchestration |
| `scripts/pipeline.py` | Pro video pipeline |
| `scripts/build_features.py` | Annotation text → 34-dim feature matrix |
| `scripts/train_phase2.py` | GBDT/RF model training |
| `scripts/qr_generator.py` | Venue QR code generation |
| `api_server.py` | FastAPI async upload/evaluation service |

## Calibrated Parameters

### Detector thresholds

```python
DETECTION_PARAMS = {
    "motion_threshold": 0.20,       # Frame-diff threshold (calibrated down from 0.35)
    "min_frames_between_hits": 30,  # Minimum gap between hits (from 20)
    "clip_before_sec": 2.0,         # Seconds before hit
    "clip_after_sec": 3.0,          # Seconds after hit
    "min_clip_frames": 60,          # Minimum clip: 2s
    "max_clip_frames": 300,         # Maximum clip: 10s
}
```

Tuning experience: 30 clips/video too many → tightened threshold to 20% + 30-frame gap → 3-8 clips/video.

### CLI Notes

```bash
# skeleton_agent uses positional args, not flags!
python agents/skeleton_agent.py <video_path> [output_dir] [video_id]

# annotation_engine also uses positional args!
python agents/annotation_engine.py <npy_path> <meta_json_path> <action_type>
```

## Feature Parsing

Annotation output is text format (not JSON), requires regex extraction of 34-dim features:

```python
from scripts.parse_features import parse_annotation
# Old annotations (104): dict-format action field
# New annotations (172): string-format action field
# build_features.py handles both compatibly
```

Feature matrix: `data/features/X_features.npy` (172×34)

## Model Training

```bash
python scripts/train_phase2.py
```

- Phase 1: RF 71.4% (104 samples, 16-dim)
- Phase 2: GBDT 76.1% CV (172 samples, 34-dim) | Test 91.4%
- Top 5 features: Power chain (0.124), Relaxation (0.120), Jump (0.118), Explosive (0.040), Impact (0.040)
- Model: `models/phase2_gradientboostingclassifier.pkl`

## Main Project Integration

```python
# webapp.py integration:
_label_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "badminton-label-system"))
sys.path.insert(0, _label_root)
from api_server import create_api_router
app.include_router(create_api_router())
```

Endpoints:
- `POST /api/v1/upload` — upload video + async annotation
- `GET /api/v1/task/{id}` — query task
- `GET /api/v1/stats` — statistics

## Python Environment

- Labeling system: system Python 3.9 (`/Library/Developer/CommandLineTools/usr/bin/python3`)
- Main project: Hermes venv Python 3.11 (`~/.hermes/hermes-agent/venv/bin/python3`)
- sklearn installed in system Python user site-packages

## Data Statistics (as of 2026-06)

| Metric | Value |
|:-----|:---:|
| Raw videos | 130 + 27 (7+6=13 categories) |
| Legacy 7 categories | 130 (clear/drop/smash/net/footwork/drive/defense) |
| New P0 | 21 (serve/drive-flat/lob/block/serve_return/transition) |
| New P1 | 6 (counter_attack) |
| Action clips | 172 (legacy) + ~147 (new P0, v1 extracted) / pending v2 rerun |
| Skeleton tracks | 197 NPY files |
| Total annotations | 276 |
| Valid features | 172×34 |

## Known Issues

- **B站 downloads**: Chrome cookies still timeout → need proxy or manual cookies. Alternative: use existing 130 teaching videos (7 categories) can break 200 annotations.
- **Grade label imbalance**: L1 only 1 sample, L2 only 12 → current model trains L3-L6 four-class only. More amateur/beginner data needed.
- **Level labels**: Need more amateur beginner data.
