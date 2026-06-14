# Hermes Kanban 初始化与操作参考

## 首次初始化

```bash
# 创建 kanban.db（每个用户只需一次）
hermes kanban init

# 创建项目看板（每个项目一个 board）
hermes kanban boards create <slug> \
  --name "项目显示名" \
  --description "描述" \
  --icon "🏸" \
  --color "#10b981" \
  --switch \
  --default-workdir "/path/to/project"
```

## 创建任务

```bash
hermes kanban create "T-NNN: 任务标题" \
  --body "任务描述，换行直接在字符串中" \
  --priority <1-5> \
  --assignee default
```

## 查看和管理

```bash
# 查看当前 board 所有任务
hermes kanban list

# 查看特定任务详情
hermes kanban show <task_id>

# 切换 board
hermes kanban boards switch <slug>

# 列出所有 board
hermes kanban boards list
```

## 任务生命周期

| 状态 | 含义 | 操作 |
|:----:|------|------|
| `todo` | 已创建但依赖未就绪 | 自动 |
| `ready` | 可被 dispatcher 领取 | 自动 |
| `running` | 正在被 worker 执行 | 自动 |
| `done` | 已完成 | `kanban complete` |
| `blocked` | 等待外部输入 | `kanban block` |
| `archived` | 已归档 | `kanban archive` |
