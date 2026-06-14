#!/usr/bin/env python3
"""
MimicMotion inference: photo + skeleton → video
Verified working on AutoDL RTX 4090 D (2026-06-02)
Four iterations across the session converged on this proven approach.

KEY FIXES over the session:
  v1: Manual component loading crashed on _execution_device
  v2: MimicMotionModel() loader worked but .to() on pipeline crashed
  v3: __dict__ injection of _execution_device was blocked by __getattr__
  v4: Passing device= to __call__ worked for one run but failed silently on another
  FINAL: MimicMotionModel + manual .to() per component + NO pipeline.to() + imageio video output

CRITICAL RULES (ignore at your peril):
  1. NEVER call pipeline.to(device) — crashes: "property '_execution_device' has no setter"
  2. NEVER import from mimicmotion.models.* — those files are "404: Not Found" stubs
  3. ALWAYS use imageio.get_writer() for video output, NEVER cv2.VideoWriter
     (OpenCV's mp4v codec on AutoDL produces corrupt green-screen videos)
  4. ALWAYS set tile_size >= num_frames or loop crashes: "IndexError: list index out of range"
  5. ALWAYS pass device=torch.device("cuda") as the kwarg to pipeline.__call__()
"""

import torch, json, cv2, numpy as np, os, sys, time
from PIL import Image
sys.path.insert(0, "/root/autodl-tmp/MimicMotion")  # Must match actual directory name

from mimicmotion.utils.loader import MimicMotionModel
from mimicmotion.pipelines.pipeline_mimicmotion import MimicMotionPipeline

# ── CONFIG ──────────────────────────────────────────────
SVD_PATH = "models/svd_base/stabilityai/stable-video-diffusion-img2vid-xt-1-1"
CKPT_PATH = "models/mimicmotion_weights/MimicMotion_1-1.pth"
REF_IMAGE = "data/test/selfie.jpg"
SKEL_JSON = "data/test/selfie_skel.json"
OUTPUT = "output/result.mp4"
DEVICE = "cuda"
NUM_STEPS = 25
TILE_SIZE = 24
TILE_OVERLAP = 4
DECODE_CHUNK = 8
FPS = 8
# ────────────────────────────────────────────────────────

_l = lambda m: print(f"[{time.strftime('%H:%M:%S')}] {m}", flush=True)

_l("Loading SVD...")
t0 = time.time()
models = MimicMotionModel(SVD_PATH)
_l(f"Structure: {time.time()-t0:.0f}s")

_l("Loading MimicMotion weights...")
t1 = time.time()
ckpt = torch.load(CKPT_PATH, map_location="cpu", weights_only=True)
models.load_state_dict(ckpt, strict=False)
del ckpt
_l(f"Weights: {time.time()-t1:.0f}s")

_l("Moving to CUDA...")
d = torch.device(DEVICE)
models.unet = models.unet.to(d, dtype=torch.float16)
models.vae = models.vae.to(d, dtype=torch.float16)
models.image_encoder = models.image_encoder.to(d, dtype=torch.float16)
models.pose_net = models.pose_net.to(d, dtype=torch.float16)
_l(f"VRAM: {torch.cuda.memory_allocated()/1e9:.1f}GB")

_l("Building pipeline...")
pipeline = MimicMotionPipeline(
    vae=models.vae, unet=models.unet, scheduler=models.noise_scheduler,
    image_encoder=models.image_encoder, feature_extractor=models.feature_extractor,
    pose_net=models.pose_net,
)

_l("Loading data...")
img = Image.open(REF_IMAGE).convert("RGB").resize((1024, 576))
with open(SKEL_JSON) as f: skel = json.load(f)
H, W = 576, 1024
BONES = [(11,12),(11,13),(13,15),(12,14),(14,16),(11,23),(12,24),
         (23,24),(23,25),(25,27),(27,29),(27,31),(24,26),(26,28),
         (28,30),(28,32),(11,0),(12,0)]
pf = []
for fr in skel["frames"]:
    l = fr["lms"]; c = np.zeros((H, W, 3), dtype=np.uint8)
    for i1, i2 in BONES:
        if i1 < len(l) and i2 < len(l):
            cv2.line(c, (int(l[i1][0]*W), int(l[i1][1]*H)),
                        (int(l[i2][0]*W), int(l[i2][1]*H)),
                        (100, 200, 255), 3)
    for lm in l: cv2.circle(c, (int(lm[0]*W), int(lm[1]*H)), 4, (255, 255, 255), -1)
    pf.append(c)
pt = torch.from_numpy(np.stack(pf)).permute(0,3,1,2).float() / 127.5 - 1.0
pt = pt[:, [2,1,0], :, :].to(d, dtype=torch.float16)
_l(f"Pose: {pt.shape}, Frames: {len(pf)}")

_l(f"Inference ({NUM_STEPS} steps)...")
t2 = time.time()
with torch.no_grad(), torch.autocast(DEVICE):
    result = pipeline(
        image=img, image_pose=pt, num_frames=len(pf),
        height=576, width=1024, num_inference_steps=NUM_STEPS,
        max_guidance_scale=2.0, tile_size=TILE_SIZE, tile_overlap=TILE_OVERLAP,
        decode_chunk_size=DECODE_CHUNK,
        device=d,  # REQUIRED kwarg — without it, 2nd+ video in batch crashes
    )
_l(f"Inference: {time.time()-t2:.0f}s")

frames = result.frames[0]
_l(f"Frames: {len(frames)}")

# Use imageio (NOT cv2.VideoWriter — produces green-screen on AutoDL)
import imageio
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
w = imageio.get_writer(OUTPUT, fps=FPS, codec='libx264', quality=8)
for f in frames: w.append_data(np.array(f))
w.close()
_l(f"Video: {OUTPUT}")
_l(f"Max VRAM: {torch.cuda.max_memory_allocated()/1e9:.1f}GB")
_l("=== DONE ===")
