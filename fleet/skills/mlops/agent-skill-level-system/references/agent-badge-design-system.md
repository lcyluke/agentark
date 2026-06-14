# Agent Badge Design System

A reusable approach for giving visual identity to agents in a multi-agent fleet — combining Unicode symbols (for terminal/CLI) with optional SVG/HTML hexagon badges (for design systems).

## Core Principle

Each agent gets:
1. **A Unicode symbol** — 1-2 chars, unique, geometric/meaningful, renderable in any monospace terminal
2. **A role-group color** — consistent across the fleet, maps to the agent's professional domain
3. **An optional SVG design** — hexagon badge with the symbol inside, matching Apex mountain theme

The system is designed to fit in Rich Table cells without breaking alignment — no multi-char emoji that pads columns differently.

## Role Group Color Scheme

| Group | Color | Hex | Agent Types |
|-------|-------|-----|-------------|
| DEV (Development) | Blue | `#3b82f6` | frontend-dev, backend-dev, fullstack-dev |
| ARCH (Architecture) | Purple | `#8b5cf6` | architect |
| OPS (Operations) | Cyan | `#06b6d4` | devops, ops-engineer |
| SEC (Security) | Red | `#ef4444` | vulnerability-scanner, penetration-tester, security-by-design |
| QA (Quality) | Green | `#22c55e` | qa-engineer |
| PM (Management) | Amber | `#f59e0b` | project-manager, apex-pm, badminton-pm |
| ANAL (Analysis) | Yellow | `#eab308` | requirements-analyst |

## Unicode Symbol Assignments

Each symbol is chosen for semantic meaning and terminal-renderability:

| Symbol | Agent | Meaning |
|--------|-------|---------|
| `≪/≫` | frontend-dev | HTML code tags, frontend identity |
| `{⚙}` | backend-dev | Curly braces + gear, backend logic |
| `⟡` | fullstack-dev | Eight-point star, full-stack mastery |
| `⊞` | architect | Crosshair/quadrant, architecture decisions |
| `✓` | devops | Checkmark, verification/automation |
| `✕` | vulnerability-scanner | X mark, finding vulnerabilities |
| `◎` | penetration-tester | Crosshair target, penetration testing |
| `▣` | security-by-design | Shield square, security design |
| `☐` | project-manager | Checkbox, task management |
| `✓` | qa-engineer | Green checkmark, quality pass |
| `◉` | requirements-analyst | Bullseye, pinpointing requirements |

## Terminal Implementation (Python/Rich)

```python
from rich.table import Table, box
from rich.style import Style

# Badge-to-agent mapping
AGENT_BADGES = {
    "frontend-dev": "≪/≫",
    "backend-dev": "{⚙}",
    "fullstack-dev": "⟡",
    "architect": "⊞",
    "devops": "✓",
    "vulnerability-scanner": "✕",
    "penetration-tester": "◎",
    "security-by-design": "▣",
    "project-manager": "☐",
    "qa-engineer": "✓",
    "requirements-analyst": "◉",
}

# Color mapping by role group
ROLE_COLORS = {
    "arch": "bright_cyan",
    "dev": "bright_blue",
    "ops": "bright_cyan",
    "sec": "bright_red", 
    "qa": "green",
    "pm": "yellow",
    "anal": "yellow",
}

def get_agent_style(agent_name):
    """Get Rich style for an agent based on its role group."""
    # Determine group from name prefixes
    for prefix, color in [("frontend", "bright_blue"), ("backend", "bright_blue"),
                          ("fullstack", "bright_blue"), ("architect", "bright_cyan"),
                          ("devops", "bright_cyan"), ("vulnerability", "bright_red"),
                          ("penetration", "bright_red"), ("security", "bright_red"),
                          ("qa", "green"), ("project", "yellow"),
                          ("requirements", "yellow")]:
        if agent_name.startswith(prefix):
            return Style(color=color, bold=True)
    return Style()
```

## Rich Table Layout

When displaying squad status, use this layout:

```python
table = Table(box=box.SQUARE, width=80, header_style="bold cyan")
table.add_column("", width=5)           # Badge column
table.add_column("Agent", width=22)      # Full name, no truncation  
table.add_column("Group", width=4)       # Role group
table.add_column("State", width=10)      # Online/Offline
table.add_column("PID", width=6)         # Process ID
table.add_column("Skills", width=5)      # Skill count
table.add_column("Lvl", width=3)         # Average level
# Then add_row with badge + styled name + ...
```

**Critical pitfall:** Rich Table with `max_width` constraints or `show_lines=True` causes columns to disappear when terminal is narrow. Use fixed `width` columns instead and test with the longest agent name.

## Short Command Names

For the command column (commonly the last column), use shortened names that still uniquely identify the agent:

| Full Name | Short Name |
|-----------|------------|
| vulnerability-scanner | vuln-scan |
| penetration-tester | pentest |
| security-by-design | sec-design |
| project-manager | pm |
| requirements-analyst | req-analyst |
| qa-engineer | qa |
| ops-engineer | ops |
| frontend-dev | frontend |
| backend-dev | backend |
| fullstack-dev | fullstack |

## SVG Hexagon Badge Design (optional — for design docs / branding)

Each badge is a 64px clipped hexagonal SVG with:
- Dark hexagon background (matching agent's role color at 15% opacity)
- Geometric inner frame (matching role color at full opacity)  
- Agent symbol in the center (white #eee)
- Optional: tooltip with agent name and skill level

Example structure:
```svg
<svg width="80" height="80" viewBox="0 0 80 80">
  <defs>
    <clipPath id="hex"><polygon points="40,4 72,22 72,58 40,76 8,58 8,22"/></clipPath>
  </defs>
  <!-- Background hex -->
  <polygon points="40,4 72,22 72,58 40,76 8,58 8,22" fill="#3b82f6" fill-opacity="0.15"/>
  <!-- Inner frame -->
  <polygon points="40,10 66,25 66,55 40,70 14,55 14,25" fill="none" stroke="#3b82f6" stroke-width="1.5"/>
  <!-- Symbol -->
  <text x="40" y="47" text-anchor="middle" fill="#eee" font-size="28" font-family="monospace">≪/≫</text>
</svg>
```

## When to Use This System

- **CLI squad dashboard** (`apex squad status`) — badge + short name + state
- **Agent attach view** (`apex squad attach <name>`) — badge in Panel title
- **Fleet monitor** (`apex fleet status`) — badge prefix per row
- **Design docs** (README, website, presentations) — SVG hexagon badges
- **Any place agents are listed** — consistency across all touchpoints

## Anti-Patterns

1. **Emoji in bullet-proof table cells** — Emoji widths vary across terminals (macOS iTerm2 vs tmux). Use Unicode symbols instead.
2. **Color-by-agent not by-group** — Having 11 different colors reduces information density. Group-level colors let the eye immediately scan role distribution.
3. **Truncating agent names** — Show full names in the agent column (22 chars is enough for even "vulnerability-scanner"), use short names only in command hints.
4. **Showing every agent in every view** — Squad view = core 9-11 agents. Fleet view = all 58 agents. Separate the two display contexts with different level of detail.
