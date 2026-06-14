#!/usr/bin/env python3
"""
B站批处理下载器 v2 — 多类别批量下载
支持按类别组织、cookie认证、720p优先、下载进度报告
使用: python3 scripts/bili_batch_download.py

前置条件:
  1. B站cookie文件存在 data/bilibili_cookies.txt
  2. yt-dlp已安装

cookie获取: 用"Get cookies.txt LOCALLY" Chrome扩展导出
"""
import subprocess, sys, os, json, time
from pathlib import Path

RAW_DIR = Path(os.path.expanduser("~/Desktop/2026AIAPP/badminton-label-system/data/raw_videos"))
COOKIE = os.path.expanduser("~/Desktop/2026AIAPP/badminton-label-system/data/bilibili_cookies.txt")

# Format: (bvid, sub_dir)
DOWNLOAD_LIST = [
    # === 示例条目 ===
    ("BV1Ht4y1P7Qs", "smash"),   # 闪跃运动4K 颠覆杀球发力认知 31:50 ⭐⭐⭐
]

def download(bvid, sub_dir):
    out_path = RAW_DIR / sub_dir
    out_path.mkdir(parents=True, exist_ok=True)
    
    existing = list(out_path.glob(f"*{bvid}*"))
    if existing:
        print(f"  ⏭️ 已存在: {bvid} -> {existing[0].name}")
        return True
    
    cmd = [
        "yt-dlp",
        "--cookies", str(COOKIE),
        "-f", "bestvideo[height<=2160]+bestaudio/best[height<=2160]",
        "-o", str(out_path / f"%(title).50s_{bvid}.%(ext)s"),
        "--merge-output-format", "mp4",
        "--no-warnings",
        f"https://www.bilibili.com/video/{bvid}",
    ]
    
    print(f"  📥 下载 {bvid} -> {sub_dir}/")
    start = time.time()
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        dur = time.time() - start
        
        new_files = list(out_path.glob(f"*{bvid}*"))
        if new_files:
            f = new_files[0]
            size_mb = f.stat().st_size / 1048576
            info = subprocess.run([
                "ffprobe", "-v", "error", "-select_streams", "v:0",
                "-show_entries", "stream=width,height,r_frame_rate",
                "-of", "csv=p=0", str(f)
            ], capture_output=True, text=True, timeout=10)
            res = info.stdout.strip()
            print(f"  ✅ {bvid}: {size_mb:.0f}MB @ {res} ({dur:.0f}s)")
            return True
        else:
            print(f"  ⚠️ {bvid}: 下载完成但找不到文件 ({dur:.0f}s)")
            return False
    except subprocess.TimeoutExpired:
        print(f"  ❌ {bvid}: 超时")
        return False
    except Exception as e:
        print(f"  ❌ {bvid}: {e}")
        return False

def main():
    print("=" * 60)
    print(f"🏸 B站批处理下载 v2")
    print(f"   目标: {len(DOWNLOAD_LIST)} 个视频")
    categories = sorted(set(d for _, d in DOWNLOAD_LIST))
    for cat in categories:
        count = sum(1 for _, d in DOWNLOAD_LIST if d == cat)
        print(f"   {cat}: {count}")
    print("=" * 60)
    
    success = 0
    fail = 0
    
    for bvid, sub_dir in DOWNLOAD_LIST:
        try:
            if download(bvid, sub_dir):
                success += 1
            else:
                fail += 1
        except KeyboardInterrupt:
            print("\n⚠️ 用户中断")
            break
    
    print(f"\n📊 下载完成: ✅ {success} / ❌ {fail} / 总 {len(DOWNLOAD_LIST)}")
    for sub_dir in sorted(set(d for _, d in DOWNLOAD_LIST)):
        files = list((RAW_DIR / sub_dir).glob("*.mp4"))
        total_mb = sum(f.stat().st_size for f in files) / 1048576
        print(f"  {sub_dir}: {len(files)} 文件, {total_mb:.0f}MB")

if __name__ == "__main__":
    main()
