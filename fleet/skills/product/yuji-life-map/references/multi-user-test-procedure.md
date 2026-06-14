# 多用户全链路测试规程

验证打卡系统在多人并发场景下的功能正确性与数据隔离性。

## 测试用户

| 用户 | 模拟场景 | 数据量 |
|------|---------|--------|
| 老卢 🏸 | 活跃球友，多种打卡类型 | 7条（3打球+2吃饭+1旅行+1生活） |
| 小王 | 新手，单一球馆重复打卡 | 2条（同一球馆） |
| 老张 | 新注册观望用户，只搜索不打 | 0条 |

## 测试步骤

```python
BASE = "http://127.0.0.1:8000"

# 1. 各用户微信登录
POST /api/auth/wechat {"code": "mock_<user>_001"}

# 2. 各用户创建打卡
POST /api/checkin multipart/form-data
  type=badminton&venue_name=南山文体中心&notes=和老王打3局&mood=😄

# 3. 验证接口
GET /api/checkins           → 各用户只能看到自己的
GET /api/checkins/timeline  → 按天分组正确
GET /api/checkins/stats     → 统计数字准确
GET /api/checkins/map       → 地图聚合正确
```

## 边界情况（必须覆盖）

| 场景 | 预期 | 实测 |
|------|------|------|
| 非法打卡类型 `type=invalid` | HTTP 400 | ✅ |
| 空关键词搜索 | 返回前N条 | ✅ |
| 未知球馆名 | 正常创建，venue_id=null | ✅ |
| 无token访问 | HTTP 401 | ✅ |
| 数据隔离（用户A看不到B的数据） | 隔离正确 | ✅ |
