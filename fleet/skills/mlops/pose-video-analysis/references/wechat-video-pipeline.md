# WeChat Video → Face Swap → Comparison Pipeline

## Overview

When the user sends a badminton training video via WeChat (auto-downloaded to `~/.hermes/cache/documents/`), run this pipeline:

1. Detect new `.mp4` files in the WeChat cache directory
2. Extract skeleton via MediaPipe PoseEstimator
3. (Optional) Run InsightFace face swap for the "your face on pro body" effect
4. Compare against pro benchmarks via `comparison_engine`
5. Return a structured evaluation report

The implementation lives at `wechat_compare_pipeline.py` in the project root, callable as:
```
python3 wechat_compare_pipeline.py <video.mp4>
python3 wechat_compare_pipeline.py --watch   # auto-detect WeChat uploads
```

## WeChat upload location

WeChat videos arrive at `~/.hermes/cache/documents/doc_*_video.mp4`. Multiple files may arrive simultaneously (the user often batches 3-6 videos in one go).

## Video metadata survey

After receiving files, survey quickly with ffprobe. Typical files: 1.7s/196KB (slow-mo snippets) to 59.7s/2.9MB (full multi-action rallies). Both portrait (720x1280, selfie) and landscape (1280x720, tripod) occur.

## Auto-detect action type from filename

Use keyword matching against the filename:
- smash/杀球/kill -> smash
- clear/高远 -> clear  
- drop/吊球 -> drop
- net/网前 -> net
- footwork/步法 -> footwork
- defense/防守 -> def
Default: 'smash'

## Pipeline steps

```python
# Skeleton extraction
skeleton = PoseEstimator().process_video(video_path)
skeleton.save_json(skel_path)

# Comparison
result = compare_full(skel_path, action_type, BENCHMARK_DIR)

# Optional face swap
if do_swap:
    FaceSwapper().swap_video(video_path, photo_path, output_path,
        max_frames=n_frames, skeleton_path=skel_json_path)
```

## Practical limits

| Orientation | Resolution | Face size | InsightFace | Comparison |
|:-----------|:----------|:---------:|:-----------:|:----------:|
| Portrait | 720x1280 | ~60-80px | Works | Works |
| Landscape | 1280x720 | ~24px | Fallback | Works |
| Slow-mo | 720x1280 | ~60px | Works | Partial only |
| Rally | 720x1280 | ~50px | Works | Best |

## File org

Copy received videos to `uploads/user_videos/` + create JSON index with filename, size_kb, duration_s, resolution.
