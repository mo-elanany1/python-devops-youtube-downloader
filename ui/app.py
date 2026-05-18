"""
ui/app.py
Main application window using CustomTkinter.
Implements the full GUI with all professional features.
"""

import os
import sys
import time
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk
import urllib.request
import io

from core import DownloadEngine, DownloadItem, DownloadStatus, HistoryManager, HistoryEntry, SettingsManager
from ui.theme import DARK, LIGHT, FONTS
from ui.widgets import QueueCard, LogConsole, StatusBar
from ui.dialogs import SettingsDialog, HistoryDialog


ctk.set_default_color_theme("dark-blue")


class YTDownloaderApp(ctk.CTk):
    """
    Main application window.
    Layout: sidebar navigation + main content area.
    """

    APP_TITLE = "YTDownloader"
    APP_VERSION = "2.0.0"
    MIN_WIDTH = 1000
    MIN_HEIGHT = 680

    def __init__(self):
        super().__init__()

        # Core services
        self.engine = DownloadEngine()
        self.history = HistoryManager()
        self.settings = SettingsManager()

        # State
        self._queue: list[DownloadItem] = []
        self._queue_cards: dict[str, "QueueCard"] = {}
        self._current_page = "download"
        self._theme_name = self.settings.get("theme", "dark")
        self._colors = DARK if self._theme_name == "dark" else LIGHT
        self._clipboard_monitor_active = False
        self._last_clipboard = ""

        # Window setup
        self.title(f"{self.APP_TITLE} v{self.APP_VERSION}")
        self.geometry("1100x720")
        self.minsize(self.MIN_WIDTH, self.MIN_HEIGHT)
        self._apply_theme()

        # Build UI
        self._build_layout()
        self._build_sidebar()
        self._build_main_area()
        self._build_download_page()
        self._build_queue_page()
        self._build_history_page()
        self._build_settings_page()

        # Show default page
        self._show_page("download")

        # Start clipboard monitor if enabled
        if self.settings.get("auto_detect_clipboard"):
            self._start_clipboard_monitor()

        # Drag & drop support
        self._setup_drag_drop()

        # Protocol
        self.protocol("WM_DELETE_WINDOW", self._on_close)

    # ── Theme ──────────────────────────────────────────────────────────────

    def _apply_theme(self):
        mode = "dark" if self._theme_name == "dark" else "light"
        ctk.set_appearance_mode(mode)
        c = self._colors
        self.configure(fg_color=c["bg_primary"])

    def _toggle_theme(self):
        self._theme_name = "light" if self._theme_name == "dark" else "dark"
        self._colors = DARK if self._theme_name == "dark" else LIGHT
        self.settings.set("theme", self._theme_name)
        self._apply_theme()
        self._refresh_all_colors()

    def _refresh_all_colors(self):
        """Re-apply colors to all widgets after theme change."""
        c = self._colors
        self.sidebar.configure(fg_color=c["bg_secondary"])
        self.main_frame.configure(fg_color=c["bg_primary"])
        self._theme_btn.configure(
            text="☀ Light" if self._theme_name == "dark" else "☾ Dark"
        )

    # ── Layout ─────────────────────────────────────────────────────────────

    def _build_layout(self):
        c = self._colors
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.sidebar = ctk.CTkFrame(
            self, width=200, corner_radius=0, fg_color=c["bg_secondary"]
        )
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_rowconfigure(8, weight=1)
        self.sidebar.grid_propagate(False)

        self.main_frame = ctk.CTkFrame(
            self, corner_radius=0, fg_color=c["bg_primary"]
        )
        self.main_frame.grid(row=0, column=1, sticky="nsew")
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)

    def _build_sidebar(self):
        c = self._colors
        s = self.sidebar

        # Logo
        logo_frame = ctk.CTkFrame(s, fg_color="transparent")
        logo_frame.grid(row=0, column=0, padx=16, pady=(24, 8), sticky="ew")

        ctk.CTkLabel(
            logo_frame,
            text="▶",
            font=("Segoe UI", 22, "bold"),
            text_color=c["accent"],
        ).pack(side="left", padx=(0, 6))
        ctk.CTkLabel(
            logo_frame,
            text="YTDown",
            font=("Segoe UI Black", 16, "bold"),
            text_color=c["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            s,
            text=f"v{self.APP_VERSION}",
            font=FONTS["tiny"],
            text_color=c["text_muted"],
        ).grid(row=1, column=0, padx=16, pady=(0, 20), sticky="w")

        # Nav separator
        ctk.CTkFrame(s, height=1, fg_color=c["border"]).grid(
            row=2, column=0, padx=16, sticky="ew", pady=(0, 12)
        )

        # Navigation buttons
        self._nav_buttons = {}
        nav_items = [
            ("download", "⬇  Download",    3),
            ("queue",    "☰  Queue",        4),
            ("history",  "⏱  History",      5),
            ("settings", "⚙  Settings",     6),
        ]

        for page_id, label, row in nav_items:
            btn = ctk.CTkButton(
                s,
                text=label,
                font=FONTS["body"],
                fg_color="transparent",
                text_color=c["text_secondary"],
                hover_color=c["bg_hover"],
                anchor="w",
                corner_radius=8,
                height=38,
                command=lambda p=page_id: self._show_page(p),
            )
            btn.grid(row=row, column=0, padx=12, pady=2, sticky="ew")
            self._nav_buttons[page_id] = btn

        # Spacer (row 8 has weight=1)

        # Theme toggle
        self._theme_btn = ctk.CTkButton(
            s,
            text="☀ Light" if self._theme_name == "dark" else "☾ Dark",
            font=FONTS["small"],
            fg_color="transparent",
            text_color=c["text_muted"],
            hover_color=c["bg_hover"],
            anchor="w",
            corner_radius=8,
            height=32,
            command=self._toggle_theme,
        )
        self._theme_btn.grid(row=9, column=0, padx=12, pady=(0, 8), sticky="ew")

        # Update yt-dlp button
        ctk.CTkButton(
            s,
            text="↻ Update yt-dlp",
            font=FONTS["small"],
            fg_color="transparent",
            text_color=c["text_muted"],
            hover_color=c["bg_hover"],
            anchor="w",
            corner_radius=8,
            height=32,
            command=self._do_update_ytdlp,
        ).grid(row=10, column=0, padx=12, pady=(0, 16), sticky="ew")

    def _show_page(self, page_id: str):
        c = self._colors
        self._current_page = page_id
        for pid, btn in self._nav_buttons.items():
            if pid == page_id:
                btn.configure(
                    fg_color=c["accent_dim"],
                    text_color=c["accent"],
                    font=("Segoe UI", 11, "bold"),
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=c["text_secondary"],
                    font=FONTS["body"],
                )
        for pid, frame in self._pages.items():
            if pid == page_id:
                frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
            else:
                frame.grid_remove()

    # ── Main area pages ────────────────────────────────────────────────────

    def _build_main_area(self):
        self._pages = {}

    def _make_page(self, page_id: str) -> ctk.CTkFrame:
        c = self._colors
        frame = ctk.CTkFrame(self.main_frame, fg_color=c["bg_primary"], corner_radius=0)
        self.main_frame.grid_columnconfigure(0, weight=1)
        self.main_frame.grid_rowconfigure(0, weight=1)
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_rowconfigure(0, weight=1)
        self._pages[page_id] = frame
        return frame

    # ── Download Page ──────────────────────────────────────────────────────

    def _build_download_page(self):
        c = self._colors
        page = self._make_page("download")
        page.grid_rowconfigure(0, weight=0)
        page.grid_rowconfigure(1, weight=0)
        page.grid_rowconfigure(2, weight=1)
        page.grid_rowconfigure(3, weight=0)

        # ── Header ──
        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, padx=32, pady=(28, 0), sticky="ew")

        ctk.CTkLabel(
            header,
            text="Download YouTube Videos",
            font=FONTS["display"],
            text_color=c["text_primary"],
        ).pack(side="left")

        ctk.CTkLabel(
            header,
            text="Single • Playlists • Shorts • Audio",
            font=FONTS["small"],
            text_color=c["text_muted"],
        ).pack(side="left", padx=(12, 0), pady=(6, 0))

        # ── URL Input Card ──
        url_card = ctk.CTkFrame(page, fg_color=c["bg_card"], corner_radius=12)
        url_card.grid(row=1, column=0, padx=32, pady=(20, 0), sticky="ew")
        url_card.grid_columnconfigure(0, weight=1)

        # URL label row
        url_label_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_label_row.grid(row=0, column=0, padx=20, pady=(16, 4), sticky="ew")

        ctk.CTkLabel(
            url_label_row,
            text="YouTube URL",
            font=FONTS["subhead"],
            text_color=c["text_primary"],
        ).pack(side="left")

        self._url_type_label = ctk.CTkLabel(
            url_label_row,
            text="",
            font=FONTS["small"],
            text_color=c["accent"],
        )
        self._url_type_label.pack(side="left", padx=(10, 0))

        # URL entry row
        url_row = ctk.CTkFrame(url_card, fg_color="transparent")
        url_row.grid(row=1, column=0, padx=20, pady=(0, 4), sticky="ew")
        url_row.grid_columnconfigure(0, weight=1)

        self._url_var = tk.StringVar()
        self._url_var.trace_add("write", self._on_url_changed)

        self._url_entry = ctk.CTkEntry(
            url_row,
            textvariable=self._url_var,
            placeholder_text="Paste YouTube link here  (Ctrl+V)",
            font=FONTS["body"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_primary"],
            height=44,
            corner_radius=8,
        )
        self._url_entry.grid(row=0, column=0, sticky="ew", padx=(0, 8))
        self._url_entry.bind("<Return>", lambda e: self._add_to_queue())

        ctk.CTkButton(
            url_row,
            text="✕ Clear",
            font=FONTS["small"],
            width=64,
            height=44,
            fg_color=c["bg_input"],
            hover_color=c["bg_hover"],
            text_color=c["text_secondary"],
            corner_radius=8,
            command=lambda: self._url_var.set(""),
        ).grid(row=0, column=1)

        # Options row
        opts_row = ctk.CTkFrame(url_card, fg_color="transparent")
        opts_row.grid(row=2, column=0, padx=20, pady=(8, 16), sticky="ew")

        # Quality dropdown
        ctk.CTkLabel(
            opts_row, text="Quality:", font=FONTS["small"], text_color=c["text_secondary"]
        ).pack(side="left", padx=(0, 6))

        self._quality_var = ctk.StringVar(value=self.settings.get("default_quality", "1080") + "p")
        quality_menu = ctk.CTkOptionMenu(
            opts_row,
            variable=self._quality_var,
            values=["2160p (4K)", "1440p", "1080p", "720p", "480p", "360p", "Best Available"],
            font=FONTS["small"],
            fg_color=c["bg_input"],
            button_color=c["bg_hover"],
            button_hover_color=c["accent"],
            dropdown_fg_color=c["bg_card"],
            text_color=c["text_primary"],
            width=140,
            corner_radius=8,
        )
        quality_menu.pack(side="left", padx=(0, 16))

        # Audio only
        self._audio_only_var = ctk.BooleanVar(value=self.settings.get("default_audio_only", False))
        ctk.CTkCheckBox(
            opts_row,
            text="Audio Only (MP3)",
            variable=self._audio_only_var,
            font=FONTS["small"],
            text_color=c["text_secondary"],
            fg_color=c["accent"],
            hover_color=c["accent_hover"],
            checkmark_color=c["text_primary"],
            border_color=c["border"],
        ).pack(side="left", padx=(0, 16))

        # Output dir
        ctk.CTkLabel(
            opts_row, text="Save to:", font=FONTS["small"], text_color=c["text_secondary"]
        ).pack(side="left", padx=(0, 6))

        self._output_dir_var = tk.StringVar(
            value=self.settings.get("download_dir")
        )
        dir_entry = ctk.CTkEntry(
            opts_row,
            textvariable=self._output_dir_var,
            font=FONTS["small"],
            fg_color=c["bg_input"],
            border_color=c["border"],
            text_color=c["text_primary"],
            width=200,
            height=32,
            corner_radius=8,
        )
        dir_entry.pack(side="left", padx=(0, 4))

        ctk.CTkButton(
            opts_row,
            text="Browse",
            font=FONTS["small"],
            width=70,
            height=32,
            fg_color=c["bg_input"],
            hover_color=c["bg_hover"],
            text_color=c["text_secondary"],
            corner_radius=8,
            command=self._browse_directory,
        ).pack(side="left")

        # Fetch info + Add to queue buttons
        btn_row = ctk.CTkFrame(url_card, fg_color="transparent")
        btn_row.grid(row=3, column=0, padx=20, pady=(0, 16), sticky="ew")

        self._fetch_btn = ctk.CTkButton(
            btn_row,
            text="🔍 Fetch Info",
            font=FONTS["body"],
            width=120,
            height=42,
            fg_color=c["bg_input"],
            hover_color=c["bg_hover"],
            text_color=c["text_primary"],
            corner_radius=8,
            command=self._fetch_video_info,
        )
        self._fetch_btn.pack(side="left", padx=(0, 10))

        self._add_btn = ctk.CTkButton(
            btn_row,
            text="+ Add to Queue",
            font=("Segoe UI", 11, "bold"),
            width=150,
            height=42,
            fg_color=c["accent"],
            hover_color=c["accent_hover"],
            text_color="white",
            corner_radius=8,
            command=self._add_to_queue,
        )
        self._add_btn.pack(side="left", padx=(0, 10))

        self._download_all_btn = ctk.CTkButton(
            btn_row,
            text="⬇ Download All",
            font=("Segoe UI", 11, "bold"),
            width=150,
            height=42,
            fg_color=c["success"],
            hover_color="#16A34A",
            text_color="white",
            corner_radius=8,
            command=self._start_all_downloads,
        )
        self._download_all_btn.pack(side="left")

        # Info preview panel
        self._info_card = ctk.CTkFrame(url_card, fg_color=c["bg_input"], corner_radius=8)
        self._info_card.grid_columnconfigure(1, weight=1)
        # Hidden by default

        self._thumb_label = ctk.CTkLabel(self._info_card, text="")
        self._thumb_label.grid(row=0, column=0, padx=(12, 10), pady=12, rowspan=3)

        self._info_title_label = ctk.CTkLabel(
            self._info_card, text="", font=FONTS["subhead"],
            text_color=c["text_primary"], anchor="w", wraplength=400,
        )
        self._info_title_label.grid(row=0, column=1, padx=(0, 12), pady=(12, 2), sticky="ew")

        self._info_meta_label = ctk.CTkLabel(
            self._info_card, text="", font=FONTS["small"],
            text_color=c["text_secondary"], anchor="w",
        )
        self._info_meta_label.grid(row=1, column=1, padx=(0, 12), pady=2, sticky="ew")

        self._info_type_label = ctk.CTkLabel(
            self._info_card, text="", font=FONTS["small"],
            text_color=c["accent"], anchor="w",
        )
        self._info_type_label.grid(row=2, column=1, padx=(0, 12), pady=(2, 12), sticky="ew")

        # ── Log Console ──
        log_frame = ctk.CTkFrame(page, fg_color=c["bg_secondary"], corner_radius=12)
        log_frame.grid(row=2, column=0, padx=32, pady=(16, 0), sticky="nsew")
        log_frame.grid_columnconfigure(0, weight=1)
        log_frame.grid_rowconfigure(1, weight=1)

        log_header = ctk.CTkFrame(log_frame, fg_color="transparent")
        log_header.grid(row=0, column=0, padx=16, pady=(12, 4), sticky="ew")

        ctk.CTkLabel(
            log_header, text="Activity Log",
            font=FONTS["subhead"], text_color=c["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            log_header, text="Clear",
            font=FONTS["tiny"], width=50, height=24,
            fg_color="transparent", hover_color=c["bg_hover"],
            text_color=c["text_muted"], corner_radius=6,
            command=lambda: self._log_console.clear(),
        ).pack(side="right")

        self._log_console = LogConsole(log_frame, self._colors)
        self._log_console.grid(row=1, column=0, padx=12, pady=(0, 12), sticky="nsew")

        # ── Status bar ──
        self._status_bar = StatusBar(page, self._colors)
        self._status_bar.grid(row=3, column=0, padx=32, pady=(8, 20), sticky="ew")

    # ── Queue Page ─────────────────────────────────────────────────────────

    def _build_queue_page(self):
        c = self._colors
        page = self._make_page("queue")
        page.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, padx=32, pady=(28, 16), sticky="ew")

        ctk.CTkLabel(
            header, text="Download Queue",
            font=FONTS["display"], text_color=c["text_primary"],
        ).pack(side="left")

        self._queue_count_label = ctk.CTkLabel(
            header, text="0 items",
            font=FONTS["small"], text_color=c["text_muted"],
        )
        self._queue_count_label.pack(side="left", padx=(12, 0), pady=6)

        ctk.CTkButton(
            header, text="Clear Finished",
            font=FONTS["small"], width=110, height=32,
            fg_color=c["bg_card"], hover_color=c["bg_hover"],
            text_color=c["text_secondary"], corner_radius=8,
            command=self._clear_finished_queue,
        ).pack(side="right")

        # Scrollable queue container
        self._queue_scroll = ctk.CTkScrollableFrame(
            page, fg_color=c["bg_secondary"], corner_radius=12,
        )
        self._queue_scroll.grid(row=1, column=0, padx=32, pady=(0, 20), sticky="nsew")
        self._queue_scroll.grid_columnconfigure(0, weight=1)

        self._empty_queue_label = ctk.CTkLabel(
            self._queue_scroll,
            text="Queue is empty.\nAdd URLs from the Download tab.",
            font=FONTS["body"],
            text_color=c["text_muted"],
        )
        self._empty_queue_label.pack(pady=40)

    # ── History Page ───────────────────────────────────────────────────────

    def _build_history_page(self):
        c = self._colors
        page = self._make_page("history")
        page.grid_rowconfigure(1, weight=1)

        header = ctk.CTkFrame(page, fg_color="transparent")
        header.grid(row=0, column=0, padx=32, pady=(28, 16), sticky="ew")

        ctk.CTkLabel(
            header, text="Download History",
            font=FONTS["display"], text_color=c["text_primary"],
        ).pack(side="left")

        ctk.CTkButton(
            header, text="Clear All",
            font=FONTS["small"], width=90, height=32,
            fg_color=c["bg_card"], hover_color=c["bg_hover"],
            text_color=c["error"], corner_radius=8,
            command=self._clear_history,
        ).pack(side="right")

        self._history_scroll = ctk.CTkScrollableFrame(
            page, fg_color=c["bg_secondary"], corner_radius=12,
        )
        self._history_scroll.grid(row=1, column=0, padx=32, pady=(0, 20), sticky="nsew")
        self._history_scroll.grid_columnconfigure(0, weight=1)

        self._refresh_history_list()

    def _refresh_history_list(self):
        c = self._colors
        for w in self._history_scroll.winfo_children():
            w.destroy()

        entries = self.history.get_all()
        if not entries:
            ctk.CTkLabel(
                self._history_scroll,
                text="No downloads yet.",
                font=FONTS["body"], text_color=c["text_muted"],
            ).pack(pady=40)
            return

        for i, entry in enumerate(entries):
            card = ctk.CTkFrame(
                self._history_scroll, fg_color=c["bg_card"], corner_radius=10,
            )
            card.pack(fill="x", padx=8, pady=4)
            card.grid_columnconfigure(1, weight=1)

            # Status icon
            icon = "✓" if entry.get("status") == "finished" else "✕"
            icon_color = c["success"] if entry.get("status") == "finished" else c["error"]
            ctk.CTkLabel(card, text=icon, font=FONTS["heading"],
                         text_color=icon_color, width=30).grid(
                row=0, column=0, padx=(12, 0), pady=10, rowspan=2)

            # Title
            ctk.CTkLabel(
                card, text=entry.get("title", "Unknown"),
                font=FONTS["subhead"], text_color=c["text_primary"],
                anchor="w",
            ).grid(row=0, column=1, padx=(8, 0), pady=(10, 0), sticky="ew")

            # Meta
            ts = entry.get("timestamp", 0)
            time_str = time.strftime("%Y-%m-%d %H:%M", time.localtime(ts)) if ts else ""
            quality = entry.get("quality", "")
            audio_label = "MP3" if entry.get("audio_only") else f"{quality}p MP4"
            meta = f"{time_str}  •  {audio_label}  •  {entry.get('file_size', '')}"

            ctk.CTkLabel(
                card, text=meta,
                font=FONTS["tiny"], text_color=c["text_muted"], anchor="w",
            ).grid(row=1, column=1, padx=(8, 0), pady=(0, 10), sticky="ew")

            # Re-download button
            url = entry.get("url", "")
            ctk.CTkButton(
                card, text="↺ Re-download",
                font=FONTS["tiny"], width=100, height=28,
                fg_color="transparent", hover_color=c["bg_hover"],
                text_color=c["text_secondary"], corner_radius=6,
                command=lambda u=url: self._redownload(u),
            ).grid(row=0, column=2, padx=12, pady=10, rowspan=2)

    # ── Settings Page ──────────────────────────────────────────────────────

    def _build_settings_page(self):
        c = self._colors
        page = self._make_page("settings")

        scroll = ctk.CTkScrollableFrame(page, fg_color=c["bg_primary"], corner_radius=0)
        scroll.pack(fill="both", expand=True, padx=32, pady=20)
        scroll.grid_columnconfigure(0, weight=1)

        ctk.CTkLabel(
            scroll, text="Settings",
            font=FONTS["display"], text_color=c["text_primary"],
        ).pack(anchor="w", pady=(8, 20))

        # Default download dir
        self._make_setting_row(
            scroll, "Default Download Folder",
            "Where downloaded files are saved by default."
        )
        dir_row = ctk.CTkFrame(scroll, fg_color="transparent")
        dir_row.pack(fill="x", pady=(0, 16))
        dir_entry = ctk.CTkEntry(
            dir_row, textvariable=self._output_dir_var,
            font=FONTS["body"], fg_color=c["bg_input"],
            border_color=c["border"], text_color=c["text_primary"],
            height=38, corner_radius=8,
        )
        dir_entry.pack(side="left", fill="x", expand=True, padx=(0, 8))
        ctk.CTkButton(
            dir_row, text="Browse", width=80, height=38,
            font=FONTS["small"], fg_color=c["bg_card"],
            hover_color=c["bg_hover"], text_color=c["text_secondary"],
            corner_radius=8, command=self._browse_directory,
        ).pack(side="left")

        # Clipboard auto-detect
        self._make_setting_row(
            scroll, "Clipboard Auto-Detect",
            "Automatically detect YouTube URLs copied to clipboard."
        )
        self._clip_var = ctk.BooleanVar(value=self.settings.get("auto_detect_clipboard"))
        ctk.CTkSwitch(
            scroll, text="",
            variable=self._clip_var,
            fg_color=c["border"], progress_color=c["accent"],
            command=lambda: self.settings.set("auto_detect_clipboard", self._clip_var.get()),
        ).pack(anchor="w", pady=(0, 16))

        # Concurrent fragments
        self._make_setting_row(
            scroll, "Concurrent Fragments",
            "Number of parallel chunks to download (higher = faster but more CPU)."
        )
        self._frag_var = ctk.IntVar(value=self.settings.get("concurrent_fragments", 4))
        frag_frame = ctk.CTkFrame(scroll, fg_color="transparent")
        frag_frame.pack(fill="x", pady=(0, 16))
        self._frag_label = ctk.CTkLabel(
            frag_frame, text=str(self._frag_var.get()),
            font=FONTS["body"], text_color=c["accent"], width=24,
        )
        self._frag_label.pack(side="right")
        ctk.CTkSlider(
            frag_frame, variable=self._frag_var, from_=1, to=10,
            number_of_steps=9,
            progress_color=c["accent"], button_color=c["accent"],
            button_hover_color=c["accent_hover"],
            command=lambda v: (
                self._frag_label.configure(text=str(int(v))),
                self.settings.set("concurrent_fragments", int(v)),
            ),
        ).pack(side="left", fill="x", expand=True, padx=(0, 8))

        # Reset button
        ctk.CTkButton(
            scroll, text="Reset to Defaults",
            font=FONTS["body"], width=160, height=38,
            fg_color=c["bg_card"], hover_color=c["bg_hover"],
            text_color=c["error"], corner_radius=8,
            command=self._reset_settings,
        ).pack(anchor="w", pady=(8, 0))

    def _make_setting_row(self, parent, title: str, desc: str):
        c = self._colors
        ctk.CTkLabel(parent, text=title, font=FONTS["subhead"],
                     text_color=c["text_primary"]).pack(anchor="w")
        ctk.CTkLabel(parent, text=desc, font=FONTS["small"],
                     text_color=c["text_muted"]).pack(anchor="w", pady=(0, 4))

    # ── Download Logic ─────────────────────────────────────────────────────

    def _on_url_changed(self, *_):
        url = self._url_var.get().strip()
        if not url:
            self._url_type_label.configure(text="")
            return
        if "list=" in url or "playlist" in url:
            self._url_type_label.configure(text="📋 Playlist detected", text_color=self._colors["success"])
        elif "shorts" in url:
            self._url_type_label.configure(text="⚡ Shorts", text_color=self._colors["warning"])
        elif "youtube.com" in url or "youtu.be" in url:
            self._url_type_label.configure(text="▶ Video", text_color=self._colors["info"])
        else:
            self._url_type_label.configure(text="")

    def _fetch_video_info(self):
        url = self._url_var.get().strip()
        if not url:
            self._log("Please enter a URL first.", level="warn")
            return

        self._fetch_btn.configure(text="Fetching...", state="disabled")
        self._log(f"Fetching info for: {url}")

        def run():
            try:
                info = self.engine.fetch_info(url)
                self.after(0, lambda: self._show_info_preview(info))
            except Exception as e:
                self.after(0, lambda: self._log(f"Error fetching info: {e}", level="error"))
            finally:
                self.after(0, lambda: self._fetch_btn.configure(text="🔍 Fetch Info", state="normal"))

        threading.Thread(target=run, daemon=True).start()

    def _show_info_preview(self, info: dict):
        c = self._colors
        if not info:
            return

        is_playlist = info.get("_type") == "playlist"
        title = info.get("title", "Unknown Title")
        count = len(info.get("entries", [])) if is_playlist else 1
        duration = info.get("duration", 0) or 0
        uploader = info.get("uploader", "")

        if is_playlist:
            meta = f"{count} videos  •  {uploader}"
            type_text = "📋 Playlist"
        else:
            mins = duration // 60
            secs = duration % 60
            meta = f"{mins}:{secs:02d}  •  {uploader}"
            type_text = "⚡ Short" if "shorts" in (info.get("webpage_url", "") or "") else "▶ Video"

        self._info_title_label.configure(text=title[:80])
        self._info_meta_label.configure(text=meta)
        self._info_type_label.configure(text=type_text)

        self._info_card.grid(row=4, column=0, padx=20, pady=(0, 16), sticky="ew")

        # Load thumbnail async
        thumb_url = info.get("thumbnail")
        if thumb_url:
            threading.Thread(
                target=self._load_thumbnail, args=(thumb_url,), daemon=True
            ).start()

        self._log(f"✓ Info fetched: {title}")

    def _load_thumbnail(self, url: str):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=5) as r:
                data = r.read()
            img = Image.open(io.BytesIO(data))
            img = img.resize((120, 68), Image.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            self.after(0, lambda: self._thumb_label.configure(image=photo, text=""))
            self.after(0, lambda: setattr(self._thumb_label, '_photo', photo))
        except Exception:
            pass

    def _get_quality_value(self) -> str:
        q = self._quality_var.get()
        if "4K" in q or "2160" in q:
            return "2160"
        for res in ["1440", "1080", "720", "480", "360"]:
            if res in q:
                return res
        return "1080"

    def _add_to_queue(self):
        url = self._url_var.get().strip()
        if not url:
            self._log("Please enter a URL.", level="warn")
            return
        if not ("youtube.com" in url or "youtu.be" in url):
            self._log("Only YouTube URLs are supported.", level="warn")
            return

        output_dir = self._output_dir_var.get().strip()
        if not output_dir:
            output_dir = self.settings.get("download_dir")

        os.makedirs(output_dir, exist_ok=True)

        is_playlist = "list=" in url or "playlist" in url.lower()

        item = DownloadItem(
            url=url,
            output_dir=output_dir,
            quality=self._get_quality_value(),
            audio_only=self._audio_only_var.get(),
            is_playlist=is_playlist,
        )
        item.title = url[:60] + "..." if len(url) > 60 else url

        self._queue.append(item)
        self._add_queue_card(item)
        self._url_var.set("")
        self._info_card.grid_remove()
        self._log(f"Added to queue: {item.url[:50]}...")
        self._update_queue_count()
        self._show_page("queue")

    def _add_queue_card(self, item: DownloadItem):
        if self._empty_queue_label.winfo_ismapped():
            self._empty_queue_label.pack_forget()

        card = QueueCard(
            self._queue_scroll, item, self._colors,
            on_start=lambda i=item: self._start_single(i),
            on_cancel=lambda i=item: self._cancel_download(i),
            on_pause=lambda i=item: self._pause_resume(i),
            on_remove=lambda i=item: self._remove_from_queue(i),
        )
        card.pack(fill="x", padx=8, pady=4)
        self._queue_cards[item.item_id] = card

    def _start_single(self, item: DownloadItem):
        self._log(f"Starting download: {item.title or item.url[:40]}...")
        self.engine.download(
            item,
            on_progress=self._on_progress,
            on_complete=self._on_complete,
            on_error=self._on_error,
        )

    def _start_all_downloads(self):
        started = 0
        for item in self._queue:
            if item.status == DownloadStatus.QUEUED:
                self._start_single(item)
                started += 1
        if started == 0:
            self._log("No queued items to download.", level="warn")
        else:
            self._log(f"Started {started} download(s).")
            self._show_page("queue")

    def _on_progress(self, item: DownloadItem):
        def update():
            card = self._queue_cards.get(item.item_id)
            if card:
                card.update_state(item)
            self._status_bar.update(item)
        self.after(0, update)

    def _on_complete(self, item: DownloadItem):
        def done():
            card = self._queue_cards.get(item.item_id)
            if card:
                card.update_state(item)
            self._log(f"✓ Completed: {item.title or item.url[:40]}")
            self._status_bar.set_idle()
            # Save to history
            self.history.add(HistoryEntry(
                title=item.title or item.url,
                url=item.url,
                output_path=item.output_dir,
                quality=item.quality,
                audio_only=item.audio_only,
                timestamp=time.time(),
                file_size=item.file_size,
                status="finished",
            ))
        self.after(0, done)

    def _on_error(self, item: DownloadItem, err: str):
        def handle():
            card = self._queue_cards.get(item.item_id)
            if card:
                card.update_state(item)
            self._log(f"✕ Error ({item.title or ''}): {err[:100]}", level="error")
            self._status_bar.set_idle()
        self.after(0, handle)

    def _cancel_download(self, item: DownloadItem):
        self.engine.cancel(item.item_id)
        self._log(f"Cancelled: {item.title or item.url[:40]}")

    def _pause_resume(self, item: DownloadItem):
        if item.status == DownloadStatus.PAUSED:
            self.engine.resume(item.item_id)
            self._log(f"Resumed: {item.title or item.url[:40]}")
        else:
            self.engine.pause(item.item_id)
            self._log(f"Paused: {item.title or item.url[:40]}")

    def _remove_from_queue(self, item: DownloadItem):
        self.engine.cancel(item.item_id)
        card = self._queue_cards.pop(item.item_id, None)
        if card:
            card.destroy()
        if item in self._queue:
            self._queue.remove(item)
        self._update_queue_count()
        if not self._queue:
            self._empty_queue_label.pack(pady=40)

    def _clear_finished_queue(self):
        finished = [
            i for i in self._queue
            if i.status in (DownloadStatus.FINISHED, DownloadStatus.CANCELLED, DownloadStatus.ERROR)
        ]
        for item in finished:
            self._remove_from_queue(item)

    def _update_queue_count(self):
        n = len(self._queue)
        self._queue_count_label.configure(text=f"{n} item{'s' if n != 1 else ''}")

    # ── Clipboard Monitor ─────────────────────────────────────────────────

    def _start_clipboard_monitor(self):
        self._clipboard_monitor_active = True
        self._monitor_clipboard()

    def _monitor_clipboard(self):
        if not self._clipboard_monitor_active:
            return
        try:
            text = self.clipboard_get()
            if text != self._last_clipboard:
                self._last_clipboard = text
                if ("youtube.com/watch" in text or "youtu.be/" in text) and not self._url_var.get():
                    self._url_var.set(text)
                    self._log("✓ YouTube URL detected from clipboard.")
        except Exception:
            pass
        self.after(1500, self._monitor_clipboard)

    # ── Misc ───────────────────────────────────────────────────────────────

    def _setup_drag_drop(self):
        """Enable drag-and-drop URL onto the window (requires tkinterdnd2 if available)."""
        try:
            from tkinterdnd2 import DND_TEXT
            self._url_entry.drop_target_register(DND_TEXT)
            self._url_entry.dnd_bind('<<Drop>>', lambda e: self._url_var.set(e.data.strip()))
        except Exception:
            pass

    def _browse_directory(self):
        directory = filedialog.askdirectory(
            title="Select Download Folder",
            initialdir=self._output_dir_var.get(),
        )
        if directory:
            self._output_dir_var.set(directory)
            self.settings.set("download_dir", directory)

    def _log(self, message: str, level: str = "info"):
        self._log_console.append(message, level)

    def _redownload(self, url: str):
        self._url_var.set(url)
        self._show_page("download")

    def _clear_history(self):
        if messagebox.askyesno("Clear History", "Are you sure you want to clear all download history?"):
            self.history.clear()
            self._refresh_history_list()

    def _reset_settings(self):
        if messagebox.askyesno("Reset Settings", "Reset all settings to defaults?"):
            self.settings.reset()
            self._output_dir_var.set(self.settings.get("download_dir"))

    def _do_update_ytdlp(self):
        self._log("Checking for yt-dlp updates...")
        self.engine.update_ytdlp(lambda msg: self.after(0, lambda m=msg: self._log(m)))

    def _on_close(self):
        self._clipboard_monitor_active = False
        self.destroy()
