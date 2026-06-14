#!/usr/bin/env python3
"""
v2 Pipeline: Precision Action Clip Extraction for Badminton Instructional Videos
Strategy: low-threshold scene detection + audio silence detection = precise demo segments

Usage:
  cd ~/Desktop/2026AIAPP/badminton-label-system
  python3 scripts/p0_pipeline_v2.py

Output:
  data/processed_videos/<category>/<video>/_demoXXX_*.mp4  (action clips)
  data/transcripts/<video>.txt / .json                      (whisper transcript)
  data/processed_videos/p0_v2_summary.json                  (summary report)

Configuration:
  SCENE_THRESHOLD = 0.15   # ffmpeg scene detection sensitivity
  SILENCE_THRESHOLD = "-30dB"  # audio noise floor
  MIN_SILENCE = 0.5        # seconds of silence = boundary
  MIN_CLIP = 3             # minimum action clip duration
  MAX_CLIP = 60            # maximum action clip duration
"""

import json, subprocess, os, sys, re
from pathlib import Path

RAW_DIR = Path("data/raw_videos").resolve()
OUTPUT_DIR = Path("data/processed_videos").resolve()
TSCRIPT_DIR = Path("data/transcripts").resolve()

SCENE_THRESHOLD = 0.15
SILENCE_THRESHOLD = "-30dB"
MIN_SILENCE = 0.5
MIN_CLIP = 3
MAX_CLIP = 60
MAX_TALK_CLIP = 180

P0_CATEGORIES = {
    "serve": "发球", "drive": "平抽挡", "lob": "挑球",
    "block": "接杀防守", "serve_return": "接发球", "transition": "过渡球",
}


def ffmpeg(cmd, timeout=60):
    result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
    return result.stdout + result.stderr


def get_duration(path):
    r = ffmpeg(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)], 10)
    try: return float(r.strip())
    except: return 0


def detect_scenes(path):
    out = ffmpeg(["ffmpeg", "-i", str(path), "-vf", f"select='gt(scene,{SCENE_THRESHOLD})',showinfo", "-vsync", "vfr", "-f", "null", "-"], 120)
    pts = []
    for line in out.split('\n'):
        if 'pts_time:' in line:
            m = re.search(r'pts_time:([0-9.]+)', line)
            if m and float(m.group(1)) > 0.3: pts.append(float(m.group(1)))
    return sorted(set(pts))


def detect_silence(path):
    out = ffmpeg(["ffmpeg", "-i", str(path), "-af", f"silencedetect=noise={SILENCE_THRESHOLD}:d={MIN_SILENCE}", "-f", "null", "-"], 120)
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


def process_video(video_path, cat_en, cat_cn):
    print(f"\n  🎬 {cat_cn}/{video_path.name}")
    duration = get_duration(video_path)
    print(f"     {duration:.0f}s")

    scenes = detect_scenes(video_path)
    sil_starts, sil_ends = detect_silence(video_path)
    boundaries = set(scenes)
    for s in sil_starts + sil_ends:
        boundaries.add(round(s, 1))
    boundaries.add(0.0)
    boundaries.add(duration)
    boundaries = sorted(boundaries)
    print(f"     Boundaries: {len(boundaries)} ({len(scenes)} scenes + silence)")

    merged = [boundaries[0]]
    for i in range(1, len(boundaries)):
        gap = boundaries[i] - merged[-1]
        if gap >= MIN_CLIP: merged.append(boundaries[i])
    merged[-1] = duration

    clip_dir = OUTPUT_DIR / cat_en / video_path.stem
    clip_dir.mkdir(parents=True, exist_ok=True)

    action_clips = []
    talking_segment = None

    for i in range(len(merged)-1):
        start, end = merged[i], merged[i+1]
        seg_type = classify_segment(start, end)
        if seg_type == "action_demo":
            clip_name = f"{video_path.stem}_demo{i:03d}_{start:.0f}s.mp4"
            clip_path = clip_dir / clip_name
            ffmpeg(["ffmpeg", "-ss", str(start), "-t", str(end-start), "-i", str(video_path), "-c", "copy", "-avoid_negative_ts", "make_zero", "-y", str(clip_path)], 120)
            if clip_path.exists() and clip_path.stat().st_size > 50000:
                size_mb = clip_path.stat().st_size / 1048576
                action_clips.append({"file": clip_name, "start": round(start,1), "end": round(end,1), "duration": round(end-start,1), "size_mb": round(size_mb,1)})
                print(f"     ✅ Demo: {start:.0f}s-{end:.0f}s ({end-start:.0f}s, {size_mb:.1f}MB)")
        elif seg_type == "talking" and talking_segment is None:
            talking_segment = {"start": start, "end": end}
            print(f"     💬 Talking: {start:.0f}s-{end:.0f}s")

    # Whisper on first 300s
    transcript_file = TSCRIPT_DIR / f"{video_path.stem}.json"
    if not transcript_file.exists():
        audio_tmp = clip_dir / "_audio_tmp.wav"
        ffmpeg(["ffmpeg", "-ss", "0", "-t", str(min(duration, 300)), "-i", str(video_path), "-vn", "-ar", "16000", "-ac", "1", "-y", str(audio_tmp)], 120)
        subprocess.run([sys.executable, "-m", "whisper", str(audio_tmp), "--model", "tiny", "--language", "zh", "--output_dir", str(TSCRIPT_DIR), "--output_format", "json"], capture_output=True, text=True, timeout=600)
        whisper_json = TSCRIPT_DIR / "_audio_tmp.json"
        if whisper_json.exists(): whisper_json.rename(transcript_file)
        if audio_tmp.exists(): audio_tmp.unlink()

    return {"video": video_path.name, "duration_s": round(duration, 1), "action_clips": action_clips, "total_clips": len(action_clips)}


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    TSCRIPT_DIR.mkdir(parents=True, exist_ok=True)
    summary, grand_total = {}, 0

    for cat_en, cat_cn in P0_CATEGORIES.items():
        print(f"\n{'='*50}\n📂 [{cat_en}] {cat_cn}\n{'='*50}")
        cat_dir = RAW_DIR / cat_en
        if not cat_dir.exists(): print(f"  ❌ Missing: {cat_dir}"); continue
        videos = sorted(cat_dir.glob("*.mp4"))
        print(f"  Videos: {len(videos)}")
        cat_total, cat_videos = 0, {}
        for v in videos:
            result = process_video(v, cat_en, cat_cn)
            cat_total += result["total_clips"]
            grand_total += result["total_clips"]
            cat_videos[v.name] = result
        summary[cat_en] = {"category": cat_cn, "videos": cat_videos, "clips": cat_total}

    (OUTPUT_DIR / "p0_v2_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2))
    print(f"\n✅ P0 v2 Complete! Total clips: {grand_total}")


if __name__ == "__main__":
    main()
