# Batch Generation with InsightFace + Report Pipeline

Complete pipeline from this session (2026-06-03): generate 25 training videos on AutoDL, process user WeChat videos, and output a comprehensive training report.

## Full E2E Flow

```
1. AutoDL: 25× MimicMotion(faceswap) + 4-view skeleton breakdown → training video
2. Download: tar.gz → local
3. Local: WeChat video archive → skeleton extraction → benchmark comparison
4. Output: training_video_report.md + reports/ dir
```

## Step 1: File Preparation (Local)

### Skill-to-skeleton mapping for batch

For 25 skill IDs, map each to the best skeleton from a 1884-file library of Bilibili-sourced clips.

**Best approach**: Use a dictionary of directory names → skill IDs, then pick the skeleton with frame count closest to 72 (MimicMotion ideal):

```python
DIR_SKILLS = {
    "（4K）颠覆你的杀球发力认知..._BV1Ht": ["smash_stand", "smash_jump", "smash_point"],
    "顶尖羽毛球高手的高远球慢动作..._BV1g3": ["clear_fh", "clear_oh"],
    "影子羽毛球高清慢动作精选...陶菲克..._BV1gs": ["clear_bh"],
    "吊球又高又慢怎么办？刘辉教练..._BV1Hz": ["drop_fh", "drop_bh", "drop_slide"],
    # ... 25 total
}
```

**Selection**: For each skill, find the skeleton file where `abs(len(frames) - 72)` is minimal and `10 <= len(frames) <= 120`. This gives consistent 48-72 frame videos (MimicMotion caps at 72).

**Packaging**: 
- 25 skeleton JSON files, total ~690KB
- Each named `{skill_id}.json` in `data/skeletons/`
- Pack as `tar czf /tmp/autodl_skeletons.tar.gz -C /tmp/autodl_upload/data/skeletons .`

### Reference photo

Choose a photo where InsightFace detects exactly 1 face with high confidence (`det_score > 0.7`). Test all available test images first:

```python
for img_name in ['test_img_1.jpg', 'test_img_2.jpg', ...]:
    img = cv2.imread(img_name)
    faces = app.get(img, max_num=1)
    print(f'{img_name}: {len(faces)} faces, score={faces[0].det_score:.3f}')
```

## Step 2: Upload and Deploy (AutoDL)

See the parent SKILL.md section "Batch generation on AutoDL" for the upload procedure.

### Critical order of operations:

1. **SSH check first**: `echo ALIVE && nvidia-smi`
2. **Kill infer_server.py** (stale model holds 19GB VRAM)
3. **Unpack skeletons** to `data/skeletons/{25 files}.json`
4. **Create output dirs**: `output/train/ output/demo/ output/skel_breakdown/`
5. **Install deps**: `pip install insightface onnxruntime-gpu imageio[pyav]`
   - Note: `python3` is NOT on PATH — use `/root/miniconda3/bin/pip` 
   - Insightface models auto-download on first use (~800MB)
   - On AutoDL CUDA 13.2, CUDAExecutionProvider not available → CPU only
6. **Fix the `device=` bug**: sed replace the pipeline() call to add `,device=d`
7. **Fix syntax warnings**: `sed -i 's/0.3or/0.3 or/g' autodl_batch.py`
8. **Launch**: `nohup ... python3 -W ignore autodl_batch.py > output/batch.log 2>&1 &`
9. **Verify**: after ~5s check `tail -5 output/batch.log` for loading message

## Step 3: Monitor Progress

Use `cronjob` to poll every 10 minutes:

- Check: `ls output/demo/*.mp4 | wc -l` for count
- Check: `tail -3 output/batch21.log` for active task
- Check: `nvidia-smi --query-gpu=memory.used,utilization.gpu --format=csv,noheader`
- ETA: remaining = (25 - done) × 180s

When all 25 are done, download:
```bash
# Remote: pack
sshpass ... ssh ... "tar czf /tmp/autodl_train.tar.gz -C output/train ."
# Local: download
sshpass ... scp ... remote:/tmp/autodl_train.tar.gz /tmp/
# Local: extract
tar xzf /tmp/autodl_train.tar.gz -C uploads/autodl_videos/train/
```

## Step 4: WeChat Video Ingestion

WeChat messages with video go to `~/.hermes/cache/documents/doc_*_video.mp4`.

