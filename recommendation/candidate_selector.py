from __future__ import annotations
from recommendation.emotion_mapping import EmotionMapping
from recommendation.models import Song


class CandidateSelector:
    """
    Builds the list of candidate songs for an emotion.
    Responsibilities:
    - Expand emotion into related playlists
    - Remove duplicate songs
    - Return Song objects
    """

    def __init__(self, mapping: EmotionMapping) -> None:
        self.mapping = mapping

    def select(self, detected_emotion: str, songs: list[Song]) -> list[Song]:
        candidate_emotions = self.mapping.all_candidates(detected_emotion)
        candidates: list[Song] = []
        seen: set[str] = set()
        for song in songs:
            if song.emotion not in candidate_emotions:
                continue
            if song.filename in seen:
                continue
            seen.add(song.filename)
            candidates.append(song)
        return candidates

    def by_playlist(self, playlist: str, songs: list[Song]) -> list[Song]:
        return [song for song in songs if song.emotion == playlist]
