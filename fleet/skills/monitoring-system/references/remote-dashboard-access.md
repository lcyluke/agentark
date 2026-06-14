# SSH Tunnel & Remote Access

When the Streamlit dashboard runs on a remote AutoDL/cloud server, the browser on your Mac cannot directly access `http://server-ip:8050`. Use SSH port forwarding.

## SSH Tunnel (Port Forwarding)

```bash
# Basic tunnel: forward remote :8050 to local :8050
ssh -p 32581 -L 8050:localhost:8050 root@connect.bjb2.seetacloud.com -N
```

- `-L 8050:localhost:8050` — forward remote 8050 to local 8050
- `-N` — no remote command, just maintain tunnel
- Keep this terminal window open. Close it to stop the tunnel.

Then open `http://localhost:8050` on your Mac browser.

## Passworded SSH (using sshpass)

```bash
# Install sshpass on Mac
brew install hudochenkov/sshpass/sshpass

# Create tunnel in background
sshpass -p 'PASSWORD' ssh -o StrictHostKeyChecking=no -p PORT \
  -L 8050:localhost:8050 root@HOST -N
```

## Keeping Streamlit Alive After SSH Disconnect

Running `nohup streamlit run ... &` from an SSH session will kill the child when the SSH session closes. Use `setsid` + `disown`:

```bash
sshpass -p 'PASSWORD' ssh -p PORT root@HOST '
export PATH=/root/miniconda3/bin:$PATH

# Kill old instance
pkill -f "streamlit.*monitor_app" 2>/dev/null; sleep 1

# Start with setsid to detach from SSH session
setsid streamlit run /root/monitor/dashboards/monitor_app.py \
  --server.port 8050 \
  --server.address 0.0.0.0 \
  > /root/monitor/logs/dashboard.log 2>&1 & disown

sleep 2
# Verify: should show "Running" + the streamlit URL (Local/Network/External)
ps aux | grep streamlit | grep -v grep
'
```

The streamlit output will show:
- `Local URL: http://localhost:8050` (inside server)
- `Network URL: http://172.17.0.9:8050` (internal Docker network)
- `External URL: http://106.39.200.226:8050` (public IP — use SSH tunnel instead)

## Base64 File Transfer (when SCP is slow)

When SCP times out on large files (e.g., 20KB+ Streamlit scripts), encode the file as base64 and write it directly over SSH:

```python
import base64, os

# Local machine: read and encode
with open("/path/to/file.py", "rb") as f:
    b64 = base64.b64encode(f.read()).decode()

# Write to remote server via SSH (single connection)
result = subprocess.run([
    "sshpass", "-p", "PASSWORD",
    "ssh", "-p", "PORT", "root@HOST",
    f"echo '{b64}' | base64 -d > /remote/path/file.py"
], capture_output=True, text=True, timeout=30)
```

This avoids slow SCP overhead and works reliably even on high-latency or rate-limited connections.

## Verifying Dashboard Started

```bash
# Check the log
sshpass -p 'PASSWORD' ssh -p PORT root@HOST 'cat /root/monitor/logs/dashboard.log | tail -10'

# Check process
sshpass -p 'PASSWORD' ssh -p PORT root@HOST 'ps aux | grep streamlit | grep -v grep'
```

Expected output shows streamlit URLs (Local/Network/External).

## AutoDL Environment Discovery

When connecting to a fresh AutoDL instance:

```bash
# Quick environment check
sshpass -p 'PASSWORD' ssh -p PORT root@HOST '
  echo "=== GPU ==="
  nvidia-smi --query-gpu=index,name,memory.total,memory.used,driver_version --format=csv,noheader
  echo "=== Python ==="
  ls /root/miniconda3/bin/python* 2>/dev/null
  /root/miniconda3/bin/python3 --version
  echo "=== PyTorch ==="
  /root/miniconda3/bin/python -c "import torch; print(f\"torch {torch.__version__}, CUDA {torch.version.cuda}\")" 2>/dev/null || echo "no torch"
  echo "=== Disk ==="
  df -h | grep -E "autodl-tmp|/$"
  echo "=== RAM ==="
  free -h | head -2
'
```

Key findings from this session's instance:
- **OS**: Ubuntu 22.04.4 LTS
- **Python**: 3.12.3 at `/root/miniconda3/bin/python3`
- **GPU**: NVIDIA GeForce RTX 4090 D (24564 MiB, driver 580.105.08)
- **Torch**: 2.5.1+cu124
- **CPU**: 16 cores, ~50GB RAM
- **Storage**: System `/` (~30GB)
- **Pip**: at `/root/miniconda3/bin/pip`
