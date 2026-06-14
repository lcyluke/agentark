# Fleet Node Heartbeat Panel — Multi-Machine Monitoring

How to add fleet-wide node heartbeat monitoring to the Apex Command Center system view.
Tracks multiple Macs/servers running Hermes Agent: online/offline status, heartbeat age, GPU stats, agent counts.

## Architecture

```
Remote Nodes (GPU servers, other Macs)
  │
  ├─ HTTP: curl POST /api/fleet/heartbeat → fleet/nodes/<id>.json
  └─ Git:  fleet_report() → fleet/nodes/<id>.json → git push
                 │
Dashboard (web.py) ─────────────────────────┘
  ├─ GET  /api/fleet/nodes     → enrich + return all nodes
  ├─ POST /api/fleet/heartbeat → receive remote heartbeat
  └─ GET  /api/fleet/status    → local machine status

Frontend (command_center.html)
  └─ v-system → renderFleetNodes() → node cards with GPU/agent stats
```

## Phase 1: Backend API Endpoints

Add three routes in `web.py` inside `create_app()`, after existing fleet routes.

### POST /api/fleet/heartbeat — Receive heartbeat from remote nodes

```python
@app.route("/api/fleet/heartbeat", methods=["POST"])
def api_fleet_heartbeat():
    """Receive heartbeat from remote fleet nodes.
    POST body: {machine_id, hostname, role, profiles, skills, gpu, ...}
    """
    try:
        from apex.interface.fleet_multi_mac import NODES_DIR, get_machine_id as _local_id

        data = request.get_json(force=True) or {}
        machine_id = data.get("machine_id", "unknown")

        # Block local machine from posting to itself via HTTP
        # (local nodes use fleet_report() which is git-based)
        local_id = _local_id()
        if machine_id == local_id:
            return jsonify({
                "ok": True, "skipped": True,
                "reason": "Use fleet_report() for local heartbeat (git-based)",
            })

        data["received_at"] = datetime.now().isoformat()
        NODES_DIR.mkdir(parents=True, exist_ok=True)
        node_file = NODES_DIR / f"{machine_id}.json"
        node_file.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str))

        return jsonify({"ok": True, "machine_id": machine_id, ...})
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### GET /api/fleet/nodes — List all nodes with enriched status

```python
@app.route("/api/fleet/nodes")
def api_fleet_nodes():
    try:
        from apex.interface.fleet_multi_mac import get_all_nodes, fleet_status, get_machine_id

        nodes = get_all_nodes()
        local_status = fleet_status()
        local_id = get_machine_id()
        now = datetime.now()

        enriched = []
        for n in nodes:
            mid = n.get("machine_id", "unknown")
            is_local = (mid == local_id)

            # Heartbeat age computation
            reported = n.get("reported_at") or n.get("received_at")
            age_secs = None
            age_str = "从未"
            if reported:
                dt = datetime.fromisoformat(reported)
                age_secs = (now - dt).total_seconds()
                mins = int(age_secs // 60)
                if mins < 1: age_str = "刚刚"
                elif mins < 60: age_str = f"{mins}分钟前"
                else: age_str = f"{mins//60}小时前"

            # Online: heartbeat within 10 minutes
            online = age_secs is not None and age_secs < 600

            if is_local:
                n = {**n, **local_status}  # merge live local status

            n["_online"] = online
            n["_heartbeat_age"] = age_str
            n["_heartbeat_age_secs"] = age_secs
            n["_is_local"] = is_local
            enriched.append(n)

        return jsonify({
            "ok": True, "total": len(enriched),
            "online": sum(1 for n in enriched if n.get("_online")),
            "offline": sum(1 for n in enriched if not n.get("_online")),
            "local_id": local_id, "nodes": enriched,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500
```

### Key design decisions

- **`_` prefix fields**: `_online`, `_heartbeat_age`, `_is_local` are computed fields, not stored in node JSON
- **10-minute threshold**: nodes without heartbeat in 10 minutes are marked offline
- **Local node blocking**: POST from local machine is rejected (it should use `fleet_report()`)
- **Node files**: stored in `fleet/nodes/<machine_id>.json` inside the Apex repo

## Phase 2: Frontend HTML

Insert into `v-system` section, after MCP status panel:

```html
<div style="height:22px"></div>
<div class="sec-h"><i class="ti ti-antenna-bars-5"></i>舰队节点监控
  <span id="fleetSummary" style="font-size:12px;color:var(--tx3);font-weight:400"></span>
</div>
<div id="fleetNodes"></div>
```

## Phase 3: Frontend JS

### Wiring — call from renderSystem()

```javascript
async function renderSystem() {
  // ... existing ...
  renderMcpStatus();
  renderFleetNodes();  // ← add this call
}
```

### Node card rendering (string concatenation, NO template literals)

Each node card shows:
- **Left border**: green (#22c55e) for online, red (#ef4444) for offline
- **Status dot**: green pulsing dot for online, red static for offline
- **Hostname** + "本机" badge (teal) for local machine
- **Machine ID** in mono font
- **Role badge**: ⚓ origin (violet) or 🔧 worker (teal)
- **Status tag**: 在线/离线 with green/red tag
- **Heartbeat age**: 刚刚 / N分钟前 / N小时前
- **Agent stats**: Profiles count + Skills count
- **GPU bar** (if GPU present): name, utilization% (color-coded), memory%, temperature

```javascript
async function renderFleetNodes() {
  var container = $('#fleetNodes');
  var summary = $('#fleetSummary');
  if (!container) return;

  // Loading state
  container.innerHTML = '<div style="text-align:center;padding:20px;color:var(--tx3)">' +
    '<i class="ti ti-loader" style="animation:spin 1s linear infinite;font-size:20px"></i>' +
    '<div style="margin-top:6px;font-size:12px">加载舰队节点...</div></div>';

  var data = await fetchJSON(API + '/fleet/nodes');
  if (!data || !data.nodes) {
    container.innerHTML = '<div class="card"><div style="text-align:center;padding:20px;color:var(--tx3)">无舰队数据</div></div>';
    return;
  }

  // Summary badge
  if (summary) {
    summary.innerHTML = '· ' + (data.online||0) + '/' + (data.total||0) + ' 在线';
  }

  var cards = data.nodes.map(function(n) {
    var isOnline = n._online;
    var dotColor = isOnline ? '#22c55e' : '#ef4444';

    // GPU bar with color-coded utilization
    var gpu = n.gpu || {};
    var gpuHtml = '';
    if (gpu.gpu_count && gpu.gpu_count > 0) {
      var utilBar = gpu.util_pct > 80 ? 'var(--red)' :
                    (gpu.util_pct > 50 ? 'var(--amber)' : 'var(--green)');
      gpuHtml = '<div style="margin-top:8px;padding:6px 8px;background:var(--bg4);border-radius:var(--r-s);font-size:11px">' +
        '<span style="color:var(--tx3)">GPU:</span> ' + gpu.gpu_names[0] +
        ' <span style="color:' + utilBar + ';font-weight:600">' + gpu.util_pct + '%</span>' +
        ' | 显存 ' + gpu.mem_pct + '% | ' + gpu.temp_c + '°C</div>';
    } else {
      gpuHtml = '<div style="margin-top:8px;padding:6px 8px;background:var(--bg4);border-radius:var(--r-s);font-size:11px;color:var(--tx3)">GPU: 无</div>';
    }

    return '<div class="card" style="margin-bottom:10px;border-left:3px solid ' + dotColor + '">' +
      '<div style="font-weight:600;font-size:14px">' +
      '<span style="display:inline-block;width:8px;height:8px;border-radius:50%;background:' + dotColor +
      ';margin-right:6px;' + (isOnline ? 'box-shadow:0 0 6px ' + dotColor : '') + '"></span>' +
      n.hostname + (n._is_local ? ' <span style="background:var(--teal);color:#000;font-size:10px;padding:1px 6px;border-radius:8px;margin-left:6px">本机</span>' : '') +
      '</div>' +
      '<div style="font-family:var(--mono);font-size:10px;color:var(--tx3)">' + n.machine_id + '</div>' +
      // Role + status + age
      '<div style="display:flex;align-items:center;gap:8px;flex-wrap:wrap;margin-top:4px">' +
      '<span class="tag ' + (isOnline ? 'green' : 'red') + '" style="font-size:10px">' + (isOnline ? '在线' : '离线') + '</span>' +
      '<span style="font-size:10px;color:var(--tx3)">' + n._heartbeat_age + '</span>' +
      '</div>' +
      // Agent stats
      '<div style="display:flex;gap:12px;margin-top:6px;font-size:11px;color:var(--tx3)">' +
      '<span><i class="ti ti-users"></i> ' + (n.profiles||0) + ' Profiles</span>' +
      '<span><i class="ti ti-bolt"></i> ' + (n.skills||0) + ' Skills</span></div>' +
      gpuHtml +
      '</div>';
  });

  container.innerHTML = cards.join('');
}
```

## Remote Node Setup

### Option A: HTTP heartbeat (GPU servers, no git access)

```bash
# Cron every 5 minutes
*/5 * * * * curl -s -X POST http://<dashboard-ip>:8080/api/fleet/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"machine_id":"'$(hostname)-$(whoami)'","hostname":"'$(hostname)'","role":"worker",...}'
```

### Option B: Git heartbeat (Macs with git push access)

```bash
cd ~/Desktop/2026AIAPP/Apex && python3 -c "
from apex.interface.fleet_multi_mac import fleet_report
print(fleet_report())
"
```

## Existing Infrastructure

The `fleet_multi_mac.py` module already provides:
- `get_machine_id()` — `hostname-username`
- `fleet_status()` — live snapshot (GPU, git, profiles, skills)
- `fleet_report()` — write + git push heartbeat
- `get_all_nodes()` — read all `fleet/nodes/*.json`
- `fleet_init()` / `fleet_join()` — fleet lifecycle
- `NODES_DIR` — `fleet/nodes/` inside Apex repo

## Verification

```bash
# 1. Test heartbeat receive
curl -s -X POST http://localhost:8080/api/fleet/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"machine_id":"test-node","hostname":"test","role":"worker","profiles":1,"skills":5}' | python3 -m json.tool

# 2. Test nodes list
curl -s http://localhost:8080/api/fleet/nodes | python3 -m json.tool | head -40

# 3. JS syntax check (standard flow)
curl -s http://localhost:8080/ -o /tmp/cc.html
python3 -c "
import re,subprocess
html=open('/tmp/cc.html').read()
js=re.findall(r'<script>(.*?)</script>',html,re.DOTALL)[0]
open('/tmp/js.js','w').write(js)
r=subprocess.run(['node','--check','/tmp/js.js'],capture_output=True,text=True)
print('OK' if not r.stderr else r.stderr[:200])
"

# 4. Browser: http://localhost:8080/ → 系统状态 → scroll to "舰队节点监控"
```
