# Downloading HF Models from China

Accessing HuggingFace model weights from mainland China is unreliable because:
- `huggingface_hub` Python library uses CloudFront CDN (blocked by GFW)
- `hf` CLI uses XetHub storage (blocked or times out)
- `huggingface-cli` is deprecated and redirects to `hf`
- Individual file resolutions on `huggingface.co` redirect to AWS S3 presigned URLs (also blocked)

## What to do

### Options (in order of reliability)

**Option 1: AutoDL/云GPU (recommended)**
Rent a GPU on AutoDL (¥1.9/h for RTX 4090). AutoDL's servers are inside China but have access to foreign CDNs:
```bash
pip install huggingface_hub
huggingface-cli download tencent/MimicMotion --local-dir models/
# This works from AutoDL
```

**Option 2: Direct curl download (partially works)**
Use the HuggingFace resolve URL directly with curl:
```bash
# For open models (gated:false) — MimicMotion weights
curl -L -C - --retry 3 --retry-delay 10 \
  -o "MimicMotion_1-1.pth" \
  "https://huggingface.co/tencent/MimicMotion/resolve/main/MimicMotion_1-1.pth?download=true"

# This bypasses the hf Python library and uses raw HTTP download.
# Speed on home broadband: ~100-160 MB/min for a 3GB file ≈ 20-25 min
# Resumable: -C - flag enables resume
```

**Option 3: User's browser download for gated models**
For gated models (gated:auto, require login + license agreement):
- Ask the user to open: `https://huggingface.co/{org}/{repo}`
- Click "Agree and access repository" to accept the license
- Then curl from the CLI will work IF the network can reach S3
- If curl still fails (401), send the user the direct download link:
  `https://huggingface.co/{org}/{repo}/resolve/main/{filename}?download=true`

### Token usage for gated models

Set `HF_TOKEN` env var to increase rate limits and access gated models:

```bash
export HF_TOKEN="hf_xxxxxxxxx"
```

For gated models that require a license agreement (gated:auto):
1. The user must be logged into their HF account — check via Firefox cookies or ask
2. Navigate to `https://huggingface.co/{org}/{repo}` in a browser while logged in
3. Click **"Expand to review and access"** — reveals a form with Name/Email/2 checkboxes
4. Fill in Name + Email + check both boxes → click **Submit**
5. After acceptance, downloads work with any valid token
6. Without step 4: even with valid token, curl returns `403 "Access to model is restricted and you are not in the authorized list"`
7. With step 4 + token: curl returns `200` (works from CLI), `hf download` works, `snapshot_download()` works
8. To check auth status: `curl -sI -H "Authorization: Bearer $HF_TOKEN" "https://huggingface.co/{org}/{repo}/resolve/main/{filename}" | head -5`
   - `401`: token missing or invalid
   - `403`: license not accepted
   - `200` or `302`: success

### What does NOT work from China

| Method | From home broadband | From AutoDL/Cloud GPU |
|--------|:-------------------:|:---------------------:|
| `huggingface-cli` | ❌ Deprecated | ❌ Deprecated |
| `hf download` | ❌ XetHub blocked | ❌ XetHub blocked |
| `huggingface_hub.hf_hub_download()` | ❌ CloudFront blocked | ❌ CloudFront blocked |
| `huggingface_hub.snapshot_download()` | ❌ CloudFront blocked | ❌ CloudFront blocked |
| HuggingFace direct (curl) | ⚠️ Sometimes | ❌ Blocked |
| `hf-mirror.com` (open models) | ❌ Blocked | ✅ Works (~1-2 MB/s) |
| `hf-mirror.com` (gated models) | ❌ Blocked | ❌ 401 even with valid token |
| ModelScope `modelscope.cn` | ⚠️ Sometimes | ✅ Works for HF mirrors (~3-4 MB/s) |

### What DOES work on AutoDL

ModelScope (`modelscope.cn`) has a growing HF mirror collection. The `snapshot_download` API works from AutoDL at 3-4 MB/s:

```python
from modelscope.hub.snapshot_download import snapshot_download

model_dir = snapshot_download(
    'stabilityai/stable-video-diffusion-img2vid-xt-1-1',  # HF repo ID
    cache_dir='/path/to/models/svd_base',
    revision='master',
    ignore_file_pattern=['svd_xt_1_1*'],  # optional filter
)
```

Check if ModelScope has your model:
```bash
# Returns JSON with model info if found
curl -s 'https://www.modelscope.cn/api/v1/models/{org}/{repo}'
# If Code=200, it's on ModelScope
```

Also on AutoDL, `hf-mirror.com` works for **open (non-gated) models** via direct curl with `?download=true`:

```bash
curl -L -C - --retry 5 --retry-delay 10 \
  -o "filename.pth" \
  "https://hf-mirror.com/org/repo/resolve/main/filename.pth?download=true"
```

For gated models on AutoDL, ONLY ModelScope works — hf-mirror.com returns 401 even with a valid HF token because it doesn't forward license acceptance.
### Detection pattern

```bash
# Test if HF is reachable from current network
timeout 10 curl -sI "https://huggingface.co" | head -5
# If this succeeds, try:
timeout 10 curl -sI "https://huggingface.co/tencent/MimicMotion/resolve/main/MimicMotion_1-1.pth?download=true" | head -5
# If 302 redirect to S3/xethub.hf.co → likely to fail for downloads
# If 200 → direct curl will work
```
