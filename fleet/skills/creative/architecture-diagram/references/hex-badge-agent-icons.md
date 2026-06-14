# Hex-Badge Agent Icon System

Design system for creating role-grouped agent badges with hexagonal SVG frames, color-coded groups, and symbolic icons.

## Proven Use Case

Apex Agent Fleet — 11 agents across 6 role groups. Each badge: 2 hexagon layers + a unique SVG symbol. Terminal: Unicode fallback icons. Full HTML design references at `/tmp/apex-agent-badges.html`.

## Frame Structure (SVG, viewBox="0 0 80 80")

### Layer 1: Filled Gradient Outer Hexagon
```svg
<polygon points="40,6 74,24 74,56 40,74 6,56 6,24"
         fill="url(#gradId)" opacity="0.15"
         stroke="#color" stroke-width="1.5"/>
```

### Layer 2: Decorative Inner Ring
```svg
<polygon points="40,14 66,28 66,52 40,66 14,52 14,28"
         fill="none" stroke="#color"
         stroke-width="1" opacity="0.3"/>
```

**NOTE:** Use exactly 2 hexagon layers. No third faint outer ring — the user explicitly rejected it.

## Per-Group Color Assignment

| Group | Accent | Gradient 0% | Gradient 100% | Stroke | Text Fill |
|-------|--------|-------------|---------------|--------|-----------|
| DEV   | #3b82f6 | #3b82f6 | #1d4ed8 | #3b82f6 | #60a5fa |
| ARCH  | #8b5cf6 | #8b5cf6 | #6d28d9 | #8b5cf6 | #a78bfa |
| OPS   | #06b6d4 | #06b6d4 | #0891b2 | #06b6d4 | #22d3ee |
| SEC   | #ef4444 | #ef4444 | #b91c1c | #ef4444 | #f87171 |
| QA    | #22c55e | #22c55e | #15803d | #22c55e | #4ade80 |
| PM    | #f59e0b | #f59e0b | #b45309 | #f59e0b | #fbbf24 |
| ANAL  | #eab308 | #eab308 | #a16207 | #eab308 | #facc15 |

## Proven Agent Icons (SVG path data, centered at x=40, y~40)

### Frontend Dev — `</>` code tags
```svg
<text x="40" y="46" text-anchor="middle" fill="#60a5fa"
      font-size="28" font-family="'Inter',sans-serif" font-weight="700">&lt;/&gt;</text>
```

### Backend Dev — `{ }` braces
```svg
<text x="40" y="46" text-anchor="middle" fill="#60a5fa"
      font-size="28" font-family="'Inter',sans-serif" font-weight="700">{ }</text>
```

### Fullstack Dev — ⟡ octagram star
```svg
<text x="40" y="46" text-anchor="middle" fill="#60a5fa"
      font-size="24" font-family="'Inter',sans-serif" font-weight="700">⟡</text>
```
Or use HTML entity: `&#x2B21;`

### Architect — Building with columns
```svg
<path d="M26,38 L32,28 L48,28 L54,38" fill="none" stroke="#a78bfa" stroke-width="2" stroke-linejoin="round"/>
<rect x="28" y="38" width="24" height="18" fill="none" stroke="#a78bfa" stroke-width="1.5"/>
<line x1="34" y1="38" x2="34" y2="56" stroke="#a78bfa" stroke-width="1.5"/>
<line x1="40" y1="38" x2="40" y2="56" stroke="#a78bfa" stroke-width="1.5"/>
<line x1="46" y1="38" x2="46" y2="56" stroke="#a78bfa" stroke-width="1.5"/>
```

### DevOps — ∞ infinity loop (CI/CD)
```svg
<path d="M28,36 C28,26 38,26 40,36 C42,46 52,46 52,36"
      fill="none" stroke="#22d3ee" stroke-width="2.5" stroke-linecap="round"/>
<path d="M28,44 C28,54 38,54 40,44 C42,34 52,34 52,44"
      fill="none" stroke="#22d3ee" stroke-width="2.5" stroke-linecap="round"/>
```

### Vulnerability Scanner — Magnifying glass + detection dots
```svg
<circle cx="42" cy="36" r="11" fill="none" stroke="#f87171" stroke-width="2.5"/>
<line x1="50" y1="44" x2="60" y2="54" stroke="#f87171" stroke-width="3" stroke-linecap="round"/>
<circle cx="38" cy="34" r="2" fill="#f87171" opacity="0.7"/>
<circle cx="44" cy="38" r="2.5" fill="#f87171" opacity="0.9"/>
<circle cx="46" cy="33" r="1.5" fill="#f87171" opacity="0.5"/>
```

### Penetration Tester — Crosshair/target
```svg
<circle cx="40" cy="40" r="8" fill="none" stroke="#f87171" stroke-width="2.5"/>
<circle cx="40" cy="40" r="3" fill="#f87171" opacity="0.6"/>
<line x1="40" y1="28" x2="40" y2="35" stroke="#f87171" stroke-width="2" stroke-linecap="round"/>
<line x1="40" y1="45" x2="40" y2="52" stroke="#f87171" stroke-width="2" stroke-linecap="round"/>
<line x1="28" y1="40" x2="35" y2="40" stroke="#f87171" stroke-width="2" stroke-linecap="round"/>
<line x1="45" y1="40" x2="52" y2="40" stroke="#f87171" stroke-width="2" stroke-linecap="round"/>
```

