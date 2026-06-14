---
name: wechat-miniprogram-testing
description: "UAT testing workflow for WeChat mini-programs using DevTools CLI. Covers preview QR generation, LAN networking for mobile testing, survey/Q&A patterns, login testing, and common failure modes specific to WeChat mini-programs."
version: 1.2.0
author: Hermes Agent
license: MIT
platforms: [macos]
metadata:
  hermes:
    tags: [wechat, miniprogram, uat, qa, testing, devtools]
    related_skills: [dogfood, systematic-debugging, badminton-pm]
---

# WeChat Mini-Program UAT Testing

## Overview

Systematic UAT testing for WeChat mini-programs using the WeChat DevTools CLI. This is distinct from web-app QA (which uses the browser toolset) — WeChat mini-programs require the DevTools CLI for preview and the mobile WeChat app for testing on real devices.

## Prerequisites

- WeChat DevTools CLI at `/Applications/wechatwebdevtools.app/Contents/MacOS/cli`
- A valid mini-program AppID (e.g., `wxdad7cddb0cfa785e`)
- Backend server running (FastAPI/Flask/etc.)
- Mobile phone with WeChat installed, on the same Wi-Fi network

## DevTools CLI Quick Reference

```bash
# Open project in DevTools
cli open --project /path/to/miniprogram

# Check login status
cli islogin

# Generate preview QR code (image format for sending to user)
# ⚠️ WARNING: cli preview is BROKEN and returns code 10 on many versions.
# Use the AppleScript fallback below instead.
cli preview --project /path/to/miniprogram -f image -o /tmp/wechat_qr/preview.png

# Re-login (if token expired)
cli login

# Close project
cli close <project>

# Quit IDE entirely
cli quit
```

### AppleScript Preview (reliable fallback)

When `cli preview` or `cli auto-preview` returns `code 10` (project path / appid required), the CLI port mechanism is broken. The IDE listens on random ports each restart — not the `--remote-port` value. **The only reliable way to trigger preview is AppleScript menu clicking:**

```bash
# Full automation: open project + click "工具 → 预览"
osascript -e '
tell application "wechatwebdevtools" to activate
delay 2
tell application "System Events"
  tell process "wechatdevtools"
    tell menu "工具" of menu bar item "工具" of menu bar 1
      click menu item "预览  [⇧⌘P]"
    end tell
  end tell
end tell
'
```

**Why CLI preview fails:** The `cli preview` and `cli auto-preview` commands connect to a hardcoded port (e.g., 3799 when `--remote-port 3799` was passed) but the IDE server starts on a different random port. The `--remote-port` flag on IDE startup doesn't reliably control the port. Symptoms: `code 10` with `Error: 错误 undefined (code 10)` — this is a known WeChat DevTools CLI bug, not a project issue.

**The menu hierarchy:** `wechatdevtools` → menu bar → "工具" → "预览  [⇧⌘P]"

**CRITICAL:** The menu item name includes the shortcut markers `[⇧⌘P]`. Using just `"预览"` without the shortcut returns error -1728 (menu item not found). Always include the full name with shortcut as shown by `name of every menu item`.

## UAT Workflow

### Phase 1: Environment Setup

