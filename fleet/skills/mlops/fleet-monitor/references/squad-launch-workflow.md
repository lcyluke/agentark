# Dev Squad Launch Workflow

## How to launch development agents

### One command (all 5 at once)
```bash
apex squad start
```
Opens 5 new macOS Terminal windows, each running `hermes -p <agent-name> chat`.

### Single agent
```bash
frontend-dev chat
# or
architect chat
```
Opens in the current Terminal — the wrapper script at `~/.local/bin/<name>` runs
`exec hermes -p <name> "$@"`.

## Launching via background PTY (for testing/monitoring)

When launching agents via `terminal(pty=True, background=True)`:

1. Start the agent:
```
terminal("frontend-dev chat", pty=True, background=True)
# Returns session_id
```

2. Verify it's ready by checking output for the prompt indicator:
```
process(action="poll", session_id="<id>")
# Look for "<agent-name> ❯" in output_preview
```

3. Send commands:
```
process(action="submit", session_id="<id>", data="your message here")
```

4. Wait for completion (depends on response length and model speed):
```
process(action="poll", session_id="<id>")
# The agent may take 30-90s for a complex response
```

5. Kill when done:
```
process(action="kill", session_id="<id>")
```

### Pitfalls
- **PTY output in background mode** contains ANSI escape codes and control
  characters — it's not human-readable via `poll()` or `log()`. The output is
  correctly rendered when connected to a real terminal.
- **`wait()` can timeout** before the agent finishes responding. Use `poll()`
  in a loop or check `output_preview` for the prompt indicator.
- **Process may appear "stuck"** while the model is generating — check for
  token count increasing in `output_preview` to confirm progress.
- **Agents accumulate state** across turns in the same session. For a clean
  state, kill the process and start a new one.
- **`notify_on_complete`** combined with `watch_patterns` lets you get
  notified when the agent produces specific output (e.g. "brainstorming" or
  "❯").

## Verifying methodology chain activation

After sending a development prompt to an agent, verify the chain activates:
1. Check output_preview for `📚 brainstorming` or similar skill invocation
2. The agent should ask clarifying questions before writing any code
3. If it starts coding immediately, the hard gate is not working
