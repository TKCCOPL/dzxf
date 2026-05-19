"""键盘模拟模块 — 全局键盘模拟 + 剪贴板中文输入."""
import time
import pyautogui
import pyperclip


def type_text(text, speed_cpm, pause_event=None, stop_event=None):
    """按指定速度打字，支持暂停和终止.

    中文连续块通过剪贴板 Ctrl+V 粘贴，
    英文/数字通过 pyautogui.typewrite 逐字输出。
    """
    if not text:
        return

    char_delay = 60.0 / speed_cpm if speed_cpm > 0 else 0.05

    i = 0
    while i < len(text):
        if stop_event and stop_event.is_set():
            return

        while pause_event and pause_event.is_set():
            time.sleep(0.1)
            if stop_event and stop_event.is_set():
                return

        char = text[i]

        if char == '\n':
            pyautogui.press("enter")
            time.sleep(char_delay * 2)
            i += 1
        elif '一' <= char <= '鿿' or '㐀' <= char <= '䶿':
            # 累积连续中文字符，通过剪贴板粘贴
            chunk = char
            j = i + 1
            while j < len(text) and (
                '一' <= text[j] <= '鿿' or '㐀' <= text[j] <= '䶿'
            ):
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
