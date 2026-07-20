from __future__ import annotations
from datetime import datetime, timedelta
import config
from utils.helpers import load_json, save_json


class History:
    """
    Stores recently played songs with timestamps.
    Example:
    [
        {
            "filename": "HAPPY/Levitating.mp3",
            "played_at": "2026-07-18T11:15:23"
        }
    ]
    """

    def __init__(self, path=config.DATABASE.HISTORY_JSON, max_items: int = 100) -> None:
        self.path = path
        self.max_items = max_items
        self.items: list[dict] = self.load()

    # Persistence
    def load(self) -> list[dict]:
        data = load_json(self.path, default=[])
        if not isinstance(data, list):
            return []
        return data

    def save(self) -> None:
        save_json(self.path, self.items)

    # Recording
    def add_song(self, filename: str) -> None:
        """
        Adds the song to history.
        Existing entry is moved to the top.
        """
        self.items = [item for item in self.items if item.get("filename") != filename]
        self.items.insert(
            0, {"filename": filename, "played_at": datetime.now().isoformat()}
        )
        self.items = self.items[: self.max_items]
        self.save()

    # Queries
    def is_recent(self, filename: str, minutes: int = 30) -> bool:
        """
        Returns True if the song has been played
        within the last N minutes.
        """
        cutoff = datetime.now() - timedelta(minutes=minutes)
        for item in self.items:
            if item.get("filename") != filename:
                continue
            played = datetime.fromisoformat(item["played_at"])
            if played >= cutoff:
                return True
        return False

    def last_played(self, filename: str) -> datetime | None:
        for item in self.items:
            if item.get("filename") == filename:
                return datetime.fromisoformat(item["played_at"])
        return None

    def minutes_since_played(self, filename: str) -> float:
        last = self.last_played(filename)
        if last is None:
            return float("inf")
        return (datetime.now() - last).total_seconds() / 60

    def played_today(self, filename: str) -> bool:
        last = self.last_played(filename)
        if last is None:
            return False
        return last.date() == datetime.now().date()

    def clear(self) -> None:
        self.items.clear()
        self.save()
