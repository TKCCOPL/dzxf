"""WhirlwindTyper 自动化打字工具 — 主入口 + GUI."""
import threading
import customtkinter as ctk
from window_locator import find_whirlwind_window, find_text_control
from text_detector import detect_text, _tesseract_available
from keyboard_emulator import type_text

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class AutoTypeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("旋风打字自动化工具")
        self.geometry("520x420")

        self.mode = "manual"
        self.speed = 80
        self.running = False
        self.paused = False

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()

        self._build_ui()

        if not _tesseract_available():
            self._update_status("未检测到 Tesseract OCR，请安装后再使用")

    def _build_ui(self):
        # 模式选择
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(pady=(15, 5), padx=20, fill="x")
        ctk.CTkLabel(mode_frame, text="工作模式:", font=ctk.CTkFont(size=14)).pack(
            side="left", padx=(10, 5)
        )
        self.mode_var = ctk.StringVar(value="manual")
        ctk.CTkRadioButton(
            mode_frame, text="手动练习", variable=self.mode_var,
            value="manual", command=self._on_mode_change
        ).pack(side="left", padx=10)
        ctk.CTkRadioButton(
            mode_frame, text="服务器下发", variable=self.mode_var,
            value="server", command=self._on_mode_change
        ).pack(side="left", padx=10)

        # 速度调节
        speed_frame = ctk.CTkFrame(self)
        speed_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(speed_frame, text="打字速度:", font=ctk.CTkFont(size=14)).pack(
            side="left", padx=(10, 5)
        )
        self.speed_slider = ctk.CTkSlider(
            speed_frame, from_=10, to=300, number_of_steps=29,
            command=self._on_speed_change
        )
        self.speed_slider.set(80)
        self.speed_slider.pack(side="left", padx=10, fill="x", expand=True)
        self.speed_label = ctk.CTkLabel(speed_frame, text="80 字/分钟", width=90)
        self.speed_label.pack(side="left", padx=(0, 10))

        # 状态显示
        self.status_label = ctk.CTkLabel(
            self, text="就绪", font=ctk.CTkFont(size=13),
            fg_color="gray20", corner_radius=6, padx=10, pady=4
        )
        self.status_label.pack(pady=5)

        # 按钮
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10, padx=20, fill="x")
        self.start_btn = ctk.CTkButton(
            btn_frame, text="开始", command=self._on_start,
            font=ctk.CTkFont(size=14), height=36
        )
        self.start_btn.pack(side="left", padx=(10, 5), fill="x", expand=True)
        self.pause_btn = ctk.CTkButton(
            btn_frame, text="暂停", command=self._on_pause,
            font=ctk.CTkFont(size=14), height=36, state="disabled"
        )
        self.pause_btn.pack(side="right", padx=(5, 10), fill="x", expand=True)

        # 文章预览
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(pady=(10, 15), padx=20, fill="both", expand=True)
        ctk.CTkLabel(preview_frame, text="当前文章预览:", font=ctk.CTkFont(size=12)).pack(
            anchor="w", padx=10, pady=(5, 0)
        )
        self.preview_text = ctk.CTkTextbox(preview_frame, font=ctk.CTkFont(size=12), wrap="word")
        self.preview_text.pack(padx=10, pady=(5, 10), fill="both", expand=True)

    def _on_mode_change(self):
        self.mode = self.mode_var.get()
        if self.mode == "server":
            self.start_btn.configure(text="开始监控")
        else:
            self.start_btn.configure(text="开始")

    def _on_speed_change(self, value):
        self.speed = int(value)
        self.speed_label.configure(text=f"{self.speed} 字/分钟")

    def _on_start(self):
        if not self.running:
            self.running = True
            self.stop_event.clear()
            self.pause_event.clear()
            self.start_btn.configure(state="disabled")
            self.pause_btn.configure(state="normal")

            if self.mode == "server":
                self._update_status("监控中，等待文章下发...")
                threading.Thread(target=self._monitor_loop, daemon=True).start()
            else:
                self._update_status("检测文章中...")
                threading.Thread(target=self._manual_type, daemon=True).start()
        else:
            self._update_status("已在运行中")

    def _on_pause(self):
        if not self.paused:
            self.paused = True
            self.pause_event.set()
            self.pause_btn.configure(text="继续")
            self._update_status("已暂停")
        else:
            self.paused = False
            self.pause_event.clear()
            self.pause_btn.configure(text="暂停")
            self._update_status("打字中...")

    def _update_status(self, text):
        self.after(0, lambda: self.status_label.configure(text=text))

    def _update_preview(self, text):
        def _update():
            self.preview_text.delete("1.0", "end")
            preview = text[:500] + ("..." if len(text) > 500 else "")
            self.preview_text.insert("1.0", preview)
        self.after(0, _update)

    def _reset_buttons(self):
        def _reset():
            self.running = False
            self.paused = False
            self.pause_event.clear()
            self.start_btn.configure(state="normal")
            self.pause_btn.configure(state="disabled")
            self.pause_btn.configure(text="暂停")
        self.after(0, _reset)

    def _manual_type(self):
        try:
            main_hwnd, title = find_whirlwind_window()
            if main_hwnd is None:
                self._update_status("未找到 WhirlwindTyper 窗口，请启动程序")
                self._reset_buttons()
                return

            text_hwnd = find_text_control(main_hwnd)
            self._update_status("OCR 识别中...")
            text = detect_text(text_hwnd)

            if not text:
                self._update_status("未检测到文字，请确保练习文章已显示")
                self._reset_buttons()
                return

            self._update_preview(text)
            self._update_status("打字中...")
            type_text(text, self.speed, self.pause_event, self.stop_event)

            if self.stop_event.is_set():
                self._update_status("已停止")
            else:
                self._update_status("已完成")
        except Exception as e:
            self._update_status(f"错误: {e}")
        finally:
            self._reset_buttons()

    def _monitor_loop(self):
        last_text = ""
        main_hwnd = None
        text_hwnd = None

        while self.running and not self.stop_event.is_set():
            try:
                if main_hwnd is None or not _hwnd_valid(main_hwnd):
                    main_hwnd, _ = find_whirlwind_window()
                    if main_hwnd is None:
                        self._update_status("监控中（等待窗口）...")
                        _sleep_check(1.0, self.stop_event)
                        continue
                    text_hwnd = find_text_control(main_hwnd)

                text = detect_text(text_hwnd)

                if text and text != last_text:
                    last_text = text
                    self._update_preview(text)
                    self._update_status("检测到新文章，开始打字...")

                    if not self.stop_event.is_set():
                        type_text(text, self.speed, self.pause_event, self.stop_event)

                    if not self.stop_event.is_set():
                        self._update_status("打完，等待下一篇文章...")

                _sleep_check(1.5, self.stop_event)

            except Exception as e:
                self._update_status(f"监控异常: {e}")
                _sleep_check(1.0, self.stop_event)

        if self.stop_event.is_set():
            self._update_status("已停止监控")


def _hwnd_valid(hwnd):
    try:
        import win32gui
        return win32gui.IsWindow(hwnd)
    except Exception:
        return False


def _sleep_check(duration, stop_event):
    import time
    for _ in range(int(duration * 10)):
        if stop_event and stop_event.is_set():
            return
        time.sleep(0.1)


def main():
    app = AutoTypeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
