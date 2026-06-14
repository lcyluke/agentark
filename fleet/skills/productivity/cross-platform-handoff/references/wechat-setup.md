# 微信接入完整指南

## 依赖安装

微信适配器需要 `aiohttp`（异步 HTTP）和 `cryptography`（AES-128-ECB 媒体加解密）。

Hermes 自带 venv 不含 pip。安装命令：

```bash
# 方法：系统 python 安装到 Hermes venv 的 site-packages
SYSPYTHON=/Library/Developer/CommandLineTools/usr/bin/python3
VENV_SITE=/Users/Mac/.hermes/hermes-agent/venv/lib/python3.11/site-packages

$SYSPYTHON -m pip install --target "$VENV_SITE" aiohttp cryptography qrcode Pillow
```

验证：
```bash
/Users/Mac/.hermes/hermes-agent/venv/bin/python3 -c "import aiohttp; from cryptography.hazmat.primitives.ciphers import Cipher; print('OK')"
```

## 扫码登录

### 坑：不要用 `hermes gateway setup` 交互式向导

交互式菜单无法从 agent 的终端可靠控制（PTY 导航问题）。直接用 iLink API 脚本。

### 扫码脚本

位置：`~/.hermes/scripts/weixin_qr_login.py`（见 scripts/ 目录）

工作流程：
1. 调用 `GET https://ilinkai.weixin.qq.com/ilink/bot/get_bot_qrcode?bot_type=3` 获取二维码数据
2. 返回 `{qrcode: "hex_token", qrcode_img_content: "liteapp_url", ret: 0}`
3. 用 `qrcode` 库生成 ASCII QR 打印到终端 + 保存 PNG 到桌面
4. 轮询 `GET .../get_qrcode_status?qrcode={hex_token}` 检查状态
5. 状态变化：`wait` → `scaned`（已扫但未确认）→ `confirmed`（确认成功）
6. `confirmed` 时拿到 `ilink_bot_id`, `bot_token`, `baseurl`, `ilink_user_id`
7. 调用 `save_weixin_account()` 保存到 `~/.hermes/weixin/accounts/`

### 坑：ASCII QR 码在终端会过期

终端输出有时间延迟 — ASCII 二维码传到用户眼前时可能已过期（60-120秒有效期）。
**最佳实践**：同时保存 PNG 到桌面 (`~/Desktop/wechat_qr.png`) 并 `open` 它，用户在桌面上扫。

### 坑：`qrcode_img_content` 不是图片

iLink API 的 `qrcode_img_content` 字段返回的是 LiteApp HTML 页面 URL（`https://liteapp.weixin.qq.com/q/...`），不是直接的图片。必须用 `qrcode` 库自己生成 QR 图片。

## 保存凭证

登录成功后的凭证：

| 字段 | 用途 | 环境变量 |
|------|------|----------|
| `ilink_bot_id` | Bot 账号 ID | `WEIXIN_ACCOUNT_ID` |
| `bot_token` | Bot 认证 token | `WEIXIN_TOKEN` |
| `baseurl` | iLink API 地址 | `WEIXIN_BASE_URL`（默认 `https://ilinkai.weixin.qq.com`） |
| `ilink_user_id` | 扫码者微信 ID | `WEIXIN_ALLOWED_USERS` |

写入 `~/.hermes/.env`：
```bash
WEIXIN_ACCOUNT_ID=d9a99b8fce99@im.bot
WEIXIN_TOKEN=d9a99b8fce99@im.bot:060000...
WEIXIN_DM_POLICY=open
WEIXIN_ALLOWED_USERS=o9cq801pPjNXqgPCdhTHLRu8eJL0@im.wechat
```

## 常见坑

### 1. "Unauthorized user" 警告

日志：`WARNING: Unauthorized user: o9cq... on weixin`

原因：`WEIXIN_DM_POLICY` 未设置或 `WEIXIN_ALLOWED_USERS` 为空。

修复：在 `.env` 中设置：
```
WEIXIN_DM_POLICY=open
WEIXIN_ALLOWED_USERS=<你的微信用户ID>  # 或用 * 允许所有人
```
然后重启网关：`hermes gateway restart`

### 2. Python 版本不兼容

系统自带 Python 3.9 不支持 Hermes 源码里的 `|` 类型语法（需要 Python 3.10+）。
必须用 Hermes 自带的 venv Python 3.11。

### 3. 网关重启后微信断开

重启后会重新连接，日志中会看到：
```
✓ weixin disconnected (0.12s)
Connecting to weixin...
weixin: restored 1 context token(s) for d9a99b8f
[Weixin] Connected account=d9a99b8f base=https://ilinkai.weixin.qq.com
✓ weixin connected
```

### 4. `limit_outbound_reply_url` 错误

如果出现此错误，检查 `~/.hermes/config.yaml` 中是否有限制外链的策略。

## 可选的微信策略配置

| 环境变量 | 说明 | 默认值 |
|----------|------|--------|
| `WEIXIN_DM_POLICY` | 私聊策略：`open` 允许所有人，`pairing` 需配对 | - |
| `WEIXIN_GROUP_POLICY` | 群聊策略：`open` / `mention` / `pairing` | - |
| `WEIXIN_ALLOWED_USERS` | 私聊白名单（逗号分隔的用户ID或 `*`） | - |
| `WEIXIN_GROUP_ALLOWED_USERS` | 群聊白名单 | - |
| `WEIXIN_CDN_BASE_URL` | CDN 地址（默认自动） | `https://novac2c.cdn.weixin.qq.com/c2c` |
