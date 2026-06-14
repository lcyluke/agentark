# B站视频批量采集实战记录 (2026-06-01)

## 场景：从旧360p升级到B站720p/4K高质量数据源

### 背景
原有1,562个骨骼数据全来自YouTube 360p视频（关节精度±15°）。
需要替换为B站720p+4K视频（关节精度≤5°/+2°），同时补齐缺失类别。

### B站视频发现方法论

不同于YouTube（直接yt-dlp搜索即可），B站视频发现需要多步：

**1. Browser搜索（而非API搜索）**
B站搜索API返回数据有限（`/x/web-interface/search/all/v2` 结果不完整），
最可靠的方式是用browser_navigate + browser_console获取页面中的BVID。

**模式：**
```python
# 搜索页面
browser_navigate("https://search.bilibili.com/all?keyword=羽毛球+杀球+教学+慢动作&order=click")

# 获取所有BVID（注意"稍后再看"是收藏标签，不是真实标题）
browser_console('(() => {...
  const links = Array.from(document.querySelectorAll('a[href*="/video/BV"]'));
  return [...new Set(links.map(a => a.href.match(/BVw+/)?.[0]).filter(Boolean))];
})()')
```

**2. API验证内容（快速过滤）**
```bash
curl -s "https://api.bilibili.com/x/web-interface/view?bvid=BVxxx" \
  -H "User-Agent: Mozilla/5.0 ..." | python3 -c "查看title+duration"
```
注意：B站API是**匿名可访问的**，不需要cookie！

**3. 判断画质**
使用 ffprobe 下载后检查：
```bash
ffprobe -v error -select_streams v:0 -show_entries stream=width,height,r_frame_rate -of csv=p=0 video.mp4
```

### 本次下载清单（13个视频，4个新类别）

| BVID | 标题 | 时长 | 类别 | 优先级 |
|:----:|:-----|:----:|:----:|:------:|
| BV1Ht4y1P7Qs | （4K）颠覆你的杀球发力认知 | 31:50 | smash | ⭐⭐⭐ |
| BV1aHweeCEVB | 如何轻松杀得尖？李宇轩教练 | 14:58 | smash | ⭐⭐ |
| BV1Hz4y1A7XQ | 吊球又高又慢怎么办？大G羽毛球 | 5:47 | drop | ⭐⭐ |
| BV1xj411t7hN | 【正手高远球】纯净版慢动作赏析 | 0:20 | clear | ⭐（纯动作） |
| BV1g34y1o71S | 顶尖高手高远球慢动作集锦 | 2:04 | clear | ⭐⭐⭐ |
| BV1fW411R7oA | 影子反手后场 | 4:13 | clear | ⭐⭐⭐ |
| BV1kN411h7cr | 反手高远球又近又慢 | 0:46 | clear | ⭐ |
| BV1gs411G7do | 影子陶菲克反手纪念版 | 3:01 | clear | ⭐⭐⭐ |
| BV16G411B7fc | 高远球吊球杀球左手放哪里 | 4:48 | clear | ⭐⭐ |
| BV1nJtUeYEmP | 后场转身慢李宇轩教练 | 13:51 | footwork | ⭐⭐ |
| BV1X24y1B7v2 | 打球步子越大越接不了球 | 30:05 | footwork | ⭐⭐ |
| BV11Gt4zTEKs | 桃田贤斗步伐攻略 | 3:11 | footwork | ⭐ |
| BV1os411K7es | 李宗伟步法慢动作分解解析 | 10:04 | footwork | ⭐⭐⭐ |

### B站下载命令模板

```bash
yt-dlp --cookies data/bilibili_cookies.txt \
  -f "bestvideo[height<=2160]+bestaudio/best[height<=2160]" \
  -o "data/raw_videos/{category}/%(title).50s_{bvid}.%(ext)s" \
  --merge-output-format mp4 \
  --no-warnings \
  "https://www.bilibili.com/video/{BVID}"
```

注意：使用 `--merge-output-format mp4` 确保视频+音频合并为单个文件。
`.50s` 截断长标题避免文件名过长问题。

### 画质实测

下载后检查分辨率：
```
flash_backhand (闪跃4K):   3840×2160 @ 25fps ✅✅✅
shadow_zhao_jianhua_rh:    1280×720  @ 25fps ✅✅
shadow_xiao_jie_lh:        1280×720  @ 25fps ✅✅
```

### B站Pipeline输出结果

5个视频（赵剑华×2+肖杰×2+闪跃4K反手）的Pipeline切割结果：

| 视频 | 画质 | 动作片段 | 骨骼追踪率 |
|:-----|:----:|:--------:|:----------:|
| 闪跃反手4K | 3840×2160 | 24段 | 99.8% 🔥 |
| 肖杰左手 | 1280×720 | 28段 | 87.2% |
| 肖杰右手 | 1280×720 | 28段 | 89.1% |
| 赵剑华左手 | 1280×720 | 19段 | 93.9% |
| 赵剑华右手 | 1280×720 | 19段 | 93.3% |
| **合计** | — | **118段** | **92.3-99.8%** |

### 经验教训

1. **Browser搜索 > API搜索** — B站搜索API返回数据不完整（很多结果被折叠），用browser_navigate更可靠
2. **横屏 vs 竖屏** — 竖屏视频（720×1280）虽然分辨率高但身体下半部分常被裁切，脚踝追踪率低。优先选横屏（1280×720）
3. **骨胳追踪结构变化** — B站clips的骨架JSON结构与旧360p不同：
   - 旧格式: `[{"x":..., "y":..., "z":..., "visibility":...}, ...]` (list of frames)
   - 新格式: `{"fps": 25, "total_frames": 378, "tracked_frames": 377, "track_rate": 0.997, "frames": [...]}`
4. **Batch下载时间预估** — 13个视频（含1个4K 31min视频）预计总耗时约15-30分钟
5. **SSL/timeout问题** — yt-dlp从B站下载时偶尔SSL握手失败，自动重试2-3次后成功（非代码bug）
6. **`notify_on_complete=true`** — 对于长时间的后台下载任务，使用此模式可以释放当前会话继续其他工作
