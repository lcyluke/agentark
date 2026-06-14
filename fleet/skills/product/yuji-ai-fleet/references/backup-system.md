# 羽球宝AI搭子 — 数据库每日备份系统

## 架构

| 组件 | 路径/值 |
|------|---------|
| **脚本** | `/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/daily_backup.sh` |
| **源数据库** | `users.db` (488K, SQLite, 42 张表, 81 用户) |
| **备份目录** | `backups/` — 存储 `.db.gz` 文件 |
| **备份日志** | `backups/backup.log` |
| **保留策略** | 30 天自动清理 (`find -mtime +30 -delete`) |
| **压缩方式** | `sqlite3 .backup` → `gzip` |

## Cron 配置

两个 cron job 都配置在每日 03:00 触发 — **存在冗余**：

| Job ID | 名称 | 脚本路径 | 状态 |
|--------|------|---------|------|
| `a64ab8981d29` | 羽球宝数据库每日备份 | ❌ `/Users/Mac/workspace/badminton-coach-ai/daily_backup.sh` | 旧路径（空目录），应禁用 |
| `22ed3110b7a0` | badminton-coach-ai 数据库每日备份 | ✅ `/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/daily_backup.sh` | 正确路径 |

> **注意**：`/Users/Mac/workspace/badminton-coach-ai/` 为空目录。项目实际根目录在 `/Users/Mac/Desktop/2026AIAPP/workspace/badminton-coach-ai/`。

## 备份完整性验证

### ❌ 错误方式 — pipe 到 sqlite3 :memory:

```bash
# 这不可靠 — .tables 返回空
gunzip -c backup.db.gz | sqlite3 :memory: ".tables"
```

### ✅ 正确方式 — 先解压到临时文件

```bash
cd backups/
gunzip -k 2026-XX-XX_XXXXXX.db.gz
sqlite3 2026-XX-XX_XXXXXX.db ".tables"
sqlite3 2026-XX-XX_XXXXXX.db "SELECT count(*) FROM users;"
rm -f 2026-XX-XX_XXXXXX.db
```

## 当前状态（2026-06-13）

| 指标 | 数值 |
|------|------|
| 备份文件数 | 33 个 `.db.gz` |
| 最早备份 | 2026-05-30 |
| 备份总大小 | 584K |
| 日志行数 | 99 行 |
| 单次备份大小 | ~26K |

## 备份脚本关键逻辑

1. `sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"` — 一致性快照（比 `cp` 安全）
2. `gzip -f "$BACKUP_FILE"` — 压缩
3. `find "$BACKUP_DIR" -name "*.db.gz" -type f -mtime +30 -delete` — 清理 30 天前
4. `tail -n 200 "$LOG_FILE"` — 日志截断
