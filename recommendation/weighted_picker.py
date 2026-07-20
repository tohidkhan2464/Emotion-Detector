from __future__ import annotations
import random
from recommendation.models import Song


class WeightedPicker:
    """
    Picks one song using weighted random selection.
    Songs with higher scores have a higher probability.
    Songs with scores <= 0 are excluded unless all candidates are excluded.
    """

    def pick(self, songs: list[Song]) -> Song | None:
        if not songs:
            return None
        weights = [max(0.0, song.score) for song in songs]
        total = sum(weights)
        if total <= 0.0:
            weights = [1.0] * len(songs)
        return random.choices(population=songs, weights=weights, k=1)[0]

    def top(self, songs: list[Song], limit: int = 10) -> list[Song]:
        return sorted(songs, key=lambda s: s.score, reverse=True)[:limit]

    def probabilities(self, songs: list[Song]) -> list[tuple[Song, float]]:
        if not songs:
            return []
        weights = [max(0.0, song.score) for song in songs]
        total = sum(weights)
        if total <= 0.0:
            total = float(len(songs))
            weights = [1.0] * len(songs)
        result = []
        for i, song in enumerate(songs):
            probability = weights[i] / total
            result.append((song, probability))
        return sorted(result, key=lambda item: item[1], reverse=True)
