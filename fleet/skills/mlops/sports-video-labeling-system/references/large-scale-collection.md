# 大规模视频采集 + 批量标注实战记录

## 场景：从 25 个标注到 107 个视频 / 104 个标注

### 背景
标注系统原有 25 个原始视频（7 类，每类 2-5 个），已标 24 条。需要快速扩展到 100+ 以提升模型精度。

### 步骤 1: 复用训练动画库（~33 个视频）
```
~/Desktop/2026AIAPP/workspace/badminton-coach-ai/data/training_animations/
```
这些是已有项目的训练动画 demo 视频（20-90s，纯动作片段）。按类别复制到 `raw_videos/{category}/`：

| 来源类别 | 目标目录 | 获取数量 |
|---------|---------|:--------:|
| drop_*.mp4 | drop | 4 |
| net_*.mp4 | net | 5 |
| fw_*.mp4 | footwork | 3 |
| def_*.mp4 | defense | 2 |
| feint_*.mp4 | feints | 12 |
| clear_*.mp4 | clear | 1 |
| smash_*.mp4 | smash | 6 |

仅复制目标目录中没有的（按文件名去重），耗时 ~2s。

### 步骤 2: 并行 yt-dlp 下载（5 个后台进程）

```bash
# 对每个缺口类别启动独立后台进程
cd ~/Desktop/2026AIAPP/badminton-label-system/data/raw_videos

yt-dlp --socket-timeout 20 --max-filesize 80M \
  "ytsearch10:羽毛球 高远球 教学 正手" \
  -o "clear/clear_%(id)s.%(ext)s"

yt-dlp --socket-timeout 20 --max-filesize 80M \
  "ytsearch10:羽毛球 吊球 教学 头顶" \
  -o "drop/drop_%(id)s.%(ext)s"

yt-dlp --socket-timeout 20 --max-filesize 80M \
  "ytsearch10:羽毛球 防守 接杀 平抽" \
  -o "defense/defense_%(id)s.%(ext)s"
```

每个进程用 `terminal(background=true)` 启动，无需等待即可开始标注。

**下载结果：** 5 个类别并行下载 ~15 min，获得 50+ 个新视频。含失败的 `.part` 文件，需清理。

### 步骤 3: 清理+去重

```bash
# 清理未完成下载
find raw_videos -name '*.part' -delete

# 去重：yt-dlp 可能为同一视频下载多个格式（f251.webm + f313.webm）
# 用视频 ID（11-12 位 alphanumeric 在 _ 之后）去重计数
```

### 步骤 4: 批量标注（与下载并行）

```python
# batch_annotate.py — 直接导入 agents，不通过 subprocess
sys.path.insert(0, os.path.join(PROJECT_ROOT, "agents"))
from skeleton_agent import SkeletonAgent
from annotation_engine import AnnotationEngine
from quality_checker import QualityChecker
```

**关键执行方式：**
```bash
# 必须用项目 venv 的 Python（系统 conda 的 numpy 不兼容）
PYTHONPATH="$PWD/agents:$PYTHONPATH" \
~/Desktop/2026AIAPP/workspace/badminton-coach-ai/venv/bin/python3 scripts/batch_annotate.py
```

**标注速率：** M1 Pro 上 ~3-4 vids/min（首个更慢 ~8-15s 因 MediaPipe 初始化），101 个视频共 ~25 min。

**成功/失败分布：** 101 个视频 → 62 成功 + 39 失败（主要因为教学视频太长含讲解画面，纯动作帧数不足）。

### 步骤 5: 重新训练模型

```bash
cd ~/Desktop/2026AIAPP/badminton-label-system
~/Desktop/2026AIAPP/workspace/badminton-coach-ai/venv/bin/python3 scripts/train_phase1.py
```

**精度提升：** 
- 104 条时等级分类精度 **71.4%**（选择 GBDT 而非 RF，前者 71.4% vs RF 61.9%）
- L4-L6 分布：25/62/17
- 特征重要性 Top3: elbow_mean, elbow_range, knee_mean

### 经验教训

1. **先复用后下载** — 训练动画库是最快来源，可零时延获得 30+ 标注素材
2. **下载 + 标注并行** — yt-dlp 后台下载不阻塞 CPU，标注 pipeline 跑在本地 GPU 上，不冲突
3. **分批策略** — 不是等全部下载完再标，而是先标已有的，同时后台补缺
4. **模型选择** — 在样本量增长后 GBDT 优于 RF（需比较），不能在旧数据上固守 RF
5. **pyton 解释器** — 标注系统无独立 venv，必须用主项目的 venv python 避免 anaconda 冲突
