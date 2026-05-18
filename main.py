"""
YTDownloader - Professional YouTube Downloader
Entry point for the application.
"""

import sys
import os

# Ensure the app directory is in the path (important for PyInstaller)
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

sys.path.insert(0, BASE_DIR)

from ui.app import YTDownloaderApp

if __name__ == "__main__":
    app = YTDownloaderApp()
    app.mainloop()
