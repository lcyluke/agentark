# Doubles Analysis Workflow — Session Reference

## Architecture (4 files)

```
badminton_coach/
├── doubles_estimator.py      # Multi-person (4) MediaPipe skeleton extraction
├── doubles_analysis.py        # Formation/rotation/tactic/coordination scoring
├── amateur_training.py        # +16 doubles skills API + training advice
└── video_privacy.py           # Face blur + audio strip + skeleton overlay
```

## DoublesEstimator key decisions

- **num_poses=4**: MediaPipe PoseLandmarker max, but realistically detects 2-3 people per frame on broadcast footage
- **min_detection_confidence=0.4**: Lower than singles (0.5) because players are smaller and more occluded
- **Player assignment**: Frame-by-frame spatial heuristic (left/right halves → front/back within each team). No tracking — assignment can flip on cross-court rallies
- **Court zones**: 4 zones defined by x=0.5 (net line) and y=0.5 (mid-court). `left_front`, `left_back`, `right_front`, `right_back`

## Formation classification thresholds (empirical from 30fps footage)

- Attack: y_diff between teammates > 0.12 AND x_diff < 0.15
- Defense: x_diff between teammates > 0.12
- Front court: both players y < 0.4
- Window=5 frames for stability majority voting

## Scoring — signal sources

| Dimension | Frame-level input | Window | Scoring formula |
|-----------|------------------|--------|-----------------|
| flat_drive | wrist landmark movement | 5 frames | min(100, movement*30 + mid_front_ratio*0.4 + 30) |
| net_kill | front zone occupancy | full video | min(100, front_pct * 0.5 + 20) |
| serve_receive | first-3-second frames | full video | min(100, first_3s_pct * 0.5 + 30) |
| back_court_smash | attack formation % | full video | min(100, attack_pct * 0.6 + 20) |
| defense_clear | defense formation % | full video | min(100, defense_pct * 0.5 + 25) |
| rotation_timing | rotations detected | full video | clip(50 + freq*10 - 20, 0, 100) |
| continuous_attack | max attack streak | full video | min(100, streak * 2 + 20) |
| court_coverage | unique court zones | full video | min(70, zone_count * 17.5) |

## Known limitations

1. **Detection collapse on broadcast footage**: If players occupy < 5% of the frame (standard TV coverage), MediaPipe detects 0-1 people. Report this as "insufficient data" rather than fabricating scores
2. **Occlusion**: Two players side-by-side, one partially behind the other — the occluded player is frequently missed. The occlusion-mask fallback (black-out detected person and re-detect) helps ~40% of cases
3. **No role tracking**: A1/A2 assignment is frame-by-frame. During rapid cross-court rallies, the assignment can swap mid-clip. A proper tracker (DeepSORT, Kalman) would fix this but adds complexity
4. **No ball tracking**: The current system infers everything from body positions and movement. It cannot detect who hit the ball, which is the optimal ground truth for event segmentation

## Upgrade path for production

1. Replace spatial heuristic with **ByteTrack** or **DeepSORT** for stable player IDs
2. Add **ball detection** (YOLOv8 trained on overhead court views) for ground-truth event timing
3. Replace formation thresholds with a **small classifier** (MLP on teammate position features)
4. Use **YOLOv8-pose** instead of MediaPipe for better small-object detection
