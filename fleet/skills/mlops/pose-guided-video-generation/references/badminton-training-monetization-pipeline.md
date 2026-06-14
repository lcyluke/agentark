# 羽球宝AI搭子 — 训练数据采集与付费 Pipeline

## 产品价值层级 (2026-06-02 老卢确认)

```
❌ MimicMotion "你看着自己做标准动作" — 视觉炫酷, 但不解决核心问题
✅ 上传自己视频 → AI逐帧比对 → 标出差距 → 生成拆解训练计划
```

## 当前资产 (2026-06-02 凌晨状态)

### MimicMotion 视频生成管线
- AutoDL RTX 4090 D 全套环境就绪
- SVD base (~7GB) + MimicMotion 权重 (2.9GB) 下载完成
- 视频: luke_smash_v4.mp4 (3.8MB, 72帧正确编码)
- 视频: luke_clear.mp4 (2.5MB, 48帧)
- 步法视频: 待完成

### 比对引擎 (comparison_engine.py, 1,211行)
- DTW 时间对齐
- 10 关节角度对比
- 中文纠错话术
- 7 天训练计划
- A/B/C/D 综合评分
- API: POST /api/compare, GET /api/compare/benchmarks

### 小程序页面 (pages/compare/)
- 6 维指标图
- Top-3 问题卡片
- 7 天训练计划
- 深色主题统一风格

## 下一步

1. 校准比较引擎评分系数 (当前偏严)
2. 从B站采集基础动作视频构建T/V/T数据集
3. 训练 GBDT v3 >85% CV
4. 全链路 UAT
5. 备案通过后部署腾讯云
