#!/usr/bin/env python3
"""
B站批量下载器 v2 — 多类别并行下载模板。
适合一次性补齐多个缺失的羽毛球技术类别。

使用方法：
1. 修改 DOWNLOAD_LIST 填入目标 BVID 和类别名
2. 确保 data/bilibili_cookies.txt 有效
3. python3 scripts/bili_batch_download_v2.py

依赖: yt-dlp, ffprobe (ffmpeg)
"""
import subprocess, sys, os, time
from pathlib import Path

RAW_DIR = Path(os.path.expanduser("~/Desktop/2026AIAPP/badminton-label-system/data/raw_videos"))
COOKIE = os.path.expanduser("~/Desktop/2026AIAPP/badminton-label-system/data/bilibili_cookies.txt")

# ===== 修改这里：填入BVID和类别目录 =====
DOWNLOAD_LIST = [
    # (BVID, category_subdir)
    # 示例: 杀球
    # ("BV1Ht4y1P7Qs", "smash"),
    # 示例: 吊球
    # ("BV1Hz4y1A7XQ", "drop"),
]

def download(bvid, sub_dir):
    out_path = RAW_DIR / sub_dir
    out_path.mkdir(parents=True, exist_ok=True)
    existing = list(out_path.glob(f"*{bvid}*"))
    if existing:
        print(f"  ⏭️ 已存在: {bvid}")
        return True
    cmd = [
        "yt-dlp", "--cookies", str(COOKIE),
        "-f", "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
        "-o", str(out_path / f"%(title).50s_{bvid}.%(ext)s"),
        "--merge-output-format", "mp4", "--no-warnings",
        f"https://www.bilibili.com/video/{bvid}",
    ]
    print(f"  📥 {bvid} -> {sub_dir}/")
    start = time.time()
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        dur = time.time() - start
        new_files = list(out_path.glob(f"*{bvid}*"))
        if new_files:
            f = new_files[0]
            size_mb = f.stat().st_size / 1048576
            info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate", "-of", "csv=p=0", str(f)],
                capture_output=True, text=True, timeout=10)
            print(f"  ✅ {bvid}: {size_mb:.0f}MB @ {info.stdout.strip()} ({dur:.0f}s)")
            return True
        else:
            print(f"  ⚠️ {bvid}: 找不到文件")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ {bvid}: 超时")
        return False
    except Exception as e:
        print(f"  ❌ {bvid}: {e}")
        return False

def main():
    print(f"🏸 B站批量下载 v2 — {len(DOWNLOAD_LIST)} 个视频")
    success = fail = 0
    for bvid, sub_dir in DOWNLOAD_LIST:
        try:
            if download(bvid, sub_dir): success += 1
            else: fail += 1
        except KeyboardInterrupt: break
    print(f"\n📊 完成: ✅ {success} / ❌ {fail} / 总 {len(DOWNLOAD_LIST)}")

if __name__ == "__main__":
    main()
