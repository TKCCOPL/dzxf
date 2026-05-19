# WhirlwindTyper 自动化打字工具 - Implementation Plan

> **Status:** Implemented — OCR primary approach with Tesseract path/language auto-detection.

**Goal:** Build a Python automation tool that detects text in WhirlwindTyper windows and simulates typing at adjustable speeds, with a customtkinter GUI supporting both manual and server-push modes.

**Architecture:** Four modules — window_locator (find app window + OCR screenshot target via win32gui), text_detector (screenshot + Tesseract OCR primary, API fallback), keyboard_emulator (pyautogui global keystrokes with clipboard-based Chinese input), and auto_type (customtkinter GUI + threading for monitor/type loops).

**Key finding:** WhirlwindTyper is an MFC app (AfxWnd42s) with custom-drawn text. GetWindowText returns empty for all child controls. UIA returns 0 descendants. Screenshot + OCR is the only viable approach.

**Tech Stack:** Python 3, pywin32, pyautogui, pyperclip, customtkinter, Pillow, pytesseract, Tesseract-OCR

---

### Task 1: Install dependencies ✓

```bash
pip install pywin32 pyautogui pyperclip customtkinter Pillow pytesseract
```

Plus install Tesseract-OCR desktop program from https://github.com/UB-Mannheim/tesseract/wiki (v5.4.0+, with chi_sim language pack).

---

### Task 2: Window Locator module ✓

**File:** `dzxf/window_locator.py`

- `find_whirlwind_window()` — searches for windows with "旋风" or "whirlwind" in title
- `find_text_control(parent_hwnd)` — two-pass: (1) find API-readable controls with text > 10 chars, (2) if none, return largest visible child for OCR screenshot
- `get_window_rect(hwnd)` — returns screen coordinates

---

### Task 3: Text Detector module ✓

**File:** `dzxf/text_detector.py`

- `_find_tesseract()` — auto-detect tesseract.exe (PATH → Program Files → LocalAppData)
- `_tesseract_available()` — check if OCR is available
- `detect_text(text_hwnd, lang)` — OCR primary: screenshot → Tesseract. Falls back to GetWindowText API. Auto-selects available language pack (chi_sim+eng → chi_sim → eng).

---

### Task 4: Keyboard Emulator module ✓

**File:** `dzxf/keyboard_emulator.py`

- `type_text(text, speed_cpm, pause_event, stop_event)` — Chinese chunks batched via clipboard Ctrl+V; English/number/symbol via pyautogui.typewrite. Chinese range covers CJK Basic (一-鿿) + Extension A (㐀-䶿).

---

### Task 5: Main GUI Application ✓

**File:** `dzxf/auto_type.py`

- `AutoTypeApp` class with customtkinter GUI
- Manual mode: detect text once, type, stop
- Server mode: poll every 1.5s via OCR, detect content changes, type each new article
- Speed slider 10-300 cpm (default 80)
- Pause/stop via threading.Event
- All GUI updates through `after()` for thread safety

---

### Task 6: Verify and test

```bash
cd dzxf && python auto_type.py
```

Prerequisites: Tesseract-OCR installed, WhirlwindTyper running with article visible.
