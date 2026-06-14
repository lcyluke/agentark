---
name: badminton-deploy
description: 羽球宝AI搭子服务器部署 — 从零到线上的完整部署流程，含服务器侦察/代码同步/nginx/HTTPS/服务管理
category: domain
triggers:
  - 部署羽球宝/上线
  - 服务器配置/nginx/https
  - 羽球宝DNS/域名解析
  - 老卢给了服务器IP或域名后说"继续"/"开干"
---

# 🏸 羽球宝AI搭子 — 服务器部署

## 部署目标

```
本地代码 (lcyluke/badmintonSmallApp) → 腾讯云服务器 (43.139.191.202) → badminton.chat
```

## 服务器信息

| 项目 | 值 |
|:--|:--|
| IP | 43.139.191.202 |
| 主机名 | VM-0-17-tencentos |
| 系统 | TencentOS Server 3.3 (x86_64) |
| 配置 | 2C / 1.9GB RAM / 50GB 磁盘 |
| Python | 3.11.9 (`/usr/local/bin/python3.11`) |
| Nginx | 1.14.1 (已装，未配置) |
| Docker | 未安装 |

## 现有部署情况

服务器上已有旧版(5月)在运行：
- **运行位置**: `/data/badminton/app/` (www-data 用户)
- **源码**: `/root/badminton-src/` (uid 502)
- **进程**: uvicorn 2 workers → `127.0.0.1:8000`
- **数据库**: `/data/badminton/app/users.db`

> ⚠️ 首次部署时先侦察服务器现状，不要假设是裸机。

## 部署流程

### Phase 1: 侦察
```bash
ssh root@43.139.191.202
# 检查现有服务、端口、已安装软件
ss -tlnp                    # 监听端口
ps aux | grep uvicorn       # 运行中的服务
ls /data/badminton/         # 已有部署
which python3.11 nginx git  # 已装工具
```

### Phase 2: 停旧 · 备份 · 拉新
```bash
# 停旧服务（用 systemctl 或 kill PID，不要 pkill 通配符）
systemctl stop badminton 2>/dev/null || true

# 备份旧版（cp 不是 rm — 保留回滚能力）
cp -a /data/badminton/app /data/badminton/app.bak.$(date +%Y%m%d)

# 拉新代码到新目录
cd /data/badminton
git clone --depth 1 https://github.com/lcyluke/badmintonSmallApp.git app-v2
```

### Phase 3: 安装依赖
```bash
/usr/local/bin/python3.11 -m venv /data/badminton/app-v2/venv
source /data/badminton/app-v2/venv/bin/activate
pip install -r /data/badminton/app-v2/requirements.txt
# opencv-python 大包可能需要 yum install gcc python3-devel 先
```

### Phase 4: 配置 .env
```bash
cp /data/badminton/app.bak/.env /data/badminton/app-v2/.env  # 复用旧配置
# 或从本地 scp 上传新 .env
```

### Phase 5: Nginx 反向代理 + HTTPS
```bash
# 安装 certbot
yum install -y certbot python3-certbot-nginx

# 先确保 DNS 已解析: badminton.chat → 43.139.191.202
# 然后:
certbot --nginx -d badminton.chat

# Nginx 配置模板 (如果 certbot 没自动配):
# proxy_pass http://127.0.0.1:8000;
# proxy_set_header Host $host;
# proxy_set_header X-Real-IP $remote_addr;
```

### Phase 6: Systemd 服务
```bash
cat > /etc/systemd/system/badminton.service << 'UNIT'
[Unit]
Description=Badminton Coach API
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/data/badminton/app-v2
ExecStart=/data/badminton/app-v2/venv/bin/uvicorn badminton_coach.webapp:app --host 127.0.0.1 --port 8000 --workers 2
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT

systemctl daemon-reload
systemctl enable --now badminton
```

### Phase 7: 验证
```bash
# 本地健康检查
curl http://127.0.0.1:8000/health
# 公网检查
curl http://43.139.191.202:8000/health
# 域名检查 (DNS生效后)
curl https://badminton.chat/health
```

## 微信小程序服务器配置

在微信公众平台 → 开发管理 → 服务器域名中配置：
- **request合法域名**: `https://badminton.chat`
- **socket合法域名**: （如有 WebSocket）
- **uploadFile合法域名**: `https://badminton.chat`
- **downloadFile合法域名**: `https://badminton.chat`

## Pitfalls & 教训

### 🔴 禁止 heredoc 远程脚本
**不要**在 `ssh … "cat > /tmp/deploy.sh" << 'EOF'` 中写远程部署脚本。
Hermes 的终端工具会拦截这种模式。改成分步执行单个 SSH 命令。

### 🔴 不要 pkill 通配符
`pkill -f "uvicorn.*badminton"` 可能匹配到 SSH 自身，导致连接断开返回 255。
改用 `systemctl stop` 或精确 `kill <PID>`。

### 🟡 先侦察再部署
老卢买的服务器可能不是裸机——先 `ss -tlnp` 和 `ps aux` 看有没有旧服务在跑，
避免盲目覆盖正在运行的生产数据。

### 🟡 DNS 是阻塞项
certbot 申请 HTTPS 证书前，DNS 必须已解析到服务器 IP。
如果 DNS 还没改（检查 `dig +short badminton.chat`），先告诉老卢去域名注册商改 A 记录。

### 🟡 备份用 cp 不用 mv
万一新版本启动失败，能用备份快速回滚。部署成功后再清理旧备份。
