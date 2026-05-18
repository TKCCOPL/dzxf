# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

This is **WhirlwindTyper (旋风打字)**, a legacy Chinese typing tutor for Windows, distributed as a compiled binary with accompanying data assets. There is no source code — the `.exe` is a pre-built Delphi/VB6-era Windows application from 2008-2009.

## File structure

- `WhirlwindTyper.exe` — Compiled Windows application (524 KB)
- `WhirlwindTyper.mdb` — Microsoft Access database (user progress, scores, exercise data)
- `set.ini` — Application configuration (DB connection, exercise timing, color theme, server settings)

## Content modules (material/)

Each subdirectory holds typing practice content loaded by the application:

| Directory | Purpose |
|-----------|---------|
| `CP/` | Numeric keypad drills (CP = 数字键位). Files named `CP{level}-{lesson}.TXT`, referenced by `info.txt` |
| `abc/` | English letter-by-letter practice (A.txt through Z.txt) |
| `Num/` | Number row practice (1.txt - 9.txt) |
| `wb/` | Wubi (五笔) Chinese input method drills, organized by lesson number and radical sets (`jm*.txt`, `sbm.txt`) |
| `fingering/` | English vocabulary word lists (`word1.txt`, `word2.txt`) |
| `常用字/` | Common Chinese characters by frequency tier (42, 100, 300, 500, 1000, 1500) |
| `*.dat` files | Binary lesson index/metadata loaded by the application |

## Article modules (文章/)

Long-form typing practice texts in multiple modes:
- `中文文章/` — Chinese articles
- `英文文章/` — English articles
- `中英综合练习/` — Mixed Chinese-English exercises
- `中英数综合练习/` — Chinese-English-number mixed exercises
- `中数综合练习/` — Chinese-number mixed exercises
- `书本对照/` — Book transcription practice
- `打字考试/` — Typing exam mode texts

## Image assets (Image/)

Keyboard layout illustrations in BMP format at two resolutions (`800 600/` and `1024 768/`). Files are numbered to correspond to key positions and lesson indicators.

## Configuration (set.ini)

Key settings (no section nesting — flat INI format):
- `DBName` — Path to the Access database file
- `ExerciseTime=300` — Default exercise duration in seconds
- `ConnectMode=1` — 1 = standalone (Access DB), 2 = client/server (MySQL via `ServerIP`/`ServerPort`)
- Color settings: `TextNormalColor`, `TextFinishedColor`, `TextSelectedColor`, `TextErrorColor` with corresponding back colors

## Database

`WhirlwindTyper.mdb` is a Microsoft Access (JET) database. In `ConnectMode=1`, the app reads/writes directly to this file. When `ConnectMode=2`, it connects to a MySQL server for multi-user classroom setups.
