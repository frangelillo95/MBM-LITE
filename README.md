# MBM-LITE

Lightweight incremental backup manager for Windows with direct file synchronization and no restore points or disk images.

---

## Features

- Incremental file backup
- Direct folder-to-folder synchronization
- Lightweight and transparent workflow
- Pause / Resume jobs
- Runtime status indicators:
  - READY
  - RUNNING
  - PAUSED
  - ERROR
- Automatic scheduler
- Retry logic on copy failures
- Error tracking and reporting
- Windows-native GUI
- Standalone Windows installer

---

## Screenshots

_Add screenshots here_

---

## Installation

Download the latest installer from the Releases section.

---

## Requirements

- Windows 10 / 11
- Local or external storage devices
- Python not required for installer version

---

## Build From Source

Install dependencies:

```bash
pip install -r requirements.txt
```

Build executable:

```bash
build_exe.bat
```

---

## Technologies

- Python
- Tkinter
- PyInstaller

---

## Project Status

Stable release: **v2.0.4**

---

## License

MIT License
