#!/usr/bin/env python3
"""
B站高画质视频场景切割Pipeline
从B站下载的720p/4K视频中精确切出动作片段
输出: data/processed_videos/bilibili/<video_name>/<demo_clips>
"""
import json, subprocess, os, sys, re, math
from pathlib import Path

RAW_DIR = Path("~/Desktop/2026AIAPP/badminton-label-system/data/raw_videos/bilibili").expanduser()
OUTPUT_DIR = Path("~/Desktop/2026AIAPP/badminton-label-system/data/processed_videos").expanduser()

SCENE_THRESHOLD = 0.12
SILENCE_THRESHOLD = "-30dB"
MIN_SILENCE = 0.3
MIN_CLIP = 2
MAX_CLIP = 45
MAX_TALK_CLIP = 120

def ffmpeg(cmd, timeout=120):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr

def get_duration(path):
    r = ffmpeg(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], 10)
    try: return float(r.strip())
    except: return 0

def detect_scenes(path):
    """快速场景检测 — 4K视频自动采用关键帧模式加速"""
    is_4k = False
    try:
        info = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
            "-show_entries", "stream=width", "-of", "csv=p=0", str(path)],
            capture_output=True, text=True, timeout=10)
        w = int(info.stdout.strip().split('\n')[0])
        is_4k = w >= 3840
    except: pass

    vf = f"select='gt(scene,{SCENE_THRESHOLD})',showinfo"
    cmd = ["ffmpeg", "-i", str(path), "-vf", vf, "-vsync", "vfr", "-f", "null", "-"]
    
    if is_4k:
        vf = f"scale=1280:720,{vf}"
        cmd = ["ffmpeg", "-skip_frame", "nokey", "-i", str(path), "-vf", vf, "-vsync", "0", "-f", "null", "-"]
    
    timeout = 300 if is_4k else 120
    out = ffmpeg(cmd, timeout)
    
    pts = []
    for line in out.split('\n'):
        if 'pts_time:' in line:
            m = re.search(r'pts_time:([0-9.]+)', line)
            if m:
                t = float(m.group(1))
                if t > 0.3: pts.append(t)
    return sorted(set(pts))

def detect_silence(path):
    out = ffmpeg([
        "ffmpeg", "-i", str(path),
        "-af", f"silencedetect=noise={SILENCE_THRESHOLD}:d={MIN_SILENCE}",
        "-f", "null", "-"
    ], 120)
    starts, ends = [], []
    for line in out.split('\n'):
        m = re.search(r'silence_start: ([0-9.]+)', line)
        if m: starts.append(float(m.group(1)))
        m = re.search(r'silence_end: ([0-9.]+)', line)
        if m: ends.append(float(m.group(1)))
    return starts, ends

def classify_segment(start, end):
    seg_dur = end - start
    if seg_dur < MIN_CLIP: return "too_short"
    if seg_dur <= MAX_CLIP: return "action_demo"
    if seg_dur <= MAX_TALK_CLIP: return "talking"
    return "oversized"

def get_video_info(path):
    info = ffmpeg([
        "ffprobe", "-v", "error",
        "-select_streams", "v:0",
        "-show_entries", "stream=width,height,r_frame_rate",
        "-of", "csv=p=0", str(path)
    ], 10)
    parts = info.strip().split(',')
    w, h = parts[0], parts[1]
    fps_frac = parts[2]
    fps = round(int(fps_frac.split('/')[0]) / int(fps_frac.split('/')[1])) if '/' in fps_frac else int(fps_frac)
    return int(w), int(h), fps

def process_bili_video(video_path):
    print(f"\n{'='*60}")
    print(f"🎬 处理: {video_path.name}")
    duration = get_duration(video_path)
    w, h, fps = get_video_info(video_path)
    print(f"   时长: {duration:.0f}s | 画质: {w}×{h} @ {fps}fps")
    
    scenes = detect_scenes(video_path)
    sil_starts, sil_ends = detect_silence(video_path)
    
    boundaries = set(scenes)
    for s in sil_starts + sil_ends:
        boundaries.add(round(s, 1))
    boundaries.add(0.0)
    boundaries.add(duration)
    boundaries = sorted(boundaries)
    
    merged = [boundaries[0]]
    for i in range(1, len(boundaries)):
        gap = boundaries[i] - merged[-1]
        if gap < MIN_CLIP:
            continue
        merged.append(boundaries[i])
    merged[-1] = duration
    
    clip_dir = OUTPUT_DIR / "bilibili" / video_path.stem
    clip_dir.mkdir(parents=True, exist_ok=True)
    
    action_clips = []
    stats = {"action_demo": 0, "talking": 0, "too_short": 0, "oversized": 0}
    
    for i in range(len(merged)-1):
        start, end = merged[i], merged[i+1]
        seg_type = classify_segment(start, end)
        stats[seg_type] += 1
        
        if seg_type == "action_demo":
            clip_name = f"{video_path.stem}_demo{i:03d}_{start:.0f}s.mp4"
            clip_path = clip_dir / clip_name
            ok = ffmpeg([
                "ffmpeg", "-ss", str(start), "-t", str(end-start),
                "-i", str(video_path), "-c", "copy",
                "-avoid_negative_ts", "make_zero", "-y", str(clip_path)
            ], 120)
            if ok and clip_path.exists() and clip_path.stat().st_size > 50000:
                size_mb = clip_path.stat().st_size / 1048576
                action_clips.append({
                    "file": clip_name, "start": round(start,1), "end": round(end,1),
                    "duration": round(end-start,1), "size_mb": round(size_mb,1)
                })
    
    return {
        "video": video_path.name,
        "resolution": f"{w}×{h}",
        "fps": fps,
        "duration_s": round(duration, 1),
        "segments": stats,
        "action_clips": action_clips,
        "total_clips": len(action_clips),
    }

def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    all_videos = sorted(RAW_DIR.rglob("*.mp4"))
    results = {}
    grand_total = 0
    
    for v in all_videos:
        rel = v.relative_to(RAW_DIR)
        result = process_bili_video(v)
        results[str(rel)] = result
        grand_total += result["total_clips"]
    
    report_path = OUTPUT_DIR / "bilibili" / "_bili_clip_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(results, ensure_ascii=False, indent=2))
    
    print(f"\n✅ 完成! 共切出 {grand_total} 个动作片段")

if __name__ == "__main__":
    main()
