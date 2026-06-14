# WXML Multi-Line Tag Pitfall — Full Reproduction Recipe

## Symptom

WeChat DevTools compilation error (lib 2.33.0):
```
[ WXML 文件编译错误] ./pages/assess/assess.wxml
unexpected character `8`
  81 |     81|      <view class="person-list-inner">
  82 |     82|        <view wx:for="{{people}}" wx:key="id"
> 83 |     83|              class="person-card ..."
     |    ^
  84 |     84|              bindtap="selectPerson" data-index="{{index}}">
```

The error character (`'8'`, `'2'`, etc.) has NO relation to any character in the source file. It's an internal compiler token code.

## Root Cause (VERIFIED)

**Multi-line WXML tags.** When an opening tag like `<view wx:for="..." wx:key="id"` ends a line without `>`, the WXML compiler in lib 2.33.0 misparses the continuation line. The first character of the next line's attribute triggers a spurious "unexpected character" error.

This is a **compiler bug**, not a syntax error in the WXML source. The same WXML compiles fine when all attributes are on a single line.

## Correct Fix

**Merge all attributes onto a single line:**

```wxml
<!-- ❌ BROKEN — attributes on continuation lines -->
<view wx:for="{{people}}" wx:key="id"
      class="person-card {{selectedPersonId === item.id ? 'person-selected' : ''}}"
      bindtap="selectPerson" data-index="{{index}}">

<!-- ✅ FIXED — all attributes on one line -->
<view wx:for="{{people}}" wx:key="id" class="person-card {{selectedPersonId === item.id ? 'person-selected' : ''}}" bindtap="selectPerson" data-index="{{index}}">
```

**Also broken — `wx:for` spread across multiple lines:**
```wxml
<!-- ❌ BROKEN -->
<view 
  wx:for="{{matchTypes}}" 
  wx:key="id" 
  class="match-type-tab {{matchType === item.id ? 'active' : ''}}"
  bindtap="selectMatchType" 
  data-type="{{item.id}}">

<!-- ✅ FIXED -->
<view wx:for="{{matchTypes}}" wx:key="id" class="match-type-tab {{matchType === item.id ? 'active' : ''}}" bindtap="selectMatchType" data-type="{{item.id}}">
```

## Affected Patterns (ALL multi-line tag variants)

| Pattern | Fails? |
|:--------|:------:|
| `<view wx:for="..." wx:key="id"\n      class="...">` | ❌ |
| `<view \n  wx:for="..." \n  wx:key="id" \n  class="...">` | ❌ |
| `<view class="x"\n      bindtap="y">` | ❌ |
| `<button class="x"\n        disabled="{{y}}">` | ❌ |
| Single-ternary `class="{{a?'x':'y'}}"` on one line | ✅ |
| Double-ternary `class="base {{a?'x':''}} {{b?'y':''}}"` on one line | ✅ |
| Nested ternary `class="{{a>=1?'done':a==0?'active':''}}"` on one line | ✅ |

## Misdiagnosis History

### Hypothesis 1: Multiple ternary blocks (❌ WRONG)
The initial diagnosis attributed the error to multiple `{{...?...:...}}` blocks in class attributes. After testing: single, double, and nested ternaries ALL compile fine when on a single line. This hypothesis came from the fact that multi-line tags often contain ternaries in their class attributes — correlation, not causation.

### Hypothesis 2: Line number prefix corruption (❌ WRONG)
When `xxd` showed bytes like `38 32 7c` ("82|") in the file, it looked like line number prefixes were embedded. This was a diagnostic artifact — the DevTools error display format (`83 |     83|`) coincidentally looks like embedded line numbers. The actual file had no prefixes.

### Hypothesis 3: BOM / invisible characters (❌ WRONG)
Checked with `xxd`, `od -c`, and Python binary reads. No BOM, no zero-width characters, no encoding issues.

### Hypothesis 4: Multi-line tags (✅ CORRECT)
The ONLY fix that resolved the error was merging attributes to single lines. Confirmed by: error disappeared after merge, unaffected files compiled fine.

## DevTools Caching — Full Restart Required

**Critical:** WeChat DevTools caches WXML files in memory. After editing files on disk, DevTools continues showing OLD content in error messages. Hot reload and recompile do NOT clear this cache.

**Fix:** Close DevTools completely (⌘Q) and reopen the project.

**Symptoms of cache poisoning:**
- Error shows file content that doesn't match what's on disk
- `sed`/`cat` verify file is correct, but DevTools shows different content
- Same error persists after multiple disk edits
- Error message filenames are correct but content is stale (e.g., shows old 3-line tag after merge to 1 line)

**Important:** Even `kill` + restart of the IDE process may not clear the in-memory file cache on all DevTools versions. A full ⌘Q + manual reopen from Finder is most reliable.

## Verification Commands (When DevTools Disagrees)

```bash
# Verify actual file content (binary-safe, no tool artifacts)
python3 -c "
with open('miniprogram/pages/X/X.wxml', 'rb') as f:
    data = f.read()
lines = data.split(b'\n')
for i in range(79, 86):
    print(f'Line {i+1}: {lines[i][:100]}')
"

# Check for line number prefix corruption (should output 0)
grep -c '^ *[0-9][0-9]*|' pages/X/X.wxml

# Check for BOM at file start
xxd pages/X/X.wxml | head -1  # First bytes should be '<' or '/', not 'EF BB BF'
```

## Detection Script

```bash
# Find all multi-line tags in WXML files
cd miniprogram
for f in pages/*/*.wxml; do
  awk '!/>$/{if(NR==prev+1 && prev_line!~/>$/){
    print FILENAME":" prev ":" prev_line;
    print FILENAME":" NR ":" $0; print ""
  }} {prev=NR; prev_line=$0}' "$f"
done
```

## Files Fixed (2026-06-10 Session)

| File | Multi-line tags merged |
|:-----|:---------------------:|
| `assess.wxml` | 3 (2× person cards, 1× detectedActions) |
| `photos.wxml` | 1 |
| `booking.wxml` | 1 |
| `matching.wxml` | 1 |
| `training-manage.wxml` | 3 |
| `payment.wxml` | 1 |

## Pre-computed Class Pattern (Still Useful, But Not Required)

Pre-computing complex class logic in JS is good practice for readability and avoiding deep nesting in templates. It's a valid pattern but is NOT required to fix the multi-line tag error.

```javascript
_refreshPeopleClasses() {
  var people = this.data.people;
  var selId = this.data.selectedPersonId;
  for (var i = 0; i < people.length; i++) {
    var p = people[i];
    var cls = 'person-card';
    if (p.id === selId) cls += ' person-selected';
    if (p.recommend) cls += ' person-recommend';
    p._class = cls;
  }
  this.setData({ people: people });
},
```
