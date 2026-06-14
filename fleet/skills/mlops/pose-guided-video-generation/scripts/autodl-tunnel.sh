#!/bin/bash
# AutoDL SSH 隧道 — 自愈守护进程（带指数退避重连）
# 启动后常驻后台，自动重连断开的隧道。
#
# 用法:
#   start   启动守护进程（幂等）
#   stop    停止守护进程
#   restart 重启守护进程
#   status  查看状态
#
# 密码从 ~/.hermes/.autodl_pass 读取（chmod 600），不在命令行泄露。

AUTODL_HOST="${AUTODL_HOST:-connect.westb.seetacloud.com}"
AUTODL_PORT="${AUTODL_PORT:-16786}"
LOCAL_PORT="${LOCAL_PORT:-8765}"
REMOTE_PORT="${REMOTE_PORT:-8765}"
PID_FILE="/tmp/autodl_tunnel_daemon.pid"
LOG_FILE="/tmp/autodl_tunnel.log"
MAX_BACKOFF=300
INITIAL_BACKOFF=10

# 从密钥文件读取密码（避免命令行泄露）
load_pass() {
    if [ -n "$AUTODL_PASS" ]; then return; fi
    for src in ~/.hermes/.autodl_pass ~/.autodl_pass /tmp/autodl_pass; do
        if [ -f "$src" ]; then
            AUTODL_PASS=$(head -1 "$src")
            chmod 600 "$src" 2>/dev/null
            return
        fi
    done
    echo "[$(date '+%m-%d %H:%M:%S')] ⚠️ 未找到密码文件" >> "$LOG_FILE"
}

log() { echo "[$(date '+%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"; }

start_daemon() {
    load_pass
    [ -z "$AUTODL_PASS" ] && return 1

    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        echo "✅ 守护进程已在运行 (PID $(cat $PID_FILE))"
        return 0
    fi

    log "🚀 守护进程启动 · $AUTODL_HOST:$AUTODL_PORT → localhost:$LOCAL_PORT"

    (
        backoff=$INITIAL_BACKOFF
        while true; do
            log "🔗 建立 SSH 隧道..."
            sshpass -p "$AUTODL_PASS" ssh \
                -o StrictHostKeyChecking=no \
                -o ServerAliveInterval=30 \
                -o ServerAliveCountMax=3 \
                -o ConnectTimeout=15 \
                -N -L "$LOCAL_PORT:localhost:$REMOTE_PORT" \
                -p "$AUTODL_PORT" "root@$AUTODL_HOST" 2>> "$LOG_FILE"

            log "🔌 隧道断开 · ${backoff}s 后重连"
            sleep "$backoff"
            backoff=$((backoff * 2))
            [ $backoff -gt $MAX_BACKOFF ] && backoff=$MAX_BACKOFF
        done
    ) &

    echo $! > "$PID_FILE"
    sleep 2

    if kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        log "✅ 守护进程运行中 (PID $(cat $PID_FILE))"
        echo "✅ 守护进程已启动"
    else
        log "❌ 启动失败"; rm -f "$PID_FILE"
        echo "❌ 启动失败，查看日志: $LOG_FILE"; return 1
    fi
}

stop_daemon() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if kill -0 "$PID" 2>/dev/null; then
            pkill -P "$PID" 2>/dev/null
            kill "$PID" 2>/dev/null
            log "🛑 守护进程已停止 (PID $PID)"
            echo "✅ 隧道已停止"
        fi
        rm -f "$PID_FILE"
    else
        echo "没有运行中的守护进程"
    fi
    pkill -f "ssh.*${LOCAL_PORT}.*localhost.*${AUTODL_PORT}" 2>/dev/null
}

show_status() {
    if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
        PID=$(cat "$PID_FILE")
        if curl -s --connect-timeout 3 "http://localhost:$LOCAL_PORT/health" >/dev/null 2>&1; then
            echo "🟢 隧道在线 · PID $PID · localhost:$LOCAL_PORT"
        else
            echo "🟡 守护进程运行中但未通 · PID $PID · 正在重连"
        fi
    else
        echo "🔴 隧道离线"
    fi
}

case "${1:-status}" in
    start)   start_daemon ;;
    stop)    stop_daemon ;;
    restart) stop_daemon; sleep 2; start_daemon ;;
    status)  show_status ;;
    *)       echo "用法: $0 {start|stop|restart|status}" ;;
esac
