# WhirlwindTyper 自动化打字工具 - Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python automation tool that detects text in WhirlwindTyper windows and simulates typing at adjustable speeds, with a customtkinter GUI supporting both manual and server-push modes.

**Architecture:** Four modules — window_locator (find app window + text control via win32gui), text_detector (GetWindowText with OCR fallback), keyboard_emulator (pyautogui global keystrokes with clipboard-based Chinese input), and auto_type (customtkinter GUI + threading for monitor/type loops).

**Tech Stack:** Python 3, pywin32, pyautogui, customtkinter, Pillow, pytesseract (optional)

---

### Task 1: Install dependencies

**Files:** None

- [ ] **Step 1: Install all Python dependencies**

```bash
pip install pywin32 pyautogui pyperclip customtkinter Pillow pytesseract
```

Expected: All packages install successfully.

---

### Task 2: Window Locator module

**Files:**
- Create: `dzxf/window_locator.py`

- [ ] **Step 1: Write find_whirlwind_window function**

```python
"""WhirlwindTyper 窗口定位模块."""
import win32gui
import win32con


def find_whirlwind_window():
    """查找 WhirlwindTyper 主窗口，返回 (hwnd, title) 或 (None, None)."""
    result = [None, None]

    def enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if "whirlwind" in title.lower() or "旋风" in title:
            result[0] = hwnd
            result[1] = title
            return False  # stop enumeration
        return True

    win32gui.EnumWindows(enum_callback, None)
    return result[0], result[1]
```

- [ ] **Step 2: Write find_text_control function**

```python
def find_text_control(parent_hwnd):
    """在父窗口中查找文字显示控件，返回控件句柄或 None.

    优先查找 RichEdit/Edit 控件，其次查找 Static 控件。
    如果都找不到，返回父窗口本身（用于 OCR 兜底方案）。
    """
    candidates = []

    def enum_child(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        class_name = win32gui.GetClassName(hwnd)
        text = win32gui.GetWindowText(hwnd)
        # RichEdit20A/W, Edit, TEdit 等编辑/文字控件
        if any(cls in class_name for cls in ["RichEdit", "Edit", "TEdit", "TMemo"]):
            if len(text) > 10:
                candidates.append((hwnd, 1))  # priority 1: edit controls with content
        elif "Static" in class_name:
            if len(text) > 10:
                candidates.append((hwnd, 2))  # priority 2: static text with content
        return True

    win32gui.EnumChildWindows(parent_hwnd, enum_child, None)

    # 按优先级排序，返回最佳匹配
    candidates.sort(key=lambda x: x[1])
    if candidates:
        return candidates[0][0]

    # 所有控件都没文字，返回父窗口供 OCR 兜底
    return parent_hwnd
```

- [ ] **Step 3: Write get_window_rect function**

```python
def get_window_rect(hwnd):
    """获取窗口屏幕坐标 (left, top, right, bottom)."""
    return win32gui.GetWindowRect(hwnd)
```

---

### Task 3: Text Detector module

**Files:**
- Create: `dzxf/text_detector.py`

- [ ] **Step 1: Write detect_text_api function**

```python
"""文字检测模块 - Windows API 方案 + OCR 兜底."""
import win32gui
import pyautogui
from PIL import Image


def detect_text_api(hwnd):
    """通过 GetWindowText 从控件抓取文字，返回文字字符串或空字符串."""
    if hwnd is None:
        return ""
    return win32gui.GetWindowText(hwnd)
```

- [ ] **Step 2: Write detect_text_ocr function**

```python
def detect_text_ocr(hwnd, lang="chi_sim+eng"):
    """截取窗口区域并 OCR 识别，返回识别文字.

    需要安装 Tesseract OCR: https://github.com/UB-Mannheim/tesseract/wiki
    lang: 'chi_sim' 中文, 'eng' 英文, 'chi_sim+eng' 中英混合
    """
    import pytesseract

    rect = _get_rect(hwnd)
    screenshot = pyautogui.screenshot(region=(
        rect[0], rect[1],
        rect[2] - rect[0], rect[3] - rect[1]
    ))
    text = pytesseract.image_to_string(screenshot, lang=lang)
    return text.strip()


def _get_rect(hwnd):
    return win32gui.GetWindowRect(hwnd)
```

