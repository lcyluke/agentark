#!/usr/bin/env python3
"""
MimicMotion FastAPI 推理服务器 — 部署到 AutoDL RTX 4090D。
用法: /root/miniconda3/bin/python3 infer_server.py
端口: 8765

POST /infer  — {"photo_b64": "...", "skeleton": {...}, "num_steps": 10, "num_frames": 48} → mp4
GET /health   — {"ok": true, "pipeline_loaded": true, "vram_gb": 8.5}
"""
import base64, json, os, sys, time, uuid
from io import BytesIO
from pathlib import Path
import cv2, numpy as np, torch
from PIL import Image
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

# === 部署前修改这行路径 ===
sys.path.insert(0, "/root/autodl-tmp/MimicMotion")
# =========================

MIMIC_HOME = Path("/root/autodl-tmp/MimicMotion")
MODEL_DIR = MIMIC_HOME / "models"
SVD_PATH = MODEL_DIR / "svd_base" / "stabilityai" / "stable-video-diffusion-img2vid-xt-1-1"
CKPT_PATH = MODEL_DIR / "mimicmotion_weights" / "MimicMotion_1-1.pth"
OUTPUT_DIR = MIMIC_HOME / "output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

pipeline = None
device = torch.device("cuda")

BONES = [(11,12),(11,13),(13,15),(12,14),(14,16),(11,23),(12,24),(23,24),(23,25),(25,27),(27,29),(27,31),(24,26),(26,28),(28,30),(28,32),(11,0),(12,0)]
H, W = 576, 1024

def render_pose_frames(skel_json):
    frames = skel_json.get("frames", [])
    pf = []
    for fr in frames:
        lms = fr.get("lms", [])
        canvas = np.zeros((H,W,3), dtype=np.uint8)
        for i1,i2 in BONES:
            if i1<len(lms) and i2<len(lms):
                cv2.line(canvas, (int(lms[i1][0]*W),int(lms[i1][1]*H)), (int(lms[i2][0]*W),int(lms[i2][1]*H)), (100,200,255), 3)
        for lm in lms:
            cv2.circle(canvas, (int(lm[0]*W),int(lm[1]*H)), 4, (255,255,255), -1)
        pf.append(canvas)
    if not pf: raise ValueError("empty skeleton")
    pt = torch.from_numpy(np.stack(pf)).permute(0,3,1,2).float()/127.5-1.0
    return pt[:,[2,1,0],:,:].to(device, dtype=torch.float16)

def load_pipeline():
    global pipeline
    from mimicmotion.utils.loader import MimicMotionModel
    from mimicmotion.pipelines.pipeline_mimicmotion import MimicMotionPipeline
    print(f"[{time.strftime('%H:%M:%S')}] Loading models...", flush=True)
    models = MimicMotionModel(str(SVD_PATH))
    ckpt = torch.load(str(CKPT_PATH), map_location="cpu", weights_only=True)
    models.load_state_dict(ckpt, strict=False); del ckpt
    models.unet = models.unet.to(device, dtype=torch.float16)
    models.vae = models.vae.to(device, dtype=torch.float16)
    models.image_encoder = models.image_encoder.to(device, dtype=torch.float16)
    models.pose_net = models.pose_net.to(device, dtype=torch.float16)
    pipeline = MimicMotionPipeline(vae=models.vae, unet=models.unet, scheduler=models.noise_scheduler, image_encoder=models.image_encoder, feature_extractor=models.feature_extractor, pose_net=models.pose_net)
    print(f"[{time.strftime('%H:%M:%S')}] Ready. VRAM: {torch.cuda.memory_allocated()/1e9:.1f}GB", flush=True)

app = FastAPI(title="MimicMotion Server")

class InferReq(BaseModel):
    photo_b64: str
    skeleton: dict
    num_steps: int = 10
    num_frames: int = 48

@app.on_event("startup")
async def startup():
    load_pipeline()

@app.get("/health")
async def health():
    return {"ok": True, "vram_gb": round(torch.cuda.memory_allocated()/1e9, 1)}

@app.post("/infer")
async def infer(req: InferReq):
    if pipeline is None: raise HTTPException(503, "not ready")
    try:
        img = Image.open(BytesIO(base64.b64decode(req.photo_b64))).convert("RGB").resize((W,H))
        pt = render_pose_frames(req.skeleton)
        n = min(pt.shape[0], req.num_frames)
        ts = min(req.num_frames, n)
        t0 = time.time()
        with torch.no_grad(), torch.autocast("cuda"):
            result = pipeline(image=img, image_pose=pt[:n], num_frames=n, height=H, width=W, num_inference_steps=req.num_steps, max_guidance_scale=2.0, tile_size=max(4,ts), tile_overlap=4, decode_chunk_size=4, device=device)
        frames = result.frames[0]
        import imageio
        out = OUTPUT_DIR / f"{uuid.uuid4().hex}.mp4"
        w = imageio.get_writer(str(out), fps=8, codec='libx264', quality=8)
        for f in frames: w.append_data(np.array(f))
        w.close()
        return FileResponse(str(out), media_type="video/mp4", filename="result.mp4", headers={"X-Time": f"{time.time()-t0:.1f}s"})
    except Exception as e:
        import traceback; traceback.print_exc()
        raise HTTPException(500, str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8765)
