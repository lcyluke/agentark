# Chinese Badminton Training Video Sources — B站 Reference

## Priority-ordered coaches/players (verified pure-action sources)

Ranked by likelihood of finding **pure technique demonstration** (talking-free, just the player executing the stroke):

| Rank | Coach/Player | Known For | B站 Channel | Action Purity | Best For |
|:----:|:------------|:----------|:------------|:-------------:|:---------|
| 1 | 赵剑华 | 《专家把脉》系列 | 影子羽毛球 | ★★★★☆ | 吊球/步法/杀球 |
| 2 | 肖杰 | 高校教材级教学 | 肖杰羽毛球 | ★★★★☆ | 高远球/网前 |
| 3 | 李玲蔚 | 《学打羽毛球》 | 李玲蔚羽毛球 | ★★★★☆ | 步法/发球 |
| 4 | 陈雨菲 | 国羽现役女单 | 赛事剪辑 | ★★★☆☆ | 拉吊/防守 |
| 5 | 李宗伟 | 传奇男单 | 赛事集锦 | ★★☆☆☆ | 跳杀/步法 |
| 6 | 林丹 | 超级丹 | 赛事集锦 | ★★☆☆☆ | 假动作/鱼跃 |
| 7 | 傅海峰 | 双打传奇 | 赛事集锦 | ★★★☆☆ | 平抽/后场杀 |
| 8 | 阿山 | 双打天王 | 赛事集锦 | ★★★☆☆ | 网前/轮转 |
| 9 | 石宇奇 | 国羽男单 | 赛事剪辑 | ★★★☆☆ | 网前/反手 |
| 10 | 谌龙 | 防守大师 | 赛事集锦 | ★★★☆☆ | 接杀/防守 |

## B站 search templates

```
# Basic skills (best results)
搜索: 羽毛球 {skill_name_zh} 动作示范
搜索: {coach_name} 羽毛球教学 {skill_name_zh}

# By coach
搜索: 影子羽毛球 {skill_name_zh}
搜索: 肖杰 {skill_name_zh}
搜索: 赵剑华 {skill_name_zh}

# Pure action (no talk)
搜索: {skill_name_zh} 慢动作示范
搜索: {player_name} {skill_name_zh} 集锦

# Skills in Chinese
正手高远球, 反手高远球, 头顶高远球, 平高球, 被动高远球
正手杀球, 起跳杀球, 点杀, 劈杀, 杀直线, 杀斜线, 头顶杀球
正手吊直线, 正手吊斜线, 头顶吊直线, 头顶吊斜线, 滑板吊球, 反手吊球
正手搓球, 反手搓球, 勾对角, 推球, 挑球, 扑球
上网步法, 后退步法, 两侧移动
接杀, 平抽, 下手防守
假动作, 杀吊一致, 停顿
```

## Download & crop workflow

```bash
# 1. Download best 720p MP4
yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  --cookies-from-browser chrome \
  -o "raw_videos/{skill_id}_raw.mp4" \
  "{{URL}}"

# 2. Trim to pure action segment (find SS:EE via preview)
ffmpeg -i raw_videos/{skill_id}_raw.mp4 \
  -ss 00:00:XX -t 30 \
  -c copy \
  raw_videos/{skill_id}_trimmed.mp4

# 3. Apply privacy pipeline (face blur + strip audio + skeleton overlay)
python3 -c "
from badminton_coach.video_privacy import process_video
process_video('raw_videos/{skill_id}_trimmed.mp4', 'data/training_animations/{skill_id}_demo.mp4')
"

# 4. Verify output
ffprobe data/training_animations/{skill_id}_demo.mp4 2>&1 | grep -E "Duration|Stream"
```

## Verified high-quality channels (HD & 4K, verified 2026-06)

These B站 channels consistently produce **横版 1280×720p or better** content suitable for MediaPipe pose tracking:

| Channel | B站 ID | Typical Resolution | Content Type | Action Purity |
|:--------|:-------|:-----------------:|:-------------|:-------------:|
| **影子羽毛球 (Shadow Badminton)** | 影子传说 | **1280×720 @ 25fps** | 教科书慢动作 (赵剑华/肖杰) | ★★★★★ |
| **闪跃运动 (Flash Sports)** | 闪跃运动 | **3840×2160 (4K)** | 动作示范教学 (反手/高远球) | ★★★★☆ |
| **大G羽毛球** | 大G羽毛球 | 1280×720 (部分竖版需筛选) | 横版杀球/防守示范 | ★★★★☆ |
| **汤老师羽毛球** | 汤老师 | 1280×720 | 系统课程 (杀球/步法/横屏) | ★★★☆☆ |
| **丹麦国羽张教练** | 丹麦国羽张教练 | 1280×720 | 侧面全身示范 | ★★★★☆ |

### Key shadow_slowmo videos (shadow slow-motion series)

These are the most valuable source — pure action, no talking, 25fps slow-mo:

