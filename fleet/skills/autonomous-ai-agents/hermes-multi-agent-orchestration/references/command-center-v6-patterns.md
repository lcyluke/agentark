# Command Center V6 — Key Development Patterns

## Canvas API Bug (recurring)
When subagents generate dashboard HTML with inline JS, Canvas rendering breaks because CSS variables are used in `ctx.fillStyle`/`grad.addColorStop()`. Canvas API does NOT understand `var(--accent)`.

**Fix:** Replace ALL CSS variables in JS Canvas context with hex:
- `var(--accent)` → `#3b82f6`
- `var(--text-muted)` → `#5a6f8a`
- `var(--text-primary)` → `#e8edf5`
- `var(--green)` → `#22c55e`
- `var(--red)` → `#ef4444`

CSS variables in `style=` strings on DOM elements are FINE and should NOT be changed.

## Subagent JS Escaping Bug (recurring)
When delegate_task produces dashboard HTML, JS string concatenation inside innerHTML gets over-escaped:
- File has: `\\\\\\\"` → browser sees literal `\` + unescaped `"` → SyntaxError
- Fix: `node -e "html.replace(/\\\\\\\"/g, '\"')"`  to remove one escaping level
- Validate: `node --check /tmp/test.js`

## Flask Route Collision Pattern
Never do this (Flask treats "teams" as <name>):
```python
@app.route("/api/items")       # GET list
@app.route("/api/items/<name>")  # GET detail — COLLISION
```
Always:
```python
@app.route("/api/items/list")
@app.route("/api/items/<name>")  # safe because "list" is not a <name> match
```

## el() Helper Must Handle Numbers
```js
function el(tag,attrs,children){
  if(children!==undefined && children!==null){
    if(typeof children==='string'||typeof children==='number') e.textContent=children;
    else if(Array.isArray(children)) children.forEach(...);
    else e.textContent=String(children);
  }
}
```
Without number handling, `el('span',{},count)` → `children.forEach is not a function`.

## Flask Template Caching
After editing an HTML template, the old version persists in browser. Fix:
1. Kill Flask server
2. Restart server
3. Browser hard-refresh (Cmd+Shift+R)
Do NOT assume changes take effect with just a browser refresh.

## osascript Error on macOS Demo
`webbrowser.open(url)` triggers `osascript` on macOS which fails with `-10814` in CLI-only contexts. Fix: use `subprocess.run(["open", url], capture_output=True)`.

## Branding: "Command Center" NOT "AI Fleet"
- Product name: "Command Center" (指挥中心)
- Sidebar view for agents: "AI舰队" (fine as a sub-view name)
- Demo banner: "Your Multi-Agent Command Center" / "5 minutes to your AI fleet"
- README: "14-view Command Center"
- URL: `http://localhost:8080/` (single entry, no aliases like /cc)

## All 14 Views
运营: 指挥中心 | 项目作战室 | 审批审计 | Pipeline
智能: AI舰队 | 自治引擎 | 知识图谱 | 数据流时序 | 模块市场 | SKILL进化
资源: 成本中心 | 系统状态 | GPU资源中心
