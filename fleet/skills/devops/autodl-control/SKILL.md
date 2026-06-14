---
name: autodl-control
description: AutoDL 实例全自动管控 — 监控闲置、通知确认、安全关机、远程开机
category: devops
triggers:
  - 用户说"关闭AutoDL"或"关机AutoDL"
  - 用户说"开启AutoDL"或"开机AutoDL"
  - 用户说"AutoDL状态"
  - 空闲监控 cron 触发
---

# 🔌 AutoDL 全自动管控

## 架构 (v2 — GPU级监控 + Dashboard集成)

```
GPU 闲置监控 (autodl_gpu_idle_monitor.py, cron 每5分钟, no_agent)
    │
    ├─ SSH → nvidia-smi 读 GPU 利用率
    ├─ GPU < 5% 且无推理连接 → 累计空闲周期
    ├─ 状态写入 /tmp/autodl_gpu_state.json（不发微信）
    │
    ├─ 1周期(5分钟) → state.alert_level = "warn"
    ├─ 3周期(15分钟) → state.alert_level = "critical"
    │
    └─ 授权已确认 → 自动执行 shutdown -h +0.5

Dashboard /cc (GPU 资源中心)
    ├─ GET /api/gpu/status → 读 state JSON + SSH 实时数据
    ├─ GET /api/gpu/projects → 项目-GPU 绑定
    ├─ POST /api/gpu/shutdown/request → 生成6位授权码
    ├─ POST /api/gpu/shutdown/confirm → 验证码 → SSH 关机
    └─ 闲置5分⚠️黄色 / 15分🛑红色 → 操作面板提示

关机 (gpu_manager.py, SSH模式, 需授权码)
    ├─ request_shutdown() → 生成 6 位授权码（30分钟有效）
    ├─ confirm_shutdown(code) → 验证码匹配 → kill 推理进程 → shutdown -h +0.5
    └─ cron 检测到 confirmed 标志 → 自动执行
```

## 文件清单

| 文件 | 功能 |
|:--|:--|
| `~/.hermes/scripts/autodl_gpu_idle_monitor.py` | GPU 闲置守护 (SSH nvidia-smi, 写状态JSON) |
| `~/.hermes/scripts/autodl_idle_monitor.py` | 旧版闲置检测 (推理连接, 已弃用) |
| `~/.hermes/scripts/autodl_health.py` | 隧道健康检查 |
| `apex/interface/gpu_manager.py` | GPU 资源中心后端 (状态/项目/关机授权) |
| `apex/interface/templates/command_center.html` | GPU 资源中心前端视图 |

## 实例

| ID | 主机 | 端口 | 密码文件 | GPU | 状态 |
|:--|:--|:--|:--|:--|:--|
| westb | connect.westb.seetacloud.com | 16786 | `~/.hermes/.autodl_west_pass` | RTX 4090 24GB | 主力 |
| bjb2 | connect.bjb2.seetacloud.com | 32581 | `~/.hermes/.autodl_pass` | — | 已过期 |

## 操作流程

### 当用户说"AutoDL状态"时

1. 优先引导到 Dashboard: http://localhost:8080/cc → GPU 资源中心
2. 或通过 API: `curl http://localhost:8080/api/gpu/status`
3. 或通过 cron: 检查 `/tmp/autodl_gpu_state.json`

### 当用户说"关闭AutoDL" / "关机AutoDL"时

1. Dashboard 路线: POST `/api/gpu/shutdown/request` → 获取授权码 → POST `/api/gpu/shutdown/confirm` 带码
2. 微信路线: 提醒用户去 Dashboard 操作，或生成授权码发送到微信由老卢回复确认
3. cron 兜底: autodl_gpu_idle_monitor.py 检测到 `confirmed: true` → 自动执行关机

### 当用户说"开启AutoDL"时

1. 需 API Token (老卢去 AutoDL 控制台获取)
2. 调用 `autodl_api.py start` → 轮询就绪 → 建立隧道 → 启动推理服务

## 密码安全

- SSH 密码: `~/.hermes/.autodl_pass` (chmod 600)
- API Token: `~/.hermes/.autodl_token` (chmod 600)
- 实例 UUID: `~/.hermes/.autodl_instance`
- 所有命令不通过参数传递密码，使用 `sshpass -e` 环境变量模式或管道

