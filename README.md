# GROM LINUX — Desktop Shell + Tiết kiệm năng lượng + AI cục bộ

Desktop UI đầy đủ chức năng cho GROM LINUX: sidebar phân loại app, tìm
kiếm nhanh, system monitor trực tiếp, chuyển chế độ nguồn 1 chạm, kèm
bộ công cụ pentest hợp pháp và trợ lý AI chạy hoàn toàn cục bộ (không
gửi dữ liệu ra ngoài máy), tối ưu cho máy cấu hình yếu.

> Đây là bản prototype của **lớp giao diện desktop + quản lý năng
> lượng + AI runtime**, chạy trên một distro nền Debian/Ubuntu để
> test. Phần kernel/base system riêng (build từ source, không dùng
> distro khác) nằm ở giai đoạn kế tiếp — xem phần "Hướng tiếp theo".

## Cấu trúc thư mục

```
grom-linux/
├── README.md
├── shell/                        # desktop shell chính
│   ├── grom_shell.py             # taskbar + sidebar + tìm kiếm + tab + system monitor
│   ├── system_monitor.py         # đọc CPU/RAM/pin từ /proc, /sys (không thư viện ngoài)
│   ├── apps/
│   │   ├── nmap_gui.py           # GUI quét mạng bằng Nmap
│   │   ├── ai_assistant.py       # chat GUI với AI cục bộ (llama-server)
│   │   └── settings_panel.py     # đổi chế độ nguồn, xem thông số hệ thống
│   └── config/
│       └── apps.json             # danh sách app trong sidebar/launcher
├── power/                        # tiết kiệm năng lượng
│   ├── grom-power-daemon.sh      # tự chuyển CPU governor + zram theo nguồn điện
│   ├── grom-power.service        # systemd unit chạy daemon khi boot
│   └── tlp-grom.conf             # cấu hình TLP (USB/Wi-Fi/đĩa/PCIe tiết kiệm điện)
├── ai/                           # AI cục bộ chạy mô hình 5-9B trên máy yếu
│   ├── setup-local-ai.sh         # build llama.cpp từ GitHub + tải model GGUF
│   ├── grom-ai-server.sh         # chạy llama-server, tự tính threads/context theo máy
│   ├── grom-ai.service           # systemd unit (tùy chọn, giới hạn CPU 80%)
│   └── models.md                 # bảng chọn model theo cấu hình máy
├── session/                      # tích hợp vào display manager
│   ├── grom.desktop
│   └── grom-session-start
└── packaging/
    └── install.sh                # cài toàn bộ lên distro nền để test
```

## Cài đặt đầy đủ (shell + tiết kiệm điện + AI)

```bash
cd grom-linux/packaging
sudo bash install.sh --with-ai qwen2.5-7b
```

Không muốn cài AI (chỉ shell + tiết kiệm điện):

```bash
sudo bash install.sh
```

Sau đó đăng xuất, ở màn hình đăng nhập chọn session **GROM LINUX**.

## Chạy thử nhanh không cần cài hệ thống

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1
cd grom-linux/shell
python3 grom_shell.py
```

## 3 trục nâng cấp đã làm

### 1. Giao diện đầy đủ chức năng
- Sidebar trái phân loại theo nhóm (Hệ thống / An ninh mạng / Trợ lý AI)
- Thanh tìm kiếm app ngay trên taskbar
- CPU%, RAM%, pin hiển thị trực tiếp, cập nhật mỗi 2 giây
- Nút "⚡ Nguồn" đổi chế độ ngay trong 1 click, không cần mở terminal

### 2. Tiết kiệm năng lượng tối đa
- `grom-power-daemon.sh`: tự chuyển CPU governor (`powersave` khi dùng
  pin, `schedutil` khi cắm điện), hoặc ép thủ công qua app Cài đặt
- **zram** thay swap đĩa — giảm ghi đĩa (tốn điện hơn nhiều so với nén
  RAM), nhanh hơn swap thường
- **TLP** tuned: USB autosuspend, Wi-Fi power save khi dùng pin, APM
  đĩa thấp hơn khi dùng pin
- Giảm độ sáng màn hình tự động ở chế độ Tiết kiệm
- Dùng openbox (không panel riêng) — GROM shell là tiến trình giao
  diện duy nhất, giảm số tiến trình chạy nền

### 3. AI 5-9B chạy mượt trên máy yếu
- **llama.cpp** (build từ source GitHub, C++ thuần, không cần GPU)
- Model GGUF quantize **Q4_K_M** — 7B chỉ cần ~4.5GB RAM (xem
  `ai/models.md` để chọn theo cấu hình máy, từ 3B đến 8B)
- `grom-ai-server.sh` tự tính số luồng (để lại 1 core cho desktop) và
  context size theo RAM máy, chạy với `nice -n 10` để AI không làm
  giật UI
- Service `grom-ai.service` giới hạn CPU 80% nếu chạy nền liên tục
- Chat GUI (`ai_assistant.py`) gọi local API — **không gửi dữ liệu ra
  ngoài máy**

## Thêm công cụ mới vào launcher

Sửa `shell/config/apps.json`, thêm object:

```json
{
  "name": "Tên hiển thị",
  "cmd": "lệnh-chạy-tool",
  "icon": "icon-name",
  "category": "pentest"
}
```


```
iso-build/
├── build-iso.bat     # chạy trên Windows — double-click, tự gọi WSL
├── build-iso.sh       # script build thật (Debian live-build), chạy trên Linux/WSL
├── output/            # file grom-linux.iso xuất hiện ở đây sau khi build xong
└── README.md          # hướng dẫn chi tiết, yêu cầu, cách ghi USB/thử bằng QEMU
```

Trên Windows: double-click `iso-build/build-iso.bat` (cần WSL2 + Ubuntu
đã cài sẵn). Trên Linux: `cd iso-build && sudo bash build-iso.sh`. Chi
tiết đầy đủ xem `iso-build/README.md`.

## Hướng tiếp theo

- Build kernel Linux + BusyBox/musl riêng để có base system độc lập,
  không phụ thuộc distro nền hiện dùng để test
- Viết `grom-pkg` — package manager riêng, đóng gói toàn bộ (shell +
  power daemon + AI) thành ISO cài đặt hoàn chỉnh
- Thêm GUI wrapper cho Wireshark, John, Aircrack-ng theo mẫu `nmap_gui.py`
- Cân nhắc chuyển governor sang `powersave` mặc định toàn hệ thống khi
  không rõ máy có pin hay không, để an toàn năng lượng theo mặc định

## Lưu ý về công cụ an ninh mạng

Các công cụ tích hợp (Nmap, Wireshark, John the Ripper, Aircrack-ng...)
là phần mềm mã nguồn mở hợp pháp, dùng cho kiểm thử bảo mật trên hệ
thống bạn sở hữu hoặc được ủy quyền. Người dùng tự chịu trách nhiệm
khi sử dụng các công cụ này.
