"""
ui/widgets.py
Reusable custom UI widgets.
"""

import time
import tkinter as tk
import customtkinter as ctk
from core.downloader import DownloadItem, DownloadStatus


class QueueCard(ctk.CTkFrame):
    """
    A card widget displaying a single download item's state.
    Shows title, progress bar, speed, ETA, and control buttons.
    """

    STATUS_COLORS = {
        DownloadStatus.QUEUED:        ("text_secondary", "—"),
        DownloadStatus.FETCHING_INFO: ("info",           "Fetching info..."),
        DownloadStatus.DOWNLOADING:   ("accent",         "Downloading"),
        DownloadStatus.MERGING:       ("warning",        "Merging..."),
        DownloadStatus.FINISHED:      ("success",        "✓ Finished"),
        DownloadStatus.ERROR:         ("error",          "✕ Error"),
        DownloadStatus.CANCELLED:     ("text_muted",     "Cancelled"),
        DownloadStatus.PAUSED:        ("warning",        "⏸ Paused"),
    }

    def __init__(self, parent, item: DownloadItem, colors: dict,
                 on_start, on_cancel, on_pause, on_remove):
        c = colors
        super().__init__(parent, fg_color=c["bg_card"], corner_radius=10)
        self._item = item
        self._colors = c
        self._on_start = on_start
        self._on_cancel = on_cancel
        self._on_pause = on_pause
        self._on_remove = on_remove

        self.grid_columnconfigure(0, weight=1)
        self._build()

    def _build(self):
        c = self._colors
        item = self._item

        # ── Row 0: Title + buttons ──
        top_row = ctk.CTkFrame(self, fg_color="transparent")
        top_row.grid(row=0, column=0, padx=14, pady=(12, 4), sticky="ew")
        top_row.grid_columnconfigure(0, weight=1)

        # Type tag
        if item.is_playlist:
            tag, tag_bg = "PLAYLIST", c["tag_playlist"]
        elif "shorts" in item.url.lower():
            tag, tag_bg = "SHORT", c["tag_shorts"]
        else:
            tag, tag_bg = "VIDEO", c["tag_single"]

        ctk.CTkLabel(
            top_row, text=tag,
            font=("Segoe UI", 9, "bold"), text_color=c["text_secondary"],
            fg_color=tag_bg, corner_radius=4,
            width=56, height=18,
        ).pack(side="left", padx=(0, 8))

        # Title
        title_text = item.title or item.url[:60]
        self._title_label = ctk.CTkLabel(
            top_row, text=title_text[:70],
            font=("Segoe UI", 11, "bold"), text_color=c["text_primary"],
            anchor="w",
        )
        self._title_label.pack(side="left", fill="x", expand=True)

        # Buttons
        btn_frame = ctk.CTkFrame(top_row, fg_color="transparent")
        btn_frame.pack(side="right")

        self._start_btn = ctk.CTkButton(
            btn_frame, text="▶ Start",
            font=("Segoe UI", 10, "bold"),
            width=70, height=28,
            fg_color=c["accent"], hover_color=c["accent_hover"],
            text_color="white", corner_radius=6,
            command=lambda: self._on_start(self._item),
        )
        self._start_btn.pack(side="left", padx=(0, 4))

        self._pause_btn = ctk.CTkButton(
            btn_frame, text="⏸",
            font=("Segoe UI", 10),
            width=32, height=28,
            fg_color=c["bg_input"], hover_color=c["bg_hover"],
            text_color=c["text_secondary"], corner_radius=6,
            command=lambda: self._on_pause(self._item),
        )
        self._pause_btn.pack(side="left", padx=(0, 4))

        self._cancel_btn = ctk.CTkButton(
            btn_frame, text="✕",
            font=("Segoe UI", 10),
            width=32, height=28,
            fg_color=c["bg_input"], hover_color=c["bg_hover"],
            text_color=c["error"], corner_radius=6,
            command=lambda: self._on_cancel(self._item),
        )
        self._cancel_btn.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            btn_frame, text="🗑",
            font=("Segoe UI", 10),
            width=32, height=28,
            fg_color=c["bg_input"], hover_color=c["bg_hover"],
            text_color=c["text_muted"], corner_radius=6,
            command=lambda: self._on_remove(self._item),
        ).pack(side="left")

        # ── Row 1: Progress bar ──
        self._progress_bar = ctk.CTkProgressBar(
            self, height=6, corner_radius=3,
            fg_color=c["progress_bg"],
            progress_color=c["accent"],
        )
        self._progress_bar.grid(row=1, column=0, padx=14, pady=(0, 4), sticky="ew")
        self._progress_bar.set(0)

        # ── Row 2: Stats ──
        stats_row = ctk.CTkFrame(self, fg_color="transparent")
        stats_row.grid(row=2, column=0, padx=14, pady=(0, 12), sticky="ew")

        self._status_label = ctk.CTkLabel(
            stats_row, text="Queued",
            font=("Segoe UI", 10), text_color=c["text_muted"],
        )
        self._status_label.pack(side="left")

        self._pct_label = ctk.CTkLabel(
            stats_row, text="",
            font=("Segoe UI", 10, "bold"), text_color=c["accent"],
        )
        self._pct_label.pack(side="left", padx=(8, 0))

        self._speed_label = ctk.CTkLabel(
            stats_row, text="",
            font=("Segoe UI", 10), text_color=c["text_secondary"],
        )
        self._speed_label.pack(side="left", padx=(10, 0))

        self._eta_label = ctk.CTkLabel(
            stats_row, text="",
            font=("Segoe UI", 10), text_color=c["text_secondary"],
        )
        self._eta_label.pack(side="left", padx=(10, 0))

        self._size_label = ctk.CTkLabel(
            stats_row, text="",
            font=("Segoe UI", 10), text_color=c["text_muted"],
        )
        self._size_label.pack(side="right")

    def update_state(self, item: DownloadItem):
        """Refresh the card to reflect the current item state."""
        c = self._colors
        self._item = item

        color_key, status_text = self.STATUS_COLORS.get(
            item.status, ("text_secondary", str(item.status.value))
        )
        color = c.get(color_key, c["text_secondary"])

        # Update title if we have a real one
        if item.title and len(item.title) > 3:
            self._title_label.configure(text=item.title[:70])

        self._status_label.configure(text=status_text, text_color=color)

        pct = item.progress
        self._progress_bar.set(pct / 100)
        if pct > 0:
            self._pct_label.configure(text=f"{pct:.1f}%")
        else:
            self._pct_label.configure(text="")

        if item.speed:
            self._speed_label.configure(text=f"⬇ {item.speed}")
        else:
            self._speed_label.configure(text="")

        if item.eta and item.eta != "--":
            self._eta_label.configure(text=f"ETA {item.eta}")
        else:
            self._eta_label.configure(text="")

        if item.file_size:
            size_text = f"{item.downloaded_bytes} / {item.file_size}"
            self._size_label.configure(text=size_text)

        # Update progress bar color based on status
        if item.status == DownloadStatus.FINISHED:
            self._progress_bar.configure(progress_color=c["success"])
            self._start_btn.configure(state="disabled", fg_color=c["bg_input"])
            self._pause_btn.configure(state="disabled")
            self._cancel_btn.configure(state="disabled")
        elif item.status == DownloadStatus.ERROR:
            self._progress_bar.configure(progress_color=c["error"])
        elif item.status == DownloadStatus.PAUSED:
            self._progress_bar.configure(progress_color=c["warning"])
            self._pause_btn.configure(text="▶")
        elif item.status in (DownloadStatus.CANCELLED,):
            self._start_btn.configure(state="disabled", fg_color=c["bg_input"])
        elif item.status == DownloadStatus.DOWNLOADING:
            self._start_btn.configure(state="disabled", fg_color=c["bg_input"])
            self._pause_btn.configure(text="⏸", state="normal")


