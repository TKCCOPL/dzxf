# WhirlwindTyper（旋风打字）

一个 **2008-2009 年**的 Windows 打字练习软件。已编译的遗留应用程序，没有源代码，仅包含可执行文件及其配套数据资产。

## 核心文件

| 文件 | 说明 |
|------|------|
| `WhirlwindTyper.exe` | 主程序（524 KB），典型的 Delphi/VB6 时代 Windows 应用 |
| `WhirlwindTyper.mdb` | Microsoft Access 数据库，存储用户进度、成绩、练习数据 |
| `set.ini` | 配置文件，含数据库连接、练习时长（默认300秒）、配色方案等 |

## 练习内容模块

**material/ 目录** 包含各类打字练习素材：

| 子目录 | 用途 |
|--------|------|
| `CP/` | 数字键位练习（小键盘），5个级别，每个级别5课 |
| `abc/` | 英文字母练习，按 A-Z 分文件 |
| `Num/` | 数字行练习（1-9） |
| `wb/` | **五笔字型**输入法练习，按课次和字根分类 |
| `fingering/` | 英文单词指法练习（word1/word2） |
| `常用字/` | 按使用频率分级的常用汉字（42、100、300、500、1000、1500字） |

## 文章练习

**文章/ 目录** 包含长篇打字练习：

| 子目录 | 用途 |
|--------|------|
| `中文文章/`、`英文文章/` | 中英文文章练习 |
| `中英综合练习/`、`中英数综合练习/`、`中数综合练习/` | 混合模式练习 |
| `书本对照/` | 书本对照录入 |
| `打字考试/` | 考试模式 |

## 图片资源

`Image/` 目录包含键盘键位示意图（BMP格式），支持 **800×600** 和 **1024×768** 两种分辨率。

## 运行模式

`set.ini` 中的 `ConnectMode` 控制两种模式：

- **Mode 1（单机模式）**：直接读写本地 Access 数据库
- **Mode 2（网络模式）**：通过 `ServerIP:9307` 连接 MySQL 服务器，用于多媒体教室多用户场景

## 配置文件说明（set.ini）

```ini
DBName=WhirlwindTyper.mdb    # 数据库文件路径
ExerciseTime=300             # 默认练习时长（秒）
ConnectMode=1                # 1=单机, 2=网络
ServerIP=                    # 网络模式服务器IP
ServerPort=9307              # 网络模式端口
```

颜色设置：

| 配置项 | 含义 |
|--------|------|
| `TextNormalColor` / `TextNormalBackColor` | 未输入文字颜色/背景 |
| `TextFinishedColor` / `TextFinishedBackColor` | 已完成文字颜色/背景 |
| `TextSelectedColor` / `TextSelectedBackColor` | 当前选中文字颜色/背景 |
| `TextErrorColor` / `TextErrorBackColor` | 错误文字颜色/背景 |
