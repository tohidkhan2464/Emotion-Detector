from __future__ import annotations
import time
import pygame
import config
from music_player.queue import MusicQueue
from recommendation.models import Song
from utils.logger import get_logger

logger = get_logger("music_player")


class MusicPlayer:
    """
    Pygame-backed music player with full playback controls.
    Manages volume, mute, seek, and song-end detection.
    """

    def __init__(self) -> None:
        self.queue = MusicQueue()
        self._initialized = False
        self._volume: float = 0.7
        self._muted: bool = False
        self._paused: bool = False
        self._play_start_time: float = 0.0   # monotonic time when play started
        self._play_offset: float = 0.0        # seconds already elapsed before last seek
        self.on_song_end: "Callable | None" = None  # callback when track finishes

    # Initialization
    def _init_backend(self) -> None:
        if self._initialized:
            return
        pygame.mixer.init()
        pygame.mixer.music.set_volume(self._volume)
        self._initialized = True
        logger.info("Pygame mixer initialized.")

    # Playback
    def play(self, song: Song) -> None:
        """Load and play a Song object. Resolves the full file path automatically."""
        self._init_backend()
        file_path = config.PLAYER.MUSIC_FOLDER / song.filename
        if not file_path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return

        self.queue.set_current(song)
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.set_volume(0.0 if self._muted else self._volume)
        pygame.mixer.music.play()

        self._paused = False
        self._play_start_time = time.monotonic()
        self._play_offset = 0.0

        # Register end-of-track event
        pygame.mixer.music.set_endevent(pygame.USEREVENT + 1)
        logger.info(f"Playing: {song.title} by {song.artist}")

    def pause(self) -> None:
        if not self._initialized or self._paused:
            return
        pygame.mixer.music.pause()
        # Accumulate elapsed time before pause
        self._play_offset = self.elapsed_seconds()
        self._paused = True
        logger.info("Paused playback.")

    def resume(self) -> None:
        if not self._initialized or not self._paused:
            return
        pygame.mixer.music.unpause()
        self._play_start_time = time.monotonic()
        self._paused = False
        logger.info("Resumed playback.")

    def stop(self) -> None:
        if not self._initialized:
            return
        pygame.mixer.music.stop()
        self._paused = False
        self._play_offset = 0.0
        logger.info("Stopped playback.")

    def toggle_pause(self) -> bool:
        """Toggle between pause and resume. Returns True if now paused."""
        if self._paused:
            self.resume()
        else:
            self.pause()
        return self._paused

    def next(self) -> Song | None:
        song = self.queue.next()
        if song:
            self.play(song)
        return song

    def previous(self) -> Song | None:
        song = self.queue.previous()
        if song:
            self.play(song)
        return song

    # Volume & Mute
    @property
    def volume(self) -> float:
        return self._volume

    def set_volume(self, volume: float) -> None:
        self._volume = max(0.0, min(1.0, volume))
        if self._initialized and not self._muted:
            pygame.mixer.music.set_volume(self._volume)
        logger.debug(f"Volume set to {self._volume:.0%}")

    def increase_volume(self, step: float = 0.1) -> float:
        self.set_volume(self._volume + step)
        return self._volume

    def decrease_volume(self, step: float = 0.1) -> float:
        self.set_volume(self._volume - step)
        return self._volume

    def mute(self) -> bool:
        self._muted = not self._muted
        if self._initialized:
            pygame.mixer.music.set_volume(0.0 if self._muted else self._volume)
        logger.info(f"Muted: {self._muted}")
        return self._muted

    # Seek & Progress
    def seek(self, seconds: float) -> None:
        """Seek to an absolute position in the track (seconds)."""
        if not self._initialized or self.queue.current_song is None:
            return
        file_path = config.PLAYER.MUSIC_FOLDER / self.queue.current_song.filename
        if not file_path.exists():
            logger.error(f"Audio file not found: {file_path}")
            return
        
        # Stop first, reload and play from position
        pygame.mixer.music.stop()
        pygame.mixer.music.load(str(file_path))
        pygame.mixer.music.set_volume(0.0 if self._muted else self._volume)
        pygame.mixer.music.play(start=seconds)
        if self._paused:
            pygame.mixer.music.pause()
            
        self._play_offset = seconds
        self._play_start_time = time.monotonic()
        logger.debug(f"Seeked to {seconds:.1f}s using play(start=...)")

    def elapsed_seconds(self) -> float:
        """Returns elapsed playback time in seconds."""
        if not self._initialized or self.queue.current_song is None:
            return 0.0
        if self._paused:
            return self._play_offset
        elapsed = self._play_offset + (time.monotonic() - self._play_start_time)
        duration = self.queue.current_song.duration
        if duration > 0:
            return min(elapsed, duration)
        return elapsed

    def progress_fraction(self) -> float:
        """Returns 0.0–1.0 playback progress."""
        song = self.queue.current_song
        if song is None or song.duration <= 0:
            return 0.0
        return min(self.elapsed_seconds() / song.duration, 1.0)

    # State
    @property
    def is_playing(self) -> bool:
        return self._initialized and pygame.mixer.music.get_busy() and not self._paused

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def current_song(self) -> Song | None:
        return self.queue.current_song

    def check_song_ended(self) -> bool:
        """
        Returns True if the song has naturally ended.
        Should be polled from the UI update loop.
        """
        if not self._initialized or self._paused:
            return False
        # pygame.mixer.music.get_busy() returns False when track ends naturally
        return not pygame.mixer.music.get_busy() and self.queue.current_song is not None

    def cleanup(self) -> None:
        if self._initialized:
            self.stop()
            pygame.mixer.quit()
            self._initialized = False
            logger.info("Pygame mixer cleaned up.")
