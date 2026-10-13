"""
system_monitor.py — đọc thông số hệ thống nhẹ, không cần thư viện ngoài.
Dùng /proc và /sys trực tiếp để tốn ít tài nguyên nhất có thể
(đúng tinh thần "tiết kiệm năng lượng" của GROM LINUX).
"""
import glob
import time


class SystemMonitor:
    def __init__(self):
        self._prev_idle = 0
        self._prev_total = 0

    # ---------- CPU ----------
    def cpu_percent(self):
        """Đọc /proc/stat, tính % CPU dùng kể từ lần gọi trước (không sleep/blocking)."""
        try:
            with open("/proc/stat") as f:
                parts = f.readline().split()[1:]
            values = list(map(int, parts))
            idle = values[3] + values[4]  # idle + iowait
            total = sum(values)

            d_idle = idle - self._prev_idle
            d_total = total - self._prev_total
            self._prev_idle, self._prev_total = idle, total

            if d_total <= 0:
                return 0.0
            return round(100.0 * (1 - d_idle / d_total), 1)
        except Exception:
            return 0.0

    # ---------- RAM ----------
    def ram_percent(self):
        try:
            meminfo = {}
            with open("/proc/meminfo") as f:
                for line in f:
                    key, val = line.split(":")
                    meminfo[key.strip()] = int(val.strip().split()[0])
            total = meminfo.get("MemTotal", 1)
            available = meminfo.get("MemAvailable", total)
            used_pct = round(100.0 * (total - available) / total, 1)
            return used_pct
        except Exception:
            return 0.0

    # ---------- Pin / Nguồn điện ----------
    def battery_info(self):
        """Trả về (phần trăm pin, đang sạc hay không). None nếu không có pin (desktop)."""
        bat_dirs = glob.glob("/sys/class/power_supply/BAT*")
        if not bat_dirs:
            return None
        bat = bat_dirs[0]
        try:
            with open(f"{bat}/capacity") as f:
                capacity = int(f.read().strip())
            with open(f"{bat}/status") as f:
                status = f.read().strip()
            return capacity, status in ("Charging", "Full")
        except Exception:
            return None

    def on_ac_power(self):
        """True nếu đang cắm sạc/nguồn điện AC, False nếu dùng pin."""
        ac_dirs = glob.glob("/sys/class/power_supply/A*")
        for ac in ac_dirs:
            try:
                with open(f"{ac}/online") as f:
                    if f.read().strip() == "1":
                        return True
            except Exception:
                continue
        return True  # mặc định coi như máy bàn (luôn có điện)

    # ---------- Governor hiện tại ----------
    def current_governor(self):
        try:
            with open(
                "/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor"
            ) as f:
                return f.read().strip()
        except Exception:
            return "n/a"