class LogConsole(ctk.CTkTextbox):
    """
    Scrollable text console for activity logging.
    Supports colored levels: info, warn, error, success.
    """

    LEVEL_COLORS = {
        "info":    "#94A3B8",
        "warn":    "#F59E0B",
        "error":   "#EF4444",
        "success": "#22C55E",
        "debug":   "#64748B",
    }

    def __init__(self, parent, colors: dict):
        c = colors
        super().__init__(
            parent,
            font=("Consolas", 10),
            fg_color=c["bg_primary"],
            text_color=c["text_secondary"],
            border_width=0,
            wrap="word",
            state="disabled",
            height=140,
        )
        self._colors = c
        # Configure tags for colored text
        for level, color in self.LEVEL_COLORS.items():
            self.tag_config(level, foreground=color)
        self.tag_config("time", foreground=c["text_muted"])

    def append(self, message: str, level: str = "info"):
        self.configure(state="normal")
        ts = time.strftime("%H:%M:%S")
        self.insert("end", f"[{ts}] ", "time")
        self.insert("end", message + "\n", level)
        self.see("end")
        self.configure(state="disabled")

    def clear(self):
        self.configure(state="normal")
        self.delete("1.0", "end")
        self.configure(state="disabled")


class StatusBar(ctk.CTkFrame):
    """
    Bottom status bar showing current download summary.
    """

    def __init__(self, parent, colors: dict):
        c = colors
        super().__init__(parent, fg_color=c["bg_secondary"], corner_radius=8, height=36)
        self._colors = c
        self.grid_propagate(False)
        self.grid_columnconfigure(1, weight=1)

        self._dot = ctk.CTkLabel(
            self, text="●", font=("Segoe UI", 12),
            text_color=c["text_muted"], width=20,
        )
        self._dot.grid(row=0, column=0, padx=(12, 4), pady=8)

        self._msg_label = ctk.CTkLabel(
            self, text="Ready",
            font=("Segoe UI", 10), text_color=c["text_muted"], anchor="w",
        )
        self._msg_label.grid(row=0, column=1, sticky="ew")

        self._speed_label = ctk.CTkLabel(
            self, text="",
            font=("Segoe UI", 10, "bold"), text_color=c["accent"],
        )
        self._speed_label.grid(row=0, column=2, padx=(0, 12))

    def update(self, item: DownloadItem):
        c = self._colors
        if item.status == DownloadStatus.DOWNLOADING:
            title = (item.title or item.url)[:40]
            pct = f"{item.progress:.0f}%"
            self._msg_label.configure(
                text=f"Downloading: {title}... {pct}",
                text_color=c["text_primary"],
            )
            self._dot.configure(text_color=c["accent"])
            if item.speed:
                self._speed_label.configure(text=item.speed)
        elif item.status == DownloadStatus.MERGING:
            self._msg_label.configure(text="Merging video + audio...", text_color=c["warning"])
            self._dot.configure(text_color=c["warning"])
        elif item.status == DownloadStatus.FINISHED:
            self._msg_label.configure(text="Download complete!", text_color=c["success"])
            self._dot.configure(text_color=c["success"])
            self._speed_label.configure(text="")

    def set_idle(self):
        c = self._colors
        self._msg_label.configure(text="Ready", text_color=c["text_muted"])
        self._dot.configure(text_color=c["text_muted"])
        self._speed_label.configure(text="")
