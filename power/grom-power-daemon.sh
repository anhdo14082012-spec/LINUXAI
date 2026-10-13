#!/bin/bash
# grom-power-daemon.sh
# Daemon tiết kiệm năng lượng cho GROM LINUX.
# Tự động chuyển CPU governor theo nguồn điện (AC/pin), thiết lập zram,
# và cho phép ép chế độ thủ công qua file /run/grom/power-mode.
#
# Cài làm service: xem packaging/install.sh (systemd) hoặc gọi trực tiếp khi boot.

STATE_DIR="/run/grom"
MODE_FILE="$STATE_DIR/power-mode"   # chứa: auto | tietkiem | canbang | hieunang
mkdir -p "$STATE_DIR"
[ -f "$MODE_FILE" ] || echo "auto" > "$MODE_FILE"

set_governor() {
    local gov="$1"
    for cpu in /sys/devices/system/cpu/cpu[0-9]*/cpufreq/scaling_governor; do
        [ -w "$cpu" ] && echo "$gov" > "$cpu" 2>/dev/null
    done
}

on_ac_power() {
    for ac in /sys/class/power_supply/A*/online; do
        [ -f "$ac" ] && [ "$(cat "$ac")" = "1" ] && return 0
    done
    return 1  # không có cổng AC -> coi như đang dùng pin, hoặc không rõ
}

apply_profile() {
    local mode="$1"
    case "$mode" in
        tietkiem)
            set_governor "powersave"
            # Giảm độ sáng màn hình nếu có backlight
            for bl in /sys/class/backlight/*/brightness; do
                [ -w "$bl" ] || continue
                max=$(cat "$(dirname "$bl")/max_brightness")
                echo $((max * 40 / 100)) > "$bl" 2>/dev/null
            done
            ;;
        hieunang)
            set_governor "performance"
            ;;
        canbang)
            set_governor "schedutil" 2>/dev/null || set_governor "ondemand"
            ;;
        auto)
            if on_ac_power; then
                set_governor "schedutil" 2>/dev/null || set_governor "ondemand"
            else
                set_governor "powersave"
            fi
            ;;
    esac
}

setup_zram() {
    # Dùng zram thay vì swap trên đĩa -> đỡ tốn điện ghi đĩa, nhanh hơn swap thường.
    command -v zramctl >/dev/null || return
    if ! zramctl | grep -q zram0; then
        mem_total_kb=$(awk '/MemTotal/ {print $2}' /proc/meminfo)
        zram_size_kb=$((mem_total_kb / 2))  # zram = 50% RAM
        dev=$(zramctl --find --size "${zram_size_kb}K")
        mkswap "$dev" >/dev/null 2>&1
        swapon "$dev" -p 100 2>/dev/null
    fi
}

echo "[grom-power] Daemon khởi động, thiết lập zram..."
setup_zram

echo "[grom-power] Vòng lặp theo dõi chế độ nguồn (kiểm tra mỗi 10s)..."
while true; do
    mode=$(cat "$MODE_FILE" 2>/dev/null || echo "auto")
    apply_profile "$mode"
    sleep 10
done