**Critical: networking for mobile testing**
The No.1 failure mode for mobile UAT is the mini-program frontend pointing to `127.0.0.1` (the phone's own localhost) instead of the Mac's LAN IP.

```bash
# Get Mac LAN IP
ipconfig getifaddr en0

# Restart backend on 0.0.0.0 (all interfaces, not 127.0.0.1)
./venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000

# Verify LAN IP is reachable
curl -s http://192.168.X.X:8000/health
```

**Critical: DevTools simulator vs mobile phone use DIFFERENT addresses**

This is a common point of confusion. The DevTools simulator runs ON the Mac, so it needs `127.0.0.1`. The phone preview runs on a real phone, so it needs the Mac's LAN IP. They cannot use the same address.

- **For DevTools simulator testing:** `apiBase: 'http://127.0.0.1:8000'`
- **For phone preview (QR code):** `apiBase: 'http://192.168.X.X:8000'` (Mac's LAN IP)

**Workflow:** Test in DevTools simulator with `127.0.0.1` first, then change to LAN IP and regenerate QR for phone testing. Remember to change back after phone testing or before the next DevTools session.

**Warning:** If `apiBase` is set to a LAN IP (e.g. `192.168.0.103:8000`) and you open the project in DevTools, the simulator may hang with `appLaunch timeout` error because the simulator's networking differs from the Mac's. The fix is switching back to `127.0.0.1` for DevTools work.

**Set the LAN IP in the mini-program's API base URL** — typically in `app.js`:
```javascript
apiBase: 'http://192.168.X.X:8000',  // NOT 127.0.0.1 — only for phone preview
```

For easy toggling, keep a comment in app.js:
```javascript
// DevTools → 127.0.0.1:8000
// Phone preview → 192.168.X.X:8000
apiBase: 'http://127.0.0.1:8000',
```

### Phase 2: Backend API Pre-Check

Before generating a preview QR, run a quick smoke test of all backend endpoints:

1. **Health check** — root URL returns 200
2. **Login mock** — POST to `/api/auth/wechat` returns token
3. **Survey questions** — GET `/api/survey/questions` returns expected structure
4. **Core assess** — POST `/api/assess` with a test image returns grade/score

### Phase 3: Generate Preview & Test

```bash
# Compile and generate preview QR
cli preview --project /path/to/miniprogram -f image -o /tmp/wechat_qr/preview.png

# Send QR to user as native image
# Include MEDIA:/tmp/wechat_qr/preview.png in response
```

**Preview QR note:** QR codes expire after a few minutes. If the user can't scan in time, regenerate.

### Phase 4: User Journey Testing

Have the user scan the QR on their phone and walk through:

| Step | Page | What to Check |
|:----:|:----|:-------------|
| 1 | Login | Button clickable, login succeeds, redirects correctly |
| 2 | Survey | All questions render, multi-select works, validation fires |
| 3 | Home | User nickname displays, tier badge shows, cards tappable |
| 4 | Assess | Mode selector works, media picks up camera/album |
| 5 | Result | Grade/score render, 6-dimension chart visible, share works |
| 6 | Profile | Tier info, upgrade flow, history loads |
| 7 | Payment | Tier comparison renders, payment method selector works, mock payment flow completes |
| 8 | Certificate | Certificate card renders with grade/score/cert ID, share button works |
| 9 | Invite | Invite code displays, copy button copies, share menu includes invite code |

### Phase 5: Rapid Iteration

When user reports issues:

1. **Identify root cause** — is it frontend (WXML/JS rendering), backend (API response), or networking (LAN/HTTPS)?
2. **Fix and regenerate** — edit code, regenerate preview QR, send new one
3. **Version the QR** — use filenames like `preview_v2.png`, `preview_v3.png` to track iterations

### Phase 6: DevTools Simulator vs Phone — Dual-Mode Strategy

**DevTools CLI commands open the IDE but don't reliably render the simulator.** The `cli open`, `cli preview`, and `cli auto-preview` commands launch the DevTools backend (IDE server on port 41161) and compile the project. They DO NOT necessarily show the GUI simulator window or guarantee the mini-program is rendering inside it.

**To actually see what's in the simulator:**

- The DevTools CLI is sufficient for compilation checking and QR generation
- For visual inspection, open the DevTools GUI manually (Finder → Applications → 微信开发者工具, or `open /Applications/wechatwebdevtools.app`)
- For automated UI testing, use the `cli auto` command to enable automation mode
- Common simulator errors like `routeTo appLaunch timeout` in logs indicate the mini-program failed to initialize — usually a networking/API issue or a blank whitelist

**Dual-address strategy for DevTools vs phone:**

| Environment | `apiBase` value | Why |
|:-----------|:---------------|:----|
| DevTools simulator | `127.0.0.1:8000` | Runs on same machine as backend |
| Phone preview (QR) | `192.168.X.X:8000` | Phone needs Mac's LAN address |
| Production (online) | `https://your-domain.com` | HTTPS mandatory for WeChat |

Remember to toggle `apiBase` in `app.js` when switching between DevTools and phone testing.

## WXML Compiler Quirks

The WXML compiler is more restrictive than standard HTML/CSS/JS. These patterns cause compilation failures that the DevTools error messages don't always pinpoint clearly.

### 1. `style` attribute cannot span multiple lines

WXML attributes must be on a single line. Multi-line `style` breaks compilation.

```wxml
<!-- ❌ BROKEN — style value spans two lines -->
<view style="font-size:24rpx;opacity:.85;
  color:{{condition?'#34d399':'#64748b'}}">{{text}}</view>

<!-- ✅ FIX — single line -->
<view style="font-size:24rpx;opacity:.85;color:{{condition?'#34d399':'#64748b'}}">{{text}}</view>
```

### 2. No ES6 methods in binding expressions

WXML `{{}}` bindings only support ES5. Common offenders:

| ES6 (unsupported) | ES5 replacement |
|:--|:--|
| `str.startsWith('✅')` | `str.indexOf('✅')===0` |
| `str.endsWith('px')` | `str.lastIndexOf('px')===str.length-2` |
| `str.includes('foo')` | `str.indexOf('foo')!==-1` |
| `arr.find(x => ...)` | `arr.filter(x => ...)[0]` |
| Arrow functions `() =>` | `function(){}` (only in JS files, not WXML) |

```wxml
<!-- ❌ BROKEN — startsWith is ES6 -->
<view style="color:{{f.startsWith('✅')?'#34d399':'#64748b'}}">{{f}}</view>

<!-- ✅ FIX — indexOf===0 is ES5 -->
<view style="color:{{f.indexOf('✅')===0?'#34d399':'#64748b'}}">{{f}}</view>
```

### 3. Inline arrow functions in event handlers break compilation

WXML `bind*` attributes cannot contain arrow functions. The compiler rejects `e=>...` with `Bad value with message: unexpected `>`.

```wxml
<!-- ❌ BROKEN — inline arrow function -->
<view bindinput="e=>venue=e.detail.value">

<!-- ✅ FIX — named JS method -->
<view bindinput="onVenueInput">
```

All logic must live in named `Page()` methods, never inline in the template.

### 4. Orphan CSS declaration outside any selector

A `font-family` (or any CSS property) floating between selector blocks with no owning `{...}` causes `Unexpected }` at the next `}`. This happens when copy-pasting or editing leaves a dangling declaration.

```css
/* ❌ BROKEN — orphan font-family + } outside any selector */
.dual-banner-arrow { font-size: 32rpx; color: #6366f1; }
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
}

