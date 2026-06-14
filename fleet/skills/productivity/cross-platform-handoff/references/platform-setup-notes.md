# Platform Setup Procedures

Concrete steps learned while connecting WeChat and DingTalk to Hermes Gateway.

## WeChat (iLink Bot) Setup

### Prerequisites
- aiohttp + cryptography installed in Hermes venv:
  ```bash
  /Library/Developer/CommandLineTools/usr/bin/python3 -m pip install \
    --target ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages \
    aiohttp cryptography qrcode
  ```

### Interactive Setup Doesn't Work Well
`hermes gateway setup` is a curses UI that's hard to drive programmatically in PTY mode.
The selection menu times out before we can navigate to the WeChat option.

### Direct QR Login (preferred)
1. Write a Python script that calls `gateway.platforms.weixin.qr_login()` directly
2. It fetches a QR code from `https://ilinkai.weixin.qq.com/ilink/bot/get_bot_qrcode?bot_type=3`
3. Generate ASCII QR in terminal + save PNG image for scanning
4. Poll `ilink/bot/get_qrcode_status` for status changes: wait → scaned → confirmed
5. On confirmation, `save_weixin_account()` persists credentials to `~/.hermes/weixin/accounts/`
6. Write env vars: `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN` to `~/.hermes/.env`
7. Set `WEIXIN_DM_POLICY=open` and `WEIXIN_ALLOWED_USERS=<user_id>` for first-time auth
8. QR codes expire quickly (~2 min) — the real-time ASCII print is hard to see before timeout.
   Best approach: save QR as PNG to Desktop and `open` it, then start polling.

### Post-Setup
- User must be authorized: gateway logs "Unauthorized user" until `WEIXIN_DM_POLICY=open` is set
- Restart gateway after env var changes: `hermes gateway restart`
- Verify: `grep weixin ~/.hermes/logs/gateway.log` should show "✓ weixin connected"

## DingTalk (Stream Mode) Setup

### Prerequisites
```bash
/Library/Developer/CommandLineTools/usr/bin/python3 -m pip install \
  --target ~/.hermes/hermes-agent/venv/lib/python3.11/site-packages \
  "dingtalk-stream>=0.20" httpx
```

### App Registration (Manual)
1. Open https://open-dev.dingtalk.com/
2. 应用开发 → 企业内部应用 → 创建应用
3. Type: 机器人 (Robot)
4. Message receiving mode: **Stream 模式** (NOT HTTP)
5. Publish the app (版本管理与发布 → 创建新版本 → 发布)
6. Copy AppKey (Client ID) and AppSecret

### Configuration
```bash
# In ~/.hermes/.env
DINGTALK_CLIENT_ID=dingxxxxxxxxxxxx
DINGTALK_CLIENT_SECRET=xxxxxxxxxxxxxxxxxxxx
DINGTALK_DM_POLICY=open
```

### Pairing
- First message from user generates a pairing code like `SPXWD5YJ`
- Approve: `hermes pairing approve dingtalk SPXWD5YJ`
- User is recognized on next message

### Post-Setup
- Verify: `grep dingtalk.*connect ~/.hermes/logs/gateway.log` → "✓ dingtalk connected"
- Known issue: "No valid session_webhook" warning appears after long connection re-join — harmless, auto-recovers

## Common Platform Issues

### No Public IP Required
Both WeChat (iLink long-poll) and DingTalk (Stream) connect OUT from the Mac to Tencent/DingTalk
servers. No inbound port forwarding or public IP needed. Feishu is the only platform that
requires a webhook callback URL.

### Gateway as Launchd Service
```bash
hermes gateway install    # Install as user-level launchd service
hermes gateway restart    # Restart (reloads .env changes)
hermes gateway status     # Check PID and load state
```
Service definition: `~/Library/LaunchAgents/ai.hermes.gateway.plist`
Logs: `~/.hermes/logs/gateway.log`

### Gmail SMTP Broken → Disable
Old Gmail credentials in .env cause continuous IMAP auth failures. Comment them out with `#DISABLED_`
prefix in .env, restart gateway.

### Slack Permission Issue
`/Users/Mac/.local/state/hermes/` is owned by root (from opencode). Fix: `sudo chown Mac:staff ...`
Not critical — Slack is not a primary platform.
