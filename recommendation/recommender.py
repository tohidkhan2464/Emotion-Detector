from __future__ import annotations
import csv
from pathlib import Path
import config
from recommendation.candidate_selector import CandidateSelector
from recommendation.emotion_mapping import EmotionMapping
from recommendation.history import History
from recommendation.models import Song
from recommendation.play_stats import PlayStats
from recommendation.preferences import Preferences
from recommendation.scorer import SongScorer
from recommendation.weighted_picker import WeightedPicker
from utils.logger import get_logger

logger = get_logger("recommender")


class Recommender:
    """
    Production recommendation pipeline.
    Emotion
        ↓
    Candidate Selection
        ↓
    Song Scoring
        ↓
    Weighted Random
        ↓
    Recommendation
    """

    def __init__(self, songs_csv: Path = config.DATABASE.SONGS_CSV) -> None:
        self.songs_csv = songs_csv
        self.history = History()
        self.play_stats = PlayStats()
        self.preferences = Preferences()
        self.mapping = EmotionMapping()
        self.selector = CandidateSelector(self.mapping)
        self.scorer = SongScorer(
            history=self.history,
            play_stats=self.play_stats,
            preferences=self.preferences,
            emotion_mapping=self.mapping,
        )
        self.picker = WeightedPicker()
        self.songs = self._load_songs()

    def _load_songs(self) -> list[Song]:
        with self.songs_csv.open("r", encoding="utf-8", newline="") as file:
            reader = csv.DictReader(file)
            return [Song.from_csv(row) for row in reader]

    def reload(self) -> None:
        """
        Reload songs.csv without restarting app.
        """
        self.songs = self._load_songs()
        logger.info("Reloaded songs list from CSV.")

    def candidates(self, emotion: str) -> list[Song]:
        return self.selector.select(detected_emotion=emotion, songs=self.songs)

    def enrich_metadata(self, song: Song) -> None:
        """
        Enrich a Song object with metadata from mutagen dynamically if not already loaded.
        """
        if song.album == "Unknown Album" and song.duration == 0.0:
            from utils.metadata_reader import get_mp3_metadata
            file_path = config.PLAYER.MUSIC_FOLDER / song.filename
            meta = get_mp3_metadata(str(file_path))
            
            if meta["title"]:
                song.title = meta["title"]
            if meta["artist"]:
                song.artist = meta["artist"]
            song.album = meta["album"] or "Unknown Album"
            song.duration = meta["duration"] or 0.0
            song.bitrate = meta["bitrate"] or 0
            song.cover_art = meta["cover_art"]

    def recommend(self, emotion: str) -> Song | None:
        candidates = self.candidates(emotion)
        if not candidates:
            return None
        ranked = self.scorer.score_all(candidates, emotion)
        song = self.picker.pick(ranked)
        if song is None:
            return None
        self.enrich_metadata(song)
        self.history.add_song(song.filename)
        self.play_stats.record_play(song.filename)
        logger.info(f"Recommended and enriched: {song.title} by {song.artist} (Emotion: {emotion})")
        return song

    def top_recommendations(self, emotion: str, limit: int = 10) -> list[Song]:
        candidates = self.candidates(emotion)
        ranked = self.scorer.score_all(candidates, emotion)
        top_songs = self.picker.top(ranked, limit)
        for song in top_songs:
            self.enrich_metadata(song)
        return top_songs

    def recommendation_probabilities(self, emotion: str):
        ranked = self.scorer.score_all(self.candidates(emotion), emotion)
        return self.picker.probabilities(ranked)

    # Player Events
    def song_completed(self, song: Song) -> None:
        self.play_stats.record_completed(song.filename)
        self.preferences.learn(song)
        logger.info(f"Song completed: {song.title}. Recorded stats and updated preferences.")

    def song_skipped(self, song: Song) -> None:
        self.play_stats.record_skip(song.filename)
        logger.info(f"Song skipped: {song.title}.")

    def like_song(self, song: Song) -> None:
        self.play_stats.like(song.filename)
        logger.info(f"Liked song: {song.title}.")

    def unlike_song(self, song: Song) -> None:
        self.play_stats.unlike(song.filename)
        logger.info(f"Unliked song: {song.title}.")
