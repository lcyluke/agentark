# 训练计划 API

## 端点

```
GET /api/training/plan
Authorization: Bearer <token>
```

## 原理

从 `training_progress` 表读取用户所有技能进度，找出短板（未开始或分数最低的5项），生成7天周计划。

### 计划生成逻辑

```
每天: 2个短板技能(L1-L3逐级) + 1个已掌握技能(巩固)
```

- 短板按最低分排序，前5个短板轮转分配
- 等级自动推进: 已通过L1则升L2，已通过L2则升L3
- 已掌握技能从通过列表中随机选取
- 每项包含: skill_id, name, level, title, volume, key_points, score_needed

## 返回值

```json
{
  "plan": [
    {
      "day": "周一",
      "tasks": [
        {"skill_id": "smash_stand", "name": "原地杀球", "level": 1, 
         "title": "基本原地杀球", "volume": "3组×15次", 
         "key_points": "侧身引拍到位", "score_needed": 60}
      ]
    }
  ],
  "summary": {
    "total_skills": 51,
    "practiced_skills": 12,
    "passed_skills": 5,
    "weakest_areas": [{"id": "smash_jump", "name": "起跳杀球", "score": 0}]
  }
}
```

## 依赖

1. 需要 `training_progress` 表有数据（通过 `POST /api/training/record` 写入）
2. 使用 `SKILL_BANK` 的 `levels` 定义获取训练量/要点
3. 未登录用户返回 401
