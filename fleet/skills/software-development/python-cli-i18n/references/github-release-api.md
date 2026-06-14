# GitHub Release via API (No `gh` CLI)

Create a GitHub Release with body text and auto-generated source archives. Uses `curl` + personal access token — no `gh` CLI needed.

## Prerequisites

- Personal access token with `repo` scope
- Token stored in macOS keychain: `security find-internet-password -s github.com -w`
- Or exported as `GITHUB_TOKEN` env var

## Create a Release

```python
import json, subprocess

# 1. Write release body to a temp file (avoids shell escaping hell)
body = open("/tmp/release_body.md").read()

# 2. Build payload
payload = json.dumps({
    "tag_name": "v1.0.0",
    "name": "v1.0.0 — First Release",
    "body": body,
    "draft": False,
    "prerelease": False
})

# 3. Get token from macOS keychain
token = subprocess.check_output(
    ["security", "find-internet-password", "-s", "github.com", "-w"],
    stderr=subprocess.DEVNULL
).decode().strip()

# 4. POST to GitHub API
result = subprocess.check_output([
    "curl", "-s", "-X", "POST",
    "-H", f"Authorization: token {token}",
    "-H", "Accept: application/vnd.github+json",
    "https://api.github.com/repos/OWNER/REPO/releases",
    "-d", payload
]).decode()

data = json.loads(result)
print(data.get("html_url", data.get("message", "ERROR")))
```

## Pitfalls

1. **Never embed multiline body in shell heredoc + inline python** — the `'''` quote nesting + shell variable interpolation will break. Write to a temp file first, then read it from Python.

2. **Tag must exist before creating the release** — push the tag first:
   ```bash
   git tag -a v1.0.0 -m "Release message"
   git push --follow-tags
   ```

3. **GitHub auto-generates source.zip + source.tar.gz** for every release tag — no need to manually upload assets for Python source projects.

4. **`execute_code` is cleaner than inline terminal** for payload construction — the JSON escaping in shell is fragile. Use the Python snippet above via `execute_code`.
