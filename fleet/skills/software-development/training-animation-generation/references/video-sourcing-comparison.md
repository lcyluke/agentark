# Video Sourcing Comparison — B站 vs YouTube for 羽毛球基础动作

## 来源选择决策树

```
需要羽毛器基础动作视频
      │
      ├── 用户的母语是中文/在CN? → 优先B站中文资源
      │      │
      │      ├── B站下载成功？ → 裁剪+脱敏 → 完成 ✅
      │      │
      │      └── B站失败（格式/会员/登录） → 切换到YouTube中文频道
      │
      └── 用户无地域偏好 → 优先YouTube (成功率更高)
```

## 来源对比

| 维度 | B站 | YouTube |
|:----|:---:|:-------:|
| 中文内容质量 | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 下载成功率 | ~60% | ~95% |
| 格式探测 | 需要先 `-F` 看可用ID | `bestvideo+bestaudio` 通用 |
| 需要cookie | ✅ 必须 `--cookies-from-browser` | ❌ 不需要 |
| 会员限制 | 720p+ 需大会员 | 无限制 |
| 内容密度 | 长视频合集多，需裁剪 | 短视频多，即下即用 |

## 推荐的 YouTube 中文频道（替代B站首选）

| 频道 | 内容特点 | 下载难度 |
|:----|:---------|:--------:|
| 包建邦羽毛球 | 高远球/杀球分解教学, 清晰动作示范 | ⭐简单 |
| 洁宝羽毛球 | 国二女生示范, 网前/搓球系列 | ⭐简单 |
| 李宇轩教练 | 台湾教练, 吊球/步法系列 | ⭐简单 |
| 陈金羽毛球 | 前国手, 杀球/吊球慢动作分解 | ⭐简单 |
| 一丸- | 杀球示范, 短视频为主 | ⭐简单 |
| Badminton Insight | 前英国国手, 全技能覆盖 | ⭐简单 |

## 已下载成功的5个基础动作视频

| Skill ID | 中文 | 时长 | 大小 | 来源 |
|:---------|:-----|:----:|:----:|:----:|
| clear_fh | 正手高远球 | 35s | 949KB | 包建邦羽毛球 (B站) |
| smash_stand | 原地杀球 | 25s | 1.6MB | 一丸- (B站) |
| smash_jump | 起跳杀球 | 30s | 1.1MB | 大话羽界 (B站) |
| net_fh_rub | 正手搓球 | 25s | 2.9MB | 洁宝羽毛球 (B站) |
| drop_fh_straight | 正手吊直线 | 40s | 1.0MB | 陈金羽毛球 (B站) |

## 通用下载命令

```bash
# YouTube
yt-dlp -f "bestvideo[height<=720][ext=mp4]+bestaudio[ext=m4a]/best[height<=720]" \
  -o "raw_videos/{skill_id}.%(ext)s" "URL"

# B站 (需要先 -F 探测)
yt-dlp --cookies-from-browser chrome -F "URL"  # 看可用格式
yt-dlp --cookies-from-browser chrome -f "30033+30280" -o "raw_videos/{skill_id}.%(ext)s" "URL"

# 裁剪 (通用)
ffmpeg -i raw_videos/{skill_id}.mp4 -ss 5 -t 30 \
  -vf "scale=640:-2:flags=lanczos,fps=24" \
  -c:v libx264 -crf 26 -preset fast -an \
  data/training_animations/{skill_id}_demo.mp4
```
