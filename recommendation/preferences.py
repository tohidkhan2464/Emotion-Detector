from __future__ import annotations

import config
from recommendation.models import Song
from utils.helpers import load_json, save_json


class Preferences:
    """
    Stores long-term user preferences.
    Example:
    {
        "languages": {
            "hindi": 24,
            "english": 11
        },
        "artists": {
            "Arijit Singh": 18,
            "Anuv Jain": 9
        },
        "emotions": {
            "happy": 21
        },
        "energy": {
            "high": 8,
            "medium": 17,
            "low": 5
        }
    }
    """

    def __init__(self, path=config.DATABASE.PREFERENCES_JSON) -> None:
        self.path = path
        self.data = self.load()

    # Persistence
    def load(self) -> dict:
        default = {
            "languages": {},
            "artists": {},
            "emotions": {},
            "energy": {},
        }
        data = load_json(self.path, default)
        if not isinstance(data, dict):
            return default
        return data

    def save(self) -> None:
        save_json(self.path, self.data)

    # Internal helper
    @staticmethod
    def _increment(bucket: dict, key: str, value: int = 1) -> None:
        bucket[key] = bucket.get(key, 0) + value

    # Learning
    def learn(self, song: Song) -> None:
        """
        Call this when a song finishes.
        """
        self._increment(self.data["languages"], song.language)
        self._increment(self.data["artists"], song.artist)
        self._increment(self.data["emotions"], song.emotion)
        self._increment(self.data["energy"], song.energy)
        self.save()

    # Queries
    def language_weight(self, language: str) -> float:
        return self.data["languages"].get(language, 0)

    def artist_weight(self, artist: str) -> float:
        return self.data["artists"].get(artist, 0)

    def emotion_weight(self, emotion: str) -> float:
        return self.data["emotions"].get(emotion, 0)

    def energy_weight(self, energy: str) -> float:
        return self.data["energy"].get(energy, 0)

    # Ranking
    def preference_score(self, song: Song) -> float:
        """
        Returns roughly 0-25 points.
        """
        score = 0.0
        score += min(self.language_weight(song.language), 10)
        score += min(self.artist_weight(song.artist), 5)
        score += min(self.emotion_weight(song.emotion), 5)
        score += min(self.energy_weight(song.energy), 5)
        return score

    # Optional helpers
    def favourite_language(self) -> str | None:
        languages = self.data["languages"]
        if not languages:
            return None
        return max(languages, key=languages.get)

    def favourite_artist(self) -> str | None:
        artists = self.data["artists"]
        if not artists:
            return None
        return max(artists, key=artists.get)

    def reset(self) -> None:
        self.data = {
            "languages": {},
            "artists": {},
            "emotions": {},
            "energy": {},
        }
        self.save()
