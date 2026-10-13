#!/bin/bash
# build-iso.sh — build file .iso GROM LINUX bằng Debian live-build.
# Chạy trực tiếp trên Linux, hoặc gọi tự động bởi build-iso.bat (Windows -> WSL).
#
# Chạy: sudo bash build-iso.sh

set -e

if [ "$EUID" -ne 0 ]; then
    echo "Script này cần quyền root. Chạy lại với: sudo bash build-iso.sh"
    exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
cd "$SCRIPT_DIR"

echo "== Cài live-build và công cụ cần thiết =="
apt-get update
apt-get install -y --no-install-recommends \
    live-build debootstrap xorriso squashfs-tools ca-certificates \
    syslinux syslinux-common syslinux-utils isolinux \
    grub-pc-bin grub-efi-amd64-bin mtools dosfstools

echo "== Dọn cấu hình build cũ (nếu có) =="
lb clean --purge 2>/dev/null || true
rm -rf config .build *.iso

echo "== Khởi tạo cấu hình live-build (nền Debian bookworm) =="
lb config \
    --distribution bookworm \
    --architectures amd64 \
    --binary-images iso-hybrid \
    --archive-areas "main contrib non-free non-free-firmware" \
    --iso-application "GROM LINUX" \
    --iso-volume "GROM_LINUX" \
    --iso-publisher "GROM LINUX Project" \
    --debian-installer none \
    --memtest none

mkdir -p config/package-lists config/includes.chroot config/hooks/live

echo "== Ghi danh sách gói cần cài trong ISO =="
cat > config/package-lists/grom.list.chroot << 'PKGEOF'
python3-gi
python3-gi-cairo
gir1.2-gtk-4.0
gir1.2-adw-1
openbox
lightdm
xterm
pcmanfm
nmap
wireshark
john
aircrack-ng
tlp
zram-tools
build-essential
cmake
git
curl
sudo
network-manager
xserver-xorg
lightdm-gtk-greeter
PKGEOF

echo "== Copy GROM shell + power + AI vào rootfs của ISO =="
mkdir -p config/includes.chroot/opt/grom-linux
cp -r "$PROJECT_ROOT/shell" config/includes.chroot/opt/grom-linux/
cp -r "$PROJECT_ROOT/power" config/includes.chroot/opt/grom-linux/
cp -r "$PROJECT_ROOT/ai" config/includes.chroot/opt/grom-linux/

mkdir -p config/includes.chroot/usr/share/xsessions
cp "$PROJECT_ROOT/session/grom.desktop" config/includes.chroot/usr/share/xsessions/

mkdir -p config/includes.chroot/usr/bin
cp "$PROJECT_ROOT/session/grom-session-start" config/includes.chroot/usr/bin/
cp "$PROJECT_ROOT/power/grom-power-daemon.sh" config/includes.chroot/usr/bin/
cp "$PROJECT_ROOT/ai/grom-ai-server.sh" config/includes.chroot/usr/bin/

mkdir -p config/includes.chroot/etc/tlp.d
cp "$PROJECT_ROOT/power/tlp-grom.conf" config/includes.chroot/etc/tlp.d/90-grom.conf

mkdir -p config/includes.chroot/etc/systemd/system
cp "$PROJECT_ROOT/power/grom-power.service" config/includes.chroot/etc/systemd/system/

echo "== Ghi hook thiết lập GROM khi tạo rootfs (chạy trong chroot lúc build) =="
cat > config/hooks/live/0100-grom-setup.hook.chroot << 'HOOKEOF'
#!/bin/sh
set -e

chmod +x /usr/bin/grom-session-start
chmod +x /usr/bin/grom-power-daemon.sh
[ -f /usr/bin/grom-ai-server.sh ] && chmod +x /usr/bin/grom-ai-server.sh

systemctl enable grom-power.service
systemctl enable tlp.service
systemctl set-default graphical.target

mkdir -p /run/grom
echo "auto" > /run/grom/power-mode
chmod 1777 /run/grom

# Đặt GROM làm session mặc định trong LightDM
mkdir -p /etc/lightdm
cat >> /etc/lightdm/lightdm.conf << 'LIGHTDMEOF'

[Seat:*]
user-session=grom
LIGHTDMEOF

# Tài khoản demo cho bản live — ĐỔI MẬT KHẨU khi cài lên đĩa thật
useradd -m -s /bin/bash -G sudo grom 2>/dev/null || true
echo "grom:grom" | chpasswd
HOOKEOF
chmod +x config/hooks/live/0100-grom-setup.hook.chroot

echo "== Build ISO (có thể mất 15-40 phút tùy máy/mạng) =="
lb build

echo "== Copy file .iso ra thư mục output/ =="
mkdir -p "$SCRIPT_DIR/output"
ISO_FILE=$(ls live-image-*.hybrid.iso 2>/dev/null | head -n1)
if [ -z "$ISO_FILE" ]; then
    ISO_FILE=$(ls ./*.iso 2>/dev/null | head -n1)
fi

if [ -n "$ISO_FILE" ]; then
    cp "$ISO_FILE" "$SCRIPT_DIR/output/grom-linux.iso"
    echo ""
    echo "== HOÀN TẤT =="
    echo "File ISO: $SCRIPT_DIR/output/grom-linux.iso"
    echo "Tài khoản demo trong bản live: grom / grom"
else
    echo "Không tìm thấy file .iso sau khi build. Kiểm tra log lỗi ở trên."
    exit 1
fi
