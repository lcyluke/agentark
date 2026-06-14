#!/usr/bin/env python3
"""Verify the installed mediapipe still ships the legacy solutions API.

Newer mediapipe builds (e.g. 0.10.35) drop mp.solutions entirely. Pose-based
pipelines that use `mp.solutions.pose.Pose` need a version that still bundles
it (verified: mediapipe==0.10.14). Run this immediately after `pip install`.

Exit 0 = good to build on. Exit 1 = wrong mediapipe; pin 0.10.14 or migrate
to the mediapipe.tasks PoseLandmarker API.
"""
import sys


def main() -> int:
    try:
        import mediapipe as mp
    except ImportError:
        print("FAIL: mediapipe not installed -> pip install 'mediapipe==0.10.14'")
        return 1

    ver = getattr(mp, "__version__", "unknown")
    if not hasattr(mp, "solutions"):
        print(f"FAIL: mediapipe {ver} has no `solutions` API.")
        print("      Pin 'mediapipe==0.10.14' OR rewrite to mediapipe.tasks "
              "PoseLandmarker.")
        return 1

    try:
        from mediapipe.python.solutions import pose  # noqa: F401
    except ModuleNotFoundError:
        print(f"FAIL: mediapipe {ver} lacks mediapipe.python.solutions.pose.")
        print("      Pin 'mediapipe==0.10.14'.")
        return 1

    print(f"OK: mediapipe {ver} has solutions.pose — safe to build on.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