### Security by Design — Shield + lock
```svg
<path d="M40,24 L54,30 L54,44 C54,54 40,58 40,58 C40,58 26,54 26,44 L26,30 Z"
      fill="none" stroke="#f87171" stroke-width="2.5"/>
<rect x="36" y="36" width="8" height="10" rx="1.5" fill="none" stroke="#f87171" stroke-width="2"/>
<path d="M36,40 C36,36 44,36 44,40" fill="none" stroke="#f87171" stroke-width="2" stroke-linecap="round"/>
```
**NOTE:** The shield width is 28px (from x=26 to x=54), wider than the initial version.

### QA Engineer — Document + checklist + checkmark
```svg
<rect x="28" y="26" width="24" height="28" rx="2" fill="none" stroke="#4ade80" stroke-width="2"/>
<line x1="28" y1="32" x2="52" y2="32" stroke="#4ade80" stroke-width="1.5"/>
<path d="M36,42 L38,44 L44,38" fill="none" stroke="#4ade80" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
<line x1="34" y1="48" x2="44" y2="48" stroke="#4ade80" stroke-width="1.5" stroke-linecap="round"/>
```

### Project Manager — Gantt chart with milestone diamond
```svg
<line x1="26" y1="30" x2="54" y2="30" stroke="#fbbf24" stroke-width="1.5"/>
<line x1="26" y1="38" x2="54" y2="38" stroke="#fbbf24" stroke-width="1.5"/>
<line x1="26" y1="46" x2="54" y2="46" stroke="#fbbf24" stroke-width="1.5"/>
<rect x="28" y="27" width="10" height="6" rx="1.5" fill="#fbbf24" opacity="0.5"/>
<rect x="36" y="35" width="14" height="6" rx="1.5" fill="#fbbf24" opacity="0.5"/>
<rect x="32" y="43" width="8" height="6" rx="1.5" fill="#fbbf24" opacity="0.5"/>
<path d="M52,28 L55,30 L52,32 L49,30 Z" fill="#fbbf24" opacity="0.9"/>
```

### Requirements Analyst — Document with annotations
```svg
<path d="M30,26 L46,26 L52,32 L52,54 L30,54 Z" fill="none" stroke="#facc15" stroke-width="2" stroke-linejoin="round"/>
<path d="M46,26 L46,32 L52,32" fill="none" stroke="#facc15" stroke-width="1.5" stroke-linejoin="round"/>
<line x1="34" y1="36" x2="48" y2="36" stroke="#facc15" stroke-width="1.5" stroke-linecap="round"/>
<line x1="34" y1="42" x2="46" y2="42" stroke="#facc15" stroke-width="1.5" stroke-linecap="round"/>
<line x1="34" y1="48" x2="44" y2="48" stroke="#facc15" stroke-width="1.5" stroke-linecap="round"/>
<circle cx="50" cy="36" r="1.5" fill="#facc15" opacity="0.6"/>
<circle cx="48" cy="42" r="1.5" fill="#facc15" opacity="0.6"/>
```

## Terminal Unicode Fallbacks

When SVG is not available (CLI output), use these Unicode symbols with ANSI color:

| Agent | Unicode | Color |
|-------|---------|-------|
| frontend-dev | ≪/≫ | Blue #3b82f6 |
| backend-dev | {⚙} | Blue #3b82f6 |
| fullstack-dev | ⟡ | Blue #3b82f6 |
| architect | ⊞ | Purple #8b5cf6 |
| devops | ✓ | Cyan #06b6d4 |
| vulnerability-scanner | ✕ | Red #ef4444 |
| penetration-tester | ◎ | Red #ef4444 |
| security-by-design | ▣ | Red #ef4444 |
| qa-engineer | ✓ | Green #22c55e |
| project-manager | ☐ | Amber #f59e0b |
| requirements-analyst | ◉ | Yellow #eab308 |

## Badge Card HTML Template Pattern

```html
<div class="badge-card group-{rolename}">
  <div class="badge">
    <svg viewBox="0 0 80 80" fill="none">
      <defs><linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0%" stop-color="{accent}"/>
        <stop offset="100%" stop-color="{dark}"/>
      </linearGradient></defs>
      <!-- 2 hexagon layers (see above) -->
      <!-- icon elements -->
    </svg>
  </div>
  <h3>{agent-name}</h3>
  <div class="subtitle">{role-title}</div>
  <div class="role-group">{GROUP}</div>
</div>
```

## CSS Class Colors

```css
.group-dev { --accent: #3b82f6; --glow-color: rgba(59,130,246,0.2); }
.group-sec { --accent: #ef4444; --glow-color: rgba(239,68,68,0.2); }
.group-qa  { --accent: #22c55e; --glow-color: rgba(34,197,94,0.2); }
.group-pm  { --accent: #f59e0b; --glow-color: rgba(245,158,11,0.2); }
.group-anal { --accent: #eab308; --glow-color: rgba(234,179,8,0.2); }
.group-arch { --accent: #8b5cf6; --glow-color: rgba(139,92,246,0.2); }
.group-ops  { --accent: #06b6d4; --glow-color: rgba(6,182,212,0.2); }
```

## Pitfalls

- **3-layer hexagon rejection:** User explicitly rejected the 3rd faint outer ring hexagon (`points="40,4 4,28..."`). Keep exactly 2.
- **SVG viewBox:** Must be `0 0 80 80`. Icons center around x=40, y=40-44.
- **Path precision matters:** Bezier curves (C commands) need exact control points. Test visually before finalizing.
- **Gradient vs solid fill:** Outer hexagon uses `opacity="0.15"` gradient; never use solid fill on it. The inner ring is always `fill="none"`.
- **Terminal fallback:** Always define a Unicode fallback for CLI display. Match the symbol to the SVG icon concept.
- **Badge color check:** QA agent (✓) and DevOps agent (✓) have identical Unicode but different colors (Green vs Cyan). This is intentional — group color differentiates them.
