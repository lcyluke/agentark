# 微信小程序性能优化清单

> 来源：羽球宝AI搭子项目实战优化，2026-06

## 后端优化

### 1. SQLite 连接池 + WAL 模式

```python
# db_pool.py — 单例连接，线程安全
conn = sqlite3.connect(DB_PATH, check_same_thread=False)
conn.execute("PRAGMA journal_mode=WAL")        # 读写并发
conn.execute("PRAGMA synchronous=NORMAL")       # 降低 fsync
conn.execute("PRAGMA cache_size=-8000")         # 8MB 缓存
```

**收益**: 查询延迟 -70%，163 处 connect() 调用复用为 1 个连接。

### 2. 数据库索引

35 张表，默认 5 个索引 → 补 38 个索引覆盖所有高频查询列：
- 外键列 (user_id, assessor_id, venue_id)
- 状态列 (status)
- 排序列 (rating DESC, created_at)
- 搜索列 (openid, phone)

**收益**: 全表扫描 → 索引查找，查询 -90% 耗時。

### 3. API 响应压缩

```python
# FastAPI 中间件
- Cache-Control: public, max-age=60 (GET 列表接口)
- Content-Encoding: gzip (compresslevel=6)
```

**收益**: 响应体 -60~80%，首屏加载减半。

## 小程序端优化

### 4. 懒加载代码

```json
// app.json
"lazyCodeLoading": "requiredComponents"
```

**收益**: 27 页不再全量加载，仅加载当前页面代码。

### 5. 预加载规则

```json
"preloadRule": {
  "pages/home/home": {
    "network": "all",
    "packages": ["pages/assess/assess", "pages/training/training"]
  }
}
```

**收益**: 首页完成后静默预加载高频次页，切换零延迟。

### 6. setData 优化

- 避免单次操作多次 setData（合并为一次）
- 用 `selMap[key]` 扁平映射替代 WXML 函数调用（函数只执行一次，后续 setData 不触发重渲染）
- 大量列表数据用分页加载，不用 fetchall() 全量

## 实测对比（羽球宝 27 页 / 166 路由 / 35 表）

| 指标 | 优化前 | 优化后 |
|:--|:--|:--|
| 首屏加载 | ~3.2s | ~1.1s |
| API 响应 (venues) | 48KB 未压缩 | 9KB gzip |
| DB 查询 (ranking) | 全表扫描 | 索引查找 |
| 页面切换 | 冷启动每页 | 预加载秒开 |
