# YTDownloader — Complete Setup & Build Guide

## Folder Structure

```
YTDownloader/
├── main.py                  ← Entry point
├── requirements.txt         ← Python dependencies
├── ytdownloader.spec        ← PyInstaller config
├── assets/
│   └── icon.ico             ← App icon (add your own)
├── ffmpeg/                  ← Place ffmpeg binaries here
│   ├── ffmpeg.exe
│   └── ffprobe.exe
├── core/
│   ├── __init__.py
│   ├── downloader.py        ← yt-dlp download engine
│   ├── history.py           ← Download history
│   └── settings.py          ← Persistent settings
└── ui/
    ├── __init__.py
    ├── app.py               ← Main window
    ├── theme.py             ← Colors & fonts
    ├── widgets.py           ← QueueCard, LogConsole, StatusBar
    └── dialogs.py           ← Modal dialogs
```

---

## Step 1 — Install Python

Download **Python 3.11** (recommended) from https://www.python.org/downloads/
During installation, check **"Add Python to PATH"**.

---

## Step 2 — Install ffmpeg

### Option A — Automatic (winget)
```powershell
winget install Gyan.FFmpeg
```
Then restart your terminal so ffmpeg is on PATH.

### Option B — Manual
1. Download ffmpeg from https://ffmpeg.org/download.html  
   (Use the "Windows builds by BtbN" link — choose `ffmpeg-master-latest-win64-gpl.zip`)
2. Extract and copy `ffmpeg.exe` and `ffprobe.exe` into the `ffmpeg/` folder inside this project.
3. Also uncomment the `binaries` lines in `ytdownloader.spec` so they get bundled into the `.exe`.

---

## Step 3 — Install Python Dependencies

Open a terminal in the `YTDownloader/` folder and run:

```powershell
pip install -r requirements.txt
```

This installs:
- `customtkinter` — Modern Tkinter UI
- `yt-dlp` — YouTube downloader engine
- `Pillow` — Image/thumbnail support
- `pyinstaller` — EXE builder
- `tkinterdnd2` — Drag & drop support

---

## Step 4 — Run in Development Mode

```powershell
python main.py
```

---

## Step 5 — Build the `.exe`

### Quick build (one-file EXE):
```powershell
pyinstaller ytdownloader.spec
```

Or if you prefer the command-line directly:
```powershell
pyinstaller main.py ^
  --onefile ^
  --windowed ^
  --name YTDownloader ^
  --hidden-import customtkinter ^
  --hidden-import yt_dlp ^
  --hidden-import PIL ^
  --collect-all customtkinter ^
  --collect-all yt_dlp ^
  --noconfirm
```

The output `.exe` will be in the `dist/` folder:
```
dist/
└── YTDownloader.exe    ← Standalone, no Python required!
```

---

## Step 6 — Add a Custom Icon (Optional)

1. Create or download a `.ico` file (e.g., from https://icon-icons.com).
2. Save it as `assets/icon.ico`.
3. In `ytdownloader.spec`, uncomment the `icon=` and `datas` lines that reference it.
4. Rebuild.

---

## Step 7 — Bundle ffmpeg into the EXE (Optional)

Place `ffmpeg.exe` and `ffprobe.exe` in the `ffmpeg/` folder, then in `ytdownloader.spec` uncomment:

```python
binaries=[
    ('ffmpeg/ffmpeg.exe',  'ffmpeg'),
    ('ffmpeg/ffprobe.exe', 'ffmpeg'),
],
```

Then rebuild. The app's `get_ffmpeg_path()` method will automatically find them inside the bundle.

---

## Updating yt-dlp

Inside the app, click **"↻ Update yt-dlp"** in the sidebar. This runs:
```
pip install --upgrade yt-dlp
```

You can also run this manually at any time.

---

## Troubleshooting

| Problem | Solution |
|---|---|
| "ffmpeg not found" | Install ffmpeg or place binaries in `ffmpeg/` folder |
| "ModuleNotFoundError: customtkinter" | Run `pip install customtkinter` |
| EXE is slow to open | Normal for PyInstaller — first launch unpacks files |
| Download stuck at 0% | Check your internet; try a different URL |
| "Sign in" error for age-restricted | yt-dlp limitation for age-restricted content |
| Antivirus flags the EXE | Add exception; false positive common for PyInstaller EXEs |

---

## Data Locations

| Data | Location |
|---|---|
| Download history | `%USERPROFILE%\.ytdownloader\history.json` |
| Settings | `%USERPROFILE%\.ytdownloader\settings.json` |
| Downloads | `%USERPROFILE%\Downloads\YTDownloader\` (default) |

---

## Features Summary

- ✅ Single videos, playlists, Shorts, audio-only (MP3)
- ✅ Quality selection: 4K, 1440p, 1080p, 720p, 480p, 360p
- ✅ Progress bar, speed, ETA, file size display
- ✅ Download queue with Start / Pause / Resume / Cancel / Remove
- ✅ Clipboard auto-detect for YouTube URLs
- ✅ Drag & drop URL support (requires tkinterdnd2)
- ✅ Thumbnail preview after fetching info
- ✅ Persistent download history with re-download
- ✅ Dark / Light mode toggle
- ✅ Settings page (folder, clipboard, fragments)
- ✅ One-click yt-dlp updater
- ✅ Threading — UI never freezes
- ✅ Retry on network errors
- ✅ PyInstaller-ready, no Python needed on target machine
