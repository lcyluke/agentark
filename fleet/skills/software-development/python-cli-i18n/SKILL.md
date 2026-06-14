---
name: python-cli-i18n
description: "Add --lang en|zh support to Python CLI tools — locale dict + detect_lang() + t() helper pattern."
version: 1.0.0
metadata:
  hermes:
    tags: [python, cli, i18n, internationalization, locale]
    pitfall_count: 5
---

# Python CLI Internationalization

Lightweight i18n for Python CLI tools. One codebase, dual language — no gettext, no .po files, no external deps. Just a locale dict + 3 helper functions.

## Triggers

- Adding `--lang` support to an existing Python CLI
- Building a new CLI tool that needs Chinese + English
- User says "中英文两个版本" or "支持中英文切换"
- Converting from single-language to dual-language

## Pattern

### Step 1: Locale Dict at Module Top

```python
T = {
    "en": {
        "hello": "Hello, {}!",
        "error": "Error: {}",
        "done": "Done.",
    },
    "zh": {
        "hello": "你好，{}！",
        "error": "错误：{}",
        "done": "完成。",
    },
}

LANG = "en"
```

### Step 2: Language Detection

```python
def detect_lang() -> str:
    """Supports --lang=zh AND --lang zh. Defaults to English."""
    argv = sys.argv[1:]
    for i, a in enumerate(argv):
        if a == "--lang":                          # --lang zh (space)
            if i + 1 < len(argv):
                lang = argv[i + 1].lower()
                if lang in ("zh", "cn", "chinese", "中文"):
                    return "zh"
            return "en"
        if a.startswith("--lang="):                # --lang=zh (equals)
            lang = a.split("=", 1)[1].lower()
            if lang in ("zh", "cn", "chinese", "中文"):
                return "zh"
            return "en"
    return "en"
```

**Why no `import locale`?** Auto-detection from system locale caused bugs — Chinese macOS users got Chinese UI even when they expected English. Default to English, let users explicitly opt into Chinese with `--lang zh`.

### Step 3: Translation Helper

```python
def t(key: str, *args) -> str:
    """Look up translated string. t('hello', name) -> '你好，Luke！'"""
    s = T.get(LANG, T["en"]).get(key, T["en"].get(key, key))
    if args:
        return s.format(*args)
    return s
```

### Step 4: Entry Point + Version/Update Flags

`handle_flags()` runs first — exits immediately for `--version` or `--update`, skipping all heavy imports.

```python
BASE_DIR = Path(__file__).parent

def get_version() -> str:
    """git tag, fallback to hardcoded."""
    import subprocess
    try:
        r = subprocess.run(
            ["git", "describe", "--tags", "--always"],
            capture_output=True, text=True, timeout=3, cwd=str(BASE_DIR)
        )
        if r.returncode == 0 and r.stdout.strip():
            return r.stdout.strip()
    except Exception:
        pass
    return "v1.0.0"

def handle_flags():
    argv = sys.argv[1:]
    if "--version" in argv or "-V" in argv:
        print(f"ToolName {get_version()}")
        sys.exit(0)
    if "--update" in argv:
        import subprocess
        print(f"ToolName {get_version()} — updating...")
        r = subprocess.run(
            ["git", "pull"], cwd=str(BASE_DIR),
            capture_output=True, text=True, timeout=30
        )
        print(r.stdout.strip() or r.stderr.strip() or "Done.")
        print(f"Now at: {get_version()}")
        sys.exit(0)

if __name__ == "__main__":
    handle_flags()      # must be first — exits early for --version/--update
    LANG = detect_lang()
    main()
```

**Order matters**: `handle_flags()` → `detect_lang()` → then heavy imports (OCR, network). Users checking `--version` shouldn't wait for `import pytesseract`.

### Step 5: Replace All UI Strings

Every `print()` / `input()` / `log.info()` that faces the user uses `t(key, *args)`:

```python
# Before:
print("✅ 已保存:", path)
choice = input("请输入 (1-5): ")

# After:
print(t("cfg_saved", str(path)))
choice = input(t("menu_prompt"))
```

## Pitfalls

### Pitfall 0: `--version`/`--update` MUST Run Before Imports

The most critical ordering rule. If `handle_flags()` runs inside `main()` or `if __name__`, then `import pyautogui` (or any heavy dependency) fails BEFORE the flag is checked — users get a `ModuleNotFoundError` instead of a version number.

**Solution: Put flag checks at the VERY TOP of the file, after the docstring, BEFORE any imports:**

```python
#!/usr/bin/env python3
"""
MyTool — description.
"""

# ── MUST be first — before ANY imports ─
import sys as _sys, os as _os
_argv = _sys.argv[1:]
if "--version" in _argv or "-V" in _argv:
    import subprocess as _sp
    _dir = _os.path.dirname(_os.path.abspath(__file__))
    try:
        r = _sp.run(["git", "describe", "--tags", "--always"],
                     capture_output=True, text=True, timeout=3, cwd=_dir)
        print(f"MyTool {r.stdout.strip()}" if r.returncode == 0 else "MyTool v1.0.0")
    except Exception:
        print("MyTool v1.0.0")
    _sys.exit(0)
if "--update" in _argv:
    import subprocess as _sp
    _dir = _os.path.dirname(_os.path.abspath(__file__))
    print("MyTool — updating from git...")
    r = _sp.run(["git", "pull"], capture_output=True, text=True, timeout=30, cwd=_dir)
    print(r.stdout.strip() or r.stderr.strip() or "Done.")
    _sys.exit(0)

# ── NOW safe to import heavy deps ─
```

