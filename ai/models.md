# Gợi ý model AI cho GROM LINUX

Tất cả đều ở định dạng GGUF, quantize **Q4_K_M** — mức cân bằng tốt nhất
giữa chất lượng trả lời và dung lượng/tốc độ trên CPU máy yếu.

| Model | Tham số | RAM cần (Q4_K_M) | Máy phù hợp | Tên dùng với setup-local-ai.sh |
|---|---|---|---|---|
| Qwen2.5-3B-Instruct | 3B | ~2.5 GB | Máy rất yếu, 4-6GB RAM | `qwen2.5-3b` |
| Qwen2.5-7B-Instruct | 7B | ~4.5 GB | Máy yếu điển hình, 8GB RAM | `qwen2.5-7b` (mặc định) |
| Llama-3.1-8B-Instruct | 8B | ~5 GB | 8-16GB RAM | `llama3.1-8b` |

## Cách chọn

```bash
bash setup-local-ai.sh qwen2.5-7b      # mặc định, cân bằng tốt
bash setup-local-ai.sh qwen2.5-3b      # máy rất yếu (netbook, VM nhỏ)
bash setup-local-ai.sh llama3.1-8b     # máy có từ 16GB RAM trở lên
```

## Vì sao Q4_K_M, không phải Q8 hay FP16

- **FP16 (gốc):** 7B model cần ~14GB RAM — không chạy nổi trên máy yếu.
- **Q8_0:** ~7.5GB RAM cho 7B — vẫn nặng với máy 8GB (hệ thống cần RAM cho việc khác).
- **Q4_K_M:** ~4.5GB RAM cho 7B, chất lượng trả lời giảm rất ít so với Q8,
  đây là lựa chọn được cộng đồng llama.cpp khuyến nghị cho máy yếu.

## Đổi model sau khi đã cài

```bash
cd /opt/grom-linux/ai/models
ln -sf qwen2.5-3b-instruct-q4_k_m.gguf current.gguf
```

Sau đó khởi động lại `grom-ai-server.sh` (hoặc service `grom-ai.service`
nếu đã cài làm service hệ thống).
