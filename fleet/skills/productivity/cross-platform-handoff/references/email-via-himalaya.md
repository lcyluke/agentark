# Himalaya CLI 邮箱配置

## 安装

```bash
brew install himalaya
```

## Outlook/Office 365 配置

Outlook 不支持直接使用登录密码（尤其开了两步验证），必须生成应用密码。

### 获取应用密码

1. 打开 https://account.microsoft.com/security
2. 登录 Outlook 账号
3. 安全信息 → 应用密码 → 创建
4. 复制 16 位密码（形如 `abcd-efgh-ijkl-mnop`）

### config.toml

`~/.config/himalaya/config.toml`：

```toml
[accounts.outlook]
email = "you@outlook.com"
display-name = "Your Name"
default = true

backend.type = "imap"
backend.host = "outlook.office365.com"
backend.port = 993
backend.encryption.type = "tls"
backend.login = "you@outlook.com"
backend.auth.type = "password"
backend.auth.cmd = "echo 'your-app-password'"

message.send.backend.type = "smtp"
message.send.backend.host = "smtp.office365.com"
message.send.backend.port = 587
message.send.backend.encryption.type = "start-tls"
message.send.backend.login = "you@outlook.com"
message.send.backend.auth.type = "password"
message.send.backend.auth.cmd = "echo 'your-app-password'"

folder.aliases.inbox = "INBOX"
folder.aliases.sent = "Sent"
folder.aliases.drafts = "Drafts"
folder.aliases.trash = "Deleted Items"
```

> ⚠️ 应用密码是明文写在 config.toml 里。更安全的方式是用 `pass` 或 macOS keychain：
> `backend.auth.cmd = "security find-generic-password -w -s 'outlook-app-password'"`

## 常用命令速查

```bash
# 列出文件夹
himalaya folder list

# 查收件箱（最新 20 封）
himalaya envelope list --page 1 --page-size 20

# 搜索
himalaya envelope list from sender@example.com subject meeting

# 查看邮件
himalaya message read 42

# 发送新邮件（非交互，pipe 方式）
cat << 'EOF' | himalaya template send
From: you@outlook.com
To: recipient@example.com
Subject: Subject Here

Body text here.
EOF

# 回复邮件
himalaya template reply 42 | sed 's/^$/\\n回复内容\\n/' | himalaya template send

# 删除
himalaya message delete 42
```

## 审批工作流模式

关键原则：**Hermes 可以读邮件，但发邮件必须展示草稿并等用户说「发」。**

```
读邮件: himalaya envelope list / himalaya message read N → 直接展示结果
起草:   himalaya template reply N | ... → 展示草稿 → 停！
发送:   用户说"发" → himalaya template send → 发送
```

不要在同一个回复里既起草又发送。起草后总是等用户确认。
