# 授权引擎集成到 Apex — 完整架构

> 日期: 2026-06-02
> 状态: ✅ 已完成

## 架构概览

```
┌─────────────────────────────────────────────────────────┐
│                    微信 (老卢)                           │
│  "授权 123456" → /approve → approve → engine.approve()   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│              Hermes Agent (default)                      │
│  收到 auth 消息 → MessageRouter → apex-pm Profile       │
│  → AuthorizationEngine.request/approve/deny/check/...   │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│           Apex Dashboard (Flask :8080)                   │
│  /api/auth/request  /approve  /deny  /check  /consume   │
│  /api/auth/revoke   /grants  /audit  /stats  /verify    │
│  /api/auth/scopes                                       │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│        ape/orchestration/authorization.py               │
│  AuthorizationEngine (核心引擎)                          │
│  AuthorizationDB (SQLite 层)                            │
│  SHA256 哈希链 (不可篡改审计)                             │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  ~/.hermes/auth/grants.db   (SQLite 授权数据库)          │
│  ~/.hermes/auth/audit.log   (append-only 审计日志)       │
└─────────────────────────────────────────────────────────┘
```

## 文件清单

| 文件 | 行数 | 说明 |
|------|------|------|
| `apex/orchestration/authorization.py` | ~650 | 核心引擎: AuthorizationEngine, AuthorizationDB, 15 scope |
| `apex/interface/web.py` (L860-1045) | +185 | 11 个 REST 端点 |
| `apex/orchestration/message_router.py` | +2 类别 | `auth` 类别 + `apex-pm` profile + 关键词 |
| `apex/orchestration/__init__.py` | +5 | 导出 AuthorizationEngine |
| `~/.hermes/scripts/authorization_engine.py` | ~200 | CLI 薄 wrapper |
| `~/.hermes/profiles/apex-pm/` | 2 文件 | SOUL.md + config.yaml |

## API 端点参考

| 方法 | 路径 | 参数 | 返回 |
|------|------|------|------|
| POST | `/api/auth/request` | `agent`, `scope`, `purpose`, `?ttl_min` | `{request_code, risk, ...}` |
| POST | `/api/auth/approve` | `request_code` | `{ok, agent, scope, expires_at}` |
| POST | `/api/auth/deny` | `request_code` | `{ok}` |
| GET | `/api/auth/check` | `?agent=&scope=` | `{authorized, message, remaining_minutes}` |
| POST | `/api/auth/consume` | `grant_id` | `{ok}` |
| POST | `/api/auth/revoke` | `grant_id`, `?reason` | `{ok}` |
| GET | `/api/auth/grants` | `?agent=&scope=&status=&limit=` | `[{...}]` |
| GET | `/api/auth/audit` | `?days=7&limit=200` | `[{action, timestamp, ...}]` |
| GET | `/api/auth/stats` | — | `{total, pending, active, used, by_scope}` |
| GET | `/api/auth/verify` | — | `{valid, total_records, breaks}` |
| GET | `/api/auth/scopes` | — | `{readonly: [...], privileged: {...}}` |

## Scope 定义 (15 个)

**免授权 (3)**:
- `autodl:ssh:health`, `autodl:ssh:status`, `autodl:ssh:ping`

**需授权 (12)**:
- AutoDL: `autodl:ssh:shutdown` (中), `autodl:ssh:exec` (高), `autodl:api:start/stop` (中), `autodl:api:create` (高), `autodl:api:release` (致命)
- 云资源: `cloud:aws:ec2:terminate` (致命), `cloud:aws:ec2:start/stop`
- 部署: `deploy:production:push` (高)
- 系统: `system:config:modify`, `system:cron:modify`
- Hermes: `hermes:profile:delete`, `hermes:config:modify`

## 消息路由器集成

新增 `auth` 类别 → 路由到 `apex-pm` profile:

```
"autodl:ssh:shutdown 需要授权"  → 🦅 Apex → 🦅 Apex总管 → 授权管理
"批准授权码 123456"             → 🦅 Apex → 🔒 安全合规 → 安全合规
"验证哈希链完整性"              → 🦅 Apex → 🦅 Apex总管 → 授权管理
```

触发关键词: `授权请求`, `授权码`, `request_code`, `审批`, `approve`, `拒绝`, `deny`, `consume`, `revoke`, `吊销`, `审计链`, `哈希链`, `verify`, `grants`, `scope`

## CLI 用法

```bash
# 请求授权
python3 ~/.hermes/scripts/authorization_engine.py request \
    --agent ops-engineer --scope autodl:ssh:shutdown \
    --purpose "空闲3小时，建议关机"

# 审批/拒绝
python3 ~/.hermes/scripts/authorization_engine.py approve 123456
python3 ~/.hermes/scripts/authorization_engine.py deny 123456

# 检查/使用/吊销
python3 ~/.hermes/scripts/authorization_engine.py check --agent ops-engineer --scope autodl:ssh:shutdown
python3 ~/.hermes/scripts/authorization_engine.py consume <grant_id>
python3 ~/.hermes/scripts/authorization_engine.py revoke <grant_id> --reason "..."

# 查询
python3 ~/.hermes/scripts/authorization_engine.py list [--agent X] [--status pending]
python3 ~/.hermes/scripts/authorization_engine.py audit --days 7
python3 ~/.hermes/scripts/authorization_engine.py stats
python3 ~/.hermes/scripts/authorization_engine.py verify
python3 ~/.hermes/scripts/authorization_engine.py scopes
```

## 安全特性

1. **SHA256 哈希链**: 每条记录包含 `prev_hash` → `record_hash`，修改任一条即断裂
2. **Append-only 审计**: `audit.log` 只追加不删除，每次操作双写（文件 + SQLite）
3. **时效绑定**: 每份授权有 TTL（5-10 分钟），过期自动失效
4. **唯一审批人**: `APPROVED_BY = "luke"`，硬编码不可修改
5. **免授权白名单**: 只读操作（health/status/ping）自动放行
