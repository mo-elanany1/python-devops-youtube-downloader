"""
core/history.py
Manages download history using a local JSON file.
"""

import os
import json
import time
from typing import List, Dict
from dataclasses import dataclass, asdict


HISTORY_FILE = os.path.join(
    os.path.expanduser("~"), ".ytdownloader", "history.json"
)


@dataclass
class HistoryEntry:
    title: str
    url: str
    output_path: str
    quality: str
    audio_only: bool
    timestamp: float
    file_size: str = ""
    status: str = "finished"


class HistoryManager:
    """Persists download history between sessions."""

    def __init__(self):
        self._ensure_dir()
        self._entries: List[Dict] = self._load()

    def _ensure_dir(self):
        os.makedirs(os.path.dirname(HISTORY_FILE), exist_ok=True)

    def _load(self) -> List[Dict]:
        try:
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save(self):
        try:
            with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self._entries, f, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add(self, entry: HistoryEntry):
        self._entries.insert(0, asdict(entry))
        # Keep only last 500 entries
        self._entries = self._entries[:500]
        self._save()

    def get_all(self) -> List[Dict]:
        return list(self._entries)

    def clear(self):
        self._entries = []
        self._save()

    def remove(self, index: int):
        if 0 <= index < len(self._entries):
            self._entries.pop(index)
            self._save()

    def is_duplicate(self, url: str) -> bool:
        """Check if a URL was recently downloaded."""
        for entry in self._entries[:50]:
            if entry.get('url') == url:
                return True
        return False
