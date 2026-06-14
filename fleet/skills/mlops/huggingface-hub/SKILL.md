---
name: huggingface-hub
description: "HuggingFace hf CLI: search/download/upload models, datasets."
version: 1.0.0
author: Hugging Face
license: MIT
tags: [huggingface, hf, models, datasets, hub, mlops]
platforms: [linux, macos, windows]
---

# Hugging Face CLI (`hf`) Reference Guide

The `hf` command is the modern command-line interface for interacting with the Hugging Face Hub, providing tools to manage repositories, models, datasets, and Spaces.

> **IMPORTANT:** The `hf` command replaces the now deprecated `huggingface-cli` command.

## Quick Start
*   **Installation:** `curl -LsSf https://hf.co/cli/install.sh | bash -s`
*   **Help:** Use `hf --help` to view all available functions and real-world examples.
*   **Authentication:** Recommended via `HF_TOKEN` environment variable or the `--token` flag.

---

## Core Commands

### General Operations
*   `hf download REPO_ID`: Download files from the Hub.
*   `hf upload REPO_ID`: Upload files/folders (recommended for single-commit).
*   `hf upload-large-folder REPO_ID LOCAL_PATH`: Recommended for resumable uploads of large directories.
*   `hf sync`: Sync files between a local directory and a bucket.
*   `hf env` / `hf version`: View environment and version details.

### Authentication (`hf auth`)
*   `login` / `logout`: Manage sessions using tokens from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens).
*   `list` / `switch`: Manage and toggle between multiple stored access tokens.
*   `whoami`: Identify the currently logged-in account.

### Repository Management (`hf repos`)
*   `create` / `delete`: Create or permanently remove repositories.
*   `duplicate`: Clone a model, dataset, or Space to a new ID.
*   `move`: Transfer a repository between namespaces.
*   `branch` / `tag`: Manage Git-like references.
*   `delete-files`: Remove specific files using patterns.

---

## Specialized Hub Interactions

### Datasets & Models
*   **Datasets:** `hf datasets list`, `info`, and `parquet` (list parquet URLs).
*   **SQL Queries:** `hf datasets sql SQL` — Execute raw SQL via DuckDB against dataset parquet URLs.
*   **Models:** `hf models list` and `info`.
*   **Papers:** `hf papers list` — View daily papers.

### Discussions & Pull Requests (`hf discussions`)
*   Manage the lifecycle of Hub contributions: `list`, `create`, `info`, `comment`, `close`, `reopen`, and `rename`.
*   `diff`: View changes in a PR.
*   `merge`: Finalize pull requests.

### Infrastructure & Compute
*   **Endpoints:** Deploy and manage Inference Endpoints (`deploy`, `pause`, `resume`, `scale-to-zero`, `catalog`).
*   **Jobs:** Run compute tasks on HF infrastructure. Includes `hf jobs uv` for running Python scripts with inline dependencies and `stats` for resource monitoring.
*   **Spaces:** Manage interactive apps. Includes `dev-mode` and `hot-reload` for Python files without full restarts.

### Storage & Automation
*   **Buckets:** Full S3-like bucket management (`create`, `cp`, `mv`, `rm`, `sync`).
*   **Cache:** Manage local storage with `list`, `prune` (remove detached revisions), and `verify` (checksum checks).
*   **Webhooks:** Automate workflows by managing Hub webhooks (`create`, `watch`, `enable`/`disable`).
*   **Collections:** Organize Hub items into collections (`add-item`, `update`, `list`).

---

## Advanced Usage & Tips

### Global Flags
*   `--format json`: Produces machine-readable output for automation.
*   `-q` / `--quiet`: Limits output to IDs only.

### Extensions & Skills
*   **Extensions:** Extend CLI functionality via GitHub repositories using `hf extensions install REPO_ID`.
*   **Skills:** Manage AI assistant skills with `hf skills add`.

## China Network Limitations

When downloading models from mainland China, the standard `hf download`, `huggingface_hub` Python library, and `hf-mirror.com` may all fail due to CloudFront/XetHub CDN blocking. See `references/download-from-china.md` for workarounds using direct curl URLs and cloud GPU alternatives.

## Authentication & gated models

### Token usage
Set `HF_TOKEN` env var to authenticate:

```bash
export HF_TOKEN="hf_xxxxxxxxx"
```

Without a token, unauthenticated requests have lower rate limits (`x-hf-warning: unauthenticated`).

### Gated models (gated:auto)

Models like `stabilityai/stable-video-diffusion-img2vid-xt-1-1` require:

#### Programmatic access acceptance (if HF_TOKEN is available)

Use `huggingface_hub.snapshot_download()` with `token=` — if the user's account already accepted the license, this works directly. If not, you'll get 403.

#### Browser-based acceptance flow

If the model returns 403 even with a valid token, the license agreement has NOT been accepted yet. The UI has changed from earlier patterns — there is NO simple "I Accept" button. Instead:

1. Navigate to `https://huggingface.co/{org}/{repo}` while logged in
2. Look for the section **"You need to agree to share your contact information to access this model"**
3. Click **"Expand to review and access"** button (NOT a direct accept)
4. Scroll down—a **form** appears with:
   - **Name** text input
   - **Company Name (if applicable)** (optional text input)
   - **Email** text input
   - **Other Comments** (optional)
   - **Checkbox**: "By clicking here, you accept the License agreement, and will use the Software Products and Derivative Works for non-commercial or research purposes only"
   - **Checkbox**: "By clicking here, you agree to sharing with Stability AI the information contained within this form and that Stability AI can contact you for the purposes of marketing our products and services"
   - **Submit** button
5. Fill in Name + Email + check both boxes → click Submit
6. On success: page shows **"You have been granted access to this model"** banner
7. After acceptance, downloads work immediately (token — even a read-only token — is sufficient)

#### Auth status detection

After acceptance:
```bash
curl -sI -H "Authorization: Bearer $HF_TOKEN" \
  "https://huggingface.co/{org}/{repo}/resolve/main/model_index.json" | head -5
```
- `401`: token missing or invalid
- `403`: license not accepted (or token lacks read scope)
- `200`: success — download works
- `302`: success (redirect to S3 CDN; the auth passed)

#### Notes

- The `hf` CLI can also accept gated model licenses: `hf repo accept-license {org}/{repo}` — though this requires appropriate token scopes.
- Once accepted by a user account, ALL tokens under that account can download the model (both read and write tokens).
- Acceptance is **per-user-account** — a different HF account would need to go through the flow separately.

### `hf` CLI vs `huggingface-cli`

The old `huggingface-cli` is **deprecated and no longer works**. Use the new `hf` CLI:
```bash
# WRONG — prints deprecation warning, does nothing:
huggingface-cli download tencent/MimicMotion

# RIGHT:
hf download tencent/MimicMotion --local-dir models/
```

Fallback if `hf` fails (e.g. XetHub CDN blocked): use direct `curl` with the resolve URL.

### Direct curl download pattern (China workaround)

When `hf download` fails due to CDN blocking, download via direct curl:

```bash
# For open models (gated:false)
curl -L -C - --retry 3 --retry-delay 10 \
  -o "model.pth" \
  "https://huggingface.co/{org}/{repo}/resolve/main/{filename}?download=true"
# -C - enables resume, --retry handles transient failures
# Speed on home broadband: ~100-160 MB/min

# For gated models (requires accepted license + token):
curl -L -C - --retry 3 --retry-delay 10 \
  -H "Authorization: Bearer $HF_TOKEN" \
  -o "model.safetensors" \
  "https://huggingface.co/{org}/{repo}/resolve/main/{subfolder}/{filename}?download=true"
```
