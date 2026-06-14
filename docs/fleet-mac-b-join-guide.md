# 🖥 Mac-B 入列指南 — 老卢舰队

> Origin: Mac-A (始祖) | 配置仓库: `lcyluke/hermes-fleet-config` (私有)

---

## 前置条件

- [x] Mac-B 已安装 macOS
- [x] Mac-B 可访问 GitHub
- [ ] 老卢有 Mac-B 的终端访问权限

---

## Step 1: 安装 Hermes Agent (3分钟)

```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/install.sh | bash
# 验证
hermes --version
```

---

## Step 2: 配置 DeepSeek API (1分钟)

```bash
hermes setup model
```

交互流程:
1. 选择 Provider → **DeepSeek**
2. 选择 Model → **deepseek-v4-pro**
3. 填入 API Key → 和 Mac-A 同一把 key（`$DEEPSEEK_API_KEY`）

验证:
```bash
hermes chat -q "你好，确认模型和版本" --quiet
```

---

## Step 3: 克隆 Apex 项目 (1分钟)

```bash
mkdir -p ~/Desktop/2026AIAPP
cd ~/Desktop/2026AIAPP
git clone https://github.com/lcyluke/apex.git
cd Apex
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

---

## Step 4: 加入舰队 (30秒)

```bash
cd ~/Desktop/2026AIAPP/Apex
source .venv/bin/activate
apex fleet join-fleet
```

自动完成:
- ✅ 拉取 `config.yaml`（DeepSeek V4 Pro 配置）
- ✅ 拉取 `SOUL.md`（始祖 Agent 人格）
- ✅ 拉取 `skills/`（136 个技能）
- ✅ 拉取 `profiles/`（46 个 Agent Profile）
- ✅ **保留本地 `.env`**（API Key 不会被覆盖）
- ❌ **不启用 cron**（Worker 不跑定时任务）

验证:
```bash
apex fleet nodes
# 应该看到:
# ⚓ MacBook-Pro-2.local-root    ORIGIN   4   46   136
# 🔧 Mac-B-hostname              WORKER   -   46   136
```

---

## Step 5: 上报心跳（让 Origin 看到你）

```bash
apex fleet report
# → 📡 上报节点心跳 → GitHub → Origin 可见
```

---

## Step 6: 同步代码仓库 (手动)

羽球宝项目:
```bash
cd ~/Desktop/2026AIAPP/workspace
git clone https://github.com/lcyluke/badmintonSmallApp.git badminton-coach-ai
```

---

## 日常使用

### Worker 拉取最新配置
```bash
apex fleet sync --pull
```

### 查看舰队状态
```bash
apex fleet nodes
apex fleet status
```

### Worker 执行任务
```bash
# 使用某个 Profile 执行任务
hermes chat -q "你的任务" --profile frontend-dev
```

---

## 架构对照

```
Mac-A (Origin)                    Mac-B (Worker)
├── Cron 22 个定时任务 ✅          ├── Cron ❌ (自动禁用)
├── Dashboard :8080                ├── 羽球宝 GB10 训练
├── 授权引擎                        ├── 前端开发 / 模型训练
├── WeChat 通知                     └── 拉取 Mac-A 的 skills/profiles
├── git push 配置变更
└── git push 配置变更               ←── git pull 同步
```

---

## 故障排查

| 问题 | 解决 |
|:--|:--|
| `git clone` 超时 | 检查网络/代理；或用 `gh repo clone` |
| `apex` 命令不存在 | 确认 `.venv/bin/activate` 已 source |
| `fleet join-fleet` 失败 | 确认 GitHub HTTPS 可访问；手动 `git clone` 后 `cp` |
| 配置被覆盖 | `.env` 不受影响；若 config.yaml 被覆盖，从 `config.yaml.bak` 恢复 |
