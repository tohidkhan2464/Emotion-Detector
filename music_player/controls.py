from __future__ import annotations
from music_player.player import MusicPlayer


class PlayerControls:
    """
    Thin facade over MusicPlayer exposing control methods
    that the UI buttons and sliders call directly.
    All methods delegate to MusicPlayer which wires pygame.
    """

    def __init__(self, player: MusicPlayer) -> None:
        self.player = player

    def play_pause(self) -> bool:
        """Toggle play/pause. Returns True if now paused."""
        return self.player.toggle_pause()

    def next_track(self):
        return self.player.next()

    def previous_track(self):
        return self.player.previous()

    def set_volume(self, volume: float) -> float:
        """volume is 0.0–1.0."""
        self.player.set_volume(volume)
        return self.player.volume

    def increase_volume(self, step: float = 0.1) -> float:
        return self.player.increase_volume(step)

    def decrease_volume(self, step: float = 0.1) -> float:
        return self.player.decrease_volume(step)

    def mute(self) -> bool:
        """Toggle mute. Returns True if now muted."""
        return self.player.mute()

    def seek(self, seconds: float) -> None:
        self.player.seek(seconds)

    @property
    def volume(self) -> float:
        return self.player.volume

    @property
    def is_muted(self) -> bool:
        return self.player._muted
