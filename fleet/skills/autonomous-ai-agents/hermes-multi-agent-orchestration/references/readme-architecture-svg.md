# README Architecture SVG Pattern

## When

Adding a visual architecture/workflow diagram to a GitHub README that renders natively without external hosting.

## Why SVG

- GitHub renders SVG inline (unlike `<video>`)
- No external hosting needed — committed to repo
- Dark/light theme support possible
- Infinitely scalable
- Can include text, arrows, layers, gradients

## Template: Dark Theme Architecture SVG

```svg
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 720"
     font-family="ui-monospace,SFMono-Regular,Menlo,Monaco,monospace">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="#0f172a"/>
      <stop offset="100%" stop-color="#1e293b"/>
    </linearGradient>
    <marker id="arrowGreen" markerWidth="8" markerHeight="6" refX="8" refY="3" orient="auto">
      <path d="M0,0 L8,3 L0,6 Z" fill="#22c55e"/>
    </marker>
    <!-- Add more markers for different colors -->
  </defs>

  <!-- Background -->
  <rect width="960" height="720" fill="url(#bg)"/>

  <!-- Title -->
  <text x="480" y="35" text-anchor="middle" fill="#06b6d4" font-size="20" font-weight="bold">
    ⚓ Project Name — Architecture
  </text>

  <!-- Layers: rect + text pattern -->
  <!-- Arrows: line/path with marker-end pattern -->
</svg>
```

## Color Palette (Tailwind Dark)

| Element | Tailwind | Hex |
|---------|----------|-----|
| Background | slate-900 | #0f172a |
| Surface | slate-800 | #1e293b |
| Border | slate-700 | #334155 |
| Text primary | slate-400 | #94a3b8 |
| Text dim | slate-500 | #64748b |
| Cyan accent | cyan-500 | #06b6d4 |
| Blue accent | blue-500 | #3b82f6 |
| Green pass | green-500 | #22c55e |
| Red block | red-500 | #ef4444 |
| Amber warn | amber-500 | #f59e0b |

## Layout Pattern

```
Layer 1 (top):      Surfaces (CLI / TUI / MCP / API)
    ↓ arrows
Layer 2:            Daemon / Core process
    ↓ arrows  
Layer 3 (middle):   Core engines (registry, eventbus, blackboard, etc.)
    ↓ arrows
Layer 4 (bottom):   Adapters / Runtimes
    ↓ arrows
Layer 5:            Security + Storage + Completion
    ↓ arrows  
Bottom legend:      lifecycle + invariants
```

## Embedding

```markdown
### Architecture

<p align="center">
  <img src="architecture.svg" alt="Architecture" width="100%">
</p>
```

## Guidelines

- **Keep it under 15KB** for fast rendering
- **Use monospace font** for consistent alignment
- **Add a legend** at the bottom explaining the flow
- **Color-code layers** for visual hierarchy
- **Include invariants** in the legend for completeness
- **Don't over-animate** — static SVG is cleaner than CSS animations in README
