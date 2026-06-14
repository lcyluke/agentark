# 网关平台运维记录

> 记录各平台的已知问题、恢复模式和操作注意事项。
> 新增平台后追加本节。

## 微信 (iLink)

### 已知问题
- **间歇 503**: 腾讯 iLink 服务端偶尔返回 503 "Service Unavailable"，指向 `http://127.0.0.1:1082`
  - 影响: 消息发送失败，持续 2-5 分钟
  - 恢复: 自动，Hermes 内置 5 次重试
  - 无本地缓解方案

- **速率限制**: 连发速度 >1条/3秒触发 "rate limited" (errcode=-2)
  - 恢复: 自动 backoff 3 秒
  
### 接入方式
- QR 扫码登录 (`hermes gateway setup` → 选13 Weixin/WeChat)
- 环境变量: `WEIXIN_ACCOUNT_ID`, `WEIXIN_TOKEN`, `WEIXIN_DM_POLICY=open`
- 凭证存储: `~/.hermes/weixin/accounts/{id}.json`

## 钉钉 (Stream)

### 已知问题
- **Session Webhook 丢失**: 长连接断开重连后出现 "No valid session_webhook"
  - 影响: 仅首次回复延迟数秒
  - 恢复: 自动重建

### 接入方式
- 钉钉开放平台 → 创建机器人应用 → 获取 AppKey/AppSecret
- 环境变量: `DINGTALK_CLIENT_ID`, `DINGTALK_CLIENT_SECRET`, `DINGTALK_DM_POLICY=open`
- 依赖: `dingtalk-stream>=0.20` + `httpx`
- 首次配对: 用户在钉钉发消息 → 拿到 pairing code → `hermes pairing approve dingtalk CODE`

## Slack

### 已知问题
- **权限拒绝**: `/Users/Mac/.local/state/hermes/` 属主为 root
  - 修复: `sudo chown Mac:staff /Users/Mac/.local/state/hermes`

## Email (Gateway 内置)

### 已知问题
- Gmail 应用密码过期 (旧凭据 `EMAIL_ADDRESS=abao180@gmail.com`)

### 替代方案
- Himalaya CLI: `brew install himalaya` 或 `cargo install himalaya`
- 配置: `~/.config/himalaya/config.toml`
- 审批模式: 查邮件自动 / 回复+发送需用户批准

## 常驻服务

- 安装: `hermes gateway install` → launchd plist
- 状态: `hermes gateway status`
- 日志: `tail -f ~/.hermes/logs/gateway.log`
- 休眠: `sudo pmset -c sleep 0` (MacBook 插电避免休眠)
