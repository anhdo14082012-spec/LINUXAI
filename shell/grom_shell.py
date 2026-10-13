#!/usr/bin/env python3
"""
GROM LINUX Desktop Shell (v2)
================================
- Sidebar bên trái: app theo danh mục (Hệ thống / Pentest / AI / Cài đặt)
- Thanh tìm kiếm app nhanh
- Taskbar: CPU/RAM/pin trực tiếp + nút đổi chế độ nguồn
- Hệ thống tab (Adwaita TabView) ở khu vực chính
- AI Assistant mở ngay trong tab thay vì cửa sổ riêng (trải nghiệm liền mạch)

Yêu cầu:
    sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-4.0 gir1.2-adw-1

Chạy:
    python3 grom_shell.py
"""
import gi
import json
import shutil
import subprocess
from pathlib import Path

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

from system_monitor import SystemMonitor

BASE_DIR = Path(__file__).resolve().parent
CONFIG_FILE = BASE_DIR / "config" / "apps.json"
APPS_DIR = BASE_DIR / "apps"
MODE_FILE = Path("/run/grom/power-mode")

CATEGORY_LABELS = {
    "system": "Hệ thống",
    "pentest": "An ninh mạng",
    "ai": "Trợ lý AI",
    "other": "Khác",
}


def load_apps():
    if not CONFIG_FILE.exists():
        return []
    with open(CONFIG_FILE, "r", encoding="utf-8") as f:
        apps = json.load(f)
    for app in apps:
        app["cmd"] = app["cmd"].replace("{APPDIR}", str(APPS_DIR))
    return apps


class GromWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="GROM LINUX")
        self.set_default_size(1366, 820)

        self.apps = load_apps()
        self.monitor = SystemMonitor()

        # ---- Layout gốc: taskbar trên, bên dưới chia sidebar + nội dung ----
        outer = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_content(outer)
        outer.append(self.build_taskbar())

        body = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        body.set_vexpand(True)
        outer.append(body)

        body.append(self.build_sidebar())
        body.append(Gtk.Separator(orientation=Gtk.Orientation.VERTICAL))

        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        main_box.set_hexpand(True)
        body.append(main_box)

        self.tab_view = Adw.TabView()
        tab_bar = Adw.TabBar(view=self.tab_view)
        main_box.append(tab_bar)
        main_box.append(self.tab_view)

        self.new_tab("Trang chủ", self.build_home_page())

        # cập nhật CPU/RAM/pin mỗi 2 giây — đủ nhanh để thấy thay đổi,
        # đủ chậm để bản thân việc đo không ngốn thêm điện
        GLib.timeout_add_seconds(2, self.update_system_stats)

    # ---------- Taskbar ----------
    def build_taskbar(self):
        bar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        bar.set_margin_top(6)
        bar.set_margin_bottom(6)
        bar.set_margin_start(10)
        bar.set_margin_end(10)

        logo = Gtk.Label(label="🐧 GROM LINUX")
        logo.add_css_class("title-4")
        bar.append(logo)

        self.search_entry = Gtk.SearchEntry()
        self.search_entry.set_placeholder_text("Tìm ứng dụng...")
        self.search_entry.set_size_request(220, -1)
        self.search_entry.connect("search-changed", self.on_search_changed)
        bar.append(self.search_entry)

        spacer = Gtk.Box(hexpand=True)
        bar.append(spacer)

        self.cpu_label = Gtk.Label(label="CPU: --%")
        self.ram_label = Gtk.Label(label="RAM: --%")
        self.bat_label = Gtk.Label(label="")
        bar.append(self.cpu_label)
        bar.append(self.ram_label)
        bar.append(self.bat_label)

        power_btn = Gtk.MenuButton(label="⚡ Nguồn")
        power_btn.set_popover(self.build_power_popover())
        bar.append(power_btn)

        clock = Gtk.Label()
        GLib.timeout_add_seconds(1, self.update_clock, clock)
        bar.append(clock)

        return bar

    def build_power_popover(self):
        popover = Gtk.Popover()
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        box.set_margin_top(6)
        box.set_margin_bottom(6)
        box.set_margin_start(6)
        box.set_margin_end(6)

        for key, label in [
            ("tietkiem", "🔋 Tiết kiệm năng lượng"),
            ("canbang", "⚖ Cân bằng"),
            ("hieunang", "🚀 Hiệu năng cao"),
            ("auto", "🔄 Tự động"),
        ]:
            btn = Gtk.Button(label=label)
            btn.connect("clicked", self.set_power_mode, key)
            box.append(btn)

        popover.set_child(box)
        return popover

    def set_power_mode(self, button, key):
        try:
            MODE_FILE.parent.mkdir(parents=True, exist_ok=True)
            MODE_FILE.write_text(key)
        except PermissionError:
            self.new_tab(
                "Lỗi quyền",
                Gtk.Label(
                    label="Không ghi được chế độ nguồn — cần cấu hình quyền /run/grom."
                ),
            )

    # ---------- Sidebar ----------
    def build_sidebar(self):
        scroller = Gtk.ScrolledWindow()
        scroller.set_size_request(230, -1)
        scroller.set_vexpand(True)

        self.sidebar_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.sidebar_box.set_margin_top(10)
        self.sidebar_box.set_margin_start(8)
        self.sidebar_box.set_margin_end(8)
        scroller.set_child(self.sidebar_box)

        self.render_sidebar(self.apps)
        return scroller

    def render_sidebar(self, apps):
        child = self.sidebar_box.get_first_child()
        while child:
            nxt = child.get_next_sibling()
            self.sidebar_box.remove(child)
            child = nxt

        categories = {}
        for app in apps:
            categories.setdefault(app.get("category", "other"), []).append(app)

        for cat, cat_apps in categories.items():
            cat_label = Gtk.Label(label=CATEGORY_LABELS.get(cat, cat.title()))
            cat_label.add_css_class("heading")
            cat_label.set_halign(Gtk.Align.START)
            cat_label.set_margin_top(10)
            self.sidebar_box.append(cat_label)

            for app in cat_apps:
                btn = Gtk.Button(label=f"  {app['name']}")
                btn.set_halign(Gtk.Align.FILL)
                btn.add_css_class("flat")
                btn.connect("clicked", self.on_launch_clicked, app)
                self.sidebar_box.append(btn)

    def on_search_changed(self, entry):
        query = entry.get_text().strip().lower()
        if not query:
            self.render_sidebar(self.apps)
            return
        filtered = [a for a in self.apps if query in a["name"].lower()]
        self.render_sidebar(filtered)

    # ---------- App launching ----------
    def on_launch_clicked(self, button, app):
        if app.get("category") == "ai":
            self.open_ai_tab()
            return

        binary = app["cmd"].split()[0]
        if binary != "python3" and shutil.which(binary) is None:
            self.new_tab(
                app["name"],
                Gtk.Label(
                    label=f"Chưa cài '{binary}'. Cài bằng grom-pkg hoặc apt trước."
                ),
            )
            return
        subprocess.Popen(app["cmd"], shell=True)

    def open_ai_tab(self):
        notice = Gtk.Label(
            label=(
                "Trợ lý AI chạy cục bộ.\n"
                "Nếu chưa chạy AI server: bash ai/grom-ai-server.sh\n"
                "Mở cửa sổ chat đầy đủ bên dưới."
            )
        )
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        box.append(notice)
        open_btn = Gtk.Button(label="Mở GROM AI Assistant")
        open_btn.add_css_class("suggested-action")
        open_btn.connect(
            "clicked",
            lambda b: subprocess.Popen(
                f"python3 {APPS_DIR / 'ai_assistant.py'}", shell=True
            ),
        )
        box.append(open_btn)
        self.new_tab("Trợ lý AI", box)

    # ---------- Tabs ----------
    def new_tab(self, title, widget):
        page = self.tab_view.append(widget)
        page.set_title(title)
        self.tab_view.set_selected_page(page)

    def build_home_page(self):
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        box.set_valign(Gtk.Align.CENTER)
        box.set_halign(Gtk.Align.CENTER)
        label = Gtk.Label(label="Chào mừng đến GROM LINUX")
        label.add_css_class("title-1")
        sub = Gtk.Label(
            label="Tìm app ở thanh trên, chọn danh mục ở sidebar bên trái"
        )
        box.append(label)
        box.append(sub)
        return box

    # ---------- Cập nhật định kỳ ----------
    def update_clock(self, label):
        label.set_label(GLib.DateTime.new_now_local().format("%H:%M:%S"))
        return True

    def update_system_stats(self):
        self.cpu_label.set_label(f"CPU: {self.monitor.cpu_percent()}%")
        self.ram_label.set_label(f"RAM: {self.monitor.ram_percent()}%")
        bat = self.monitor.battery_info()
        if bat:
            pct, charging = bat
            icon = "🔌" if charging else "🔋"
            self.bat_label.set_label(f"{icon} {pct}%")
        else:
            self.bat_label.set_label("")
        return True


class GromApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.grom.linux.shell")

    def do_activate(self):
        win = GromWindow(self)
        win.present()


if __name__ == "__main__":
    app = GromApp()
    app.run([])
