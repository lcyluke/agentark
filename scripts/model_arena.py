#!/usr/bin/env python3
"""
AgentArk Fleet Model Arena — 本地 vs 云端模型评测
═══════════════════════════════════════════════════
同题对比 GB10 本地模型 vs 官方云端 API。

Usage:
  python3 scripts/model_arena.py                    # 跑全部评测
  python3 scripts/model_arena.py --models qwen72b   # 单模型对比
  python3 scripts/model_arena.py --category code     # 仅测代码
  python3 scripts/model_arena.py --quick             # 快速版(1题)

Output: ~/.apex/model_arena_results.json
"""

from __future__ import annotations

import json
import os
import sys
import time
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Optional

try:
    import httpx
except ImportError:
    print("pip install httpx")
    sys.exit(1)

# ─── Config ─────────────────────────────────────────────────
GB10_BASE = "http://localhost:11434/v1"
DEEPSEEK_BASE = "https://api.deepseek.com/v1"
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_API_KEY", os.environ.get("OPENAI_API_KEY", ""))
RESULTS_FILE = Path(os.path.expanduser("~/.apex/model_arena_results.json"))

# Pairings: local model → cloud counterpart
PAIRINGS = {
    "qwen72b": {
        "local": ("gb10-qwen72b", GB10_BASE, "ollama"),
        "cloud": ("deepseek-v4-pro", DEEPSEEK_BASE, DEEPSEEK_KEY),
        "desc": "Qwen 2.5 72B (本地) vs DeepSeek V4 Pro (云端)",
    },
    "deepseek": {
        "local": ("deepseek-r1:70b", GB10_BASE, "ollama"),
        "cloud": ("deepseek-v4-pro", DEEPSEEK_BASE, DEEPSEEK_KEY),
        "desc": "DeepSeek-R1 70B (本地) vs DeepSeek V4 Pro (云端)",
    },
    "qwen32b": {
        "local": ("qwen2.5:32b", GB10_BASE, "ollama"),
        "cloud": ("deepseek-v4-pro", DEEPSEEK_BASE, DEEPSEEK_KEY),
        "desc": "Qwen 2.5 32B (本地) vs DeepSeek V4 Pro (云端)",
    },
    "llama": {
        "local": ("llama3.3:70b", GB10_BASE, "ollama"),
        "cloud": ("deepseek-v4-pro", DEEPSEEK_BASE, DEEPSEEK_KEY),
        "desc": "Llama 3.3 70B (本地) vs DeepSeek V4 Pro (云端)",
    },
}

# ─── Test Prompts ───────────────────────────────────────────
PROMPTS = {
    "reasoning": [
        {
            "id": "logic-1",
            "prompt": "如果所有的猫都是哺乳动物，所有的哺乳动物都是动物，那么所有的猫都是动物吗？请一步步推理。",
            "metric": "逻辑正确性",
        },
        {
            "id": "logic-2",
            "prompt": "一个房间里有3个开关，分别控制隔壁房间的3盏灯。你只能进隔壁房间一次。如何确定哪个开关控制哪盏灯？",
            "metric": "推理步骤完整性",
        },
    ],
    "code": [
        {
            "id": "code-1",
            "prompt": "用 Python 写一个函数，输入一个整数数组，返回所有和为0的三元组。要求 O(n²) 时间复杂度。只输出代码。",
            "metric": "代码正确性+复杂度",
        },
        {
            "id": "code-2",
            "prompt": "写一个快速的 JSON 解析器，处理嵌套对象和数组，用 Python。只输出代码。",
            "metric": "代码完整可用性",
        },
    ],
    "chinese": [
        {
            "id": "cn-1",
            "prompt": "用200字解释区块链的共识机制，让一个非技术人员能听懂。",
            "metric": "中文表达流畅度",
        },
        {
            "id": "cn-2",
            "prompt": "写一首五言绝句，主题是「AI与人类共存」。",
            "metric": "文学创造力和意境",
        },
    ],
    "knowledge": [
        {
            "id": "kn-1",
            "prompt": "量子纠缠是什么？根据最新研究（2024-2025），有哪些应用突破？简要回答。",
            "metric": "知识准确性+时效性",
        },
    ],
}


