# Security MCP Status Panel — Dashboard Integration Pattern

How to add an MCP server status panel to the Apex Command Center system view.
Implemented for Semgrep MCP, reusable for any future MCP server (GitHub, filesystem, etc.).

## Architecture

```
Backend (web.py):       /api/security/mcp-status → inline function in create_app()
Frontend (HTML):        <div id="mcpStatus"> in v-system section
Frontend (JS):          renderMcpStatus() → fetch → render 4 cards + tools grid
```

## Phase 1: Backend API Endpoint

Add to `web.py` inside `create_app()`. For simple status checks, use an inline function
(rather than a separate manager file) to keep the check self-contained.

```python
@app.route("/api/security/mcp-status")
def api_security_mcp_status():
    """Security scanning MCP status — CLI + server + config + tools"""
    import shutil, json as _json, os as _os
    import subprocess as sp
    result = {"ok": True}

    # 1. Tool CLI check
    tool_path = shutil.which("tool-name")
    result["tool"] = {
        "installed": tool_path is not None,
        "path": tool_path or None,
        "version": None,
    }
    if tool_path:
        try:
            r = sp.run([tool_path, "--version"], capture_output=True, text=True, timeout=10)
            result["tool"]["version"] = r.stdout.strip().split("\n")[0]
        except:
            result["tool"]["version"] = "error"

    # 2. MCP Server check (npm global)
    npm_global = "/opt/homebrew/lib/node_modules"
    mcp_path = _os.path.join(npm_global, "mcp-server-xxx", "build", "index.js")
    result["mcp_server"] = {
        "installed": _os.path.exists(mcp_path),
        "path": mcp_path if _os.path.exists(mcp_path) else None,
        "version": read_package_json(npm_global, "mcp-server-xxx"),
    }

    # 3. Config status — parse config.yaml
    result["config"] = {"configured": False}
    try:
        import yaml
        with open(_os.path.expanduser("~/.hermes/config.yaml")) as f:
            cfg = yaml.safe_load(f)
        mcp = cfg.get("mcp_servers", {}).get("server_name", {})
        if mcp:
            result["config"]["configured"] = True
            result["config"]["allowed_roots"] = mcp.get("env", {}).get("ALLOWED_ROOTS_KEY")
    except:
        pass

    # 4. Available tools (static list from package docs)
    result["tools"] = [
        {"name": "tool_a", "desc": "Description A"},
        {"name": "tool_b", "desc": "Description B"},
    ]

    return jsonify(result)
```

### Key points
- Import `subprocess`, `shutil`, `json`, `os` inside the function (Flask closure pattern)
- Return `{"ok": True, ...}` — consistent with other Apex API conventions
- Config.yaml is read-only here (parsed via yaml.safe_load), never written

## Phase 2: Frontend HTML

Insert into the existing `v-system` section in `command_center.html` — do NOT create a new view:

```html
<div style="height:22px"></div>
<div class="sec-h"><i class="ti ti-shield-check"></i>安全扫描 MCP 状态</div>
<div id="mcpStatus"></div>
```

Use `ti ti-shield-check` icon for security tools. The placeholder `<div id="mcpStatus">`
is populated by the JS function.

## Phase 3: Frontend JS

### Wiring — call from renderSystem()

```javascript
async function renderSystem() {
  // ... existing code ...

  // MCP security status
  renderMcpStatus();
}
```

### Render function — use string concatenation, NOT template literals

