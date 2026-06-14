# Phase 1 Pipeline Build — Session Log (2026-05-31)

## Files Created

| File | Lines | Purpose |
|:-----|:-----:|:--------|
| `agents/collector_agent.py` | 270+ | Agent 1 v2 — dual-track (amateur/professional) B站/YouTube download with manifest dedup |
| `agents/detector_agent.py` | 300+ | Agent 2 v2 — frame-diff motion peak detection + clip extraction |
| `scripts/amateur_pipeline.py` | 350+ | Full pipeline orchestrator: collect→detect→annotate→report |
| `scripts/qr_generator.py` | 200+ | Venue QR code generator (8 Shenzhen default venues) |
| `api_server.py` | 550+ | FastAPI async upload service: /api/v1/upload, /task/{id}, /stats |
| `docs/TASK_ROADMAP.md` | 400+ | World's-best roadmap: 104→10,000+ samples across 4 phases |
| `docs/API_SPEC_UPLOAD.md` | 250+ | Mini-program upload API specification |
| `README.md` | — | Rewritten for Phase 1 status |

## Integration Into Main Project

`webapp.py` patched to mount the labeling API router:

```python
_label_root = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "..", "badminton-label-system"))
sys.path.insert(0, _label_root)
from api_server import create_api_router
app.include_router(create_api_router())
```

**Path resolution:** The path is `badminton_coach/webapp.py` → `..` = `badminton_coach/` → `..` = `workspace/badminton-coach-ai/` → `..` = `workspace/` → `..` = `2026AIAPP/` → `badminton-label-system`. That's three `..` levels. Verified with `os.path.abspath`.

## Pipeline Verification (End-to-End Test)

Single 10MB amateur YouTube video ran through all 4 stages:

```
collect → 10MB amateur rally video
detect → 26 action clips (5-7s each, 51MB total)
skeleton → 152-frame NPY (27KB) + meta JSON
annotate → 28-dim annotation with all 16 base + 12 extended metrics
```

**Pipeline performance:** ~15 seconds per video on M1 Pro.

## Detector v2 Implementation

Uses **frame-difference motion scoring** (no MediaPipe needed for detection pass):

1. Sample every N frames (default: 3), compute `cv2.absdiff` normalized score
2. Find peaks above μ + 1.5σ → hit candidates
3. Confirm as local maxima (±5 frame window)
4. Extract clips: hit_frame − 3s to hit_frame + 4s

**Parameters:** motion_threshold=0.15, min_frames_between_hits=20, clip_before=3s, clip_after=4s

**Threshold tuning note:** Current settings produce ~26 clips from a 7,297-frame video. For production, increase motion_threshold to 0.20 or raise sigma multiplier to 2.0 to reduce false positives (target: 3-8 clips per video).

## MediaPipe Import Fix

The detector has an optional MediaPipe import that was crashing:

```python
# BEFORE (fragile):
import mediapipe as mp
from mediapipe.tasks.python import vision  # AttributeError if not installed
mp_pose = mp.solutions.pose

# AFTER (resilient):
try:
    import mediapipe as mp
    mp_pose = mp.solutions.pose
    _HAS_MEDIAPIPE = True
except (ImportError, AttributeError):
    mp = None; mp_pose = None; _HAS_MEDIAPIPE = False
```

The detector uses OpenCV frame-diff by default and only needs MediaPipe if you want skeleton-based detection. The import is purely optional.

## Skeleton Agent Argument Convention

The skeleton agent uses **positional arguments**, not `--flags`:

```bash
# CORRECT:
python agents/skeleton_agent.py <video_path> <output_dir> <video_id>

# WRONG (fails silently — parses --video as video_path):
python agents/skeleton_agent.py --video path.mp4 --output path.npy
```

This is unlike most other agents which use argparse `--flags`. Check each agent's argument parser before calling.

## Network Limitations (China)

- **B站 downloads require authentication.** Free formats (360p+) may fail with "format not available" unless logged in. Use `--cookies-from-browser` or `--cookies`.
- **YouTube is blocked.** yt-dlp can't reach YouTube from Chinese ISPs without proxy/VPN.
- **yt-dlp search (`ytsearchN:`) defaults to YouTube.** This is why B站 searches timed out — they were searching YouTube.
- **Workaround for B站:** Use direct URLs or configure yt-dlp with `--cookies-from-browser chrome` for authenticated B站 access.

## Amateur Pipeline Manifest Sync Issue

The `amateur_pipeline.py` collector writes to `video_manifest.json`, but the pipeline's report mode reads from a different internal counter. The report showed `已采集: 0` even after successful downloads. This needs fixing — the pipeline should read manifest counts directly rather than maintaining a separate counter.

## API Server Design Decisions

- **Async task model:** Upload returns `task_id` immediately, client polls `GET /task/{id}` for results
- **Thread-based processing:** Each task spawns a daemon thread that runs the full pipeline
- **In-memory task store:** `TASKS` dict (not persistent). Tasks lost on restart — acceptable for MVP
- **No queue/worker:** Single-threaded per task. For production, swap to Celery/Redis queue
- **Upload page included:** A self-contained HTML page at `/api/v1/upload-page` for testing without the mini-program

## QR Generator Design

Generates venue-specific QR codes pointing to mini-program assessment URL:

```
POSTER LAYOUT:
████████████
████████████  ← QR code (version=None, box_size=8, error_correction=H)
████████████
████████████
  📍 福田体育公园羽毛球馆
  编号: V001
  日期: 2026-05-31
```

8 preset Shenzhen venues: Futian, Shenzhen Bay, Luohu, Baoan, Longgang, Longhua, Nanshan, Pingshan.
