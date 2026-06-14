# 技能→视频映射 + 小程序集成 (2026-06-01)

> 把B站高画质动作片段映射到小程序训练页，让用户点击技能时直接观看4K/60fps示范视频

## 核心文件

| 文件 | 路径 | 用途 |
|:----|:-----|:-----|
| 映射JSON | `badminton-label-system/data/skill_video_mapping.json` | 子技能ID→B站clip路径 |
| 映射文档 | `badminton-label-system/docs/SKILL_TO_VIDEO_MAP_v2.md` | 23类127子技能完整映射表 |
| 后端API | `badminton-coach-ai/badminton_coach/webapp.py` | 3个新端点 |

## 后端新增API

```python
# 在 webapp.py 的 amateur_training import 之后添加

# 1. 全量映射
@app.get("/api/training/video-mapping")
def skill_video_mapping():
    ...

# 2. 单技能最佳视频
@app.get("/api/training/skill-video/{skill_id}")
def skill_best_video(skill_id: str, level: int = 1):
    ...

# 3. 静态文件服务（在_init_部分）
app.mount("/clips", StaticFiles(directory=CLIPS_DIR), name="action_clips")
app.mount("/skeletons", StaticFiles(directory=SKEL_DIR), name="skeleton_data")
```

## 小程序前端改动

### training.js 新增方法
```javascript
_loadDemoVideo(skillId, level) {
  wx.request({
    url: `${API}/api/training/skill-video/${skillId}?level=${level}`,
    success: (res) => {
      if (res.data && res.data.url) {
        this.setData({ demoVideo: res.data, demoVideoLoading: false });
      }
    }
  });
}
```

### training.wxml 视频区域
```html
<view class="video-box">
  <view wx:if="{{demoVideoLoading}}">⏳ 加载示范视频...</view>
  <view wx:elif="{{demoVideo && demoVideo.url}}">
    <video src="{{API}}{{demoVideo.url}}" controls ...></video>
    <view class="video-meta">
      <text>{{demoVideo.source}}</text>
      <text>{{demoVideo.resolution}}</text>
      <text>🦴骨骼{{demoVideo.skeleton_ready?'已就绪':'收集中'}}</text>
    </view>
    <view class="video-desc">{{demoVideo.best_for}}</view>
  </view>
</view>
```

## pitfall: 小程序WXML不支持表达式

WXML的 `{{ }}` 只支持数据引用，不支持任何函数调用、表达式、Date/Array操作。必须全部在.js预计算好再setData。

## pitfall: 视频路径globbing

映射JSON中 `src` 字段是glob模式（`demo*.mp4`），后端API需要将`*`替换为目录路径。当前实现仅返回目录前缀，小程序播放器会播放目录下的第一个mp4文件。
