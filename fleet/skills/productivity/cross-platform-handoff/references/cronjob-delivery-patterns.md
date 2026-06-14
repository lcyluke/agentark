# Cronjob 定时任务交付模式

## 背景

老卢有多个平台可用（CLI、微信、钉钉），cronjob 交付目标选择直接影响消息能否送达。

## 核心规则

### 1. 使用 `deliver="origin"`（推荐）

当老卢在某个平台上提出创建定时任务时，**始终使用 `deliver="origin"`**（即默认，省略参数即可）。这会自动把消息发回当前对话窗口，无需猜测目标 ID。

```python
# ✅ 正确 — 自动回到当前会话
cronjob(action='create', prompt="...", schedule="30 9 * * *", name="每日工作简报")
# deliver 省略 = auto-detect = origin（当前对话）
```

### 2. 钉钉目标 ID

老卢的钉钉目标可通过 `send_message(action='list')` 查看。目前已知：
- `dingtalk:Luke (dm)` — 卢克的私聊窗口，这是唯一确认可用的钉钉目标

不要尝试猜测钉钉的 chat_id（如 `p3yhcbr`），系统无法解析。

### 3. 内容区分：工作 vs 副业

老卢有明确的两类事务：
- **正职工作（day job）** — 每日提醒应当聚焦于此
- **副业项目（深圳羽球地图等）** — 除非老卢明确要求，不要把副业内容塞进工作提醒

如果用户说「与工作有关，不是运动」，说明 cronjob 内容应聚焦他的正职工作内容，而非副业/兴趣项目。

### 4. 测试流程

创建 cronjob 后，可以先发一条普通 `send_message` 到目标确认送达，再创建定时任务：
```python
# 先测试送达
send_message(target="origin", message="测试消息...")

# 再创建定时任务
cronjob(action='create', name="...", schedule="...", prompt="...")
```

### 5. 已知坑

- `send_message` 未设 home channel 时无法直接发 `dingtalk:ChatID`
- 列表中的 `dingtalk:Luke (dm)` 是已配对用户，实际发送可能也受限于 home channel 配置
- 最稳妥的方式：老卢在哪个平台提出需求，就发回哪个平台（`origin` 自动检测）