# ═══════════════════════════════════════════════════════════
# API Call
# ═══════════════════════════════════════════════════════════

def call_model(model: str, base_url: str, api_key: str,
               prompt: str, timeout: int = 120) -> dict:
    """Call OpenAI-compatible API and return timing + output."""
    client = httpx.Client(timeout=timeout)
    t0 = time.monotonic()

    try:
        r = client.post(
            f"{base_url}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 1024,
                "temperature": 0.3,
            },
        )
        elapsed = time.monotonic() - t0

        if r.status_code != 200:
            return {
                "error": f"HTTP {r.status_code}",
                "output": r.text[:500],
                "elapsed_s": elapsed,
            }

        data = r.json()
        content = data["choices"][0]["message"]["content"]
        usage = data.get("usage", {})

        return {
            "output": content,
            "elapsed_s": round(elapsed, 1),
            "input_tokens": usage.get("prompt_tokens", 0),
            "output_tokens": usage.get("completion_tokens", 0),
            "tokens_per_sec": round(
                usage.get("completion_tokens", 0) / max(elapsed - 0.5, 0.1), 1
            ),
        }
    except Exception as e:
        return {
            "error": str(e)[:300],
            "output": "",
            "elapsed_s": round(time.monotonic() - t0, 1),
        }
    finally:
        client.close()


# ═══════════════════════════════════════════════════════════
# Runner
# ═══════════════════════════════════════════════════════════

def run_arena(pairings: list[str], categories: list[str],
              quick: bool = False) -> dict:
    """Run head-to-head comparisons."""
    results = {
        "timestamp": datetime.now().isoformat(),
        "pairings": {},
    }

    total_tests = 0
    for pair_key in pairings:
        pair = PAIRINGS[pair_key]
        local_name, local_url, local_key = pair["local"]
        cloud_name, cloud_url, cloud_key = pair["cloud"]

        pair_results = {
            "desc": pair["desc"],
            "local_model": local_name,
            "cloud_model": cloud_name,
            "tests": [],
            "summary": {"local_wins": 0, "cloud_wins": 0, "tie": 0,
                        "local_avg_s": 0, "cloud_avg_s": 0},
        }

        local_times, cloud_times = [], []

        for cat in categories:
            prompts = PROMPTS.get(cat, [])
            if quick:
                prompts = prompts[:1]

            for p in prompts:
                test_id = f"{pair_key}/{p['id']}"
                print(f"\n{'='*60}")
                print(f"  🆚 {test_id}")
                print(f"  📋 {p['prompt'][:80]}...")
                print(f"{'='*60}")

                # Local
                print(f"  🏠 {local_name} ...", end=" ", flush=True)
                local_r = call_model(local_name, local_url, local_key, p["prompt"])
                if local_r.get("error"):
                    print(f"❌ {local_r['error']}")
                else:
                    print(f"✅ {local_r['elapsed_s']}s {local_r.get('tokens_per_sec',0)}t/s")

                # Cloud
                print(f"  ☁️  {cloud_name} ...", end=" ", flush=True)
                cloud_r = call_model(cloud_name, cloud_url, cloud_key, p["prompt"])
                if cloud_r.get("error"):
                    print(f"❌ {cloud_r['error']}")
                else:
                    print(f"✅ {cloud_r['elapsed_s']}s {cloud_r.get('tokens_per_sec',0)}t/s")

                test_result = {
                    "id": test_id,
                    "prompt": p["prompt"],
                    "metric": p["metric"],
                    "local": local_r,
                    "cloud": cloud_r,
                }

                # Speed comparison
                if not local_r.get("error"):
                    local_times.append(local_r["elapsed_s"])
                if not cloud_r.get("error"):
                    cloud_times.append(cloud_r["elapsed_s"])

                if local_r.get("elapsed_s") and cloud_r.get("elapsed_s"):
                    speedup = cloud_r["elapsed_s"] / max(local_r["elapsed_s"], 0.1)
                    test_result["speed_winner"] = "local" if speedup > 1 else "cloud"
                    test_result["speed_ratio"] = round(speedup, 2)

                pair_results["tests"].append(test_result)
                total_tests += 1

        if local_times:
            pair_results["summary"]["local_avg_s"] = round(sum(local_times)/len(local_times), 1)
        if cloud_times:
            pair_results["summary"]["cloud_avg_s"] = round(sum(cloud_times)/len(cloud_times), 1)

        results["pairings"][pair_key] = pair_results

    results["total_tests"] = total_tests
    return results


