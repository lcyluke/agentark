# Mini-Program Training Page Architecture

## File locations
- `miniprogram/pages/training/training.js` — data + logic
- `miniprogram/pages/training/training.wxml` — dual-sort layout
- `miniprogram/pages/training/training.wxss` — styles

## Data architecture

### Built-in fallback (BUILTIN_CATEGORIES)
The page ships with built-in training data so it works offline without the backend:

```javascript
const BUILTIN_CATEGORIES = [
  { id: 'clear', emoji: '🏸', name: '高远球', sub_skills: [
    { id: 'clear_fh', name: '正手高远球', difficulty: 1, levels: [{ level:1, volume:'...', pass_score:60, key_points:[...], common_mistakes:[...] }, ...] },
    ...
  ]},
  ...
];
```

Status: 7 categories · 21 sub-skills · ~3 levels each. This is a SUBSET of the backend's full 23-category system in `skill_definitions_full.py`. The frontend built-in data is the curated core; the backend returns the full 23 categories via `GET /api/training/categories`.

### Level difficulty mapping
Each sub-skill has `difficulty: 1|2|3`:
- difficulty=1 → 基本功 (basic fundamentals)
- difficulty=2 → 业余级 (amateur/intermediate)
- difficulty=3 → 专业级 (advanced/pro)

### LEVEL_GROUPS computation
`LEVEL_GROUPS` is computed dynamically in `_computeLevelGroups()`:

```javascript
const LEVEL_GROUPS = [
  { id: 'basic',    label: '基本功',   emoji: '⭐',    color: '#10b981', minDiff: 1, maxDiff: 1 },
  { id: 'amateur',  label: '业余级',   emoji: '🌟🌟',   color: '#3b82f6', minDiff: 2, maxDiff: 2 },
  { id: 'advanced', label: '专业级',   emoji: '🌟🌟🌟', color: '#f97316', minDiff: 3, maxDiff: 3 },
];
```

Each group collects all sub_skills whose `difficulty` falls in [minDiff, maxDiff], annotating them with `catId`, `catEmoji`, `catName` for cross-reference.

## Dual-sort pattern

The page supports two views via `sortMode` toggle:

### Mode 1: 按动作 (category view)
- `sortMode: 'category'`
- Renders `categories` array as collapsible panels (`cat-bar` → `skill-grid`)
- Uses `toggleCat` to expand/collapse
- Each skill cell shows L{difficulty} badge in top-left

### Mode 2: 按等级 (level-group view)
- `sortMode: 'level'`
- Renders `levelGroups` array as level cards with inline skill lists
- Each level card has colored header (基本功 green / 业余级 blue / 专业级 orange)
- Skills listed as rows: emoji → name → category name → difficulty badge → status checkmark

### Sort toggle UI
```xml
<view class="sort-bar">
  <view class="sort-tab {{sortMode==='category'?'active':''}}" bindtap="switchSort" data-mode="category">🔤 按动作</view>
  <view class="sort-tab {{sortMode==='level'?'active':''}}" bindtap="switchSort" data-mode="level">📊 按等级</view>
</view>
```

## Progress tracking pattern
- Progress loaded from `GET /api/training/progress` (falls back to local storage)
- `passSet` — Set of skill IDs marked as passed
- `_computeLevelGroups()` re-runs after progress load to propagate `passed` flags to both views
- Post `recordPractice()`: updates categories, recomputes levelGroups, persists to `wx.setStorageSync('trainingCats', cats)`

## Video demo display (dynamic loading from B站 clips)

Each skill detail modal now loads a **B站-sourced action clip** via the video mapping API:

### JS: `_loadDemoVideo(skillId, level)`

```javascript
_loadDemoVideo(skillId, level) {
  wx.request({
    url: `${API}/api/training/skill-video/${skillId}?level=${level}`,
    success: (res) => {
      if (res.data && res.data.url) {
        this.setData({
          demoVideo: res.data,
          demoVideoLoading: false,
        });
      } else {
        this.setData({ demoVideo: null, demoVideoLoading: false });
      }
    },
    fail: () => {
      this.setData({ demoVideo: null, demoVideoLoading: false });
    }
  });
}
```

Called from `openDetail()` for level 1, and from `switchLevel()` on level change.

### WXML: Video player with metadata

```xml
<view class="video-box">
  <view wx:if="{{demoVideoLoading}}" class="video-loading">⏳ 加载示范视频...</view>
  <view wx:elif="{{demoVideo && demoVideo.url}}">
    <video src="{{API}}{{demoVideo.url}}" controls objectFit="contain" 
           show-center-play-btn="{{true}}" style="width:100%;height:340rpx;border-radius:16rpx;"></video>
    <view class="video-meta">
      <text class="video-meta-tag">{{demoVideo.source}}</text>
      <text class="video-meta-tag">{{demoVideo.resolution}}</text>
      <text class="video-meta-tag">🦴骨骼{{demoVideo.skeleton_ready?'已就绪':'收集中'}}</text>
    </view>
    <view class="video-desc">{{demoVideo.best_for}}</view>
  </view>
  <view wx:elif="{{!demoVideoLoading && !demoVideo}}" class="video-empty">
    📹 暂无示范视频（Pipeline采集中）
  </view>
</view>
```

**Note:** `API` must be exposed to the template via `data: { API: API, ... }` in `Page()`.

### Fallback behavior
- Backend down → `fail` handler → `demoVideo: null` video box shows "暂无示范视频"
- No mapping for that skill_level → API returns `{url: null}` → same empty state
- Both cases render the `.video-empty` placeholder without breaking the modal UI

## Other updates

### frontend `skill_cell` now shows `skill.videoUrl` placeholder
The training detail format above shows `detailSkill.videoUrl` which is a field added to per-skill data when it's loaded from server. If demo isn't available, the video area becomes an empty-state "Pipeline采集中" placeholder.
The home page reads `trainingCats` from storage to compute the training completion percentage ring:
```javascript
const cats = wx.getStorageSync('trainingCats');
const total = cats.reduce((s, c) => s + c.sub_skills.length, 0);
const passed = cats.reduce((s, c) => s + c.sub_skills.filter(sk => sk.passed).length, 0);
this.setData({ trainingPct: total > 0 ? Math.round(passed / total * 100) : 0 });
```

## Reuse this pattern
The dual-sort pattern (category vs computed-group view) is reusable for any mini-program page that needs multiple organizational axes:
1. Define `sortMode` in data
2. Compute the secondary grouping from the primary data array
3. Show/hide sections with `wx:if="{{sortMode==='X'}}"`
4. Pass `sortTabs` for the toggle bar
5. Keep both views in sync — update the alternate grouping whenever the primary data changes
