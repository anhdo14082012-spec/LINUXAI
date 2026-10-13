#!/usr/bin/env python3
"""
GROM Settings — đổi chế độ nguồn điện (Tiết kiệm / Cân bằng / Hiệu năng)
và xem thông số hệ thống. Ghi lựa chọn vào /run/grom/power-mode để
power/grom-power-daemon.sh đọc và áp dụng.
"""
import gi
import sys
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from system_monitor import SystemMonitor

MODE_FILE = Path("/run/grom/power-mode")
MODES = [
    ("tietkiem", "Tiết kiệm năng lượng"),
    ("canbang", "Cân bằng"),
    ("hieunang", "Hiệu năng cao"),
    ("auto", "Tự động (theo AC/pin)"),
]


class SettingsWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Cài đặt — GROM LINUX")
        self.set_default_size(480, 420)
        self.monitor = SystemMonitor()

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        root.set_margin_top(16)
        root.set_margin_bottom(16)
        root.set_margin_start(16)
        root.set_margin_end(16)
        self.set_content(root)

        title = Gtk.Label(label="Chế độ nguồn điện")
        title.add_css_class("title-3")
        title.set_halign(Gtk.Align.START)
        root.append(title)

        current_mode = self.read_current_mode()
        group = None
        for key, label in MODES:
            btn = Gtk.CheckButton(label=label)
            if group is None:
                group = btn
            else:
                btn.set_group(group)
            btn.set_active(key == current_mode)
            btn.connect("toggled", self.on_mode_toggled, key)
            root.append(btn)

        sep = Gtk.Separator()
        root.append(sep)

        stats_title = Gtk.Label(label="Thông số hệ thống")
        stats_title.add_css_class("title-3")
        stats_title.set_halign(Gtk.Align.START)
        root.append(stats_title)

        self.stats_label = Gtk.Label()
        self.stats_label.set_halign(Gtk.Align.START)
        self.stats_label.set_wrap(True)
        root.append(self.stats_label)

        self.update_stats()
        GLib.timeout_add_seconds(2, self.update_stats)

    def read_current_mode(self):
        try:
            return MODE_FILE.read_text().strip()
        except Exception:
            return "auto"

    def on_mode_toggled(self, button, key):
        if not button.get_active():
            return
        try:
            MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
            MODE_FILE.write_text(key)
        except PermissionError:
            # /run/grom có thể cần quyền root tùy cấu hình hệ thống
            print("Cần quyền ghi vào /run/grom — kiểm tra lại cài đặt service.")

    def update_stats(self):
        cpu = self.monitor.cpu_percent()
        ram = self.monitor.ram_percent()
        gov = self.monitor.current_governor()
        bat = self.monitor.battery_info()

        lines = [
            f"CPU: {cpu}%",
            f"RAM: {ram}%",
            f"CPU governor: {gov}",
        ]
        if bat:
            pct, charging = bat
            lines.append(f"Pin: {pct}%{' (đang sạc)' if charging else ''}")
        else:
            lines.append("Pin: không có (máy bàn)")

        self.stats_label.set_label("\n".join(lines))
        return True


class SettingsApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.grom.linux.settings")

    def do_activate(self):
        win = SettingsWindow(self)
        win.present()


if __name__ == "__main__":
    app = SettingsApp()
    app.run([])
