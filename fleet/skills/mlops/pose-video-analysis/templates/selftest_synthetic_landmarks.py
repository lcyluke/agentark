"""Template: synthetic-landmark selftest for a pose-analysis pipeline.

WHY: MediaPipe is trained on real humans — synthetic stick-figure *videos*
get ~17% detection and zero events, so a video-based demo cannot verify the
analyzer/diagnoser. This harness hand-builds MediaPipe-format landmark
arrays directly and runs them through analyzer -> footwork -> reference
comparison -> coach, exercising every code path with no video / network /
model weights. It also doubles as a regression test.

Adapt: swap the imports for your package, and shape the two motion segments
to a "good execution" and a "flawed execution" for YOUR sport so every
diagnosis branch fires.

MediaPipe Pose landmark indices used here (full set is 33):
  0 nose | 11 L-shoulder 12 R-shoulder | 13 L-elbow 14 R-elbow
  15 L-wrist 16 R-wrist | 23 L-hip 24 R-hip | 25 L-knee 26 R-knee
  27 L-ankle 28 R-ankle. Each landmark row = (x, y, z, visibility),
  x/y normalized 0..1, origin top-left (y grows downward).
"""
import numpy as np

# from yourpkg.pose_estimator import FramePose
# from yourpkg.stroke_analyzer import StrokeAnalyzer
# from yourpkg.footwork_analyzer import FootworkAnalyzer
# from yourpkg.reference_library import ReferenceLibrary
# from yourpkg.coach import Coach

FPS = 30.0
N = 120


def make_frame(FramePose, fr, rw, re, rs, ls, hp, kn, ak):
    """Build one FramePose from a few key (x,y) points; rest filled plausibly.

    rw=right wrist, re=right elbow, rs=right shoulder, ls=left shoulder,
    hp=hip, kn=knee, ak=ankle  — each a (x, y) tuple in 0..1.
    """
    lm = np.zeros((33, 4), np.float32)
    lm[:, 3] = 0.95  # visibility — keep > 0.3 or points get filtered
    lm[0] = [0.50, 0.12, 0, 0.95]            # nose
    lm[12] = [*rs, 0, 0.95]; lm[11] = [*ls, 0, 0.95]
    lm[14] = [*re, 0, 0.95]; lm[16] = [*rw, 0, 0.95]
    lm[13] = [0.40, 0.40, 0, 0.95]; lm[15] = [0.38, 0.55, 0, 0.95]
    lm[24] = [*hp, 0, 0.95]; lm[23] = [0.45, 0.55, 0, 0.95]
    lm[26] = [*kn, 0, 0.95]; lm[25] = [0.45, 0.78, 0, 0.95]
    lm[28] = [*ak, 0, 0.95]; lm[27] = [0.45, 0.97, 0, 0.95]
    return FramePose(fr, fr / FPS, lm)


def build_poses(FramePose):
    """Two motion segments: a clean execution then a flawed one.

    Segment 1 (good): high contact point, full arm extension, strong
    rotation, knee bend — a fast wrist spike around frame 20-26.
    Segment 2 (flawed): low contact, half-bent arm, no rotation, no knee
    bend — a weaker spike around frame 22-28 of the segment.
    """
    poses = []
    for i in range(N):
        if i < 50:
            t = i / 50.0
            if 20 <= i <= 26:                # fast wrist spike = the "hit"
                wy, wx = 0.10 + (i - 20) * 0.06, 0.60 + (i - 20) * 0.02
            else:
                wy, wx = 0.45 - 0.35 * np.sin(np.pi * t), 0.58
            poses.append(make_frame(
                FramePose, i, (wx, wy), (0.55, 0.28), (0.52, 0.32),
                (0.40, 0.40), (0.50, 0.55), (0.55, 0.74), (0.52, 0.96)))
        else:
            j = i - 50
            t = j / 50.0
            if 22 <= j <= 28:
                wy, wx = 0.42 + (j - 22) * 0.015, 0.54
            else:
                wy, wx = 0.55 - 0.10 * np.sin(np.pi * t), 0.52
            poses.append(make_frame(
                FramePose, i, (wx, wy), (0.50, 0.45), (0.49, 0.40),
                (0.46, 0.41), (0.48, 0.56), (0.48, 0.77), (0.48, 0.97)))
    return poses


def run_selftest(FramePose, StrokeAnalyzer, FootworkAnalyzer,
                 ReferenceLibrary, Coach):
    poses = build_poses(FramePose)
    events = StrokeAnalyzer(fps=FPS).analyze(poses)
    fw = FootworkAnalyzer(
        fps=FPS, stroke_frames=[e.frame_idx for e in events]).analyze(poses)
    cmps = ReferenceLibrary().compare_session(events)
    print(f"selftest: {N} synthetic frames, {len(events)} events detected\n")
    print(Coach(use_llm=False).full_report(events, fw, cmps))
    assert len(events) >= 1, "event detection failed"
    assert cmps, "reference comparison failed"
    print("\nOK: detection + footwork + comparison + coaching all green")


if __name__ == "__main__":
    # Wire up your real imports and call:
    # run_selftest(FramePose, StrokeAnalyzer, FootworkAnalyzer,
    #              ReferenceLibrary, Coach)
    raise SystemExit("Wire imports for your package, then call run_selftest()")
