from __future__ import annotations
import random
import config
from utils.helpers import load_json


class EmotionMapping:
    """
    Loads emotion_mapping.json and provides
    weighted playlist selection.
    """
    def __init__(self, path=config.DATABASE.EMOTION_MAPPING_JSON):
        self.path = path
        self.mapping = self.load()

    def load(self) -> dict:
        return load_json(self.path, default={})

    def get_playlists(self, emotion: str) -> list[dict]:
        """
        Returns playlist definitions.
        Example:
        [
            {"emotion":"happy","weight":70},
            {"emotion":"party","weight":20}
        ]
        """
        return self.mapping.get(emotion, {}).get("playlists", [])

    def playlist_names(self, emotion: str) -> list[str]:
        return [item["emotion"] for item in self.get_playlists(emotion)]

    def choose_playlist(self, emotion: str) -> str:
        """
        Weighted random playlist selection.
        """
        playlists = self.get_playlists(emotion)
        if not playlists:
            return emotion

        return random.choices(
            [p["emotion"] for p in playlists],
            weights=[p["weight"] for p in playlists],
            k=1,
        )[0]

    def all_candidates(self, emotion: str) -> list[str]:
        """
        Returns every candidate playlist.
        Used later by CandidateSelector.
        """
        return self.playlist_names(emotion)
