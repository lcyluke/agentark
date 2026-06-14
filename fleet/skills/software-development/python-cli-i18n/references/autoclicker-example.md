# Real-World Example: AutoClicker i18n (Final State)

Source: lcyluke/AutoClicker, v1.0.3. Three scripts, all using identical i18n pattern.

## Final Pattern (After All Fixes)

Key differences from initial implementation:
- **No `import locale`** — system locale auto-detect removed (defaults to English, explicit `--lang zh`)
- **`--version`/`--update` at file TOP** (before any imports, after docstring) — works without deps installed
- **`detect_lang()` handles both `--lang zh` AND `--lang=zh`** (space and equals)
- **`.lower()` on lang value** — `--lang EN`, `--lang ZH` all work

## Flag Check (MUST be at file top)

```python
# ── Flag check BEFORE imports (so --version/--update work even if deps missing) ─
import sys as _sys, os as _os
_argv = _sys.argv[1:]
if "--version" in _argv or "-V" in _argv:
    import subprocess as _sp
    _dir = _os.path.dirname(_os.path.abspath(__file__))
    try:
        r = _sp.run(["git", "describe", "--tags", "--always"],
                     capture_output=True, text=True, timeout=3, cwd=_dir)
        print(f"AutoClicker {r.stdout.strip()}" if r.returncode == 0 else "AutoClicker v1.0.2")
    except Exception:
        print("AutoClicker v1.0.2")
    _sys.exit(0)
if "--update" in _argv:
    import subprocess as _sp
    _dir = _os.path.dirname(_os.path.abspath(__file__))
    print("AutoClicker — updating from git...")
    r = _sp.run(["git", "pull"], capture_output=True, text=True, timeout=30, cwd=_dir)
    print(r.stdout.strip() or r.stderr.strip() or "Done.")
    _sys.exit(0)
```

## Language Detection (Final)

```python
def detect_lang() -> str:
    """Supports --lang=zh AND --lang zh. Defaults to English."""
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--lang":                          # --lang zh
            if i + 1 < len(argv):
                lang = argv[i + 1].lower()
                if lang in ("zh", "cn", "chinese", "中文"):
                    return "zh"
            return "en"
        if a.startswith("--lang="):                # --lang=zh
            lang = a.split("=", 1)[1].lower()
            if lang in ("zh", "cn", "chinese", "中文"):
                return "zh"
            return "en"
    return "en"
```

## Files Converted

| File | Keys | Notes |
|------|------|-------|
| `clicker.py` | 80+ | Main: record + loop + OCR |
| `auto_confirm.py` | 40+ | Auto-confirm daemon |
| `capture_template.py` | 15 | Template screenshot tool |

## README Approach

Two separate files with mutual links — proven cleaner than single-page `<details>` for this project:
- `README.md` — English (GitHub default)
- `README_CN.md` — Chinese
- Each has `English | 中文` link at top
- Logo is clickable → opens demo video (`autoclicker.mp4`)

## Cross-Platform Notification

See `references/cross-platform-notify.md` for the `platform.system()` three-branch pattern used in `auto_confirm.py`.

## Lessons Learned (This Session)

1. **`--version` before imports is non-negotiable** — first implementation put `handle_flags()` in `main()`, which required `import pyautogui` to succeed first. Moved to file top, all three scripts now work without deps.
2. **`--lang EN` (uppercase) must work** — added `.lower()` to lang value.
3. **`--lang zh` (space) must work** — first implementation only checked `--lang=`. Fixed to iterate argv and check both forms.
4. **GitHub `<video>` tag silently fails** — replaced with clickable logo image linking to raw `.mp4`.
5. **Empty `GH_TOKEN` is a trap** — `env` shows it set, but it's empty string. Always verify with a real API call.
