# End-to-End Video Motion Analysis Pipeline

A companion workflow to `pose-video-analysis` — take a badminton coaching video (from WeChat, Xiaohongshu, etc.) and run a complete analysis pipeline from ingestion to report.

## Pipeline Shape

```
Video file (MP4/HEVC, any resolution)
  |
  1. Info extraction: ffprobe for duration, fps, resolution
  |
  2. Audio extraction then Whisper transcription (Chinese voiceover)
  |
  3. MediaPipe PoseLandmarker for 33-keypoint skeleton per frame
  |
  4. Motion segmentation: wrist-Y + knee-Y trajectories to detect phases
  |
  5. Action identification: match segments to known technique templates
  |
  6. Output: JSON report + keyframe images + skeleton data
```

## Step-by-Step

### Step 1: Video Info

```bash
ffprobe -v quiet -print_format json -show_format -show_streams video.mp4
```

### Step 2: Audio to Whisper Transcription

```bash
# Extract audio:
ffmpeg -y -i video.mp4 -vn -acodec pcm_s16le audio.wav

# Transcribe:
python3 -c "
import whisper
model = whisper.load_model('base')
result = model.transcribe('audio.wav', language='zh')
for seg in result['segments']:
    print(f'[{seg[\"start\"]:.1f}s] {seg[\"text\"]}')
"
```

### Step 3: MediaPipe Skeleton Extraction

Use the existing `PoseEstimator.process_video()` pipeline from `pose-video-analysis`.

### Step 4: Motion Segmentation

Collect per-frame features from key joints:

```python
features = []
for i, f in enumerate(frames):
    if not f.detected: continue
    lm = f.landmarks  # (33, 4) numpy array
    features.append({
        'frame': i, 'time': i / 30.0,
        'r_wrist_y': float(lm[16][1]),    # right wrist Y
        'r_elbow_y': float(lm[14][1]),     # right elbow Y
        'r_knee_y': float(lm[26][1]),      # right knee Y
        'r_ankle_y': float(lm[28][1]),     # right ankle Y
        'shoulder_y': float((lm[11][1] + lm[12][1]) / 2),
    })

# Find motion peaks (highest arm = lowest wrist_y)
wrist_vals = sorted(features, key=lambda f: f['r_wrist_y'])
```

### Step 5: Action Template Matching

Match detected motion segments to known badminton technique profiles:

| Technique | wrist_y pattern | knee_y pattern | elbow_y pattern |
|:--|:--|:--|:--|
| Block (接杀挡网) | mid (0.47) | mid (0.60) | mid (0.46) |
| Deep lift (接杀挑球) | low to high | deep squat (0.74) | low to high |
| Counter (接杀反击) | high (0.33) | mid to jump | high |
| Smash | very high (<0.30) | jump | extended |
| Clear | high | mid-stable | high |

### Step 6: Output

```python
import json
data = {
    'source': video_path,
    'total_frames': len(frames),
    'detected': detected,
    'segments': [
        {'name': 'Block', 'start_frame': 0, 'end_frame': 900, 'duration_s': 30.0},
    ],
    'skeleton': [
        [[float(v) for v in kp] for kp in f.landmarks]
        if f.detected else None
        for f in frames
    ]
}
```

## Reference frames for manual verification

```bash
# Scene change detection:
ffmpeg -y -i video.mp4 -vf "select='gt(scene,0.15)',scale=360:640" -vsync vfr scene_%02d.png

# Timestamp-based key frames:
for t in 10 20 30 40 50; do
  ffmpeg -y -ss $t -i video.mp4 -vframes 1 -s 360x640 "key_${t}s.png"
done
```

## Pitfalls

1. **Xiaohongshu blocks all headless access.** Browser navigation, REST API endpoints, and share link interfaces all return IP-risk errors (code 300012). Extracting video content requires: (a) user sends video directly via WeChat, OR (b) user copy-pastes the video transcript/description. WeChat-sent videos arrive at `~/.hermes/cache/documents/doc_*_video.mp4` as HEVC MP4.
2. **Whisper model download can fail with SSL errors on slow connections.** The base model is ~139MB. Run `pip install --upgrade certifi` if SSL-related download failures occur.
3. **Wrist-Y values are inverted in screen coordinates.** Lower Y = higher physical position (arm raised). Higher Y = lower physical position (arm down). Knee-Y: higher = deeper squat.
4. **Landmark access is by INDEX, not attribute.** `FramePose.landmarks` is a `(33, 4)` numpy array. Access right wrist Y with `lm[16][1]`, NOT `lm[16].y`.
5. **First frame often undetected.** MediaPipe needs a few frames to initialize the pose detector. Skip frame 0 when computing detection rate.
