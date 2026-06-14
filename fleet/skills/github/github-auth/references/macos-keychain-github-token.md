# macOS Keychain Token Extraction

When `gh auth status` shows not authenticated and no `GITHUB_TOKEN` env var is set, try the macOS keychain as a fallback.

## Extraction Command

```bash
GITHUB_TOKEN=$(security find-internet-password -s github.com -w 2>/dev/null)
```

This reads the GitHub personal access token stored in the macOS Keychain (if the user previously saved it via browser or `git credential-osxkeychain`).

## Usage Pattern

```python
import subprocess

token = subprocess.check_output(
    ["security", "find-internet-password", "-s", "github.com", "-w"],
    stderr=subprocess.DEVNULL
).decode().strip()

# Use with curl for API calls
curl -s -H "Authorization: token $GITHUB_TOKEN" \
  https://api.github.com/user
```

## Create Repo via API (when gh CLI is unavailable)

```python
payload = json.dumps({
    "name": "repo-name",
    "description": "Description",
    "private": False
})
subprocess.run(["curl", "-s", "-X", "POST",
    "-H", f"Authorization: token {token}",
    "-H", "Accept: application/vnd.github+json",
    "https://api.github.com/user/repos",
    "-d", payload])
```

## Pitfall

- `gh auth login --with-token` requires device flow interaction (browser) — avoid in headless/remote contexts. Use the keychain → curl path instead.
- SSH keys often work for `git push/pull` but NOT for GitHub API calls. API always needs a PAT.
