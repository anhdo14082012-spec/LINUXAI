#!/usr/bin/env python3
"""
GROM AI Assistant — GUI chat kết nối tới llama-server chạy local
(ai/grom-ai-server.sh). Không gửi dữ liệu ra ngoài máy — toàn bộ
suy luận chạy tại chỗ trên model GGUF đã quantize.

Yêu cầu: đã chạy ai/grom-ai-server.sh (hoặc service grom-ai.service)
"""
import gi
import json
import threading
import urllib.request
import urllib.error

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib

AI_SERVER_URL = "http://127.0.0.1:8089/v1/chat/completions"


class AiAssistantWindow(Adw.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app, title="GROM AI — Trợ lý cục bộ")
        self.set_default_size(650, 700)

        self.history = [
            {
                "role": "system",
                "content": "Bạn là trợ lý AI chạy cục bộ trên GROM LINUX, trả lời ngắn gọn, hữu ích bằng tiếng Việt.",
            }
        ]

        root = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        root.set_margin_top(12)
        root.set_margin_bottom(12)
        root.set_margin_start(12)
        root.set_margin_end(12)
        self.set_content(root)

        status = Gtk.Label(label="Chạy cục bộ — không gửi dữ liệu ra ngoài")
        status.add_css_class("caption")
        root.append(status)

        scroller = Gtk.ScrolledWindow()
        scroller.set_vexpand(True)
        self.chat_view = Gtk.TextView()
        self.chat_view.set_editable(False)
        self.chat_view.set_wrap_mode(Gtk.WrapMode.WORD)
        self.chat_buffer = self.chat_view.get_buffer()
        scroller.set_child(self.chat_view)
        root.append(scroller)

        input_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        self.entry = Gtk.Entry()
        self.entry.set_placeholder_text("Nhập câu hỏi rồi Enter...")
        self.entry.set_hexpand(True)
        self.entry.connect("activate", self.on_send)
        input_row.append(self.entry)

        send_btn = Gtk.Button(label="Gửi")
        send_btn.add_css_class("suggested-action")
        send_btn.connect("clicked", self.on_send)
        input_row.append(send_btn)

        root.append(input_row)

    def on_send(self, widget):
        message = self.entry.get_text().strip()
        if not message:
            return
        self.entry.set_text("")
        self.append_chat(f"\nBạn: {message}\n")
        self.history.append({"role": "user", "content": message})

        self.append_chat("GROM AI: ")
        thread = threading.Thread(target=self.query_ai, daemon=True)
        thread.start()

    def query_ai(self):
        payload = json.dumps(
            {
                "messages": self.history,
                "temperature": 0.7,
                "max_tokens": 512,
            }
        ).encode("utf-8")

        req = urllib.request.Request(
            AI_SERVER_URL,
            data=payload,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(req, timeout=120) as resp:
                data = json.loads(resp.read())
            reply = data["choices"][0]["message"]["content"]
        except urllib.error.URLError:
            reply = (
                "[Không kết nối được AI server. "
                "Chạy: bash ai/grom-ai-server.sh]"
            )
        except Exception as e:
            reply = f"[Lỗi: {e}]"

        self.history.append({"role": "assistant", "content": reply})
        GLib.idle_add(self.append_chat, reply + "\n")

    def append_chat(self, text):
        end_iter = self.chat_buffer.get_end_iter()
        self.chat_buffer.insert(end_iter, text)
        # auto-scroll xuống cuối
        mark = self.chat_buffer.get_insert()
        self.chat_view.scroll_mark_onscreen(mark)


class AiAssistantApp(Adw.Application):
    def __init__(self):
        super().__init__(application_id="com.grom.linux.aiassistant")

    def do_activate(self):
        win = AiAssistantWindow(self)
        win.present()


if __name__ == "__main__":
    app = AiAssistantApp()
    app.run([])
