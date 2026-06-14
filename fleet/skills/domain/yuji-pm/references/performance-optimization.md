# 羽球宝性能优化手册

> 基于 2026-06-09 会话的实战优化记录。羽球宝后端 30K行/166路由/35表/27小程序页，
> 性能瓶颈集中在 DB、网络传输、小程序加载三个方面。

## 一、DB 连接池 — 最大收益

### 问题
10 个模块各自定义 `_conn()` → `sqlite3.connect()`，每次查询新建连接（163 个调用点）。

### 方案
创建 `db_pool.py`，WAL 模式 + 8MB 缓存 + 线程单例：

```python
# db_pool.py
def get_db() -> sqlite3.Connection:
    if not hasattr(_local, "conn"):
        _local.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        _local.conn.execute("PRAGMA journal_mode=WAL")
        _local.conn.execute("PRAGMA synchronous=NORMAL")
        _local.conn.execute("PRAGMA cache_size=-8000")
    return _local.conn
```

### 批量替换
所有模块的 `_conn()` 函数改为一行：
```python
def _conn():
    from .db_pool import get_db
    return get_db()
```

**涉及文件**：`amateur_training.py`, `assessor_system.py`, `auth_api.py`, `checkin.py`, `matching.py`, `monetization.py`, `ranking_engine.py`, `training_game.py`, `training_tracker.py`, `wechat_pay.py`

**验证**：替换后 `grep -rn 'sqlite3.connect' badminton_coach/ --include='*.py' | grep -v db_pool | grep -v db_indexes` 应返回空。

## 二、数据库索引 — 高频查询加速

### 问题
35 张表仅 5 个索引，大量 `WHERE user_id=?` / `WHERE status=?` 全表扫描。

### 方案
创建 `db_indexes.py`，38 个 `CREATE INDEX IF NOT EXISTS` 覆盖：
- 外键：`user_id`, `assessor_id`, `venue_id`
- 状态：`status`, `booking_date`, `checkin_date`
- 排序：`rating DESC`, `created_at`

```bash
python -m badminton_coach.db_indexes  # 幂等执行
```

**注意**：`daily_quests` 等表可能缺少某些列，用 `try/except OperationalError` 逐条执行。

## 三、API 响应压缩 + 缓存

### 问题
`/api/ranking` 等端点返回 8KB+ JSON，无压缩、无缓存头。

### 方案
FastAPI middleware (`api_optimizer.py`)：
- `Accept-Encoding: gzip` → 压缩响应（省 60-80%）
- GET 请求 → `Cache-Control: public, max-age=60`
- 白名单路径：`/api/coaches`, `/api/assessors`, `/api/venues`, `/api/ranking` 等

```python
app.add_middleware(OptimizeMiddleware)
```

**验证**：`curl -sH "Accept-Encoding: gzip" http://localhost:8000/api/ranking --compressed | wc -c`（应为原始的 20-40%）

## 四、小程序懒加载

### 问题
27 页全量加载，无 `lazyCodeLoading`，无 `preloadRule`。

### 方案
`app.json` 加：
```json
{
  "lazyCodeLoading": "requiredComponents",
  "preloadRule": {
    "pages/home/home": {
      "network": "all",
      "packages": ["pages/assess/assess", "pages/training/training"]
    }
  }
}
```

图片加 `lazy-load`：
```xml
<!-- 所有 <image> 标签 -->
<image src="..." lazy-load mode="aspectFill" />
```

**涉及文件**：`home.wxml`, `assess.wxml`, `profile.wxml`, `mimic.wxml`, `checkin.wxml`, `photos.wxml`

## 五、setData 合并

### 问题
小程序 282 次 `setData`，部分页面连续 3 次独立调用（每次触发一次渲染）。

### 方案
`app.js` 添加 `batchSetData` 工具：
```javascript
batchSetData(page, updates, delayMs) {
  if (!page._batchQueue) page._batchQueue = {};
  Object.assign(page._batchQueue, updates);
  if (!page._batchTimer) {
    page._batchTimer = setTimeout(() => {
      page.setData(page._batchQueue);
      page._batchQueue = {};
      page._batchTimer = null;
    }, delayMs || 16);
  }
}
```

**最严重页面**（需手动合并）：
| 页面 | setData 次数 | 可合并点 |
|:--|:--|:--|
| assess.js | 37 | tierStates + selectedTier (3→1) |
| matching.js | 29 | profile + requests (2→1) |
| booking.js | 19 | 待审计 |

**合并模式**：将条件分支内的 setData 提取为公共变量，分支只赋值，最后统一 setData。

## 六、完整审计命令

```bash
# DB连接审计
grep -rn 'sqlite3.connect' badminton_coach/ --include='*.py' | grep -v db_pool | grep -v db_indexes

# setData 热点
for f in miniprogram/pages/*/; do
  echo "$(grep -c 'setData' $f*.js 2>/dev/null) $(basename $f)"
done | sort -rn

# 图片懒加载覆盖率
grep -rn '<image ' miniprogram/ --include='*.wxml' | grep -v 'lazy-load' | wc -l

# API 响应大小
curl -s http://localhost:8000/api/ranking | wc -c  # 应 < 2KB (压缩后)
```
