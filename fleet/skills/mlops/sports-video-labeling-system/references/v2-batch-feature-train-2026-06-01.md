# V2 批量特征提取+训练 — 2026-06-01

> **结果:** 从旧172个360p样本（76.1% CV）→ 1,884个B站高画质样本（97.6% CV / 98.1% test）
> **关键变化:** 直接从骨架JSON提特征，跳过文本标注解析步骤

## 脚本

`scripts/batch_feature_train_v2.py` — 端到端单脚本：骨架JSON→28维特征→多模型训练

## 28维特征计算

直接从MediaPipe 33个landmarks计算，每帧：

### 关节角度（从骨骼坐标算）
```
right_elbow   = angle(shoulder→elbow→wrist)
right_shoulder = angle(elbow→shoulder→hip)
right_knee    = angle(hip→knee→ankle)
right_hip     = angle(shoulder→hip→knee)
waist_twist   = angle(shoulder_line, hip_line)
right_wrist   = angle(elbow→wrist→thumb)
```

### 运动学特征
```
P1 发力时序: 膝/髋/肩/肘的角速度峰值时间顺序 [0-1]×4
P2 爆发力:   所有关节速度的均值 / 10, clamp到[0,1]
P3 松弛度:   1/(1 + 角速度CV), 值越高越松弛 [0-1]
P4 弹跳:     肩部Y坐标变化范围 ×100, clamp
P5 链效率:   1 - 角速度偏差std/10
P6 肩内旋:   肩关节速度均值/10
P7 髋旋转:   骨盆倾斜变化×10
P8 一致性:   1 - 帧间角度变化std/均值
P9 冲击力:   腕关节峰值速度/20 + 前10%均值/10
```

### 身体指标
```
B1 脚步:     踝关节活跃度均值/5
B2 握拍:     腕角均值/180 + 腕角std/60
B3 协调性:   左右肩对称性
B4 膝外翻:   默认0.3（2D视频无法精确测量）
```

## 模型结果

| 模型 | 旧(172样本 360p) | 新(1,884样本 B站v2) | 提升 |
|:----|:---------------:|:------------------:|:---:|
| RandomForest | 77.1% test / 66.1% CV | **97.9% test / 97.6% CV** | **+31.5pp** |
| GradientBoosting | 91.4% test / 76.1% CV | **98.1% test / 97.0% CV** | **+20.9pp** |
| Ensemble | 91.4% test | **98.1% test** | +6.7pp |
| 爆发力回归 | N/A | **R²=1.000** | new |

## 特征重要性 (新模型)
1. P2_explosive (29.5%) ← 爆发力
2. P6_sh_ir_speed (22.4%) ← 肩内旋速度
3. P7_hip_rot_speed (9.1%) ← 髋旋转速度
4. A8_pelvis_std (4.2%) ← 骨盆稳定性
5. B1_foot (3.7%) ← 脚步活跃度

## 输出模型文件
```
models/
  phase1_randomforest_v2.pkl    (1.2MB)
  phase2_gbdt_v2.pkl            (1.3MB)
  phase2_ensemble_v2.pkl        (5.0MB)
  phase2_regression_v2.pkl      (14.7MB)
```

## 验证

```bash
cd ~/Desktop/2026AIAPP/badminton-label-system
python3 -c "
import pickle, json
with open('models/phase2_gbdt_v2.pkl','rb') as f:
    d = pickle.load(f)
with open('data/phase_v2_report.json') as f:
    r = json.load(f)
print(f'模型: GBDT v2')
print(f'样本: {r[\"samples_bili\"]}')
print(f'精度: test={r[\"models\"][\"GradientBoosting\"][\"test_acc\"]:.1%}, cv={r[\"models\"][\"GradientBoosting\"][\"cv_mean\"]:.1%}')
"
```

## 关键坑
1. **速度单位是归一化坐标/帧** — 不是真实m/s，只在同类型视频间比较
2. **慢动作教学视频的爆发力得分低（2-9）** — 正常！因为慢放降低了角速度。别重归一化
3. **MediaPipe坐标Y轴向下** — 所有"高度"计算都要用 Y-down 坐标系，不要翻转
4. **旧模型文件不兼容** — `phase_*.pkl` vs `phase_*_v2.pkl` 文件名不同，需更新webapp.py引用
5. **V2模型结构是扁平dict `{model, scaler}`** — 不是V1的嵌套 `{grade_model:{model:...}}`

## 部署到主项目

```bash
# 复制模型到主项目
cp ~/badminton-label-system/models/phase*_v2.pkl ~/workspace/badminton-coach-ai/models/

# 重启后端
kill $(lsof -ti:8000) 2>/dev/null
cd ~/workspace/badminton-coach-ai && ./venv/bin/python3 -m uvicorn badminton_coach.webapp:app --host 0.0.0.0 --port 8000

# 验证模型可加载
curl -s http://localhost:8000/api/annotation/models
```

主项目的 `label_integration.py` 需要用 V2 版本（见 `references/fastapi-integration-pattern.md`），因为 V2 模型的结构（`{model, scaler}`）和 V1（`{grade_model:{model:...}}`）完全不兼容。
