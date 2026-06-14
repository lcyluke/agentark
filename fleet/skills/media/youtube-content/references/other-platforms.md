# 非 YouTube 平台视频下载

## 小红书 (Xiaohongshu / RED)

### 问题

小红书有强反爬机制：
- 短链接 `xhslink.com/o/xxx` 重定向到实际页面
- 直接 `curl` 返回安全验证页（IP at risk / 406）
- API 端点 `edith.xiaohongshu.com` 需要 cookie + xsec_token 签名
- Python requests 即使带完整 headers 和 cookies 也容易触发 406
- `browser_navigate` 也会被安全限制拦截

### 解决方案：yt-dlp

`yt-dlp` 内置 `XiaoHongShu` 提取器，能自动处理短链接重定向和反爬：

```bash
# 安装（macOS）
brew install yt-dlp

# 下载视频（支持短链接和完整链接）
yt-dlp -o "~/Downloads/视频名.mp4" "http://xhslink.com/o/XXXXX"

# 查看可用格式
yt-dlp -F "http://xhslink.com/o/XXXXX"
```

### 提取器原理

yt-dlp 的 `XiaoHongShuIE` 提取器：
1. 解析短链接 `xhslink.com` → 跟随重定向
2. 使用移动端 UA 请求页面
3. 从 `__INITIAL_STATE__` JSON 提取 video stream URL
4. 直接下载 mp4/m3u8 流

### 失败路径（不要尝试）

| 方法 | 结果 |
|:--|:--|
| `curl` 直接请求 | 安全验证页 |
| Python `requests` + UA | 406 / IP at risk |
| `browser_navigate` | 安全限制页面 |
| API 端点 `edith.xiaohongshu.com/api/sns/web/v1/feed` | 406，需要有效 cookie+签名 |

### 输出

yt-dlp 输出为标准 mp4 文件。示例：
```
[download] 100% of 21.04MiB in 00:00:13 at 1.60MiB/s
→ ~/Downloads/视频名.mp4
```

## 通用原则

对于中国社交平台（小红书/抖音/B站/快手）的视频下载：
1. **优先用 yt-dlp** — 它维护了大量中国平台的提取器
2. **不要手写 HTTP 客户端** — 反爬签名复杂且频繁更新
3. **yt-dlp 失败时更新到最新版本** — 提取器修复很快
