"""
core/downloader.py
Handles all download logic using yt-dlp.
FIXED: audio missing issue (AV1/Opus incompatibility resolved)
"""

import os
import sys
import re
import time
import threading
import yt_dlp
from dataclasses import dataclass
from typing import Callable, Optional
from enum import Enum


class DownloadStatus(Enum):
    QUEUED = "queued"
    FETCHING_INFO = "fetching_info"
    DOWNLOADING = "downloading"
    MERGING = "merging"
    FINISHED = "finished"
    ERROR = "error"
    CANCELLED = "cancelled"
    PAUSED = "paused"


@dataclass
class DownloadItem:
    url: str
    output_dir: str
    quality: str = "1080"
    audio_only: bool = False
    item_id: str = ""
    status: DownloadStatus = DownloadStatus.QUEUED
    progress: float = 0.0
    speed: str = ""
    eta: str = ""
    file_size: str = ""
    downloaded_bytes: str = ""
    error_msg: str = ""
    is_playlist: bool = False

    def __post_init__(self):
        if not self.item_id:
            import uuid
            self.item_id = str(uuid.uuid4())[:8]


class DownloadEngine:

    def __init__(self):
        self._cancel_flags = {}
        self._pause_flags = {}
        self._lock = threading.Lock()

    # ─────────────────────────────────────────────
    # FFmpeg detection
    # ─────────────────────────────────────────────
    def get_ffmpeg_path(self) -> Optional[str]:
        if getattr(sys, 'frozen', False):
            base = sys._MEIPASS
        else:
            base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

        candidates = [
            os.path.join(base, "ffmpeg", "ffmpeg.exe"),
            os.path.join(base, "bin", "ffmpeg.exe"),
            "ffmpeg",
        ]

        for path in candidates:
            if path == "ffmpeg":
                return None
            if os.path.isfile(path):
                return os.path.dirname(path)

        return None

    # ─────────────────────────────────────────────
    # Build yt-dlp options (FINAL FIX)
    # ─────────────────────────────────────────────
    def _build_ydl_opts(self, item, progress_hook, post_hook):

        if item.audio_only:
            fmt = "bestaudio[ext=m4a]/bestaudio/best"
            postprocessors = [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }]
            ext = "mp3"

        else:
            height = item.quality.replace("p", "")

            # 🔥 FINAL FIX: BLOCK AV1 + VP9 (causing audio issues)
            fmt = (
                f"bestvideo[ext=mp4][height<={height}][vcodec!*=av01][vcodec!*=vp9]"
                f"+bestaudio[ext=m4a]/best[ext=mp4]/best"
            )

            postprocessors = [{
                'key': 'FFmpegVideoConvertor',
                'preferedformat': 'mp4',
            }]
            ext = "mp4"

        outtmpl = os.path.join(item.output_dir, f"%(title)s.{ext}")

        opts = {
            'format': fmt,
            'outtmpl': outtmpl,
            'merge_output_format': 'mp4',

            # 🔥 stability flags
            'prefer_ffmpeg': True,
            'keepvideo': False,

            'postprocessors': postprocessors,

            'concurrent_fragment_downloads': 4,
            'retries': 10,
            'fragment_retries': 10,

            'progress_hooks': [progress_hook],
            'postprocessor_hooks': [post_hook],

            'noplaylist': not item.is_playlist,
            'quiet': True,
            'no_warnings': True,
        }

        ffmpeg_location = self.get_ffmpeg_path()
        if ffmpeg_location:
            opts['ffmpeg_location'] = ffmpeg_location

        return opts

    # ─────────────────────────────────────────────
    # Download engine
    # ─────────────────────────────────────────────
    def download(self, item, on_progress, on_complete, on_error):

        cancel_event = threading.Event()
        pause_event = threading.Event()

        with self._lock:
            self._cancel_flags[item.item_id] = cancel_event
            self._pause_flags[item.item_id] = pause_event

        def progress_hook(d):

            if cancel_event.is_set():
                raise yt_dlp.utils.DownloadCancelled()

            while pause_event.is_set():
                item.status = DownloadStatus.PAUSED
                on_progress(item)
                time.sleep(0.5)

            if d.get('status') == 'downloading':
                item.status = DownloadStatus.DOWNLOADING

                downloaded = d.get('downloaded_bytes', 0)
                total = d.get('total_bytes') or d.get('total_bytes_estimate') or 0

                item.progress = (downloaded / total * 100) if total else 0
                item.speed = str(d.get('speed') or "--")
                item.eta = str(d.get('eta') or "--")

                on_progress(item)

            elif d.get('status') == 'finished':
                item.status = DownloadStatus.MERGING
                item.progress = 99
                on_progress(item)

        def post_hook(d):
            if d.get('status') == 'finished':
                item.status = DownloadStatus.FINISHED
                item.progress = 100
                on_progress(item)

        def run():
            item.status = DownloadStatus.FETCHING_INFO
            on_progress(item)

            try:
                opts = self._build_ydl_opts(item, progress_hook, post_hook)

                with yt_dlp.YoutubeDL(opts) as ydl:
                    ydl.download([item.url])

            except Exception as e:
                item.status = DownloadStatus.ERROR
                item.error_msg = str(e)
                on_error(item, str(e))

            else:
                item.status = DownloadStatus.FINISHED
                item.progress = 100
                on_complete(item)

        t = threading.Thread(target=run, daemon=True)
        t.start()
        return t