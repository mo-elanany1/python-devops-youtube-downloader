"""
core/settings.py
Manages persistent app settings.
"""

import os
import json
from typing import Any

SETTINGS_FILE = os.path.join(
    os.path.expanduser("~"), ".ytdownloader", "settings.json"
)

DEFAULTS = {
    "download_dir": os.path.join(os.path.expanduser("~"), "Downloads", "YTDownloader"),
    "default_quality": "1080",
    "default_audio_only": False,
    "theme": "dark",
    "auto_detect_clipboard": True,
    "concurrent_fragments": 4,
    "auto_update_ytdlp": False,
    "show_notifications": True,
    "log_level": "info",
}


class SettingsManager:
    """Load/save user preferences."""

    def __init__(self):
        self._ensure_dir()
        self._data = {**DEFAULTS}
        self._load()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(SETTINGS_FILE), exist_ok=True)

    def _load(self):
        try:
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                saved = json.load(f)
                self._data.update(saved)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def save(self):
        try:
            with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._data, f, indent=2)
        except Exception:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self._data.get(key, DEFAULTS.get(key, default))

    def set(self, key: str, value: Any):
        self._data[key] = value
        self.save()

    def reset(self):
        self._data = {**DEFAULTS}
        self.save()
