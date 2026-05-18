# ytdownloader.spec
# PyInstaller specification file for building YTDownloader.exe
# Run with: pyinstaller ytdownloader.spec

import sys
import os
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None

# Collect all CustomTkinter assets (themes, fonts, images)
ctk_datas = collect_data_files('customtkinter')

# Collect yt-dlp data files
ytdlp_datas = collect_data_files('yt_dlp')

a = Analysis(
    ['main.py'],
    pathex=['.'],
    binaries=[
        # Include ffmpeg.exe and ffprobe.exe if they are in a local 'ffmpeg' folder
        # ('ffmpeg/ffmpeg.exe',  'ffmpeg'),
        # ('ffmpeg/ffprobe.exe', 'ffmpeg'),
    ],
    datas=[
        *ctk_datas,
        *ytdlp_datas,
        # Add your app icon if you have one:
        # ('assets/icon.ico', 'assets'),
    ],
    hiddenimports=[
        'customtkinter',
        'PIL',
        'PIL._imagingtk',
        'PIL.ImageTk',
        'PIL.Image',
        'yt_dlp',
        'yt_dlp.extractor',
        'yt_dlp.extractor.youtube',
        'tkinter',
        'tkinter.ttk',
        'tkinterdnd2',
        *collect_submodules('yt_dlp'),
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['matplotlib', 'numpy', 'scipy', 'pandas'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='YTDownloader',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,            # Compress with UPX if available
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,       # No console window — GUI only
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # icon='assets/icon.ico',   # Uncomment after adding an icon
    version_file=None,
    uac_admin=False,
)
