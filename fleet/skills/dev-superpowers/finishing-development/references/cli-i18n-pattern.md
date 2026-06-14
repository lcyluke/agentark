# CLI i18n Pattern — Dual-Language Support with `--lang` Flag

Reusable pattern from AutoClicker and AIAgentOps projects. Single codebase, full locale support.

## Pattern

```python
# Top of file, BEFORE any heavy imports (so --version/--update work without deps):
import sys as _sys, os as _os
_argv = _sys.argv[1:]

# Flag handlers that work even if deps are missing
if "--version" in _argv or "-V" in _argv:
    print("ToolName v1.0.0")
    _sys.exit(0)

# Locale dict
T = {
    "en": {
        "banner": "Welcome to ToolName",
        "menu_1": "  1. Start",
    },
    "zh": {
        "banner": "欢迎使用 ToolName",
        "menu_1": "  1. 开始",
    },
}

def detect_lang() -> str:
    """Support --lang=zh and --lang zh. Default English."""
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--lang" and i + 1 < len(argv):
            return "zh" if argv[i+1].lower() in ("zh","cn","chinese") else "en"
        if a.startswith("--lang="):
            return "zh" if a.split("=",1)[1].lower() in ("zh","cn","chinese") else "en"
    return "en"  # DEFAULT ENGLISH (not auto-detect)

LANG = "en"

def t(key, *args):
    s = T.get(LANG, T["en"]).get(key, T["en"].get(key, key))
    return s.format(*args) if args else s

# In main():
if __name__ == "__main__":
    LANG = detect_lang()
    print(t("banner"))
```

## Key Design Decisions

- **Default English** — not auto-detect from OS locale (user preference: Luke uses English as default)
- **Support both `--lang=zh` and `--lang zh`** — users expect both
- **Case-insensitive**: `--lang EN`, `--lang Zh` all work
- **Flag check BEFORE imports** — so `--version` works even if `pip install` not done
- **No separate files** — single codebase, not `clicker_en.py` + `clicker_zh.py`

## README i18n

For GitHub projects: two separate README files with mutual links is the cleanest pattern (User rejected `<details>` fold/unfold approach):

```markdown
<!-- README.md -->
<p align="center">
  <a href="README.md"><b>English</b></a> | <a href="README_CN.md">中文</a>
</p>

<!-- README_CN.md -->
<p align="center">
  <a href="README.md">English</a> | <a href="README_CN.md"><b>中文</b></a>
</p>
```