**Best practice**: Copy to project dir immediately:
```bash
mkdir -p uploads/user_videos/
cp ~/.hermes/cache/documents/doc_*_video.mp4 uploads/user_videos/
# Write index
python3 -c "
import json, os, subprocess
from datetime import datetime

videos = []
for f in sorted(os.listdir('uploads/user_videos/')):
    if not f.endswith('.mp4'): continue
    fpath = os.path.join('uploads/user_videos/', f)
    size = os.path.getsize(fpath)//1024
    r = subprocess.run(f'ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 \"{fpath}\"', shell=True, capture_output=True, text=True)
    dur = float(r.stdout.strip()) if r.stdout.strip() else 0
    r2 = subprocess.run(f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=s=x:p=0 \"{fpath}\"', shell=True, capture_output=True, text=True)
    res = r2.stdout.strip() if r2.stdout.strip() else '?'
    videos.append({'file': f, 'size_kb': size, 'duration_s': round(dur,1), 'resolution': res})

with open('uploads/user_videos/_index.json', 'w') as f:
    json.dump({'count': len(videos), 'videos': videos, 'saved_at': datetime.now().isoformat()}, f, indent=2)
"
```

### Duration → action type heuristics

| Duration | Resolution | Likely content |
|:---------|:-----------|:---------------|
| < 2.5s | 1280×720 | Slow-motion clip, single stroke |
| 2.5-4s | 1280×720 | Short clip, one action |
| 4-10s | 1280×720 | 1-2 complete actions |
| 10-20s | 720×1280 | Repeat practice, multiple strokes |
| 20-60s | 720×1280 | Full sequence, possible multiple actions |

## Step 5: Report Generation

The `generate_training_report.py` script creates a 4-section Markdown report:

1. **Training video generation report** — counts per skill category, sizes
2. **User video analysis** — archived WeChat videos, their metadata
3. **3-week training plan** — tiered by average score level (L3-L4 / L4-L5 / L5-L6 / L6+)
4. **System validation report** — component health status (backend, generation, comparison, face swap, frontend)

### Score tiers for training plan:

```python
if avg_score < 40:
    level_desc = "L3-L4 (入门级)"  # focus: 基本功纠正
elif avg_score < 60:
    level_desc = "L4-L5 (初中级)"  # focus: 动作规范性提升
elif avg_score < 75:
    level_desc = "L5-L6 (中级)"    # focus: 发力效率优化
else:
    level_desc = "L6+ (高级)"      # focus: 技战术精细化
```

### Recommended report structure:

```python
report = f'''═══ 第一部分：训练视频生成报告 ═══
AutoDL: {count}/25
分组清单（按技能类别）

═══ 第二部分：用户视频分析 ═══
共 {n} 个视频，逐条列出

═══ 第三部分：专属训练方案 ═══
3周计划 + 重点推荐动作

═══ 第四部分：系统验证 ═══
11项组件状态一览
'''
```

## Startup resilience: backend restart pattern

The local FastAPI backend (`:8000`) may OOM-kill (exit 137) after processing heavy MediaPipe tasks. **Always restart in background mode**:

```bash
cd ~/Desktop/2026AIAPP/workspace/badminton-coach-ai
# Kill old
lsof -ti:8000 | xargs kill -9 2>/dev/null
sleep 1
# Start new in background
./venv/bin/python3 -m uvicorn badminton_coach.webapp:app --host 0.0.0.0 --port 8000
# Verify: curl http://127.0.0.1:8000/api/avatar/skills
```

The backend auto-detects code changes from `--reload` mode when used in the project. Without `--reload`, it's more stable but requires manual restart after changes.

## Known issues from this session

### MimicMotionPipeline `device=` kwarg required

On newer versions of MimicMotion (>=2026-06), the `pipeline.__call__()` signature requires an explicit `device` kwarg. Without it, the SECOND call to the same pipeline fails with:

```
ValueError: Expected a cuda device, but got: cpu
  File "mimicmotion/pipelines/pipeline_mimicmotion.py", line 549, in __call__
    with torch.cuda.device(device):
```

**Fix:** Add `device=d` (where `d = torch.device("cuda")`) to every pipeline call. The fix is needed despite the first call working — `MimicMotionPipeline` resets its internal device reference after each inference.

### Server already running on port 15502

When `cli open --compile` fails with "IDE may already started at port 15502", it still works — the CLI auto-reconnects to the existing IDE server. The compile step is happening regardless of the warning.

### ModelScope vs hf-mirror for gated models

Confirmed this session (2026-06-03): from AutoDL inside China, **hf-mirror returns 401 for gated repos** even with valid Bearer tokens in headers. ModelScope must be used for `stabilityai/stable-video-diffusion-img2vid-xt-1-1` and all other gated models from AutoDL.

### `PoseNet` constructor confirmed working

On this version (2026-06-03, MimicMotion from tagged release), `PoseNet(noise_latent_channels=320)` is the correct constructor — no `unet_in_channels` or other params. This was extracted from `mimicmotion/utils/loader.py` which calls `PoseNet(noise_latent_channels=unet.config.block_out_channels[0])`.
