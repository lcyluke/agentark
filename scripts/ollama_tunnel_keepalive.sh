#!/bin/bash
# GB10 Ollama SSH隧道保活 — 每2分钟检查+自动重连
# Usage: hermes cron create "every 2m" --script scripts/ollama_tunnel_keepalive.sh --no-agent

PORT=11434
TUNNEL_HOST="pm02@16.146.125.163"
TUNNEL_PORT=6023
KEY="$HOME/Desktop/2026workspace/spark.pem"

# Check if tunnel is alive (port listening AND API responds)
if lsof -ti :$PORT > /dev/null 2>&1; then
    if curl -s --max-time 5 http://localhost:$PORT/api/tags > /dev/null 2>&1; then
        exit 0  # All good, silent
    fi
fi

# Tunnel is down — reconnect
echo "[ollama-tunnel] $(date): Reconnecting..."
ssh -i "$KEY" \
    -o StrictHostKeyChecking=no \
    -o ConnectTimeout=10 \
    -o ServerAliveInterval=30 \
    -o ExitOnForwardFailure=yes \
    -L ${PORT}:localhost:${PORT} \
    ${TUNNEL_HOST} -p ${TUNNEL_PORT} -N \
    > /tmp/ollama-tunnel.log 2>&1 &
echo "[ollama-tunnel] PID: $!"