Use `_sys`, `_sp` aliases to avoid shadowing the real `sys`/`subprocess` imports later. Use `_os.path.dirname(_os.path.abspath(__file__))` for robust path resolution.

### Pitfall 1: `--lang zh` (space) Is NOT the Same as `--lang=zh` (equals)

Users naturally type `python myscript.py --lang zh` with a space. If you only check `startswith("--lang=")`, the space syntax is silently ignored and the tool stays in English. The `detect_lang()` above handles BOTH. **Always test both syntaxes after implementing.**

### Pitfall 2: Case Sensitivity — Always Call `.lower()`

`--lang EN`, `--lang Zh`, `--lang=ZH` must all work. A single `.lower()` on the extracted value handles it. Without it, `"EN" in ("zh", "cn", ...)` is `False`.

### Pitfall 3: Module-Level Print Runs Before LANG Is Set

`LANG = "en"` at module level is a default. The real value is set in `main()` or the `if __name__` guard. If any module-level code calls `t()` before `LANG` is reassigned, it gets English silently.

```python
# ❌ Module-level print runs before main() sets LANG
OCR_OK = check_ocr()
print(t("ocr_warn"))  # Always English

# ✅ Check LANG at runtime inside main()
def main():
    if not OCR_OK:
        print(t("ocr_warn"))  # Respects --lang flag
```

Workaround for module-level warnings: print them in both languages, or defer to `main()`.

### Pitfall 4: Empty Env Vars Look Set But Aren't

`env | grep TOKEN` showing `GH_TOKEN=` does NOT mean the token exists — it's set to empty string. Always test with a real API call, not presence check.

### Pitfall 5: Missing Keys Silently Degrade

If a key is missing in the active language dict, `t()` falls back to English, then to the raw key string. This means typos in key names won't crash but will show raw key names to the user. Always do a quick sanity check after adding new strings:

```python
# Quick audit: print all keys that differ between languages
en_keys = set(T["en"].keys())
zh_keys = set(T["zh"].keys())
print("Missing in zh:", en_keys - zh_keys)
print("Missing in en:", zh_keys - en_keys)
```

## Bilingual README on GitHub

**Preferred: Two separate files with mutual links.** Each language gets a clean, single-language page. Users switch by clicking the language link at the top.

```markdown
<!-- README.md (English, shown by default) -->
# AutoClicker
<p align="center">
  <a href="README.md"><b>English</b></a> | <a href="README_CN.md">中文</a>
</p>
... full English content ...

<!-- README_CN.md (Chinese) -->
# AutoClicker
<p align="center">
  <a href="README.md">English</a> | <a href="README_CN.md"><b>中文</b></a>
</p>
... full Chinese content ...
```

This approach is cleaner than `<details>` fold/unfold — one language per page, no visual clutter, works on every GitHub viewer including mobile.

**Alternative: `<details>` single-page (use sparingly).** GitHub renders `<details>` as collapsible sections. Put `open` on the default language:

```markdown
<details open>
<summary><b>English</b></summary>
... English content ...
</details>

<details>
<summary><b>中文</b></summary>
... Chinese content ...
</details>
```

Downside: both languages still load on one page (long scroll), and folding behavior varies across GitHub clients.

### GitHub README Video/GIF Embedding

**`<video>` tags are silently stripped by GitHub.** The only reliable way to get auto-playing media in a README is an **animated GIF**.

**Movie files (.mp4) >5MB are blocked** by GitHub with "Sorry about that, but we can't show files that are this big right now." Compressed MP4s under ~1MB may work as clickable links.

**✅ Best approach: Convert MP4 to GIF for inline README playback.**

```bash
# 720p, 15fps, optimized palette — good for screen recordings
ffmpeg -y -i input.mp4 \
  -vf "fps=15,scale=720:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=diff[p];[s1][p]paletteuse=dither=bayer:bayer_scale=5" \
  -loop 0 output.gif
```

- `fps=15`: smooth enough for UI demos
- `scale=720:-1`: 720px wide, proportional height
- `palettegen=stats_mode=diff` + `paletteuse=dither=bayer`: best quality for screen capture content
- Typical size: ~3MB for 30s screen recording

Then embed in README:
```html
<p align="center">
  <img src="demo.gif" alt="Demo" width="100%">
</p>
```

**Alternative (if GIF too large):** Use a clickable thumbnail image that links to the raw video file:
```html
<a href="https://github.com/user/repo/blob/main/demo.mp4">
  <img src="logo.png" alt="▶ Watch Demo" width="400">
</a>
```
Raw `.mp4` URLs on GitHub play natively in browsers when clicked.

## When NOT to Use This Pattern

- Web apps with multiple pages → use a proper i18n framework (next-intl, i18next)
- Projects with 5+ languages → gettext/.po files scale better
- User-facing product strings that need translator workflows → .po + Weblate/Crowdin

## Related Patterns

- **Cross-platform desktop notifications**: see `references/cross-platform-notify.md` for `platform.system()` three-branch pattern (macOS/Windows/Linux).
- **GitHub Release via API**: see `references/github-release-api.md` for creating releases with curl + execute_code.
