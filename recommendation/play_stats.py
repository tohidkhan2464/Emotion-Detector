from __future__ import annotations
import config
from utils.helpers import load_json, save_json


class PlayStats:
    """
    Stores statistics for every song.
    Example:
    {
        "HAPPY/Levitating.mp3": {
            "plays": 14,
            "completed": 11,
            "skipped": 3,
            "liked": true
        }
    }
    """

    def __init__(self, path=config.DATABASE.PLAY_STATS_JSON) -> None:
        self.path = path
        self.stats: dict = self.load()

    # Persistence
    def load(self) -> dict:
        data = load_json(self.path, default={})
        if not isinstance(data, dict):
            return {}
        return data

    def save(self) -> None:
        save_json(self.path, self.stats)

    # Internal helpers
    def _ensure_song(self, filename: str) -> None:
        if filename not in self.stats:
            self.stats[filename] = {
                "plays": 0,
                "completed": 0,
                "skipped": 0,
                "liked": False,
            }

    # Recording
    def record_play(self, filename: str) -> None:
        self._ensure_song(filename)
        self.stats[filename]["plays"] += 1
        self.save()

    def record_skip(self, filename: str) -> None:
        self._ensure_song(filename)
        self.stats[filename]["skipped"] += 1
        self.save()

    def record_completed(self, filename: str) -> None:
        self._ensure_song(filename)
        self.stats[filename]["completed"] += 1
        self.save()

    def like(self, filename: str) -> None:
        self._ensure_song(filename)
        self.stats[filename]["liked"] = True
        self.save()

    def unlike(self, filename: str) -> None:
        self._ensure_song(filename)
        self.stats[filename]["liked"] = False
        self.save()

    # Queries
    def get(self, filename: str) -> dict:
        self._ensure_song(filename)
        return self.stats[filename]

    def play_count(self, filename: str) -> int:
        return self.get(filename)["plays"]

    def skip_count(self, filename: str) -> int:
        return self.get(filename)["skipped"]

    def completed_count(self, filename: str) -> int:
        return self.get(filename)["completed"]

    def is_liked(self, filename: str) -> bool:
        return self.get(filename)["liked"]

    # Metrics
    def completion_rate(self, filename: str) -> float:
        info = self.get(filename)
        plays = info["plays"]
        if plays == 0:
            return 1.0
        return info["completed"] / plays

    def skip_rate(self, filename: str) -> float:
        info = self.get(filename)
        plays = info["plays"]
        if plays == 0:
            return 0.0
        return info["skipped"] / plays

    def popularity_boost(self, filename: str) -> float:
        """
        Returns score between roughly -20 and +20
        """
        info = self.get(filename)
        score = 0.0
        if info["liked"]:
            score += 15
        score += self.completion_rate(filename) * 10
        score -= self.skip_rate(filename) * 20
        score -= min(info["plays"], 30) * 0.3
        return score

    def reset(self) -> None:
        self.stats.clear()
        self.save()
