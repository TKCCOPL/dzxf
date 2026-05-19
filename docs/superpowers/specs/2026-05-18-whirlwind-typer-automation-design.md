# WhirlwindTyper 自动化打字工具 - 设计文档

## 概述

为 WhirlwindTyper（旋风打字）Windows 打字练习软件编写 Python 自动化打字脚本。提供 GUI 控制面板，支持两种工作模式：手动练习模式和服务器下发模式。

## 技术选型

| 决策点 | 选择 | 理由 |
|--------|------|------|
| 文字检测（主方案） | 截图 + Tesseract OCR | 程序为 MFC 自绘控件（AfxWnd42s），GetWindowText 始终返回空 |
| 文字检测（兜底） | Windows API `GetWindowText` | 老控件偶尔可读，作为快速路径 |
| 键盘模拟 | pyautogui 全局键盘模拟 | 兼容性最好，MFC 老应用 WM_CHAR 可能无效 |
| GUI 框架 | customtkinter | 现代外观，API 与 tkinter 一致，依赖轻（<2MB） |

### 根因探测结论

| 发现 | 结论 |
|------|------|
| 窗口标题 | "打字旋风"，MFC 对话框（#32770） |
| 控件类名 | `AfxWnd42s` + `SPGInputAreaGrayClass` |
| GetWindowText | 所有子控件均返回空 |
| UIA (pywinauto) | 后代元素为 0，未实现无障碍接口 |
| **唯一可行方案** | 截图 + Tesseract OCR |

## 架构

```
┌─────────────────────────────────────────────────┐
│                  customtkinter GUI               │
│  [模式选择] [速度滑块] [开始] [暂停] [状态栏]     │
└──────────────────────┬──────────────────────────┘
                       │ 控制指令
┌──────────────────────▼──────────────────────────┐
│                  AutomationCore                  │
│                                                 │
│  ┌────────────┐  ┌────────────┐  ┌──────────┐  │
│  │ 窗口定位器  │  │ 文字检测器  │  │ 键盘模拟器│  │
│  │ Window     │  │ Text       │  │ Keyboard  │  │
│  │ Locator    │  │ Detector   │  │ Emulator  │  │
│  └────────────┘  └────────────┘  └──────────┘  │
│       │                │                │       │
│       ▼                ▼                ▼       │
│  WhirlwindTyper    截图 + OCR       系统键盘缓冲区  │
│     窗口句柄       (主方案)        (pyautogui)    │
└─────────────────────────────────────────────────┘
```

### 模块职责

**WindowLocator（窗口定位器）**
- 通过窗口标题 "打字旋风"/"旋风"/"Whirlwind" 查找主窗口句柄
- 查找文字显示区域：优先 API 可读控件，找不到则取面积最大子控件供 OCR 截图
- 使用 `win32gui.EnumWindows`、`EnumChildWindows`

**TextDetector（文字检测器）**
- 主方案：截图 + Tesseract OCR（chi_sim+eng 中英混合）
- 兜底方案：`GetWindowText`（作为快速路径，老控件偶尔可用）
- Tesseract 路径自动探测：PATH → Program Files → LocalAppData
- 语言包自动选择：检测已安装语言，chi_sim 未装时退回 eng
- 中文 Unicode 范围覆盖 CJK Basic + Extension A（㐀-䶿）

**KeyboardEmulator（键盘模拟器）**
- 英文字母/数字/符号：`pyautogui.typewrite` 逐字符发送
- 中文：累积连续中文字符，拷贝至剪贴板 → `Ctrl+V` 粘贴
- 支持速度调节（字/分钟），通过字符间延迟控制

## 两种工作模式

### 模式一：手动练习

```
用户手动选文章并开始 → 脚本截图 OCR 识别文字 → 自动打字
```

- 用户自行在 WhirlwindTyper 中选择练习内容并开始
- 点击 GUI "开始" 按钮后，脚本截图文字区域并 OCR 识别
- 识别到文字后直接开始打字，打完自动停止
- 适用场景：单机模式（ConnectMode=1），练习本地素材

### 模式二：服务器下发（网络模式）

```
持续监控窗口文字 → OCR 检测新文章(内容变化) → 自动打字 → 打完继续监控
```

- 脚本启动后进入**持续监控**状态
- 每 1.5 秒截图 OCR 检查一次文字区域内容
- 当检测到文字内容发生变化（新文章下发），自动开始打字
- 打完当前文章后，回到监控状态，等待下一篇
- 适用场景：网络模式（ConnectMode=2），服务器随机分发文章

## GUI 面板布局

```
┌────────────────────────────────────┐
│  旋风打字自动化工具                  │
│                                    │
│  工作模式: ○ 手动练习  ● 服务器下发   │
│                                    │
│  打字速度: ───●──────── 80 字/分钟   │
│                                    │
│  状态: 监控中，等待文章下发...        │
│                                    │
│  [▶ 开始监控]  [⏸ 暂停]             │
│                                    │
│  当前文章预览:                      │
│  ┌──────────────────────────────┐  │
│  │ (OCR 识别到的文字内容预览)      │  │
│  └──────────────────────────────┘  │
└────────────────────────────────────┘
```

## 数据流

### 手动模式下的一次完整流程
```
1. 用户点击"开始"按钮
2. AutomationCore 调用 WindowLocator → 获取目标窗口句柄
3. WindowLocator 找最大子控件 → 定位截图区域
4. TextDetector 截图 + Tesseract OCR → 获取当前文章文字
5. 文字显示在预览框，通知 KeyboardEmulator 开始打字
6. KeyboardEmulator 逐字符输出，间隔由速度设置决定
7. 所有字符发送完毕 → 状态更新"已完成"
```

### 服务器下发模式的循环流程
```
1. 用户点击"开始监控"按钮
2. [监控循环] 每 1.5 秒：
   a. TextDetector OCR 抓取当前文字
   b. 与上次记录的文字比对
   c. 如果不同（新文章出现）→ 进入步骤 3
3. 文字显示在预览框，通知 KeyboardEmulator 开始打字
4. KeyboardEmulator 打完所有字符
5. 状态更新"等待下一篇"，回到步骤 2
```

## 线程模型

- **主线程**：gui 事件循环
- **监控线程**：定时 OCR 检测文字（daemon，随主线程退出）
- **打字线程**：执行键盘模拟（daemon，可通过暂停中断）

线程间通过 `threading.Event` 通信：
- `pause_event`：打字线程检查此事件，设置时暂停输出
- `stop_event`：打字线程检查此事件，设置时终止

## 错误处理

- 窗口未找到：提示用户确认 WhirlwindTyper 已启动
- 文字检测失败：Tesseract 未安装时提示，无中文语言包时退回英文 OCR
- 键盘模拟异常：捕获 pyautogui 异常，显示错误信息
- 线程安全：所有 GUI 更新通过 `after()` 调度到主线程

## 依赖项

```
pywin32       - Windows API 调用（窗口查找、GetWindowText）
pyautogui     - 截图 + 键盘模拟
pyperclip     - 剪贴板操作（中文粘贴）
customtkinter - GUI 界面
Pillow        - 截图处理
pytesseract   - OCR 引擎 Python 绑定
Tesseract-OCR - OCR 引擎桌面程序（需单独安装，含 chi_sim 语言包）
```

## 文件结构

```
dzxf/
├── auto_type.py          # 主入口 + GUI
├── window_locator.py     # 窗口查找模块
├── text_detector.py      # 文字检测模块（OCR 主方案）
├── keyboard_emulator.py  # 键盘模拟模块
└── README.md
```
