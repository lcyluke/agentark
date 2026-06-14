# Git Push Troubleshooting — Large Repos & Network Blocks

## Symptoms

- `git push` times out after 60-300s
- `LibreSSL SSL_connect: SSL_ERROR_SYSCALL` on HTTPS
- `Connection closed by 198.18.x.x port 22` on SSH
- `HTTP 408` — RPC failed, remote end hung up
- `send-pack: unexpected disconnect while reading sideband packet`

## Root Cause

Either (a) the git pack is too large for the network connection (>50MB), or (b) a network proxy/firewall is intercepting GitHub connections.

## Solutions (try in order)

### 1. Fresh Repo from Current State (most reliable)

```bash
# Extract current state without .git history
tar -czf /tmp/project.tar.gz \
  --exclude='.git' --exclude='venv' --exclude='__pycache__' \
  --exclude='*.db' --exclude='*.mp4' --exclude='models' \
  .

# Create fresh repo
cd /tmp && mkdir push && cd push
tar xzf /tmp/project.tar.gz
git init && git add -A
git commit -m "Initial"
git remote add origin <url>
git push -u origin main --force
```

This reduces 74MB repos to ~6MB by stripping git history.

### 2. Try SSH over port 443

```bash
git remote set-url origin ssh://git@ssh.github.com:443/user/repo.git
GIT_SSH_COMMAND="ssh -o ConnectTimeout=30" git push
```

### 3. GitHub API push (no git protocol)

Use Git Data API to create blobs/trees/commits via REST. Works when both SSH and HTTPS are blocked but REST API is accessible. Slower for 200+ files due to per-blob API calls.

### 4. Test connectivity first

```bash
# Clone a small repo to verify GitHub access
cd /tmp && git clone --depth 1 https://github.com/lcyluke/AutoClicker.git test
rm -rf test
```

If this fails, the network is blocking GitHub entirely — none of the above will work.

## Prevention

- Keep repos lean. Exclude large files (models/, venv/, raw_videos/) in .gitignore.
- Use `git gc --aggressive` before pushing to pack loose objects.
- For initial pushes of large projects, prefer the fresh-repo approach.
