# Data Flywheel: Badminton Training Evaluation Monitization

## Core Thesis
Collect basic-action clips from B站/小红书/YouTube → skeleton extraction → T/V/T dataset → GBDT training → blind validation >85% → deploy to mini-program → users upload own videos → AI evaluates with 6-dim radar → show vs pro comparison → upgrade to paid tier.

## Phase 0: MimicMotion Pipeline (Done 2026-06-02)
- AutoDL RTX 4090 D, 24GB VRAM
- SVD base (7GB) + MimicMotion weights (2.9GB) downloaded  
- User selfie + 4K smash skeleton (72 frames, 25 steps) → 1.3MB MP4 in 4min
- Max VRAM: 17.6GB

## Phase 1: Foundational Data Pipeline (Next)
### Action selection
1. 正手高远球 L1 — 5 coach videos
2. 原地杀球 L1 — 5 coach videos  
3. 正手吊球 L1 — 5 coach videos
4. 网前搓球 L1 — 5 coach videos
5. 正手上网步法 L1 — 5 coach videos

### Collection sources (China-friendly)
- B站: use cookies for downloading (Chrome encrypted cookies issue; need plain cookies.txt)
- YouTube: blocked from China; skip or use archive.org
- 小红书: has native video uploads but no batch API

### Dataset construction
- Per action: 50-100 clips (6..20s each)
- Manual labeling: correct / mistake-A / mistake-B / fail (4 categories)
- Split: 60% train, 20% val, 20% test

### Model training
- Feature engineering: 28-dim biomechanical features extracted from skeleton
- Model: GBDT (current best at 97.9% RF, 98.1% GBDT on 498 clips)
- Validation gate: >85% cross-val accuracy on test set
- Blind test: 5 unseen videos, user acceptance ("靠谱") required

## Phase 2: Product Packaging
See `pose-guided-video-generation` skill: `references/badminton-training-monetization-pipeline.md`

## Phase 3: Tier Progression
L1 base actions online → user retention validated → L2 mid-tier actions → L3 advanced → doubles module → all 23 categories × 127 sub-skills
