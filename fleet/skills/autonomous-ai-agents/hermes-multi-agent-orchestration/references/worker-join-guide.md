# Mac-B Worker 入列指南 (v2 — 单仓库)

## 一键入列

```bash
curl -fsSL https://raw.githubusercontent.com/lcyluke/apex/main/scripts/fleet-join-worker.sh | bash
```

## 手动步骤 (5步)

### Step 1: 安装 Hermes (3分钟)
```bash
curl -fsSL https://raw.githubusercontent.com/NousResearch/hermes-agent/main/install.sh | bash
hermes --version
```

### Step 2: 配置 API Key (1分钟)
```bash
hermes setup model
# → DeepSeek → deepseek-v4-pro → 填入 Key
# (和 Mac-A 同一把 key)
```

### Step 3: 克隆 Apex (1分钟)
```bash
mkdir -p ~/Desktop/2026AIAPP
cd ~/Desktop/2026AIAPP
git clone https://github.com/lcyluke/apex.git
cd Apex
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
```

### Step 4: 加入舰队 (30秒)
```bash
apex fleet join-fleet
```
自动完成:
- ✅ 拉取 `fleet/config.yaml` → `~/.hermes/config.yaml`
- ✅ 拉取 `fleet/SOUL.md` → `~/.hermes/SOUL.md`
- ✅ 拉取 `fleet/skills/` → `~/.hermes/skills/`
- ✅ 拉取 `fleet/profiles/` → `~/.hermes/profiles/`
- ✅ **保留本地 `.env`** (API Key 不被覆盖)
- ❌ **不启用 cron** (Worker 不跑定时任务)

### Step 5: 上报心跳 (30秒)
```bash
apex fleet report
# → 心跳+GPU 写入 fleet/nodes/<machine_id>.json
# → git push → Origin 拉取后可见
```

## 验证

```bash
apex fleet nodes
# 应显示: ⚓ Origin (Mac-A) + 🔧 Worker (本机)
```

## 同步清单

| 内容 | 同步方式 | 频率 |
|------|---------|------|
| config.yaml | Git pull (fleet/) | 手动/需时 |
| SOUL.md | Git pull | 手动 |
| skills/ | Git pull | 手动 |
| profiles/ | Git pull | 手动 |
| .env (API Key) | **不同步** | — |
| state.db (记忆) | **不同步** | — |
| nodes/ (心跳) | Git push (fleet report) | cron 3h |

## 日常

```bash
apex fleet sync --pull    # 拉最新配置
apex fleet report         # 上报心跳+GPU
apex fleet nodes          # 查舰队
apex fleet gpu-status     # 查GPU
```
