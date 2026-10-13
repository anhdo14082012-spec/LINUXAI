#!/bin/bash
# install.sh — cài GROM LINUX desktop shell + power daemon + AI (tùy chọn)
# lên một hệ thống Debian/Ubuntu-based, dùng để test trước khi tích hợp
# vào ISO GROM LINUX riêng.
#
# Chạy: sudo bash install.sh [--with-ai [tên-model]]

set -e
WITH_AI=0
MODEL_CHOICE="qwen2.5-7b"
if [ "$1" = "--with-ai" ]; then
    WITH_AI=1
    [ -n "$2" ] && MODEL_CHOICE="$2"
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "== Cài gói phụ thuộc hệ thống =="
apt update
apt install -y \
    python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1 \
    openbox lightdm xterm pcmanfm \
    nmap wireshark john aircrack-ng \
    tlp zram-tools

echo "== Copy GROM shell vào /opt/grom-linux =="
mkdir -p /opt/grom-linux
cp -r "$SCRIPT_DIR/../shell" /opt/grom-linux/

echo "== Cài session file =="
cp "$SCRIPT_DIR/../session/grom.desktop" /usr/share/xsessions/grom.desktop
cp "$SCRIPT_DIR/../session/grom-session-start" /usr/bin/grom-session-start
chmod +x /usr/bin/grom-session-start

echo "== Cài power daemon (tiết kiệm năng lượng) =="
cp "$SCRIPT_DIR/../power/grom-power-daemon.sh" /usr/bin/grom-power-daemon.sh
chmod +x /usr/bin/grom-power-daemon.sh
cp "$SCRIPT_DIR/../power/grom-power.service" /etc/systemd/system/grom-power.service
cp "$SCRIPT_DIR/../power/tlp-grom.conf" /etc/tlp.d/90-grom.conf
systemctl daemon-reload
systemctl enable --now grom-power.service
systemctl enable --now tlp.service

# Cho phép người dùng thường ghi /run/grom (chế độ nguồn từ Settings app)
mkdir -p /run/grom
chmod 1777 /run/grom

if [ "$WITH_AI" = "1" ]; then
    echo "== Cài AI cục bộ (model: $MODEL_CHOICE) =="
    cp "$SCRIPT_DIR/../ai/grom-ai-server.sh" /usr/bin/grom-ai-server.sh
    chmod +x /usr/bin/grom-ai-server.sh
    bash "$SCRIPT_DIR/../ai/setup-local-ai.sh" "$MODEL_CHOICE"
    cp "$SCRIPT_DIR/../ai/grom-ai.service" /etc/systemd/system/grom-ai.service
    systemctl daemon-reload
    systemctl enable --now grom-ai.service
fi

echo "== Hoàn tất =="
echo "Đăng xuất, ở màn hình đăng nhập chọn session 'GROM LINUX', rồi đăng nhập lại."
echo "Đổi chế độ nguồn: mở app 'Cài đặt' trong GROM LINUX, hoặc:"
echo "  echo tietkiem | sudo tee /run/grom/power-mode"
if [ "$WITH_AI" = "1" ]; then
    echo "AI server đang chạy ở 127.0.0.1:8089 (service grom-ai.service)."
fi
