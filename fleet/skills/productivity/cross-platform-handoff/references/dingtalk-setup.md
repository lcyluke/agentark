# 钉钉接入指南

## 依赖安装

```bash
# 系统 python 安装到 Hermes venv
SYSPYTHON=/Library/Developer/CommandLineTools/usr/bin/python3
VENV_SITE=/Users/Mac/.hermes/hermes-agent/venv/lib/python3.11/site-packages

$SYSPYTHON -m pip install --target "$VENV_SITE" "dingtalk-stream>=0.20" httpx
```

验证：
```bash
/Users/Mac/.hermes/hermes-agent/venv/bin/python3 -c "import dingtalk_stream; import httpx; print('OK')"
```

## 钉钉开放平台配置

### 1. 创建应用
- 打开 https://open-dev.dingtalk.com/
- 应用开发 → 企业内部应用 → 创建应用
- 应用类型选 **机器人**
- 填名字、描述、图标

### 2. 获取凭证
创建后在应用详情页：
- **AppKey**（即 `DINGTALK_CLIENT_ID`）
- **AppSecret**（即 `DINGTALK_CLIENT_SECRET`）— 需点眼睛图标查看

### 3. 消息接收模式
- 左侧菜单 → 消息接收模式
- 选 **Stream 模式**（不是 HTTP 回调）
- 保存

> **Stream 模式不需要公网 IP** — Hermes 主动连钉钉服务器，和微信一样。

### 4. 发布
- 版本管理与发布 → 创建新版本 → 发布

## 环境变量

写入 `~/.hermes/.env`：
```bash
DINGTALK_CLIENT_ID=dingxxxxxxxx
DINGTALK_CLIENT_SECRET=xxxxxxxxxxxx
DINGTALK_DM_POLICY=open
```

重启网关：`hermes gateway restart`

验证日志：
```
Connecting to dingtalk...
[Dingtalk] Connected via Stream Mode
✓ dingtalk connected
```

## 首次配对

首次发送消息时，钉钉会返回配对码（如 `SPXWD5YJ`）而不是 AI 回复：

```
Hi~ I don't recognize you yet!
Here's your pairing code: SPXWD5YJ
```

需要在终端执行：

```bash
hermes pairing approve dingtalk SPXWD5YJ
```

之后该用户的消息会被正常处理。

> ⚠️ **注意区分：钉钉自带的「小钉」是官方 AI 助手，不是 Hermes。**
> 需要搜索你在开放平台创建的机器人名字，而不是用「小钉」。

## 可选配置

| 环境变量 | 说明 |
|----------|------|
| `DINGTALK_DM_POLICY` | 私聊策略: `open` / `pairing` |
| `DINGTALK_REQUIRE_MENTION` | 群聊需 @ 才回复 |
| `DINGTALK_ALLOWED_USERS` | 私聊白名单 |

## 微信 vs 钉钉

| 项目 | 微信 | 钉钉 |
|------|------|------|
| 接入方式 | iLink 长轮询 | dingtalk-stream WebSocket |
| 注册流程 | 扫码即可 | 需建应用+发布 |
| 公网IP | 不需要 | 不需要 |
| 群聊 | 支持 | 支持(可设@提及) |
| 媒体 | 文字/图片/语音/视频/文件 | 文字/图片/语音/富文本 |
