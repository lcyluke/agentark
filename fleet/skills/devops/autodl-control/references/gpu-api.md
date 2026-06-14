# GPU 资源中心 API 参考

## 端点

### GET /api/gpu/status
返回 GPU 实时状态 + 闲置信息 + 授权状态。

```json
{
  "online": true,
  "gpu_name": "NVIDIA GeForce RTX 4090",
  "gpu_util_pct": 0,
  "memory_used_mb": 1,
  "memory_total_mb": 24564,
  "temperature_c": 35,
  "fan_pct": 30,
  "power_w": 12,
  "inference_busy": false,
  "idle_minutes": 10,
  "idle_cycles": 2,
  "alert_level": "warn",
  "last_check": "2026-06-05T...",
  "pending_shutdown": false,
  "auth_pending": false,
  "auth_code": ""
}
```

alert_level: "normal" | "warn" | "critical"

### GET /api/gpu/projects
返回项目-GPU 绑定列表。

```json
{
  "projects": {
    "羽球宝AI": {"instance": "westb", "gpu": "RTX 4090 24GB", "bound_at": "..."},
    "Apex": {"instance": "westb", "gpu": "RTX 4090 24GB", "bound_at": "..."}
  },
  "instances": [
    {"id": "westb", "host": "connect.westb.seetacloud.com", "port": 16786, "gpu_type": "RTX 4090 24GB"}
  ]
}
```

### POST /api/gpu/projects/bind
绑定项目到实例。

```json
{"project": "羽球宝AI", "instance": "westb"}
```

### POST /api/gpu/shutdown/request
发起关机请求，生成 6 位授权码。

```json
// Request
{"project": "羽球宝AI"}

// Response
{"status": "pending_approval", "code": "A3F8B2", "message": "关机需授权，请确认码 A3F8B2", "expires_in_minutes": 30}
```

### POST /api/gpu/shutdown/confirm
输入授权码确认关机。

```json
// Request
{"code": "A3F8B2"}

// Response (成功)
{"ok": true, "action": "shutdown", "message": "GPU 服务器将在 30 秒后关机"}

// Response (失败)
{"error": "授权码不匹配"}
```

## 状态文件

| 文件 | 内容 |
|:--|:--|
| /tmp/autodl_gpu_state.json | 闲置周期、GPU 利用率、最后检查时间、alert_level |
| /tmp/autodl_gpu_projects.json | 项目-实例绑定关系 |
| /tmp/autodl_gpu_auth.json | 待审批授权 (code, pending, confirmed) |

## 后端模块

`apex/interface/gpu_manager.py`:
- `get_gpu_status()` — SSH nvidia-smi + 状态文件 → 完整状态
- `get_gpu_projects()` — 项目绑定列表
- `bind_project(project, instance)` — 绑定
- `request_shutdown(project)` — 生成授权码
- `confirm_shutdown(code)` — 验证码 + 执行关机