```javascript
async function renderMcpStatus() {
  var container = $('#mcpStatus');
  if (!container) return;

  // Loading state
  container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--tx3)">' +
    '<i class="ti ti-loader" style="animation:spin 1s linear infinite;font-size:20px"></i>' +
    '<div style="margin-top:6px;font-size:12px">加载 MCP 状态...</div></div>';

  var data = await fetchJSON(API + '/security/mcp-status');
  if (!data) {
    container.innerHTML = '<div class="card"><div style="text-align:center;padding:20px;color:var(--red)">' +
      '<i class="ti ti-alert-circle" style="font-size:24px"></i>' +
      '<div style="margin-top:6px">无法获取 MCP 状态</div></div></div>';
    return;
  }

  var rows = [];

  // Card 1: CLI status
  var cli = data.tool || {};
  rows.push('<div class="card" style="margin-bottom:12px">' +
    '<div class="sec-h" style="margin-bottom:10px"><i class="ti ti-code"></i>Tool CLI</div>' +
    '<div class="kv"><span class="k">状态</span><span class="vv">' +
    '<span class="tag ' + (cli.installed ? 'green' : 'red') + '">' +
    (cli.installed ? (cli.version || '已安装') : '未安装') + '</span></span></div>' +
    (cli.path ? '<div class="kv"><span class="k">路径</span><span class="vv" style="font-size:11px">' + cli.path + '</span></div>' : '') +
    '</div>');

  // Card 2: MCP Server
  var mcp = data.mcp_server || {};
  rows.push('<div class="card" style="margin-bottom:12px">' +
    '<div class="sec-h" style="margin-bottom:10px"><i class="ti ti-plug-connected"></i>MCP Server (npm)</div>' +
    '<div class="kv"><span class="k">状态</span><span class="vv">' +
    '<span class="tag ' + (mcp.installed ? 'green' : 'red') + '">' +
    (mcp.installed ? 'v' + (mcp.version || '?') : '未安装') + '</span></span></div>' +
    '</div>');

  // Card 3: Config status
  var cfg = data.config || {};
  rows.push('<div class="card" style="margin-bottom:12px">' +
    '<div class="sec-h" style="margin-bottom:10px"><i class="ti ti-settings"></i>Hermes Config</div>' +
    '<div class="kv"><span class="k">mcp_servers</span><span class="vv">' +
    '<span class="tag ' + (cfg.configured ? 'green' : 'amber') + '">' +
    (cfg.configured ? '已配置' : '未配置') + '</span></span></div>' +
    '</div>');

  // Card 4: Tools grid
  var tools = data.tools || [];
  if (tools.length > 0) {
    var toolCards = tools.map(function(t) {
      return '<div style="background:var(--bg4);padding:8px 11px;border-radius:var(--r-s);border:1px solid var(--line2)">' +
        '<div style="font-family:var(--mono);font-size:11px;color:var(--teal);margin-bottom:2px">mcp_server_' + t.name + '</div>' +
        '<div style="font-size:12px;color:var(--tx3)">' + t.desc + '</div></div>';
    }).join('');

    rows.push('<div class="card">' +
      '<div class="sec-h" style="margin-bottom:10px"><i class="ti ti-tool"></i>可用 MCP 工具 (' + tools.length + ')</div>' +
      '<div class="grid" style="grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:8px">' +
      toolCards + '</div></div>');
  }

  container.innerHTML = rows.join('');
}
```

### Design tokens used
- `.card` — standard card container
- `.sec-h` — section header with icon
- `.kv` / `.k` / `.vv` — key-value row
- `.tag.green` / `.tag.red` / `.tag.amber` — status badges
- `.grid` — responsive grid layout
- `--bg4` / `--line2` / `--teal` / `--tx3` — color variables

## Verification

```bash
# 1. Test API endpoint
curl -s http://localhost:8080/api/security/mcp-status | python3 -m json.tool

# 2. Verify JS syntax
curl -s http://localhost:8080/ -o /tmp/cc.html
python3 -c "
import re,subprocess
html=open('/tmp/cc.html').read()
scripts=re.findall(r'<script>(.*?)</script>',html,re.DOTALL)
for i,js in enumerate(scripts):
    open(f'/tmp/js_{i}.js','w').write(js)
    r=subprocess.run(['node','--check',f'/tmp/js_{i}.js'],capture_output=True,text=True)
    print(f'Script {i}:', 'OK' if not r.stderr else 'ERROR: '+r.stderr[:100])
"

# 3. Restart server (mandatory — Flask caches templates)
kill $(lsof -ti:8080)
cd ~/Desktop/2026AIAPP/Apex && .venv/bin/python3 -c "
from apex.interface.web import run_dashboard
run_dashboard()
" &

# 4. Browser: navigate to http://localhost:8080/ → 系统状态 → scroll to "安全扫描 MCP 状态"
```

## Reuse Checklist

To adapt this pattern for a new MCP server (e.g., GitHub, filesystem):
1. Change the route path: `/api/security/mcp-status` → `/api/<category>/<server>-status`
2. Change tool CLI check: `shutil.which("semgrep")` → `shutil.which("gh")` or whatever CLI
3. Change npm package path: `mcp-server-semgrep` → `@modelcontextprotocol/server-github`
4. Change tools list: update the static array with the new server's tools
5. Change card icons: `ti ti-shield-check` → appropriate Tabler icon
6. Change section title: "安全扫描 MCP 状态" → "GitHub MCP 状态" etc.
