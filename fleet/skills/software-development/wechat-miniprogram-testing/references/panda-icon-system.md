# Kung-Fu Panda SVG Icon System for WeChat Mini-Programs

## Overview

Generate themed SVG icons programmatically (Python), encode as base64 data URIs, and deliver via WXSS classes. This approach avoids:
- External icon font hosting (WeChat blocks most CDNs)
- PNG sprite sheets (manual maintenance)
- Emoji dependency (inconsistent rendering across platforms)

## Generation Pipeline

### 1. Define icon specs in Python

Each icon: 48×48 viewBox, simple geometric shapes forming panda silhouette + badminton elements.

Color palette:
```python
BLACK = "#2d2d2d"   # panda body/outline
WHITE = "#ffffff"   # panda face
ORANGE = "#f97316"  # badminton brand
GREEN = "#22c55e"   # court / positive
GOLD = "#fbbf24"    # achievement
RED = "#ef4444"     # alert
```

### 2. Generate SVGs via Python script

Use reusable component functions (`panda_head()`, `shuttlecock()`, `racket()`) to compose icons. Each icon is a single `<svg>` string wrapped with `svg_wrap()`.

```python
def panda_head(cx=24, cy=20, r=10):
    """Panda head: white circle with black ears and eye patches"""
    return f'''
    <circle cx="{cx-7}" cy="{cy-9}" r="4" fill="{BLACK}"/>
    <circle cx="{cx+7}" cy="{cy-9}" r="4" fill="{BLACK}"/>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="{WHITE}" stroke="{BLACK}" stroke-width="1.5"/>
    <ellipse cx="{cx-4}" cy="{cy-1}" rx="3" ry="3.5" fill="{BLACK}"/>
    <ellipse cx="{cx+4}" cy="{cy-1}" rx="3" ry="3.5" fill="{BLACK}"/>
    <circle cx="{cx-4}" cy="{cy-1}" r="1" fill="{WHITE}"/>
    <circle cx="{cx+4}" cy="{cy-1}" r="1" fill="{WHITE}"/>
    <ellipse cx="{cx}" cy="{cy+2}" rx="1.5" ry="1" fill="{BLACK}"/>
    '''
```

### 3. Encode as data URIs in WXSS

```python
for name, svg in icons.items():
    b64 = base64.b64encode(svg.encode()).decode()
    wxss_lines.append(f'.panda-icon.{name} {{')
    wxss_lines.append(f'  background-image: url("data:image/svg+xml;base64,{b64}");')
    wxss_lines.append(f'}}')
```

### 4. WXSS base class with size variants

```css
.panda-icon {
  display: inline-block;
  width: 48rpx; height: 48rpx;
  background-size: contain;
  background-repeat: no-repeat;
  background-position: center;
  vertical-align: middle;
}
.panda-icon.size-sm { width: 32rpx; height: 32rpx; }
.panda-icon.size-md { width: 48rpx; height: 48rpx; }
.panda-icon.size-lg { width: 64rpx; height: 64rpx; }
.panda-icon.size-xl { width: 96rpx; height: 96rpx; }
```

### 5. Import globally in app.wxss

```css
@import "/utils/panda-icons.wxss";
```

### 6. Use in WXML

```html
<!-- Replace emoji -->
<view>🏸 AI 技能测评</view>

<!-- With panda icon -->
<view>
  <view class="panda-icon icon-shuttlecock size-sm"></view>
  AI 技能测评
</view>
```

## File Structure

```
miniprogram/
├── images/icons/          # SVG source files (for reference/docs)
│   ├── icon-shuttlecock.svg
│   ├── icon-target.svg
│   └── ...
├── utils/
│   └── panda-icons.wxss   # Generated WXSS with base64 data URIs
└── app.wxss               # @import the icon WXSS
docs/
└── panda-icon-system.md   # Full icon mapping + design spec
```

## Icon Mapping Template

For each new icon needed:
1. Add an entry to the design doc mapping (emoji → icon-name → panda pose description)
2. Write the SVG generator function in the Python script
3. Regenerate WXSS
4. Replace emoji in WXML with `<view class="panda-icon icon-XXX">`

## Pitfalls

- **SVG format:** Must be clean XML with `xmlns` attribute. Avoid CSS `@keyframes` in SVGs — they don't render in WeChat's WebView.
- **WXSS size:** Keep total WXSS under 500KB. If too many icons, split into per-page imports instead of global.
- **Inline `<view>` limitation:** Panda icons use `background-image`, so the `<view>` must have explicit width/height. The base class sets 48rpx.
- **Emoji fallback:** Keep emoji as text content inside the icon view as a fallback for accessibility.
