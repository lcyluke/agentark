# 各平台连接需求矩阵

## 连接方式总览

| 平台 | 连接技术 | 方向 | 需要公网IP？ | 需要开发平台注册？ | 接入复杂度 |
|------|----------|------|:---:|:---:|:---:|
| 微信 | iLink Bot API（长轮询） | Mac → 腾讯 | ❌ | ❌（扫码即可） | 中 |
| 钉钉 | dingtalk-stream SDK（WebSocket） | Mac → 钉钉 | ❌ | ✅ 需建应用 | 低 |
| Slack | Slack Bolt（WebSocket） | Mac → Slack | ❌ | ✅ 需建 App | 低 |
| 飞书 | Webhook 回调 | 飞书 → Mac | **✅ 需要** | ✅ 需建应用 | 高 |
| Discord | Discord Gateway（WebSocket） | Mac → Discord | ❌ | ✅ 需建 Bot | 低 |
| Telegram | Telegram Bot API（长轮询） | Mac → Telegram | ❌ | ✅ 需 @BotFather | 低 |
| CLI | 本地终端 | N/A | ❌ | ❌ | 无 |

## 关键洞察

**微信和钉钉都不需要公网 IP**——它们从 Hermes 主动出站连接平台服务器（长轮询/WebSocket），所以 Mac 在任何网络环境下都能用。

**飞书是唯一需要公网 IP 的主流平台**——飞书的 Webhook 模式要求飞书服务器主动 POST 到你的 URL，所以 Hermes 必须有一个公网可达的地址。

## 飞书公网 IP 解决方案

思路：用腾讯云服务器（43.139.191.202）做 frp 内网穿透

```
飞书服务器 → POST https://43.139.191.202/feishu/webhook
                              ↓
                    frps（腾讯云，端口转发）
                              ↓
                    frpc（Mac 本地，接收转发）
                              ↓
                    Hermes Gateway（:端口/feishu/webhook）
```

### frp 配置示例

**腾讯云 frps.ini：**
```ini
[common]
bind_port = 7000
vhost_http_port = 8080
```

**Mac frpc.ini：**
```ini
[common]
server_addr = 43.139.191.202
server_port = 7000

[feishu]
type = http
local_port = 8080
custom_domains = 43.139.191.202
```

然后在飞书开放平台配置事件订阅 URL 为 `https://43.139.191.202:8080/feishu/webhook`。

## 各平台环境变量速查

| 平台 | 必需环境变量 | 可选环境变量 |
|------|-------------|-------------|
| 微信 | `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN` | `WEIXIN_DM_POLICY`, `WEIXIN_ALLOWED_USERS` |
| 钉钉 | `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET` | `DINGTALK_DM_POLICY` |
| Slack | `SLACK_BOT_TOKEN`, `SLACK_APP_TOKEN` | - |
| 飞书 | `FEISHU_APP_ID`, `FEISHU_APP_SECRET` | `FEISHU_WEBHOOK_HOST`, `FEISHU_WEBHOOK_PORT` |
| Discord | `DISCORD_BOT_TOKEN` | - |
| Telegram | `TELEGRAM_BOT_TOKEN` | - |
| Email | `EMAIL_ADDRESS`, `EMAIL_PASSWORD`, `EMAIL_IMAP_HOST`, `EMAIL_SMTP_HOST` | - |

## Gateway 常驻服务

```bash
# 安装为 launchd 用户服务（开机自启）
hermes gateway install

# 服务文件位置
~/Library/LaunchAgents/ai.hermes.gateway.plist

# 状态检查
hermes gateway status

# 日志查看
tail -f ~/.hermes/logs/gateway.log
```

## macOS 休眠对网关的影响

| Mac 状态 | 网关是否活跃 | 说明 |
|----------|:---:|------|
| 正常使用 | ✅ | - |
| 屏保 | ✅ | 系统正常运行 |
| 显示器关闭 | ✅ | 仅屏幕关闭 |
| 插电无操作 | ✅（如果 `sleep 0`） | 见下方配置 |
| 插电无操作（默认） | ❌（10分钟后休眠） | 默认 `sleep 10` |
| 合盖 + 外接显示器 | ✅ | Clamshell 模式不休眠 |
| 合盖（不外接） | ❌ | 强制休眠 |
| 电池 + 无操作 | ❌ | 默认休眠 |

**推荐配置（插电不休眠）：**
```bash
sudo pmset -c sleep 0    # 插电时永不休眠
sudo pmset -b sleep 10   # 电池保留默认休眠时间
```
