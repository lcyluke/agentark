# JS Template String Debugging

## Problem

Page HTML loads but JavaScript is dead silent — no `state`, no functions, no events. 
Root cause: a single unclosed template literal `` ` `` anywhere in the JS block breaks all subsequent JavaScript.

## Symptom

```javascript
// Browser console
typeof state              // "undefined"
typeof renderDashboard    // "undefined"
// All JS functions are missing
```

## Diagnosis

Count backticks in the served HTML's `<script>` block:

```python
import urllib.request

url = 'http://localhost:8080/cc'
with urllib.request.urlopen(url) as f:
    content = f.read().decode('utf-8')

js_start = content.find('<script>')
js_end = content.rfind('</script>')
js = content[js_start+8:js_end]

bt = js.count('`')
print(f"Backticks: {bt} → {'EVEN ✅' if bt%2==0 else 'ODD ❌'}")
```

## Locate

Track running parity line-by-line to find the first transition from even to odd:

```python
lines = content.split('\n')
running = 0
for i, line in enumerate(lines):
    cnt = line.count('`')
    running += cnt
    if running % 2 == 1:  # Odd = inside an unclosed template
        # Check context around this line
        context = '\n'.join(lines[max(0,i-2):min(len(lines),i+3)])
        # The unclosed template likely started within 5-10 lines before this
```

## Common Causes

1. **Backend agent added code** — When delegating to a subagent, they may add GPU/API/fleet code with unclosed template strings.
2. **Copy-paste from design file** — AgentCorp-OS.html has templates that may not transfer cleanly.
3. **Escaped backticks in onClick** — `onclick='...'` inside template literals need careful escaping.

## Fix

Find the line where the unclosed template starts and add the closing `` ` ``:

```javascript
// Before (broken):
ctrlHTML += `<button class="btn warn" onclick="requestGPUShutdown()"><i class="ti ti-power"></i>请求关机</button>

// After (fixed):
ctrlHTML += `<button class="btn warn" onclick="requestGPUShutdown()"><i class="ti ti-power"></i>请求关机</button>`;
```

The fix is always at the last running-to-odd transition point — the template that opened but never closed.