- [ ] **Step 3: Write detect_text with fallback logic**

```python
def detect_text(text_hwnd, use_ocr_fallback=True):
    """检测文字内容，API 失败时可选 OCR 兜底.

    Args:
        text_hwnd: 文字控件句柄
        use_ocr_fallback: API 失败时是否启用 OCR

    Returns:
        检测到的文字字符串
    """
    text = detect_text_api(text_hwnd)

    if text:
        return text

    if not use_ocr_fallback:
        return ""

    try:
        text = detect_text_ocr(text_hwnd)
    except Exception:
        text = ""

    return text
```

- [ ] **Step 4: Write classify_text function**

```python
def classify_text(text):
    """判断文字类型，返回 'chinese' | 'english' | 'number' | 'mixed'.

    用于决定键盘模拟方式：
    - 'chinese': 使用剪贴板 Ctrl+V
    - 'english'/'number': 使用 pyautogui.typewrite
    - 'mixed': 逐字符判断
    """
    if not text:
        return "english"

    has_chinese = any('一' <= c <= '鿿' for c in text)
    has_english = any(c.isascii() and c.isalpha() for c in text)
    has_digit = any(c.isdigit() for c in text)

    if has_chinese and (has_english or has_digit):
        return "mixed"
    if has_chinese:
        return "chinese"
    if has_digit and not has_english:
        return "number"
    return "english"
```

---

### Task 4: Keyboard Emulator module

**Files:**
- Create: `dzxf/keyboard_emulator.py`

- [ ] **Step 1: Write type_english function**

```python
"""键盘模拟模块 - 全局键盘模拟 + 剪贴板中文输入."""
import time
import pyautogui
import pyperclip


def _type_english(text, char_delay):
    """逐字符键入英文/数字."""
    pyautogui.typewrite(text, interval=char_delay)
```

- [ ] **Step 2: Write type_chinese function**

```python
def _type_chinese(text, char_delay):
    """通过剪贴板粘贴输入中文."""
    pyperclip.copy(text)
    time.sleep(char_delay)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(char_delay * 2)
```

- [ ] **Step 3: Write main type_text function**

```python
def type_text(text, speed_cpm, pause_event, stop_event):
    """按指定速度打字，支持暂停和终止.

    Args:
        text: 要打的文字
        speed_cpm: 速度（字/分钟）
        pause_event: threading.Event，set 时暂停
        stop_event: threading.Event，set 时终止
    """
    if not text:
        return

    char_delay = 60.0 / speed_cpm if speed_cpm > 0 else 0.05

    for i, char in enumerate(text):
        # 检查终止
        if stop_event and stop_event.is_set():
            return

        # 检查暂停
        if pause_event and pause_event.is_set():
            while pause_event.is_set():
                time.sleep(0.1)
                if stop_event and stop_event.is_set():
                    return

        if char == '\n':
            pyautogui.press("enter")
            time.sleep(char_delay * 2)
        elif '一' <= char <= '鿿':
            # 中文字符：累积连续中文一起粘贴
            chunk = char
            j = i + 1
            while j < len(text) and '一' <= text[j] <= '鿿':
                chunk += text[j]
                j += 1
            _type_chinese(chunk, char_delay)
            # 跳过已处理的中文字符
            for _ in range(len(chunk) - 1):
                next(iter([]), None)
            # 调整 i（这里需要实际处理，string iteration 不能简单跳过）
        else:
            pyautogui.typewrite(char, interval=char_delay)
```

- [ ] **Step 4: Fix type_text to handle Chinese chunk skipping properly**

