#!/bin/bash
# GB10 Hermes API + Ollama 双隧道保活
# 端口: 11434 (Ollama) + 8989 (Hermes API)

for PORT in 11434 8989; do
    if lsof -ti :$PORT > /dev/null 2>&1; then
        continue  # alive
    fi
    echo "[tunnel] $(date): Reconnecting port $PORT..."
    ssh -i "$HOME/Desktop/2026workspace/spark.pem" \
        -o StrictHostKeyChecking=no \
        -o ConnectTimeout=10 \
        -o ServerAliveInterval=30 \
        -o ExitOnForwardFailure=yes \
        -L ${PORT}:localhost:${PORT} \
        pm02@16.146.125.163 -p 6023 -N \
        > /tmp/gb10-tunnel-${PORT}.log 2>&1 &
done
