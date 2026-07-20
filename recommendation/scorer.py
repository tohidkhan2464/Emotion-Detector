from __future__ import annotations
import random
from recommendation.emotion_mapping import EmotionMapping
from recommendation.history import History
from recommendation.models import Song
from recommendation.play_stats import PlayStats
from recommendation.preferences import Preferences


class SongScorer:
    """
    Calculates recommendation scores.
    """

    ENERGY_SCORE = {
        "low": 10,
        "medium": 20,
        "high": 30,
    }

    def __init__(
        self,
        history: History,
        play_stats: PlayStats,
        preferences: Preferences,
        emotion_mapping: EmotionMapping,
    ) -> None:
        self.history = history
        self.play_stats = play_stats
        self.preferences = preferences
        self.emotion_mapping = emotion_mapping

    def score(self, song: Song, detected_emotion: str) -> float:
        score = 0.0
        score += self._emotion_score(song, detected_emotion)
        score += self._popularity_score(song)
        score += self._freshness_score(song)
        score += self._play_stats_score(song)
        score += self._preference_score(song)
        score += self._energy_score(song)
        # Diversity bonus
        score += random.uniform(0, 5)
        song.score = round(score, 2)
        return song.score

    def score_all(
        self,
        songs: list[Song],
        detected_emotion: str,
    ) -> list[Song]:
        for song in songs:
            self.score(song, detected_emotion)
        return sorted(songs, key=lambda s: s.score, reverse=True)

    def _emotion_score(self, song: Song, detected_emotion: str) -> float:
        playlists = self.emotion_mapping.get_playlists(detected_emotion)
        for playlist in playlists:
            if playlist["emotion"] == song.emotion:
                return playlist["weight"]
        return 0

    def _popularity_score(self, song: Song) -> float:
        return song.popularity * 0.40

    def _freshness_score(self, song: Song) -> float:
        minutes = self.history.minutes_since_played(song.filename)
        if minutes == float("inf"):
            return 35
        if minutes >= 720:
            return 30
        if minutes >= 180:
            return 20
        if minutes >= 60:
            return 10
        return -100.0

    def _play_stats_score(self, song: Song) -> float:
        return self.play_stats.popularity_boost(song.filename)

    def _preference_score(self, song: Song) -> float:
        return self.preferences.preference_score(song)

    def _energy_score(self, song: Song) -> float:
        return self.ENERGY_SCORE.get(song.energy.lower(), 10)