```python
def type_text(text, speed_cpm, pause_event, stop_event):
    """按指定速度打字，支持暂停和终止."""
    if not text:
        return

    char_delay = 60.0 / speed_cpm if speed_cpm > 0 else 0.05

    i = 0
    while i < len(text):
        if stop_event and stop_event.is_set():
            return

        # 检查暂停
        while pause_event and pause_event.is_set():
            time.sleep(0.1)
            if stop_event and stop_event.is_set():
                return

        char = text[i]

        if char == '\n':
            pyautogui.press("enter")
            time.sleep(char_delay * 2)
            i += 1
        elif '一' <= char <= '鿿':
            # 累积连续中文字符
            chunk = char
            j = i + 1
            while j < len(text) and '一' <= text[j] <= '鿿':
                chunk += text[j]
                j += 1
            pyperclip.copy(chunk)
            time.sleep(0.05)
            pyautogui.hotkey("ctrl", "v")
            time.sleep(char_delay * len(chunk))
            i = j
        else:
            pyautogui.typewrite(char, interval=char_delay)
            i += 1
```

---

### Task 5: Main GUI Application

**Files:**
- Create: `dzxf/auto_type.py`

- [ ] **Step 1: Write imports and core class skeleton**

```python
"""WhirlwindTyper 自动化打字工具 - 主入口 + GUI."""
import threading
import customtkinter as ctk
from window_locator import find_whirlwind_window, find_text_control
from text_detector import detect_text, classify_text
from keyboard_emulator import type_text

ctk.set_appearance_mode("system")
ctk.set_default_color_theme("blue")


class AutoTypeApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("旋风打字自动化工具")
        self.geometry("520x420")

        self.mode = "manual"  # "manual" or "server"
        self.speed = 80  # 字/分钟
        self.running = False
        self.paused = False

        self.pause_event = threading.Event()
        self.stop_event = threading.Event()
        self.monitor_thread = None
        self.type_thread = None

        self._build_ui()
```

- [ ] **Step 2: Write UI build method**

```python
    def _build_ui(self):
        # 模式选择
        mode_frame = ctk.CTkFrame(self)
        mode_frame.pack(pady=(15, 5), padx=20, fill="x")
        ctk.CTkLabel(mode_frame, text="工作模式:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 5))
        self.mode_var = ctk.StringVar(value="manual")
        ctk.CTkRadioButton(mode_frame, text="手动练习", variable=self.mode_var,
                           value="manual", command=self._on_mode_change).pack(side="left", padx=10)
        ctk.CTkRadioButton(mode_frame, text="服务器下发", variable=self.mode_var,
                           value="server", command=self._on_mode_change).pack(side="left", padx=10)

        # 速度调节
        speed_frame = ctk.CTkFrame(self)
        speed_frame.pack(pady=10, padx=20, fill="x")
        ctk.CTkLabel(speed_frame, text="打字速度:", font=ctk.CTkFont(size=14)).pack(side="left", padx=(10, 5))
        self.speed_slider = ctk.CTkSlider(speed_frame, from_=10, to=300, number_of_steps=29,
                                          command=self._on_speed_change)
        self.speed_slider.set(80)
        self.speed_slider.pack(side="left", padx=10, fill="x", expand=True)
        self.speed_label = ctk.CTkLabel(speed_frame, text="80 字/分钟", width=90)
        self.speed_label.pack(side="left", padx=(0, 10))

        # 状态显示
        self.status_label = ctk.CTkLabel(self, text="就绪", font=ctk.CTkFont(size=13),
                                         fg_color="gray20", corner_radius=6, padx=10, pady=4)
        self.status_label.pack(pady=5)

        # 按钮
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10, padx=20, fill="x")
        self.start_btn = ctk.CTkButton(btn_frame, text="开始", command=self._on_start,
                                       font=ctk.CTkFont(size=14), height=36)
        self.start_btn.pack(side="left", padx=(10, 5), fill="x", expand=True)
        self.pause_btn = ctk.CTkButton(btn_frame, text="暂停", command=self._on_pause,
                                       font=ctk.CTkFont(size=14), height=36, state="disabled")
        self.pause_btn.pack(side="right", padx=(5, 10), fill="x", expand=True)

        # 文章预览
        preview_frame = ctk.CTkFrame(self)
        preview_frame.pack(pady=(10, 15), padx=20, fill="both", expand=True)
        ctk.CTkLabel(preview_frame, text="当前文章预览:", font=ctk.CTkFont(size=12)).pack(anchor="w", padx=10, pady=(5, 0))
        self.preview_text = ctk.CTkTextbox(preview_frame, font=ctk.CTkFont(size=12), wrap="word")
        self.preview_text.pack(padx=10, pady=(5, 10), fill="both", expand=True)
```