# ═══════════════════════════════════════════════════════════
# Report
# ═══════════════════════════════════════════════════════════

def print_report(results: dict):
    """Pretty-print results."""
    print("\n")
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║           ⚓ AgentArk Model Arena — Results                 ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()

    for pk, pr in results.get("pairings", {}).items():
        s = pr["summary"]
        print(f"  🆚 {pr['desc']}")
        print(f"     {'─'*50}")

        local_avg = s.get("local_avg_s", 0)
        cloud_avg = s.get("cloud_avg_s", 0)
        if local_avg and cloud_avg:
            faster = "🏠 本地更快" if local_avg < cloud_avg else "☁️ 云端更快"
            ratio = cloud_avg / max(local_avg, 0.01)
            print(f"     ⏱ 平均速度: 本地 {local_avg}s | 云端 {cloud_avg}s | {faster} ({ratio:.1f}x)")
        else:
            print(f"     ⏱ 平均速度: 本地 {local_avg}s | 云端 {cloud_avg}s")

        for t in pr["tests"]:
            lid = t["id"].split("/")[-1]
            lerr = t["local"].get("error")
            cerr = t["cloud"].get("error")
            lspeed = t["local"].get("tokens_per_sec", 0)
            cspeed = t["cloud"].get("tokens_per_sec", 0)

            local_status = f"❌ {lerr[:40]}" if lerr else f"✅ {lspeed}t/s"
            cloud_status = f"❌ {cerr[:40]}" if cerr else f"✅ {cspeed}t/s"

            print(f"     {lid:10s} 🏠 {local_status:30s} ☁️ {cloud_status:30s}")
            if not lerr and not cerr:
                print(f"     {'':10s} 🏠 {t['local']['output'][:120].strip()}...")
                print(f"     {'':10s} ☁️ {t['cloud']['output'][:120].strip()}...")

        print()

    print(f"  📊 Total: {results['total_tests']} tests")
    print(f"  📁 Saved: {RESULTS_FILE}")


# ═══════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════

def main():
    import argparse
    parser = argparse.ArgumentParser(description="AgentArk Model Arena")
    parser.add_argument("--models", "-m", default="all",
                        help="Comma-separated: qwen72b,deepseek,qwen32b,llama")
    parser.add_argument("--category", "-c", default="all",
                        help="Test category: reasoning,code,chinese,knowledge")
    parser.add_argument("--quick", "-q", action="store_true",
                        help="Quick mode: 1 prompt per category")
    parser.add_argument("--output", "-o", default="",
                        help="Output file path")
    args = parser.parse_args()

    pairings = list(PAIRINGS.keys()) if args.models == "all" else args.models.split(",")
    categories = list(PROMPTS.keys()) if args.category == "all" else args.category.split(",")

    print(f"⚓ AgentArk Model Arena")
    print(f"   Models: {', '.join(pairings)}")
    print(f"   Categories: {', '.join(categories)}")
    print(f"   Mode: {'Quick' if args.quick else 'Full'}")
    print()

    results = run_arena(pairings, categories, quick=args.quick)

    # Save
    output_path = Path(args.output) if args.output else RESULTS_FILE
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))

    print_report(results)


if __name__ == "__main__":
    main()