/* ✅ FIX — remove the orphan lines */
.dual-banner-arrow { font-size: 32rpx; color: #6366f1; }
```

Error message: `pages/compare/compare.wxss:21:1: Unexpected }` — note the line and column point to the CLOSING `}`, not the orphan declaration itself. Look backwards from the error line to find orphaned property declarations.

### 5. `.reduce()` and `.map()` with arrow functions fail in WXML

These are the most common ES6 offenders in template expressions. Must precompute in JS.

```wxml
<!-- ❌ BROKEN — .reduce() and .map() with arrow functions -->
<text>{{selectedSkills.reduce((s,c) => s + c.subCount, 0)}}个视频·{{selectedSkills.map(s => s.name).join(' · ')}}</text>

<!-- ✅ FIX — precompute in JS, bind single string -->
<!-- In JS: this.setData({ skillSummaryText: '共' + totalVideos + '个视频·' + names.join(' · ') }) -->
<text wx:if="{{skillSummaryText}}">{{skillSummaryText}}</text>
```

Pattern: any WXML `{{}}` expression involving `.reduce(`, `.map(`, `.filter(`, `.find(` with a `=>` arrow function will fail. Move all such logic to a named JS method that precomputes a flat data property, then bind that property in WXML.

### 7. Multi-line WXML tags — "unexpected character" (lib 2.33.0)

**CRITICAL: This is the most common WXML compilation error that is misdiagnosed.** When the DevTools error says `unexpected character 'N'` at a line that has no visible `N`, the real problem is almost always a **multi-line tag** — an XML tag whose attributes span multiple lines.

**Root cause:** In WXML lib 2.33.0, when an opening tag like `<view wx:for="..." wx:key="id"` ends a line without `>`, the compiler misparses the continuation line. The first character of the next line's attribute (e.g. `class`) generates a spurious "unexpected character" error. The number in the error message (e.g. `'8'`, `'2'`) is an internal token code, not a character in your source.

```wxml
<!-- ❌ BROKEN — multi-line tag → "unexpected character '8'" at line 83 -->
<view wx:for="{{people}}" wx:key="id"
      class="person-card {{selectedPersonId === item.id ? 'person-selected' : ''}}"
      bindtap="selectPerson" data-index="{{index}}">

<!-- ✅ FIX — merge all attributes to one line -->
<view wx:for="{{people}}" wx:key="id" class="person-card {{selectedPersonId === item.id ? 'person-selected' : ''}}" bindtap="selectPerson" data-index="{{index}}">

<!-- Also broken: wx:for spread across multiple lines -->
<view
  wx:for="{{matchTypes}}"
  wx:key="id"
  class="match-type-tab {{matchType === item.id ? 'active' : ''}}"
  bindtap="selectMatchType"
  data-type="{{item.id}}">
```

**This bug affects ALL multi-line XML tags, not just those with `class` or `wx:for`.** A `<button>` or `<view>` with `bindtap` on a continuation line can also trigger it. The error character varies (seen: `'2'`, `'8'`) and has no relation to the actual file content.

**Fix: Merge all attributes onto a single line.** Use `sed` to find and fix multi-line tags:

```bash
# Find all multi-line tags (lines without > that are followed by continuation)
grep -n 'wx:for=' pages/*/*.wxml | while read line; do
  # Check if the next line is a continuation (no new tag opener)
done
```

**Note on ternaries in class:** The original diagnosis (multiple ternary blocks cause errors) was WRONG. After merging to single lines, both single-ternary (`class="base {{a?'x':''}}"`) and double-ternary (`class="base {{a?'x':''}} {{b?'y':''}}"`) patterns compile fine. Ternaries in `class` attributes are not the problem — multi-line tags are.

**Pre-computed class pattern** (still valid for complex logic, but not required to fix this error):
```javascript
// Optional optimization — pre-compute complex class logic in JS
_refreshClasses() {
  var people = this.data.people;
  for (var i = 0; i < people.length; i++) {
    var p = people[i];
    p._class = 'person-card' + (p.id === this.data.selectedPersonId ? ' person-selected' : '') + (p.recommend ? ' person-recommend' : '');
  }
  this.setData({ people: people });
},
```

**Files affected by this bug (fixed 2026-06-10):** `assess.wxml`, `photos.wxml`, `booking.wxml`, `matching.wxml`, `training-manage.wxml`, `payment.wxml` — 6 files, ~10 multi-line tags merged.

Full reproduction recipe: see `references/wxml-multiline-tag-pitfall.md`.

**Debugging methodology for "unexpected character" errors:**
1. The error character ('8', '2', etc.) is a compiler token code — do NOT search for it in the file
2. Look at the line BEFORE the error line — if it's an incomplete tag (no `>`), the error is a multi-line tag bug
3. Merge all attributes to one line and recompile — if the error moves or disappears, it confirms the diagnosis
4. Do NOT chase red herrings: ternary syntax, invisible characters, BOM markers — those are almost never the cause

### DevTools File Caching — Restart Required After Disk Edits

**Critical pitfall:** WeChat DevTools aggressively caches WXML/JS/WXSS files in memory. After editing files on disk (via `sed`, `patch`, or any external tool), DevTools continues showing the OLD file content in error messages. Hot reload (`⌘S`) and recompile do NOT clear this cache.

**Symptoms of cache poisoning:**
- Error message shows file content that doesn't match what's on disk
- `sed`/`patch` verified the file is correct, but DevTools shows different content
- The error line numbers and content don't update after disk edits

**Fix: Full DevTools restart**
1. Close the WeChat DevTools application completely (⌘Q)
2. Reopen the project from Finder or CLI
3. Verify the error now reflects actual file content

**Sub-agent warning:** If sub-agents (via `delegate_task`) modify the same file during debugging, the file content can silently change between reads. Always re-read files after sub-agent activity to confirm current state before patching.

### Verifying File Content (When DevTools Disagrees)

```bash
# NEVER trust DevTools error display alone — verify disk content with:
python3 -c "
with open('miniprogram/pages/X/X.wxml', 'rb') as f:
    data = f.read()
lines = data.split(b'\n')
for i in range(79, 86):
    print(f'Line {i+1}: {lines[i][:100]}')
"

# Check for prefix corruption (line numbers embedded in content):
grep -c '^ *[0-9][0-9]*|' pages/X/X.wxml  # should return 0

# Check for BOM:
xxd pages/X/X.wxml | head -3  # should start with <!-- or <view, not EF BB BF
```

### 6. tabBar `iconPath` cannot be empty — error 800059

Error `800059: iconPath=, file not found` means one or more tabBar items have `"iconPath": ""`. WeChat requires real PNG files (40KB limit, 81x81 recommended).

**Fix:** Create minimal PNG files and wire them into `app.json`:

```json
{
  "tabBar": {
    "list": [
      {"pagePath": "pages/home/home", "text": "首页",
       "iconPath": "images/tabbar/home.png",
       "selectedIconPath": "images/tabbar/home-active.png"}
    ]
  }
}
```

Generate solid-color placeholder PNGs via Python if no designer icons are available:

```python
# Generate 48x48 solid-color PNG
import struct, zlib
def make_png(hex_color, path):
    r,g,b = int(hex_color[0:2],16), int(hex_color[2:4],16), int(hex_color[4:6],16)
    w,h = 48,48
    raw = b''.join(b'\x00' + bytes([r,g,b,255])*w for _ in range(h))
    ihdr = struct.pack('>IIBBBBB', w, h, 8, 6, 0, 0, 0)
    def chunk(t,d):
        c = t+d; return struct.pack('>I',len(d))+c+struct.pack('>I',zlib.crc32(c)&0xffffffff)
    png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR',ihdr) + chunk(b'IDAT',zlib.compress(raw)) + chunk(b'IEND',b'')
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,'wb') as f: f.write(png)
```

---

## Common Failure Modes

### 1. Phone can't click login / API calls fail

**Root cause:** `apiBase` is `127.0.0.1` (phone's own loopback, can't reach Mac).
**Fix:** Change to Mac's LAN IP (e.g., `192.168.0.103:8000`).
**Verify:** `curl http://192.168.X.X:8000/` from Mac gives 200.

### 2. Preview compiles OK but phone shows blank

**Root cause:** Could be `enhance: true` in project.config.json (babel transpilation error), missing page declarations in app.json, or JS syntax error not caught during preview.

**Fix:**
- Set `"enhance": false` and `"libVersion": "2.33.0"` in project.config.json
- Ensure ALL page paths are in `app.json` → `pages` array
- Check DevTools console logs for runtime errors

### 3. Survey multi-select not working

**Root cause (common):** Template uses `pickSingle` for all questions instead of `toggleMulti` for multi=true items.

**Check:**
- Backend returns `"multi": true` for the question in `/api/survey/questions`
- WXML uses `wx:if="{{q.multi}}"` branch (toggleMulti) vs `wx:else` branch (pickSingle)
- submit() validation checks `Array.isArray(v) ? v.length : v` for multi questions

**Subtle bug — `data-multi` boolean serialization:**
In WeChat WXML, `data-multi="{{q.multi}}"` serializes `true` as the **string** `"true"`, not a boolean. This means:
- `wx:if="{{q.multi}}"` works fine in WXML (boolean context — WeChat treats truthy strings as true)
- But `e.currentTarget.dataset.multi` in JS will be `"true"` (string) not `true` (boolean)
- So `if (multi === true)` fails silently — the handler does nothing
- `if (multi)` (truthy check) DOES work with strings, but is fragile

**BEST fix — separate branches with wx:if/wx:else (no dataset magic):**

Don't use a unified `onSelect` handler with `data-multi` at all. Instead, use WXML `wx:if="q.multi"` to render different `bindtap` targets directly:

```wxml
<block wx:for="{{q.options}}" wx:for-item="opt" wx:key="*this">
  <!-- 多选: directly bind to toggleMulti -->
  <view wx:if="{{q.multi}}" bindtap="toggleMulti" data-qid="{{q.id}}" data-opt="{{opt}}"
        class="option {{_isSel(answers[q.id],opt) ? 'option-selected' : ''}}">
    <view class="checkbox {{_isSel(answers[q.id],opt) ? 'checkbox-checked' : ''}}">
      <text wx:if="{{_isSel(answers[q.id],opt)}}">✓</text>
    </view>
    <view class="option-text">{{opt}}</view>
  </view>
  <!-- 单选: directly bind to pickSingle -->
  <view wx:else bindtap="pickSingle" data-qid="{{q.id}}" data-opt="{{opt}}"
        class="option {{answers[q.id]===opt ? 'option-selected' : ''}}">
    <view class="option-text">{{opt}}</view>
  </view>
</block>
```

This avoids the `data-multi` serialization problem entirely because:
- The WXML `wx:if="{{q.multi}}"` evaluates `multi` in boolean context (correct)
- Each branch hardcodes the correct handler name (no runtime routing)
- The `wx:else` branch never receives multi-select data, so no ambiguity

**Fallback — unified handler with dual-type check (use only if you MUST unify):**
```javascript
onSelect(e) {
    const { qid, opt, multi } = e.currentTarget.dataset;
    // multi arrives as string "true"/"false" in dataset
    if (multi === true || multi === 'true') {
      this._toggleMulti(qid, opt);
    } else {
      this._pickSingle(qid, opt);
    }
},
```

**Visual checkbox for multi-select:**
Always add a visual checkbox (☐/✓) to multi-select options so users immediately recognize they can pick multiple:

```wxml
<view bindtap="onSelect" data-qid="{{q.id}}" data-opt="{{opt}}" data-multi="{{q.multi}}"
      class="option {{isChecked(answers,q.id,opt) ? 'option-selected' : ''}}">
  <view wx:if="{{q.multi}}" class="checkbox {{isChecked(answers,q.id,opt) ? 'checkbox-checked' : ''}}">
    <text wx:if="{{isChecked(answers,q.id,opt)}}">✓</text>
  </view>
  <view class="option-text">{{opt}}</view>
</view>
```
```css
.checkbox { width:36rpx; height:36rpx; border-radius:8rpx; border:2rpx solid rgba(255,255,255,.3); margin-right:16rpx; display:flex; align-items:center; justify-content:center; }
.checkbox-checked { background:#3b82f6; border-color:#3b82f6; }
```

### 4. Preview compiles OK but DevTools simulator shows blank / appLaunch timeout

**Error in logs:** `routeTo appLaunch timeout`

**Root cause:** The DevTools simulator runs inside the Mac's sandboxed environment. If `apiBase` is set to the Mac's LAN IP (e.g. `192.168.0.103:8000`), the simulator's networking stack may not be able to resolve or connect to it, causing the mini-program to hang during initialization (the login/survey/home page can't fetch its initial data).

**Fix:** Set `apiBase` to `127.0.0.1:8000` while testing in DevTools. Only use the LAN IP for phone preview QR codes.

**Note:** This error can also occur if the backend is down or if there's a genuine code error during app startup. Check:
- Is the backend running? `curl http://127.0.0.1:8000/`
- Does `cli preview` compile without errors?
- Check WeappLog logs under `~/Library/Application Support/微信开发者工具/*/WeappLog/` for the actual error

### 5. Backend returns old data after edit

**Root cause:** Backend process still running with old code. Need full restart.

**Fix:**
```bash
kill $(lsof -ti:8000)
sleep 2
./venv/bin/python3 -m uvicorn app:app --host 0.0.0.0 --port 8000
```

### 5b. Backend 500 only with gzip (Accept-Encoding)

**Symptom:** `POST http://127.0.0.1:8000/api/... 500` but `curl` without gzip headers returns 200.

**Root cause:** FastAPI middleware with `gzip.compress()` on Starlette `response.body` — the body can be `memoryview` (not `bytes`), causing an unhandled exception.

**Fix:** Wrap gzip in try/except with `isinstance(body, memoryview)` check, or disable middleware gzip entirely.
**Full details:** `references/backend-pitfalls.md`

### 6. Videos won't play / user says "I can't click the link"

**Root cause:** The `MEDIA:` syntax in agent responses is unreliable on WeChat. Users may see the text but not be able to tap/click it.

**Fix (from most reliable to least):**
1. **HTTP link** from backend static server (user must be on same WiFi): `http://192.168.X.X:8000/training_animations/video.mp4`
2. **send_message** with `MEDIA:` in the body to the user's WeChat DM
3. **Avoid GIF** — WeChat doesn't play GIFs inline. Always use MP4.
4. If all fails, restart the backend and ensure it's on `0.0.0.0`

### Survey Question Patterns (for Luke's projects)

Based on user preference feedback:

### CRITICAL: WXML 函数调用不重渲染的根因 — THE `selMap` PATTERN

This is the single most important WeChat mini-program frontend technique for any project with selectable options. It applies to: surveys, tier selectors, skill pickers, shopping cart, tag filters, etc.

**问题现象：** 用户点击多选题选项后，UI 没有任何变化（checkbox 不变色、✓ 不出现），感觉像"被屏蔽层挡住了"。但 JS 日志显示 `setData` 确实被执行且数据已更新。

**根因：** 微信 WXML 中的**函数调用（如 `{{_isSel(answers[q.id],opt)}}`）只在组件首次渲染时执行一次求值，后续 `setData` 更新数据后不会重新调用函数**。这与 Vue/React 的响应式系统完全不同——WXML 不是响应式模板引擎，它的数据绑定是基于 `setData` 推送的扁平数据快照，而非计算的 getter。

**错误模式（不工作）：**
```wxml
<!-- WXML: 函数调用只在初始化时执行一次 -->
<view class="option {{_isSel(answers[q.id],opt) ? 'option-selected' : ''}}" bindtap="toggleMulti">
  <view class="checkbox {{_isSel(answers[q.id],opt) ? 'checkbox-checked' : ''}}">
    <text wx:if="{{_isSel(answers[q.id],opt)}}">✓</text>
  </view>
</view>
```

```javascript
// JS: setData 更新 answers，但 WXML 不会重调用 _isSel()
// 即使 answers 正确更新了，界面也毫无变化！
toggleMulti(e) {
  const { qid, opt } = e.currentTarget.dataset;
  let cur = [...(this.data.answers[qid] || [])];
  const idx = cur.indexOf(opt);
  if (idx >= 0) { cur.splice(idx, 1); } else { cur.push(opt); }
  this.setData({ [`answers.${qid}`]: cur });
},

// WXML 调用的这个函数只执行一次，后续永不重算
_isSel(val, opt) {
  if (Array.isArray(val)) return val.indexOf(opt) >= 0;
  return val === opt;
},
```

**正确方案（用 `selMap` 扁平映射替代函数调用）：**

核心思想：**WXML 的 `setData` 只重新渲染那些直接被 `setData` 修改了的路径**。所以不能用函数求值，必须用直接的键值对映射。

```javascript
// survey.js
Page({
  data: {
    questions: [],
    selMap: {},  // "qid_idx": true/false — 扁平映射，setData 后直接触发重渲染
    loading: false,
    err: ''
  },

  async onLoad() {
    const r = await request({ url: '/api/survey/questions' });
    // 将纯字符串选项转为 { text, _key } 对象
    const questions = (r.questions || []).map(q => ({
      ...q,
      options: (q.options || []).map((opt, oi) => {
        const text = typeof opt === 'string' ? opt : opt.text || opt;
        return { text, _key: q.id + '_' + oi };  // e.g. "pain_2"
      })
    }));
    this.setData({ questions });
  },

  // 单选
  pickSingle(e) {
    const { key, opt } = e.currentTarget.dataset;
    const qid = key.split('_')[0];
    const prefix = qid + '_';
    const newMap = {};
    // 清空本题目所有选项
    for (const k in this.data.selMap) {
      if (k.startsWith(prefix)) newMap[k] = false;
    }
    newMap[key] = true;
    this.setData({ selMap: { ...this.data.selMap, ...newMap } });
  },

  // 多选（含互斥逻辑）
  toggleMulti(e) {
    const { key, opt } = e.currentTarget.dataset;
    const qid = key.split('_')[0];
    const curVal = this.data.selMap[key] || false;
    let newMap = {};

    if (opt === '没有') {
      // 选"没有"→清其他所有
      const prefix = qid + '_';
      for (const k in this.data.selMap) {
        if (k.startsWith(prefix)) newMap[k] = false;
      }
      newMap[key] = !curVal;
    } else {
      // 选具体选项→确保"没有"被取消
      const noKey = qid + '_' + this._findNoIndex(qid);
      newMap[noKey] = false;
      newMap[key] = !curVal;
    }

    this.setData({ selMap: { ...this.data.selMap, ...newMap } });
  },
});
```

```wxml
<!-- WXML: 改用 selMap 直接键值绑定，setData 后立即重渲染 -->
<block wx:for="{{q.options}}" wx:for-item="opt" wx:for-index="oi" wx:key="_key">
  <!-- 多选 -->
  <view wx:if="{{q.multi}}" bindtap="toggleMulti" data-key="{{opt._key}}" data-opt="{{opt.text}}"
        class="option {{selMap[opt._key] ? 'option-selected' : ''}}">
    <view class="checkbox {{selMap[opt._key] ? 'checkbox-checked' : ''}}">
      <text wx:if="{{selMap[opt._key]}}">✓</text>
    </view>
    <view class="option-text">{{opt.text}}</view>
  </view>
  <!-- 单选 -->
  <view wx:else bindtap="pickSingle" data-key="{{opt._key}}" data-opt="{{opt.text}}"
        class="option {{selMap[opt._key] ? 'option-selected' : ''}}">
    <view class="option-text">{{opt.text}}</view>
  </view>
</block>
```

**提交时从 selMap 重建 answers：**
```javascript
async submit() {
  const answers = {};
  for (const q of this.data.questions) {
    const vals = [];
    const prefix = q.id + '_';
    for (const k in this.data.selMap) {
      if (k.startsWith(prefix) && this.data.selMap[k]) {
        const oi = parseInt(k.split('_').pop(), 10);
        vals.push(q.options[oi].text);
      }
    }
    answers[q.id] = q.multi ? vals : (vals.length ? vals[0] : null);
  }

  // 校验
  const need = this.data.questions.filter(q => {
    const v = answers[q.id];
    return q.multi ? (!v || !v.length) : (v === undefined || v === null);
  });
  if (need.length) return this.setData({ err: `还有 ${need.length} 题未答` });

  // ... 提交
}
```

**要点总结：**
- **永远不要在 WXML 中使用函数调用做条件渲染** — 函数只在初始化时执行一次
- 用 `selMap[key]` 扁平对象替代，键为 `qid_idx`，值为 `true/false`
- 每次 `setData` 传递整个 `selMap` 的更新切片（`...this.data.selMap, ...newMap`）
- `wx:key="_key"` 确保微信能正确 diff 数组元素
- 这种方案同时解决了单选、多选、互斥逻辑三种场景

### Multi-Select Rules
- Questions that logically allow multiple answers MUST use `multi: true` and the `toggleMulti` handler
- **Injury/body-part questions:** "没有" should be mutually exclusive with specific answers. If user taps "没有", clear all selected body parts. If user taps a body part while "没有" is selected, clear "没有" first.

### Wording Rules
- Replace "AI" with "我" when the question asks from the app's perspective
  - `"最想 AI 帮你解决什么？"` → `"最想我帮你解决什么？"`
  - `"帮 AI 给你更准的建议"` → `"帮你获得更准的建议"`
  - `"愿意为 AI 教练付费"` → `"愿意为羽球宝付费"`
- Add `（多选）` tag in the question text when `multi: true`

### Example Survey Structure

```python
SURVEY_QUESTIONS = [
    {"id": "level", "q": "你目前自评的羽毛球水平？", "multi": False,
     "options": [...]},
    {"id": "freq", "q": "每周打球频率？", "multi": False,
     "options": [...]},
    {"id": "pain", "q": "最想我帮你解决什么？（多选）", "multi": True,
     "options": [...]},
    {"id": "injury", "q": "过去一年是否有运动伤痛？（多选）", "multi": True,
     "options": ["没有", "肩部", "肘部", "腕部", "腰部", "膝盖", "踝部", "其他"]},
    {"id": "pay", "q": "愿意为羽球宝付费的月预算？", "multi": False,
     "options": [...]},
]
```

### Frontend Multi-Select with Mutual Exclusion

```javascript
// In survey.js — toggleMulti handler with 没有/body-part mutual exclusion
toggleMulti(e) {
    const { qid, opt } = e.currentTarget.dataset;
    let cur = [...(this.data.answers[qid] || [])];
    const idx = cur.indexOf(opt);
    if (idx >= 0) {
      cur.splice(idx, 1);
    } else {
      if (opt === '没有') { cur = ['没有']; }
      else { cur = cur.filter(v => v !== '没有'); cur.push(opt); }
    }
    this.setData({ [`answers.${qid}`]: cur });
},
```

### Validation in submit()

```javascript
const need = this.data.questions.filter(q => {
    const v = this.data.answers[q.id];
    return q.multi ? !(v && v.length) : !v;
});
```

## UAT Checklist

- [ ] Backend running on `0.0.0.0:8000` (not `127.0.0.1`)
- [ ] `apiBase` in app.js uses Mac's LAN IP
- [ ] Phone and Mac on same Wi-Fi
- [ ] Preview QR generated and sent
- [ ] Login → Survey → Home → Assess → Result flow tested
- [ ] Survey multi-select works (multiple options selectable)
- [ ] "没有" auto-cancels other selections (or vice versa)
- [ ] All 5 survey questions render correctly
- [ ] /api/assess returns grades with test images
- [ ] /api/tiers/info returns 3 tiers with feature lists
- [ ] /api/payment/create returns order_id + amount
- [ ] /api/invite/code returns invite_code
- [ ] /api/certificate/generate returns cert_id
- [ ] DevTools compiles without errors (watch for start cli server error noise)
- [ ] User confirms all wording ("AI" → "我" etc.)

## Mini-Program API Integration Patterns

When migrating miniprogram pages from hardcoded mock data (or raw `wx.request` with hardcoded `Bearer test` tokens) to the project's proper API wrapper, use this mechanical checklist. This pattern was battle-tested across 5 pages (training, practice, compare, daily, mimic) in a single session.

### Prerequisites: Project API Wrapper

The project must have `miniprogram/utils/api.js` with:

```javascript
const app = getApp();

function request(opts) {
  return new Promise((resolve, reject) => {
    const header = opts.header || {};
    if (app.globalData.token) header.Authorization = 'Bearer ' + app.globalData.token;
    wx.request({
      url: app.globalData.apiBase + opts.url,
      method: opts.method || 'GET',
      data: opts.data,
      header,
      success(res) {
        if (res.statusCode === 401) { app.logout(); return reject(...); }
        if (res.statusCode >= 400) return reject(new Error(msg));
        resolve(res.data);
      },
      fail(err) { reject(new Error('网络错误: ' + err.errMsg)); }
    });
  });
}

function upload(filePath, url) {
  // similar — uses app.globalData.token + returns promise
}

module.exports = { request, upload };
```

### Page Migration Checklist

**Step 1: Add the import**

```javascript
// Before (mock pattern)
const app = getApp();
const API = 'http://127.0.0.1:8000';

// After (API pattern)
const app = getApp();
const { request, upload } = require('../../utils/api.js');
```

**Step 2: Replace `wx.request` calls**

```javascript
// ❌ Before — hardcoded API + manual auth
wx.request({
  url: API + '/api/training/categories',
  header: { 'authorization': 'Bearer test' },
  success: (res) => { if (res.data) ... },
  fail: () => { /* fallback */ },
});

// ✅ After — promise-based wrapper
request({ url: '/api/training/categories' })
  .then(data => { if (data && data.categories) ... })
  .catch(() => { /* fallback to built-in data */ });
```

**Step 3: Replace `wx.uploadFile` calls**

```javascript
// ❌ Before — raw wx.uploadFile
wx.uploadFile({
  url: `${apiBase}/api/compare?action_type=${actionType}`,
  filePath: videoPath,
  name: 'file',
  success: (res) => { ... JSON.parse(res.data) ... },
});

// ✅ After — upload wrapper returns parsed JSON
upload(videoPath, `/api/compare?action_type=${actionType}`)
  .then(data => this._processResult(data))
  .catch(e => { wx.showToast({ title: e.message, icon: 'error' }); });
```

**Step 4: Fix template URL references**

```wxml
<!-- ❌ Before — hardcoded API: in data -->
<video src="{{API}}{{demoVideo.url}}">

<!-- ✅ After — use globalData.apiBase from app.js -->
<video src="{{apiBase}}{{demoVideo.url}}">
```

```javascript
// JS data must include:
data: {
  apiBase: app.globalData.apiBase,  // for template interpolation
}
```

**Step 5: Remove duplicate / dead code**

ES5/ES6 merging often leaves duplicate method definitions (e.g., two `chooseVideo()`). The earlier one (with API calls) is the real one; remove the later one (the mock/simulate version). Always run `node --check` after merging to catch syntax errors.

### API Discovery Pattern

To find available endpoints for a feature without reading source code:

```bash
# List all relevant endpoints
curl -s http://127.0.0.1:8000/openapi.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
for p in sorted(d['paths']):
    if any(k in p.lower() for k in ['training','daily','progress']):
        print(p)
"
```

### API Gap Detection Pattern

When a miniprogram has many frontend pages but some API endpoints are missing, use this mechanical comparison:

```bash
# Extract all frontend API calls
grep -rohE "(apiBase|\+)\s*['\"](/api/[^'\"]+)" miniprogram/ | sort -u

# Extract all backend route definitions
grep -rohE '@app\.(get|post|put|delete)\("([^"]+)"' badminton_coach/ | sort -u

# Diff to find missing endpoints
diff <(grep -rohE "...frontend pattern..." miniprogram/ | sort -u) \
     <(grep -rohE "...backend pattern..." badminton_coach/ | sort -u)
```

This pattern caught 3 missing endpoints (ranking, certificate, payment callback) that had frontend code calling them but no backend implementation.
# Inspect endpoint schema
curl -s http://127.0.0.1:8000/openapi.json | python3 -c "
import json,sys
d=json.load(sys.stdin)
print(json.dumps(d['paths']['/api/training/v2/skill-breakdown/{skill_id}'], indent=2, ensure_ascii=False)[:600])
"
```

### Backend-First Validation Order

Before touching frontend code, verify backend endpoints actually return useful data:

```bash
# 1. Start the backend (kill old process first)
kill $(lsof -ti:8000) 2>/dev/null
sleep 1
cd ~/Desktop/2026AIAPP/workspace/<project>
./venv/bin/python3 -m uvicorn <module>:app --host 0.0.0.0 --port 8000 &

# 2. Verify DB tables init cleanly
./venv/bin/python3 -c "
from module.training_tracker import init_tables; init_tables()
print('✅ DB OK')
"

# 3. Hit each endpoint and check structure
for ep in /api/training/categories /api/training/v2/skill-breakdown/clear_fh?level=1 /api/compare/benchmarks; do
  echo "=== $ep ==="
  curl -s "http://127.0.0.1:8000$ep" | python3 -m json.tool | head -20
  echo
done
```

### Promise Chain Consistency

All frontend API calls should use the same `.then(data => ...).catch(() => {})` pattern. Never mix `success`/`fail` callbacks with promise chains in the same file — it confuses the compiler and causes silent failures. After migration, verify no `wx.request(` or `wx.uploadFile(` calls remain in the file:

```bash
grep -n 'wx\.request\|wx\.uploadFile' miniprogram/pages/*/target.js
# Should return nothing
```

### Post-Migration Syntax Check

```bash
for f in miniprogram/pages/*/target.js; do
  node --check "$f" && echo "✅ $f" || echo "❌ $f"
done
```

## Pitfalls "start cli server error: [object Object]" in DevTools logs is a benign noise — doesn't affect compilation or preview
- **QR code expires fast:** Regenerate if user takes more than 2-3 minutes to scan
- **DevTools not running:** `lsof -ti:8000` showing backend is up doesn't mean DevTools is up. Check with `ps aux | grep wechatdevtools` or `cli islogin`. If DevTools process isn't running, start it with `cli open --project <path>`.
- **CLI preview/auto-preview broken (code 10):** `cli preview` and `cli auto-preview` both return `code 10: Error: 错误 undefined (code 10)` regardless of correct arguments. This is a WeChat DevTools bug — the CLI connects to a hardcoded port while the IDE server listens on a random one. Fix: use AppleScript to click "工具 → 预览" in the GUI (see AppleScript Preview section above).
- **WeChat DevTools login drift:** If `cli islogin` returns false, re-login via `cli login` (requires user to approve on phone)
- **HTTPS requirement for production:** HTTP works for local/dev testing but production needs HTTPS + ICP备案 + domain whitelist in WeChat console
- **Preview size limit:** Small preview packages (~67-70KB) compile fine; watch for template syntax errors if it grows
- **numpy 2.x conflict on macOS:** If backend uses MediaPipe and fails with ImportError, ensure you're running with `./venv/bin/python3` directly, not `source venv/bin/activate` (which may pull in Anaconda's numpy 2.x)
- **uvicorn `--reload` OOM on memory-constrained systems:** `--reload` runs a second watcher process that doubles memory consumption. On systems with limited RAM or large import graphs (MediaPipe + OpenCV + FastAPI), this can cause exit code 137 (SIGKILL / OOM kill). Drop `--reload` and use `--workers 1` for long-running background processes. Restart manually after code changes instead.

## Reference Files

- `references/tier-system-api.md` — Full API reference for Luke's 羽球宝AI搭子 three-tier system (payment, invite, certificates, photos)
- `references/badminton-coach-api-endpoints.md` — Complete API reference for training, tracking, compare, avatar, massage, and game endpoints discovered during P0.5 migration
- `references/wxml-multiline-tag-pitfall.md` — Deep-dive on WXML multi-line tag error diagnosis, DevTools caching, and fix methodology
- `references/backend-pitfalls.md` — FastAPI gzip middleware 500 (memoryview), UAT state contamination, SQL subquery parent-record pattern
