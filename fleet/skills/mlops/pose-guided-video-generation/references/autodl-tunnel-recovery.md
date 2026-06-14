# AutoDL SSH Tunnel Recovery

When the SSH tunnel to AutoDL dies (exit 255, "Connection closed by remote host"), the inference server process may also be gone.

## Preferred approach: self-healing daemon

Use `scripts/autodl-tunnel.sh` as a daemon with exponential backoff. It automatically reconnects after tunnel drops.

```bash
scripts/autodl-tunnel.sh start    # start daemon (idempotent)
scripts/autodl-tunnel.sh status   # check status
scripts/autodl-tunnel.sh stop     # stop daemon
```

**Key design decisions:**
- Password read from `~/.hermes/.autodl_pass` (chmod 600) — never in command line
- Exponential backoff: 10s → 20s → 40s → ... → 300s max
- `SSH ServerAliveInterval=30` + `ServerAliveCountMax=3` for keepalive
- Kills old tunnels + daemon on restart via `pkill -P`

## Low-noise health monitoring with cron

Do NOT run the SSH tunnel as a Hermes background process — when the tunnel dies, Hermes shows the raw `sshpass -p 'PASSWORD' ... Connection closed` in your notification stream, which leaks the password.

Instead, use a **no_agent=true** cron job with a Python health-check script. The script:
- Calls `http://localhost:8765/health` every N minutes
- Only outputs a message when state CHANGES (up→down or down→up)
- Has a cooldown period (300s) to avoid re-notifying the same state
- Uses friendly messages like `🔴 AutoDL 隧道已断开` instead of raw SSH errors

```bash
hermes cron create "every 2m" --name "AutoDL健康监控" \
  --no-agent --script autodl_health.py --deliver origin
```

The script template is at the project level — search for `autodl_health.py`. Key traits:
- State file at `/tmp/autodl_tunnel_state` tracks last status + timestamp
- `should_notify(status, prev_state)` enforces cooldown
- Empty stdout = silent (no notification sent to user)

## Manual recovery (if daemon isn't running)

### Symptom

```bash
curl http://127.0.0.1:8765/infer  # → connection refused / exit code 7
ps aux | grep 'ssh.*8765'        # → no tunnel process
```

### Recovery Sequence

#### 1. Verify host is alive

```bash
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no -o ConnectTimeout=10 -p PORT root@HOST "echo ALIVE && nvidia-smi --query-gpu=name,memory.used,memory.total --format=csv,noheader"
```

#### 2. Check inference server process

```bash
sshpass -p 'PASSWORD' ssh -p PORT root@HOST "ps aux | grep -i infer | grep -v grep; tail -5 /tmp/mimic_server.log"
```

#### 3. Start server if needed (use absolute path to python3)

```bash
sshpass -p 'PASSWORD' ssh -p PORT root@HOST \
  "cd /root/autodl-tmp/MimicMotion && nohup /root/miniconda3/bin/python /root/autodl-tmp/MimicMotion/infer_server.py > /tmp/mimic_server.log 2>&1 &"
```

Wait ~20s for model load. Verify: `tail -10 /tmp/mimic_server.log` should show "Application startup complete" and "Ready. VRAM: XXGB".

#### 4. Start daemon

```bash
scripts/autodl-tunnel.sh start
```

#### 5. Verify end-to-end

```bash
curl -s http://127.0.0.1:8765/health  # → {"ok":true,"vram_gb":4.5}
```

## Why this fails silently

- AutoDL SSH relay drops idle connections after ~30 minutes
- Tunnel `-N` flag means it forks silently
- The `infer_server.py` process may survive the tunnel dying
- `python3` is NOT on AutoDL's default PATH — always use `/root/miniconda3/bin/python`
