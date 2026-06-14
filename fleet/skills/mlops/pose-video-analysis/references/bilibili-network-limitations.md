# B站 Video Download — China Network Limitations (2026-06-01)

## Tested Approaches (from Shenzhen, no VPN)

| Approach | Result | Detail |
|:---------|:------:|:-------|
| B站 without cookies | ❌ | "format not available" for 360p+ |
| `--cookies-from-browser chrome` | ❌ | Extracts 3344 cookies but MISSES SESSDATA/DedeUserID/bili_jct (HttpOnly encrypted in Chrome) |
| `--cookies-from-browser safari` | ❌ | macOS sandbox blocks cookie access |
| YouTube without VPN | ❌ | All searches timeout (GFW blocked) |
| YouTube Chinese keywords (Shenzhen) | ⚠️ | 1 video in ~120s, most timeout |

## Working Approaches

1. **Manual cookie export**: Install "Get cookies.txt LOCALLY" Chrome extension → open B站 → export → `yt-dlp --cookies cookies.txt ...`
2. **Deploy collector on Tencent Cloud** (43.139.191.202): direct CN internet, no GFW for B站
3. **Focus on user-generated content**: miniapp uploads + venue QR codes provide real-player data at higher quality than scraped videos
4. **Use cached local files**: 129 teaching videos + 1 amateur video from prior sessions — run detect→annotate pipeline on existing data first

## Recommendation

When operating from Shenzhen without VPN: skip B站/YouTube scraping. Use the miniapp upload API (`/api/v1/upload`) and venue QR code conversion funnel to collect amateur data instead. The data quality from real users (with self-rating, play_years, handedness metadata) is higher than scraped teaching videos.
