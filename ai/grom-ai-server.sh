#!/bin/bash
# grom-ai-server.sh — chạy llama-server với tham số tự tính theo phần cứng,
# ưu tiên chạy mượt + tiết kiệm năng lượng trên máy yếu.

INSTALL_DIR="/opt/grom-linux/ai"
MODEL="$INSTALL_DIR/models/current.gguf"
BIN="$INSTALL_DIR/llama.cpp/build/bin/llama-server"
PORT=8089

if [ ! -f "$MODEL" ]; then
    echo "Chưa có model. Chạy setup-local-ai.sh trước."
    exit 1
fi
if [ ! -x "$BIN" ]; then
    echo "Chưa build llama-server. Chạy setup-local-ai.sh trước."
    exit 1
fi

CORES=$(nproc)
# Để lại 1 core cho hệ thống/UI, tránh giật desktop khi AI đang chạy —
# đúng tinh thần "mượt trên máy yếu" (ưu tiên trải nghiệm hơn tốc độ tối đa).
THREADS=$((CORES > 1 ? CORES - 1 : 1))

MEM_TOTAL_MB=$(awk '/MemTotal/ {print int($2/1024)}' /proc/meminfo)

# Context ngắn hơn trên máy ít RAM để tránh swap (swap = chậm + tốn điện ghi đĩa)
if [ "$MEM_TOTAL_MB" -lt 6000 ]; then
    CTX=1024
    BATCH=128
elif [ "$MEM_TOTAL_MB" -lt 12000 ]; then
    CTX=2048
    BATCH=256
else
    CTX=4096
    BATCH=512
fi

echo "== GROM AI Server =="
echo "Model:   $MODEL"
echo "Threads: $THREADS / $CORES cores"
echo "RAM:     ${MEM_TOTAL_MB}MB -> context=$CTX, batch=$BATCH"
echo "Port:    $PORT"
echo ""
echo "Nice -n 10: hạ ưu tiên CPU của AI so với desktop để UI luôn mượt."

exec nice -n 10 "$BIN" \
    --model "$MODEL" \
    --threads "$THREADS" \
    --ctx-size "$CTX" \
    --batch-size "$BATCH" \
    --port "$PORT" \
    --host 127.0.0.1
