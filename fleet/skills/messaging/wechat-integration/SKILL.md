---
name: wechat-integration
description: "Connect Hermes Agent to a personal WeChat account via iLink Bot API — QR login, credential persistence, gateway startup."
version: 1.0.0
platforms: [linux, macos]
metadata:
  author: Luke (老卢)
  related_skills: [hermes-agent]
---

# WeChat (微信) Integration for Hermes

Connects Hermes Agent to a **personal WeChat account** (not Official Account) via
Tencent's iLink Bot API. Once set up, anyone messaging your WeChat gets AI replies.

This is **not** the same as WeCom (企业微信) — that's a separate Hermes platform
adapter. This skill covers personal WeChat (`Platform.WEIXIN`).

## Prerequisites

Install the required Python packages into the Hermes venv:

```bash
# Determine Hermes Python
HERMES_PY=$(ls ~/.hermes/hermes-agent/venv/bin/python3)
SYSTEM_PIP="/Library/Developer/CommandLineTools/usr/bin/python3 -m pip"  # macOS

# Install into Hermes venv site-packages
$SYSTEM_PIP install --target ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages \
  aiohttp cryptography qrcode Pillow
```

On Linux, use the system pip with `--target` pointing to the Hermes venv.

## QR Login Flow

The interactive `hermes gateway setup` wizard is hard to drive programmatically
via PTY. Use the bundled script instead:

```bash
$HERMES_PY ~/.hermes/skills/messaging/wechat-integration/scripts/qr_login.py
```

**What happens:**
1. Fetches a QR code from `ilinkai.weixin.qq.com/ilink/bot/get_bot_qrcode?bot_type=3`
2. Generates a PNG image at `~/Desktop/wechat_qr.png` and opens it via `open` (macOS)
3. Polls `get_qrcode_status` every second for up to 2 minutes
4. On confirmation, saves credentials to `~/.hermes/weixin/accounts/<bot_id>.json`
5. Writes `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN`, `WEIXIN_BASE_URL` into `~/.hermes/.env`

**Pitfall:** QR codes expire in ~60 seconds. Do NOT use terminal ASCII QR codes —
by the time the user sees them they're already expired. Always generate a PNG file
and open it immediately so the user can scan at the same time polling begins.

## After Login

**⚠️ CRITICAL: By default, all inbound WeChat messages are REJECTED as "Unauthorized".**
After login, you MUST either:
- Set `WEIXIN_DM_POLICY=open` in `~/.hermes/.env` (allow anyone to DM), OR
- Add your WeChat user ID to `WEIXIN_ALLOWED_USERS`

The qr_login.py script now auto-sets both (open policy + your user ID as allowed).
If you logged in manually, add these to `.env` before starting the gateway, then run
`/reload` in CLI or restart the gateway.

Start the gateway:

```bash
hermes gateway start
```

Or install as a background service:

```bash
hermes gateway install
hermes gateway start
```

Verify it's running:

```bash
hermes gateway status
```

## Environment Variables

Set in `~/.hermes/.env`:

| Variable | Required | Description |
|----------|----------|-------------|
| `WEIXIN_ACCOUNT_ID` | Yes | Bot ID returned on QR confirm |
| `WEIXIN_TOKEN` | Yes | Bot token (Bearer auth for iLink API) |
| `WEIXIN_BASE_URL` | No | Override iLink base URL (default: `https://ilinkai.weixin.qq.com`) |
| `WEIXIN_DM_POLICY` | No | `open` (anyone can DM) or `allowlist` (default) |
| `WEIXIN_GROUP_POLICY` | No | `open` or `allowlist` for group chats |
| `WEIXIN_ALLOWED_USERS` | No | Comma-separated whitelist for DMs |
| `WEIXIN_GROUP_ALLOWED_USERS` | No | Comma-separated whitelist for groups |

## How It Works Under the Hood

- **Transport:** Long-poll `getupdates` → process messages → `sendmessage`
- **CDN:** Media files (images, voice, video) move through AES-128-ECB encrypted CDN (`novac2c.cdn.weixin.qq.com`)
- **Session:** `context_token` per peer persists conversation context
- **Login:** QR code from `get_bot_qrcode` → user scans → poll `get_qrcode_status` → receive `ilink_bot_id` + `bot_token`
- **Adapter:** `gateway/platforms/weixin.py` — `WeixinAdapter(BasePlatformAdapter)`

## Multi-Platform Sessions (Cross-Platform Behavior)

Hermes can connect to many platforms simultaneously (WeChat, CLI, Slack, DingTalk,
Feishu, Telegram, etc.), but **each platform has an independent session** —
they do NOT share conversation context.

What IS shared across platforms:
- **Memory** — facts saved with the `memory` tool are injected into every session
- **Skills** — installed skills load regardless of which platform you're on
- **Filesystem** — all sessions run on the same machine

What is NOT shared:
- **Conversation history** — WeChat doesn't know what you said on CLI
- **Session state** — each platform has its own session ID and message transcript

Practical implication: use CLI for complex project work, WeChat for quick Q&A.
Key decisions should be saved to memory so other platforms can pick them up.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| QR login returns `ret=-2, errcode=-2` "unknown error" | Stale session — re-run QR login |
| QR expires before scan | Run script again, scan immediately |
| `pip` missing in Hermes venv | Use system Python with `--target` flag |
| `Pillow` C extension fails | Use system Python to generate QR PNG, not Hermes Python |
| aiohttp SSL verify error on macOS | `pip install certifi` — the adapter auto-uses it |
| "Unauthorized user" in gateway logs after login | Add `WEIXIN_DM_POLICY=open` + `WEIXIN_ALLOWED_USERS=<your_id>` to `.env`, restart gateway |
| `hermes gateway restart` hangs or gateway stops | Run `hermes gateway run` in background instead: `terminal(background=true)` |
| WeChat connects but disconnects on restart | Normal — just re-run `hermes gateway run`, the gateway auto-reconnects |
