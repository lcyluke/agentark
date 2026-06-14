# WeChat DevTools CLI Workflow (羽球宝AI搭子)

WeChat Developer Tools CLI at `/Applications/wechatwebdevtools.app/Contents/MacOS/cli`
on the local dev machine (`/Users/Mac`).

## Available Commands

```
cli open             — Open project in IDE
cli auto             — Open project + start automation mode (preferred over `open`)
cli preview          — Generate preview QR code (scan on phone)
cli auto-preview     — Auto open + preview in one command
cli upload           — Upload code to WeChat backend for release
cli build-npm        — Build npm dependencies
cli login            — Re-login IDE
cli islogin          — Check login status
cli close            — Close project
cli quit             — Quit IDE
```

## Workflow: Compile + Preview (local devtest)

### Quick compile (`auto`)

```bash
CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
PROJ="/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/miniprogram"

# One-shot: open IDE, load project, start automation, compile
"$CLI" auto --project "$PROJ"
```

Expected output on success:
```
✔ IDE server has started, listening on http://127.0.0.1:43673
✔ Using AppID: wxdad7cddb0cfa785e
✔ auto
```

### Generate preview QR (scan on phone)

```bash
mkdir -p /tmp/wechat_qr
"$CLI" preview --project "$PROJ" --qr-format image --qr-output /tmp/wechat_qr/preview.png

# Also outputs terminal table with bundle size:
# ┌─────────┬───────────┬─────────────┐
# │ (index) │   size    │ size (Byte) │
# ├─────────┼───────────┼─────────────┤
# │  TOTAL  │ '67.4 KB' │    69032    │
# └─────────┴───────────┴─────────────┘
```

⚠️ **QR codes expire** (appx 5-10 min) — send to user immediately via MEDIA:/tmp/wechat_qr/preview.png.

## Key Config: project.config.json location and structure

**CRITICAL: DevTools CLI always reads `project.config.json` from `--project <dir>`.**
- If `--project ./miniprogram` → looks for `./miniprogram/project.config.json`
- The `miniprogramRoot` field is ONLY needed if `project.config.json` is at the repo root AND `app.json` is under `miniprogram/`
- When passing `--project <dir>` directly to the miniprogram directory, **do NOT include `miniprogramRoot`** — it confuses the CLI and produces "请检查 project.config.json 是否存在及是否有效 (code 19)"

Correct config when `--project` points to miniprogram dir:
```json
{
  "setting": {
    "urlCheck": false,
    "es6": true,
    "enhance": false,          /* MUST be false — see @babel bug below */
    "postcss": true,
    "minified": true,
    "minifyWXML": true
  },
  "compileType": "miniprogram",
  "libVersion": "2.33.0",      /* MUST be 2.33.0 not 3.4.0+ — see @babel bug */
  "appid": "wxdad7cddb0cfa785e",
  "projectname": "badminton-coach-ai"
}
```

## Pitfalls (from actual session experience)

### 1. `--project` path must point to the dir containing `project.config.json`

- Good: `--project ./miniprogram` (where project.config.json lives)
- Bad: `--project .` (if root has no project.config.json) — produces "请检查 project.config.json (code 19)"
- The `auto` command is more tolerant than `open` — `auto` tries to connect to a running IDE first

### 2. `@babel/runtime` / enhance mode packaging bug

Error: `module '@babel/runtime/helpers/typeof.js' is not defined`
Root cause: `enhance: true` + `libVersion: 3.4.0+` triggers a broken es6-compile path in DevTools.

Fix (confirmed working):
```json
{
  "setting": { "enhance": false },
  "libVersion": "2.33.0"
}
```
Also remove `lazyCodeLoading` from `app.json` if present. If the bug persists:
```bash
# Nuke DevTools cache and reopen
rm -rf ~/Library/Application\ Support/微信开发者工具/*/Default/
"$CLI" open --project <dir>
```

### 3. Stale DevTools daemon on port 43673

The CLI reuses an existing daemon if one is running. If you quit via `cli quit`, the daemon process may still be alive (check with `pgrep -fl wechatwebdevtools`). To force a clean restart:
```bash
"$CLI" quit 2>/dev/null
pkill -f wechatwebdevtools 2>/dev/null
sleep 2
# Then re-launch
```

### 4. `auto-preview` has a QR output path bug

`auto-preview` produces: `错误: 二维码输出路径无效或不存在 %s (code 17)` — the auto mode can't find a default output path.
**Use `preview --qr-format image --qr-output <path>` instead** — it works correctly and gives you the file.

### 5. Bundle size tracking

`preview` output includes a bundle-size table. Keep an eye on it:
- Total <100KB is healthy for MVP
- >300KB risks slow load on slow networks
- If size spikes unexpectedly, check for accidentally included large files in `packOptions.ignore`

### 6. IDE must not already be running on a different HTTP port

If DevTools GUI is open, CLI operations may fail silently. Close the GUI first or use `cli quit`.

### 7. Preview requires DevTools to be logged in

After reinstall or cache clear, run `cli login` first (opens a QR code scan for WeChat auth).

### 9. Regenerate QR for each UAT round — don't reuse old images

Old QR codes link to the previous build. When the user says "UAT测试" or "再来一轮", always generate a fresh QR:

```bash
TIMESTAMP=$(date +%s)
"$CLI" preview --project "$PROJ" --qr-format image --qr-output /tmp/wechat_qr/uat_$TIMESTAMP.png 2>&1
```

### 10. DevTools log `start cli server error: [object Object]` is a false positive

The DevTools log (`~/Library/Application Support/微信开发者工具/*/WeappLog/logs/*.log`) may show:
```
[ERROR] start cli server error: [object Object]
```

This is the DevTools IPC layer failing to register an internal CLI command handler during startup handshake. It does NOT:
- Indicate compile failure
- Block preview generation
- Mean the mini-program won't load

If `preview` outputs a bundle-size table (TOTAL: XX KB), the build is valid. Ignore this error.

On a fresh AppID (never uploaded), `cli upload` will fail. The first upload must go through the GUI workflow (mp.weixin.qq.com).

## Quick-start for new sessions

```bash
# Fresh compile + preview QR in one shot:
CLI="/Applications/wechatwebdevtools.app/Contents/MacOS/cli"
PROJ="/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/miniprogram"

# Kill stale IDE
"$CLI" quit 2>/dev/null
pkill -f wechatwebdevtools 2>/dev/null
sleep 2

# Compile
"$CLI" auto --project "$PROJ"

# Preview QR
"$CLI" preview --project "$PROJ" --qr-format image --qr-output /tmp/wechat_qr/preview.png 2>&1
# Result file: /tmp/wechat_qr/preview.png
# Send to user: MEDIA:/tmp/wechat_qr/preview.png
```

## Related

- Main project skill: `badminton-coach-ai` (SKILL.md)
- Mini-program scaffold: `references/wechat-miniprogram-scaffold.md`