- [ ] **Step 3: Write event handlers**

```python
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
```

- [ ] **Step 4: Write manual mode logic**

```python
    def _manual_type(self):
        try:
            main_hwnd, title = find_whirlwind_window()
            if main_hwnd is None:
                self._update_status("未找到 WhirlwindTyper 窗口，请启动程序")
                self._reset_buttons()
                return

            text_hwnd = find_text_control(main_hwnd)
            text = detect_text(text_hwnd)

            if not text:
                self._update_status("未检测到文字，请确保练习已开始")
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
```

- [ ] **Step 5: Write server monitor loop**

```python
    def _monitor_loop(self):
        last_text = ""
        main_hwnd = None
        text_hwnd = None

        while self.running and not self.stop_event.is_set():
            try:
                # 查找窗口（每轮重找，支持窗口重开）
                if main_hwnd is None or not _hwnd_valid(main_hwnd):
                    main_hwnd, _ = find_whirlwind_window()
                    if main_hwnd is None:
                        self._update_status("监控中（等待窗口）...")
                        _sleep_check(1.0, self.stop_event)
                        continue
                    text_hwnd = find_text_control(main_hwnd)

                text = detect_text(text_hwnd)

                if text and text != last_text:
                    # 新文章出现
                    last_text = text
                    self._update_preview(text)
                    self._update_status("检测到新文章，开始打字...")

                    if not self.stop_event.is_set():
                        type_text(text, self.speed, self.pause_event, self.stop_event)

                    if not self.stop_event.is_set():
                        self._update_status("打完，等待下一篇文章...")

                _sleep_check(1.0, self.stop_event)

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
    """分段 sleep，支持随时响应 stop."""
    for _ in range(int(duration * 10)):
        if stop_event and stop_event.is_set():
            return
        import time
        time.sleep(0.1)
```

- [ ] **Step 6: Write main entry**

```python
def main():
    app = AutoTypeApp()
    app.mainloop()


if __name__ == "__main__":
    main()
```

---

### Task 6: Verify and test

**Files:** None (manual testing)

- [ ] **Step 1: Verify all imports resolve**

```bash
python -c "from window_locator import find_whirlwind_window, find_text_control; from text_detector import detect_text, classify_text; from keyboard_emulator import type_text; from auto_type import main; print('All imports OK')"
```

Expected: "All imports OK"

- [ ] **Step 2: Start the GUI**

```bash
cd dzxf && python auto_type.py
```

Expected: GUI window opens with all controls visible.

- [ ] **Step 3: Manual test checklist**
  1. 启动 WhirlwindTyper，进入练习界面显示文字
  2. 启动 auto_type.py
  3. 手动模式：点击"开始" → 验证自动检测并打字
  4. 调整速度滑块 → 验证速度变化
  5. 点击"暂停" → 验证暂停 → 点击"继续" → 验证恢复
  6. 切换到"服务器下发" → 点击"开始监控" → 验证持续监控状态
  7. 在 WhirlwindTyper 中切换文章 → 验证自动检测新文章并打字
