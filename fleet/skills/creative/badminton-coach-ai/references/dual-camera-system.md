# Dual-Camera Fusion Analysis System

Built: P0.7-⑦ (commit `ff42198`), P0.7-⑧ (commit `5c6656f`)

## Architecture

```
正面视频 → MediaPipe (XY平面) → front_metrics ─┐
                                               ├→ DTW alignment per view
侧面视频 → MediaPipe (XZ平面) → side_metrics ─┘  → fusion scoring → report
```

Each view extracts what it sees best:
- **Front**: arm symmetry, racket-arm trajectory, shoulder leveling, knee symmetry
- **Side**: torso lean angle, knee flexion, center-of-gravity forward tilt, hip-shoulder rotation

Fusion happens at the scoring and correction layer (not the skeleton layer).

## API

### Sequential Upload (WeChat mini-program compatible)

```
POST /api/dual/upload?view=front&action_type=smash
  File: front video
  → {"session_id": "abc123", "status": "front_uploaded"}

POST /api/dual/upload?view=side&session_id=abc123&action_type=smash
  File: side video
  → DualAnalysisResult (full fusion report)
```

Session TTL: 5 minutes (auto-cleanup on each new `?view=front` call).

### Actions List

```
GET /api/dual/actions
  → 7 action types: smash/clear/drop/net/footwork/feint/def
```

## Report Structure

```json
{
  "front": {
    "frames": 5,
    "detection_rate": 0.01,
    "deviations": {"右肘角度_正面": 175.6, "肩部倾斜度": 1.2, ...}
  },
  "side": {
    "frames": 5,
    "detection_rate": 0.01,
    "deviations": {"躯干前倾角": 174.0, "右膝屈曲角": 105.1, ...}
  },
  "fusion": {
    "overall_score": 74.5,
    "grade": "B",
    "symmetry_score": 94.2,
    "posture_score": 82.0,
    "kinetic_chain": 33.3,
    "rotation_quality": 84.6,
    "racket_head_speed": 6.3,
    "action": "smash",
    "benchmark": "L6"
  },
  "corrections": [
    {"joint": "右肘", "view": "正面", "severity": "高", "issue": "...", "drill": "..."}
  ],
  "training_plan": [
    {"day": 1, "phase": "基础纠错", "tasks": ["..."]}
  ]
}
```

## 6 Fused 3D-Enhanced Metrics

| Metric | Source | Range | Description |
|:-------|:-------|:-----:|:------------|
| symmetry_score | Front | 0-100 | Left-right shoulder/wrist/knee leveling |
| posture_score | Side | 0-100 | Torso lean angle (ideal 5-15°) |
| kinetic_chain | Front DTW | 0-100 | Motion fluidity vs benchmark |
| rotation_quality | Side | 0-100 | Hip-shoulder rotation amplitude |
| racket_head_speed | Front wrist | 0-100 | Normalized wrist displacement |
| overall_score | Fusion | 0-100 | Weighted composite → A/B/C/D |

## Mini-Program Pages

### pages/dual/dual.wxml — Results Display
- Action type selector (smash/clear/drop/net/footwork/def)
- Dual-column video upload (album picker)
- "录制双角度视频" entry card → navigates to camera page
- Fusion grade badge + score card
- 6-metric grid
- Dual-column deviation comparison table
- Corrections list with severity badges (高/中/低)
- 7-day training plan with day phases

### pages/camera/camera.wxml — Guided Recording
- 2-step progress bar (正面录制 / 侧面录制)
- 5 action type chips
- Per-step tip banners ("面对镜头" / "转身90°")
- 3-2-1 countdown overlay → opens `wx.chooseMedia({sourceType:['camera']})`
- Preview + retake + confirm for each angle
- Submit → sequential upload → navigate to dual page with results via `app.globalData`

## Test Recipe

```bash
# Download test video (no real badminton footage needed for smoke test)
curl -sL -o /tmp/test_front.mp4 \
  "https://github.com/intel-iot-devkit/sample-videos/raw/master/person-bicycle-car-detection.mp4"
cp /tmp/test_front.mp4 /tmp/test_side.mp4

# Step 1: Upload front
SID=$(curl -s -X POST "http://127.0.0.1:8000/api/dual/upload?view=front&action_type=smash" \
  -F "file=@/tmp/test_front.mp4" | python3 -c "import json,sys;print(json.load(sys.stdin)['session_id'])")

# Step 2: Upload side → get report
curl -s -X POST "http://127.0.0.1:8000/api/dual/upload?view=side&session_id=$SID&action_type=smash" \
  -F "file=@/tmp/test_side.mp4" | python3 -m json.tool
```

Note: the test video has low detection rate (~1%) because it's not badminton footage. A real badminton video with a full-body player will give 80%+ detection and meaningful metrics.

## Key Design Decisions

1. **Sequential upload over multi-file POST**: WeChat `wx.uploadFile` only sends one file. The two-step session pattern with 5-minute TTL was chosen over the original single-request `/api/dual/compare` (which required two files in one POST — incompatible with mini-program runtime).

2. **In-memory session store**: Simpler than Redis/file-based sessions for a single-worker setup. Sessions auto-expire at 5 minutes. If scaling to multiple workers, replace with Redis.

3. **View-level metrics over 3D skeleton reconstruction**: True 3D from two cameras requires calibrated stereo — infeasible on mobile. Instead, each view computes metrics independently from 2D MediaPipe, and fusion happens at the report layer. This is simpler, more robust, and the 2D projections already capture the diagnostically-relevant features.

4. **`wx.chooseMedia` over `<camera>` component**: The mini-program `<camera>` component renders behind other UI elements and lacks frame-access APIs. `wx.chooseMedia` opens the system camera with full native quality — simpler and more reliable.
