#!/usr/bin/env python3
"""
Nmap GUI — wrapper đồ họa đơn giản cho Nmap, dùng trong GROM LINUX.
Chỉ dùng để quét các mục tiêu bạn có quyền kiểm tra (máy của bạn,
mạng của bạn, hoặc hệ thống đã được ủy quyền pentest).

Yêu cầu: đã cài nmap (sudo apt install nmap)
"""
import gi
import shutil
import subprocess
import threading

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib


class NmapWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="Nmap Scanner — GROM LINUX")
        self.set_default_size(700, 500)

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(12)
        root.set_margin_end(12)
        self.set_content(root)

        if shutil.which("nmap") is None:
            warn = Gtk.Label(
                label="⚠ Nmap chưa được cài. Chạy: sudo apt install nmap"
            )
            root.append(warn)

        notice = Gtk.Label(
            label="Chỉ quét các mục tiêu bạn có quyền kiểm tra."
        )
        notice.add_css_class("caption")
        root.append(notice)

        input_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.target_entry = Gtk.Entry()
        self.target_entry.set_placeholder_text("IP hoặc dải mạng, vd: 192.168.1.0/24")
        self.target_entry.set_hexpand(True)
        input_row.append(self.target_entry)

        self.scan_type = Gtk.DropDown.new_from_strings(
            ["Quét nhanh (-F)", "Quét cổng phổ biến (-sV)", "Quét đầy đủ (-p-)"]
        )
        input_row.append(self.scan_type)

        scan_btn = Gtk.Button(label="Scan")
        scan_btn.add_css_class("suggested-action")
        scan_btn.connect("clicked", self.on_scan_clicked)
        input_row.append(scan_btn)

        root.append(input_row)

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        self.output_view = Gtk.TextView()
        self.output_view.set_editable(False)
        self.output_view.set_monospace(True)
        self.output_buffer = self.output_view.get_buffer()
        scroller.set_child(self.output_view)
        root.append(scroller)

    def on_scan_clicked(self, button):
        target = self.target_entry.get_text().strip()
        if not target:
            self.append_output("Hãy nhập một mục tiêu trước khi scan.\n")
            return

        flags = {
            0: ["-F"],
            1: ["-sV"],
            2: ["-p-"],
        }[self.scan_type.get_selected()]

        self.output_buffer.set_text("")
        self.append_output(f"$ nmap {' '.join(flags)} {target}\n\n")

        thread = threading.Thread(
            target=self.run_scan, args=(flags, target), daemon=True
        )
        thread.start()

    def run_scan(self, flags, target):
        try:
            proc = subprocess.run(
                ["nmap", *flags, target],
                capture_output=True,
                text=True,
                timeout=300,
            )
            output = proc.stdout + proc.stderr
        except FileNotFoundError:
            output = "Lỗi: không tìm thấy nmap. Cài bằng: sudo apt install nmap\n"
        except subprocess.TimeoutExpired:
            output = "Lỗi: scan quá thời gian cho phép (300s).\n"
        except Exception as e:
            output = f"Lỗi: {e}\n"

        GLib.idle_add(self.append_output, output)

    def append_output(self, text):
        end_iter = self.output_buffer.get_end_iter()
        self.output_buffer.insert(end_iter, text)


class NmapApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.grom.linux.nmapgui")

    def do_activate(self):
        win = NmapWindow(self)
        win.present()


if __name__ == "__main__":
    app = NmapApp()
    app.run([])