| BV ID | Content | Resolution | Duration | Size |
|:-----:|:--------|:----------:|:--------:|:----:|
| BV1jt41197as | 赵剑华教科书式动作示范右手版 | 1280×720 | 5.5 min | 16MB |
| BV1Et41197bx | 赵剑华教科书式动作示范左手版 | 1280×720 | 5.5 min | 16MB |
| BV1Wb411U71C | 肖杰教科书式动作示范右手版 | 1280×720 | 8.7 min | 19MB |
| BV1Wb411U7UL | 肖杰教科书式动作示范左手版 | 1280×720 | 8.7 min | 18MB |

### Key flash_sports video (4K)

| BV ID | Content | Resolution | Duration | Size |
|:-----:|:--------|:----------:|:--------:|:----:|
| BV1hZ4y1d7Hs | 反手杀球、高远球简化版示范教学 | **3840×2160 4K** | 6.5 min | 432MB |

### Download commands for these specific BV IDs

```bash
# shadow_slowmo series (1280×720)
yt-dlp --cookies-from-browser firefox \
  -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  -o "data/raw_videos/bilibili/shadow_slowmo/shadow_zhao_jianhua_rh.mp4" \
  "https://www.bilibili.com/video/BV1jt41197as/"

# flash_sports 4K video
yt-dlp --cookies-from-browser firefox \
  -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best" \
  -o "data/raw_videos/bilibili/flash_sports/flash_backhand.mp4" \
  "https://www.bilibili.com/video/BV1hZ4y1d7Hs/"
```

## Pitfalls

1. **yt-dlp B站 cookies**: Without `--cookies-from-browser`, B站 limits downloads to 360p. Safari cookies are sandbox-protected on macOS — use Chrome if available

   **Cookie extraction reality (macOS, verified 2026-06):** `yt-dlp --cookies-from-browser chrome` extracts **3344 cookies** from Chrome, but the login-critical ones (SESSDATA, DedeUserID, bili_jct) are NOT among them — even from default profile and 2 additional Chrome profiles. `python3 -c "import browser_cookie3"` sees only non-encrypted cookies (buvid3, buvid4, preferences) — 19 total, no login tokens. The SESSDATA cookie appears to be `HttpOnly` or protected by Chrome's encrypted cookie store in a way neither tool can decrypt.
   
   **Fix (option A — Chrome):** If B站 HD downloads are required, the user must manually export cookies via the "Get cookies.txt LOCALLY" Chrome extension (https://chrome.google.com/webstore/detail/get-cookiestxt-locally/cclelndahbckbenkjhflpdbgdldlbecc) — open B站, click the extension, save. Then pass the file to yt-dlp: `--cookies /path/to/cookies.txt`

   **Fix (option B — Firefox, preferred, verified 2026-06-01):** Firefox does NOT encrypt its cookie store in the same way as Chrome. `python3 -c "import browser_cookie3; c = browser_cookie3.firefox(domain_name='.bilibili.com')"` successfully extracts **all cookies including login tokens** — SESSDATA, bili_jct, DedeUserID, buvid3, buvid4, etc. Use `yt-dlp --cookies-from-browser firefox <URL>` for automatic HD downloads:

   ```bash
   # Verify cookies from Firefox:
   python3 -c "
   import browser_cookie3
   cj = browser_cookie3.firefox(domain_name='.bilibili.com')
   bili_cookies = {c.name: c.value for c in cj}
   has_login = all(k in bili_cookies for k in ['SESSDATA', 'bili_jct', 'DedeUserID'])
   print(f'B站 cookies: {len(bili_cookies)} total')
   print(f'Login session: {\"✅ PRESENT\" if has_login else \"❌ MISSING\"}')"
   
   # Download B站 720p video:
   yt-dlp --cookies-from-browser firefox \
     -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
     -o "output.mp4" "BV号或B站URL"
   ```

   **Tested on macOS 15 (Sequoia):** Firefox profile auto-detected at ~/Library/Application Support/Firefox/Profiles/*.default-release. Cookies remain valid for ~6 months (expiry dates checked on extracted cookies).
   
   **Fallback path (no B站):** yt-dlp can download Chinese badminton instruction from **YouTube** (search with Chinese keywords like `ytsearch10:羽毛球 发球 教学 中文`). YouTube offers format 18 (360p, ~5-30MB per 5-min video) without auth. Validated channels: 刘辉羽毛球, 影子羽毛球, 肖杰, 李玲蔚. The down side: from a Chinese ISP without VPN, YouTube is blocked — so this is only viable from a non-China server or VPN-connected machine.
2. **Multiple skills in one video**: A single 20-min tutorial may cover 8 skills. Download once, then trim each segment separately with different `-ss`/`-t` values
3. **Mixed language videos**: Some "Chinese" videos have English titles but Chinese audio. Prefer titles in Chinese characters for authentic content
4. **Copyright watermark**: B站 originals have a "Bilibili" watermark. If user objects, use the face-blur pipeline's region-based blur to mask it (add the watermark bounding box as a blur region)
5. **Format compatibility**: WeChat mini-program supports H.264 MP4 only. After processing, verify: `ffprobe output.mp4 2>&1 | grep -c "h264"` or `libx264`. If not H.264, re-encode: `ffmpeg -i input.mp4 -vcodec libx264 -preset fast -crf 23 output.mp4`
