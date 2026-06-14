# Dashboard Performance Debugging Recipe

Recipe from 2026-06-07 session: Dashboard "连接中..." → 6s API + JS dead.

## Symptoms
- Dashboard shows "连接中..." forever
- `typeof state === 'undefined'` in browser console
- API responds in 6+ seconds

## Diagnosis Steps

### 1. Time each API endpoint
```bash
for ep in command-center hermes/status gpu/status live/projects; do
  time curl -s -o /dev/null -w "%{http_code} %{time_total}s\n" http://localhost:8080/api/$ep
done
```

### 2. Identify slow sub-function
Look at `get_command_center_data()` in `hermes_bridge.py`. Each sub-call is a candidate:
- Subprocess calls (`hermes cron list` / `hermes profile list`) → ~1s each
- SSH calls (`_check_instance_ssh`) → 5s timeout × N instances

### 3. Check for JS parse errors
```bash
curl -s http://localhost:8080/ | python3 -c "
import re, sys
html = sys.stdin.read()
m = re.search(r'<script>(.*?)</script>', html, re.DOTALL)
js = m.group(1)
open('/tmp/cc_check.js','w').write(js)
" && node --check /tmp/cc_check.js
```
If node reports SyntaxError → template literal escaping issue.

### 4. Check Flask template caching
If disk file is correct but browser shows old version:
```bash
# Compare disk vs served
diff <(grep "const API" apex/interface/templates/command_center.html) \
     <(curl -s http://localhost:8080/ | grep "const API")
```
No output = template is fresh. Output = cached.

## Fix Patterns

### Fix A: Parallelize slow calls
Replace sequential calls in `get_command_center_data()` with `ThreadPoolExecutor`.
See main SKILL.md "性能优化模式" section.

### Fix B: Reduce SSH timeout
Change `ConnectTimeout=5` → `ConnectTimeout=2`, add `BatchMode=yes`.

### Fix C: Fix template literal escaping
The pattern `\"\\\\'\"` (bytes: `5c 22 5c 5c 5c 5c 27 5c 22`) in a template literal causes JS parse error. Must be `"\\'"` (bytes: `22 5c 5c 27 22`).

Use binary-mode Python to replace:
```python
with open(path, 'rb') as f:
    content = f.read()
broken = b'\\"\\\\\\\\\'\\"'
correct = b'"\\\\\'"'
content = content.replace(broken, correct)
with open(path, 'wb') as f:
    f.write(content)
```

### Fix D: Restart server (clears Flask template cache)
```bash
kill $(lsof -ti:8080)
sleep 1
cd apex && .venv/bin/python3 -c "from apex.interface.web import run_dashboard; run_dashboard()" &
```

## Verification After Fix
```bash
# 1. API speed
time curl -s -o /dev/null -w "%{time_total}s\n" http://localhost:8080/api/command-center
# Target: < 2s

# 2. JS valid
node --check /tmp/cc_check.js && echo "JS OK"

# 3. Browser check
# In console: typeof state !== 'undefined' && state.connected
# Should return true
```

## Actual Session Results (2026-06-07)
- API: 6.0s → 1.4s (77% improvement)
- JS: 4 syntax errors fixed (template literal escaping)
- Root causes: ThreadPoolExecutor + SSH timeout + Flask cache
