from __future__ import annotations
from recommendation.models import Song


class MusicQueue:
    """
    Manages a playlist of Song objects with previous/next navigation.
    """

    def __init__(self) -> None:
        self.previous_songs: list[Song] = []
        self.current_song: Song | None = None
        self.next_songs: list[Song] = []

    def set_current(self, song: Song) -> None:
        if self.current_song is not None:
            self.previous_songs.append(self.current_song)
        self.current_song = song

    def add_next(self, song: Song) -> None:
        self.next_songs.append(song)

    def load_songs(self, songs: list[Song]) -> None:
        """Replace the upcoming queue with a fresh list of songs."""
        self.next_songs = list(songs)

    def next(self) -> Song | None:
        if not self.next_songs:
            return None
        self.set_current(self.next_songs.pop(0))
        return self.current_song

    def previous(self) -> Song | None:
        if not self.previous_songs:
            return None
        # Push current back to next if it exists
        if self.current_song is not None:
            self.next_songs.insert(0, self.current_song)
        self.current_song = self.previous_songs.pop()
        return self.current_song

    def clear(self) -> None:
        """Clear all queued upcoming songs."""
        self.next_songs.clear()

    def has_next(self) -> bool:
        return len(self.next_songs) > 0

    def peek_next(self, limit: int = 3) -> list[Song]:
        """Return up to `limit` upcoming songs without consuming them."""
        return self.next_songs[:limit]
