#!/bin/bash
# setup-local-ai.sh — cài llama.cpp (build từ source) + tải model GGUF
# đã quantize, chạy được model 5-9B trên máy yếu (CPU, 8GB RAM trở lên).
#
# Chạy: bash setup-local-ai.sh [tên-model]
#   tên-model mặc định: qwen2.5-7b   (xem lựa chọn trong ai/models.md)

set -e

MODEL_CHOICE="${1:-qwen2.5-7b}"
INSTALL_DIR="/opt/grom-linux/ai"
MODEL_DIR="$INSTALL_DIR/models"

echo "== Cài gói build cần thiết =="
sudo apt update
sudo apt install -y build-essential cmake git curl libcurl4-openssl-dev

echo "== Clone và build llama.cpp (từ GitHub, không dùng bản dựng sẵn) =="
sudo mkdir -p "$INSTALL_DIR"
sudo chown "$(whoami)" "$INSTALL_DIR"
cd "$INSTALL_DIR"

if [ ! -d llama.cpp ]; then
    git clone --depth 1 https://github.com/ggerganov/llama.cpp.git
fi
cd llama.cpp

# Build CPU-only, tối ưu cho máy yếu (không cần GPU/CUDA).
# -DGGML_NATIVE=ON: tận dụng tập lệnh CPU của chính máy (AVX2/NEON...) để nhanh hơn,
# tiết kiệm năng lượng hơn vì ít chu kỳ CPU hơn cho cùng 1 token.
cmake -B build -DGGML_NATIVE=ON -DCMAKE_BUILD_TYPE=Release
cmake --build build --config Release -j"$(nproc)" --target llama-server llama-cli

echo "== Tải model GGUF đã quantize =="
mkdir -p "$MODEL_DIR"
cd "$MODEL_DIR"

case "$MODEL_CHOICE" in
    qwen2.5-7b)
        URL="https://huggingface.co/Qwen/Qwen2.5-7B-Instruct-GGUF/resolve/main/qwen2.5-7b-instruct-q4_k_m.gguf"
        FILE="qwen2.5-7b-instruct-q4_k_m.gguf"
        ;;
    qwen2.5-3b)
        URL="https://huggingface.co/Qwen/Qwen2.5-3B-Instruct-GGUF/resolve/main/qwen2.5-3b-instruct-q4_k_m.gguf"
        FILE="qwen2.5-3b-instruct-q4_k_m.gguf"
        ;;
    llama3.1-8b)
        URL="https://huggingface.co/bartowski/Meta-Llama-3.1-8B-Instruct-GGUF/resolve/main/Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
        FILE="Meta-Llama-3.1-8B-Instruct-Q4_K_M.gguf"
        ;;
    *)
        echo "Model không nhận diện được: $MODEL_CHOICE"
        echo "Xem ai/models.md để biết các lựa chọn hợp lệ."
        exit 1
        ;;
esac

if [ ! -f "$FILE" ]; then
    echo "Đang tải $FILE ..."
    curl -L -o "$FILE" "$URL"
else
    echo "$FILE đã tồn tại, bỏ qua tải lại."
fi

ln -sf "$MODEL_DIR/$FILE" "$MODEL_DIR/current.gguf"

echo "== Hoàn tất =="
echo "Model hiện tại: $MODEL_DIR/current.gguf"
echo "Chạy server bằng: bash grom-ai-server.sh"
