"""文字检测模块 — OCR 截图识别（主方案），中英文均支持."""
import os
import shutil
import win32gui
import pyautogui

# Tesseract 安装路径探测
_TESSERACT_CMD = None


def _find_tesseract():
    """查找 tesseract.exe，返回路径或 None."""
    global _TESSERACT_CMD
    if _TESSERACT_CMD is not None:
        return _TESSERACT_CMD

    # 1. 先查 PATH
    path = shutil.which("tesseract")
    if path:
        _TESSERACT_CMD = path
        return path

    # 2. 查默认安装位置
    candidates = [
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Tesseract-OCR\tesseract.exe"),
    ]
    for p in candidates:
        if os.path.isfile(p):
            _TESSERACT_CMD = p
            return p

    return None


def _tesseract_available():
    """检查 tesseract 是否可用."""
    return _find_tesseract() is not None


def _configure_pytesseract():
    """配置 pytesseract 使用找到的 tesseract 路径，并返回可用语言列表."""
    import pytesseract
    exe = _find_tesseract()
    if exe:
        pytesseract.pytesseract.tesseract_cmd = exe
        try:
            return pytesseract.get_languages()
        except Exception:
            return []
    return []


def _get_rect(hwnd):
    return win32gui.GetWindowRect(hwnd)


def detect_text(text_hwnd, lang="chi_sim+eng"):
    """截取控件区域并 OCR 识别文字.

    自动检测可用语言包，chi_sim 未安装时退回 eng。

    Args:
        text_hwnd: 文字区域控件句柄
        lang: 期望的 OCR 语言

    Returns:
        识别到的文字字符串
    """
    if text_hwnd is None:
        return ""

    # 先试 API（老控件偶尔能用）
    api_text = win32gui.GetWindowText(text_hwnd)
    if api_text:
        return api_text

    exe = _find_tesseract()
    if not exe:
        return ""

    try:
        import pytesseract
        pytesseract.pytesseract.tesseract_cmd = exe

        # 选择实际可用的语言
        try:
            available = pytesseract.get_languages()
        except Exception:
            available = ["eng"]

        # 尝试匹配期望语言，不可用则退回 eng
        for candidate in [lang, "chi_sim+eng", "chi_sim", "eng"]:
            if all(part in available for part in candidate.split("+")):
                use_lang = candidate
                break
        else:
            use_lang = "eng"

        rect = _get_rect(text_hwnd)
        w, h = rect[2] - rect[0], rect[3] - rect[1]
        if w <= 0 or h <= 0:
            return ""

        screenshot = pyautogui.screenshot(region=(rect[0], rect[1], w, h))
        text = pytesseract.image_to_string(screenshot, lang=use_lang)
        return text.strip()
    except Exception:
        return ""