## Pitfalls

- **command_center.html JS 模板字符串陷阱**: 在 Flask Jinja 模板中嵌入 JS 时，模板字符串内的 ` 容易与 patch 工具交互出错。**JS 生成 HTML 时优先用字符串拼接** (`+`) 而非模板字符串，避免多行模板字符串被意外截断。修改后必须用 `node --check` 验证语法，再重启 Flask 服务器。
- **patch 工具与模板字符串**: `patch(old_string=..., new_string=...)` 时，如果 old_string 包含反引号模板字符串，确保 new_string 的模板字符串完整闭合（尤其是多行模板字符串）。最常见 bug: return 语句的模板字符串被意外截断，导致后续 HTML 标签被 JS 解析器当作语法错误。
- **Flask 路由重复名**: `create_app()` 内所有路由用 `@app.route()` 装饰，同一函数名不能注册两次。新增路由前先搜索是否已存在同名端点。
- **SSH 授权网关**: 所有 SSH 操作必须通过 `autodl_ssh.py`。安全命令(health/status)免授权，危险命令(shutdown/exec)需授权确认。授权状态文件 `/tmp/autodl_ssh_auth.json`，审计日志 `/tmp/autodl_ssh.log`。
- **SSH 密码泄露风险**: 绝对不在命令行参数中用 `sshpass -p '明文密码'`。cron 通知会把命令错误消息发到微信，可能包含命令行。用 `SSHPASS` 环境变量 + `sshpass -e` 或 `stdin` 管道。
- **Cron script 参数限制**: `no_agent=True` 的 cron job，`script` 字段不能带参数（`"script.py arg"` 会被当整体文件名）。每个角色需要独立 wrapper 脚本。
- **关机不可逆**: `shutdown -h now` 执行后无法 SSH 取消。生产环境用 `shutdown -h +0.5`（30秒倒计时）给用户反悔窗口。
- **推理进程 PID 查找**: AutoDL 上 python 路径为 `/root/miniconda3/bin/python`，`pgrep -f` 要匹配这个路径而非 `python3`。
- **SSH 立即被拒 (`Connection closed by`)**: 实例刚开机或重启后，SSH 服务可能需要 30-120 秒才能接受连接。表现为所有端口都返回 `Connection closed by <ip> port <port>` 而非 `Connection refused` 或 `timeout`。**诊断流程**: (1) 检查隧道守护进程 `autodl_tunnel.sh status` (2) 等待 60 秒后重试 (3) 尝试多个已知端口 (32581/16786/33553) (4) 检查 AutoDL 控制台确认实例确为「运行中」而非「启动中」 (5) 如持续失败，密码或端口可能已变更，需要去控制台获取新 SSH 信息。**不要反复重试同一端口** — 指数退避重连由隧道守护进程自动处理。

## Cron 清单

| Job | 频率 | 脚本 | 功能 |
|:--|:--|:--|:--|
| a5981094038f | 每2分钟 | autodl_health.py | 隧道健康检查 |
| a19942f3f9f4 | 每5分钟 | autodl_gpu_idle_monitor.py | GPU 闲置检测 → 状态 JSON |

## Dashboard /cc GPU 资源中心

- URL: http://localhost:8080/cc → 侧栏「GPU 资源中心」
- 视图函数: `renderGPU()` in command_center.html
- 后端 API: `/api/gpu/status`, `/api/gpu/projects`, `/api/gpu/shutdown/request`, `/api/gpu/shutdown/confirm`
- 后端模块: `apex/interface/gpu_manager.py`
- 关机关卡: 请求 → 6位授权码 → 输入码确认 → SSH 执行
- 状态文件: `/tmp/autodl_gpu_state.json`, `/tmp/autodl_gpu_auth.json`

## 方案升级路径

| 阶段 | 能力 | 依赖 |
|:--|:--|:--|
| ✅ A. SSH关机 | 安全关机现有实例 | SSH密码 (已有) |
| ⏳ B. API开关 | 远程开机/关机 | API Token (待老卢提供) |
| 📋 C. 创建实例 | 从零创建GPU实例 | Token + 镜像UUID |
