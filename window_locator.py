"""窗口定位模块."""
import win32gui


def find_whirlwind_window():
    """查找 WhirlwindTyper 主窗口，返回 (hwnd, title) 或 (None, None)."""
    result = [None, None]

    def enum_callback(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        title = win32gui.GetWindowText(hwnd)
        if "旋风" in title or "whirlwind" in title.lower():
            result[0] = hwnd
            result[1] = title
            return False
        return True

    win32gui.EnumWindows(enum_callback, None)
    return result[0], result[1]


def find_text_control(parent_hwnd):
    """定位文字显示区域控件，返回最佳 OCR 截图目标句柄.

    优先查找有文字内容的 Standard/Edit 控件（API 可读），
    找不到则返回面积最大的可见子控件（供 OCR 截图用）。
    """
    # 第一轮：找 API 可读的有文字控件
    text_candidates = []

    def enum_child(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        class_name = win32gui.GetClassName(hwnd)
        text = win32gui.GetWindowText(hwnd)
        if len(text) > 10:
            # 有足够文字的控件，API 可直接读取
            priority = 1 if any(
                cls in class_name
                for cls in ["RichEdit", "Edit", "TEdit", "TMemo", "Static"]
            ) else 3
            text_candidates.append((hwnd, priority))
        return True

    win32gui.EnumChildWindows(parent_hwnd, enum_child, None)

    if text_candidates:
        text_candidates.sort(key=lambda x: x[1])
        return text_candidates[0][0]

    # 第二轮：无 API 可读控件，找面积最大的子控件供 OCR 截图
    largest = [parent_hwnd, 0]  # [hwnd, area]

    def enum_size(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd):
            return True
        r = win32gui.GetWindowRect(hwnd)
        area = (r[2] - r[0]) * (r[3] - r[1])
        if area > largest[1]:
            largest[0] = hwnd
            largest[1] = area
        return True

    win32gui.EnumChildWindows(parent_hwnd, enum_size, None)
    return largest[0]


def get_window_rect(hwnd):
    """获取窗口屏幕坐标 (left, top, right, bottom)."""
    return win32gui.GetWindowRect(hwnd)
