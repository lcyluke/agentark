# Fleet Agent Card CSS Reference

Proven CSS for agent status cards used in the Apex Command Center.
Combines state dots, load bars, task queue breakdowns, and "can accept" tags.

```css
.fleet-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 12px;
}
.fleet-card {
  background: var(--bg2);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 15px;
  transition: .15s;
  cursor: pointer;
  position: relative;
}
.fleet-card:hover { border-color: var(--line2); }
.fleet-card .fh {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 10px;
}
.fleet-card .fstatus {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;
}
.fleet-card .fname {
  font-family: var(--disp);
  font-size: 13.5px;
  font-weight: 600;
}
.fleet-card .frole {
  font-size: 11px;
  color: var(--tx2);
  margin-top: 1px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.fleet-card .fmeta {
  display: flex;
  gap: 16px;
  margin: 8px 0;
  font-size: 11px;
  color: var(--tx2);
  flex-wrap: wrap;
}
.fleet-card .fmeta span { display: flex; align-items: center; gap: 4px; }
.fleet-card .fmeta i { font-size: 13px; }
.fleet-card .ftasks { margin-top: 6px; font-size: 11px; }
.fleet-card .ftasks .dt {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 2px 0;
}
.fleet-card .ftasks .dtag {
  font-size: 10px;
  padding: 1px 6px;
  border-radius: 10px;
  font-family: var(--mono);
}
.fleet-card .fbar {
  height: 4px;
  border-radius: 2px;
  background: var(--bg4);
  margin-top: 6px;
  overflow: hidden;
}
.fleet-card .fbar i { display: block; height: 100%; border-radius: 2px; }
.fleet-card .fbtns { display: flex; gap: 6px; margin-top: 10px; }
.fleet-card .fcan {
  position: absolute;
  top: 12px;
  right: 12px;
  font-size: 10px;
  padding: 2px 8px;
  border-radius: 10px;
  font-family: var(--mono);
  font-weight: 600;
}
```

## Board Management CSS

```css
.board-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 14px; }
.board-section {
  background: var(--bg2);
  border: 1px solid var(--line);
  border-radius: var(--r);
  padding: 16px;
}
.board-section h4 {
  font-family: var(--disp);
  font-size: 13px;
  font-weight: 600;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  gap: 7px;
}
.board-member {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 10px;
  border-radius: var(--r-s);
  transition: .15s;
  cursor: pointer;
}
.board-member:hover { background: var(--bg3); }
.board-member .bmav {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: grid;
  place-items: center;
  font-size: 12px;
  font-weight: 700;
  font-family: var(--mono);
  flex-shrink: 0;
}
.board-member .bminfo { flex: 1; font-size: 12px; }
.board-member .bminfo .bmname { font-weight: 500; }
.board-member .bminfo .bmrole { font-size: 10.5px; color: var(--tx3); }
.board-member .bmremove {
  color: var(--tx3);
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  border-radius: 4px;
}
.board-member .bmremove:hover { color: var(--red); background: var(--red-d); }
.board-add { display: flex; gap: 8px; margin-top: 8px; }
.board-add input { flex: 1; }
```

## Task Breakdown Tag Colors

| Status | Background | Text Color | Icon |
|--------|-----------|-----------|------|
| Running (进行中) | `var(--blue-d)` | `var(--blue)` | ⟳ |
| Pending (待办) | `var(--bg4)` | `var(--tx2)` | ○ |
| Blocked (阻塞) | `var(--red-d)` | `var(--red)` | ⊘ |
| Done (完成) | `var(--green-d)` | `var(--green)` | ✓ |
| No tasks (无任务) | N/A | `var(--tx3)` | -- |

## Data Sources and Cross-Referencing

```
hermes sessions (/api/live/runtime.sessions[])
  └─ id, source, model, tokens, cost, runtime_min
  
apex profiles (/api/profiles[])
  └─ name, role, model, skills[], expertise

hermes profiles (/api/fleet/profiles/list[])
  └─ name, model, has_soul, has_config

workloads (/api/ops/agents/workloads[])
  └─ name/agent/id, load/saturation (0-1)

tasks (/api/tasks[])
  └─ title, assignee, status, priority
```

Cross-reference: `apexProfiles[name]` → `workloads.find(w => w.name === name)` → `tasks.filter(t => t.assignee === name)`
