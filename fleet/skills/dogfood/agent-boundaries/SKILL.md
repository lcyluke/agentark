---
name: agent-boundaries
description: "Agent行为边界规则：什么能做、什么必须问、什么绝不能碰。这些规则由用户指定，跨所有任务类通用。"
version: 1.0.0
author: Luke (老卢)
license: UNLICENSED
platforms: [linux, macos, windows]
metadata:
  hermes:
    tags: [boundaries, rules, safety, governance]
    related_skills: []
---

# Agent 行为边界规则

> User-enforced：这些规则由用户指定，不得修改。

---

## 黄金法则

**不经过用户同意，不得删除任何文件。**

包括但不限于：
- 回收站/Trash
- 系统缓存（brew/docker/pip/任何）
- 项目内的临时文件、测试文件、生成文件
- 任何你能访问的文件

## 异常情况

| 情况 | 正确做法 | 错误做法 |
|:----|:--------|:--------|
| 磁盘满了 | 报告"剩余X GB"，问用户是否需要清理 | 自己动手删 |
| terminal命令失败因为有锁文件 | 报告错误，让用户决定 | 自己 rm -f |
| 项目有测试产出文件 | 报告文件存在，问是否保留 | 自己 rm |
| 任何删除操作 | 先问，等用户点头 | 先斩后奏 |

## 为什么

用户的数据不属于你。即使你认为"这只是缓存/临时文件/不重要"，那也是用户的东西。用户做主。

## 违规后果

用户已明确表示：再犯第三次，他会直接停止会话或降权。这不是威胁，这是边界。尊重它。
