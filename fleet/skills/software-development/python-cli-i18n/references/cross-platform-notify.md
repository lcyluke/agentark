# Cross-Platform Desktop Notification

Three-branch notification using `platform.system()`. Best-effort — notification is cosmetic, console log is the real record.

```python
import platform
import os
import subprocess

def notify(title: str, msg: str):
    """Send desktop notification. Falls back silently on failure."""
    system = platform.system()

    try:
        if system == "Darwin":
            # macOS: osascript
            os.system(
                f'osascript -e \'display notification "{msg}" with title "{title}"\''
            )
        elif system == "Windows":
            # Windows: try win10toast, fallback to ctypes MessageBox
            try:
                from win10toast import ToastNotifier
                ToastNotifier().show_toast(title, msg, duration=3, threaded=True)
            except ImportError:
                import ctypes
                ctypes.windll.user32.MessageBoxW(0, msg, title, 0x40)
        else:
            # Linux: notify-send
            subprocess.run(
                ["notify-send", title, msg],
                capture_output=True, timeout=3
            )
    except Exception:
        pass  # notification is best-effort
```

## Platform Notes

| Platform | Primary Method | Fallback | Extra Dep |
|----------|---------------|----------|-----------|
| macOS | `osascript display notification` | — | None |
| Windows | `win10toast` | `ctypes MessageBoxW` | `pip install win10toast` |
| Linux | `notify-send` (libnotify) | — | `apt install libnotify-bin` |

## Pitfalls

- **Never block on notification** — use `threaded=True` on Windows, `capture_output` + `timeout` on Linux.
- **Notification is best-effort** — the console log (`log.info(...)`) is the source of truth. If notify fails, the user still sees the click in the log.
- **Don't import platform-specific modules at the top** — `win10toast` will crash `import` on macOS/Linux. Import inside the function body.
