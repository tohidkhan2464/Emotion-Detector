from __future__ import annotations
import traceback
import io
import queue
from concurrent.futures import ThreadPoolExecutor
from time import monotonic
import cv2
import customtkinter as ctk
from PIL import Image
import config
from camera.frame_processor import FrameProcessor
from camera.webcam import Webcam
from emotion_detection.emotion_smoother import EmotionSmoother
from emotion_detection.factory import EmotionDetectorFactory
from face_detection.haarcascade_detector import HaarCascadeFaceDetector
from music_player.controls import PlayerControls
from music_player.player import MusicPlayer
from recommendation.models import Song
from recommendation.recommender import Recommender
from utils.logger import get_logger

logger = get_logger("home_view")

# Mapping of emotions to their emoji representations
EMOTION_EMOJI = {
    "happy": "😊",
    "sad": "😢",
    "angry": "😠",
    "neutral": "😐",
    "surprise": "😲",
    "fear": "😨",
    "disgust": "🤢",
}

# Modern UI Theme Constants (Sleek Dark Theme)
COLOR_BG = "#0f111a"          # Very deep dark blue/gray
COLOR_CARD = "#171a26"        # Deep card background
COLOR_CARD_ALT = "#1e2235"    # Slightly lighter card background for headers
COLOR_ACCENT = "#00e5ff"      # Neon Cyber Cyan
COLOR_BUTTON = "#1db954"      # Spotify Green
COLOR_BUTTON_HOVER = "#1aa34a" # Lighter green
COLOR_TEXT_PRIMARY = "#ffffff"  # Pure White
COLOR_TEXT_SECONDARY = "#8b949e" # Muted Gray
COLOR_BORDER = "#2f364d"      # Subtle card borders

def _format_duration(seconds: float) -> str:
    s = int(seconds)
    return f"{s // 60:02d}:{s % 60:02d}"


class HomeView:
    def __init__(self, master) -> None:
        self.master = master
        self.frame = ctk.CTkFrame(master, fg_color=COLOR_BG)

        # ── Core services ────────────────────────────────────────────────
        self.webcam: Webcam | None = None
        self.processor = FrameProcessor()
        self.face_detector: HaarCascadeFaceDetector | None = None
        self.emotion_detector = None
        self.smoother = EmotionSmoother(window_size=5)
        self.recommender = Recommender()
        self.player = MusicPlayer()
        self.controls = PlayerControls(self.player)

        # ── Thread safety ────────────────────────────────────────────────
        self.executor = ThreadPoolExecutor(max_workers=1)
        self._is_predicting = False
        self._result_queue: queue.Queue = queue.Queue()

        # ── State ────────────────────────────────────────────────────────
        self.running = False
        self.last_emotion_check = 0.0
        self.current_emotion = "neutral"
        self.current_confidence = 0.0
        self.video_image = None

        # Stability tracking (issue #6)
        self._stable_emotion: str = "neutral"
        self._stable_confidence: float = 0.0
        self._stability_start: float = 0.0
        self._last_triggered_emotion: str = ""

        # Recent emotions (last 5 triggered)
        self._recent_emotions: list[str] = []

        self._build_layout()

    # Layout
    def _build_layout(self) -> None:
        """Two-panel layout: left=camera+emotion, right=player+queue."""

        # ── Header ──────────────────────────────────────────────────────
        header = ctk.CTkFrame(self.frame, fg_color=COLOR_CARD, height=60, corner_radius=12)
        header.pack(fill="x", padx=20, pady=(16, 8))
        header.pack_propagate(False)
        
        ctk.CTkLabel(
            header,
            text="🎵  Emotion-Sync Audio Player",
            font=("Segoe UI", 20, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
        ).pack(side="left", padx=20, pady=12)
        
        self.status_label = ctk.CTkLabel(
            header,
            text="Start the camera to begin detection.",
            font=("Segoe UI", 12, "italic"),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.status_label.pack(side="right", padx=20, pady=12)

        # ── Main content (two columns) ───────────────────────────────────
        content = ctk.CTkFrame(self.frame, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=20, pady=8)
        content.columnconfigure(0, weight=3)
        content.columnconfigure(1, weight=2)
        content.rowconfigure(0, weight=1)

        self._build_left_panel(content)
        self._build_right_panel(content)

        # ── Footer buttons ───────────────────────────────────────────────
        footer = ctk.CTkFrame(self.frame, fg_color="transparent")
        footer.pack(fill="x", padx=20, pady=(8, 14))
        self.start_btn = ctk.CTkButton(
            footer,
            text="▶  Start Camera",
            width=150,
            height=40,
            corner_radius=8,
            font=("Segoe UI", 13, "bold"),
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            text_color="#000000",
            command=self.start_camera,
        )
        self.stop_btn = ctk.CTkButton(
            footer,
            text="⏹  Stop",
            width=100,
            height=40,
            corner_radius=8,
            font=("Segoe UI", 13, "bold"),
            state="disabled",
            fg_color="#21262d",
            hover_color="#30363d",
            text_color=COLOR_TEXT_PRIMARY,
            command=self.stop_camera,
        )
        self.start_btn.pack(side="left", padx=(0, 8))
        self.stop_btn.pack(side="left")

    def _build_left_panel(self, parent) -> None:
        left = ctk.CTkFrame(parent, corner_radius=16, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))

        # Title Label
        ctk.CTkLabel(
            left, text="📷  Camera Stream & Detection", font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w", padx=16, pady=(16, 6))

        # Camera feed container
        self.video_label = ctk.CTkLabel(
            left,
            text="📷  Camera stopped",
            width=580,
            height=360,
            fg_color=COLOR_BG,
            corner_radius=12,
            font=("Segoe UI", 14),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.video_label.pack(padx=16, pady=8, fill="both", expand=True)

        # Emotion Info Card
        emo_card = ctk.CTkFrame(left, fg_color=COLOR_CARD_ALT, corner_radius=12, border_color=COLOR_BORDER, border_width=1)
        emo_card.pack(fill="x", padx=16, pady=(8, 12))

        # Emotion row
        emo_row = ctk.CTkFrame(emo_card, fg_color="transparent")
        emo_row.pack(fill="x", padx=14, pady=10)

        self.emotion_emoji_label = ctk.CTkLabel(
            emo_row, text="😐", font=("Segoe UI", 38)
        )
        self.emotion_emoji_label.pack(side="left", padx=(0, 12))

        emo_text = ctk.CTkFrame(emo_row, fg_color="transparent")
        emo_text.pack(side="left", fill="x", expand=True)
        self.emotion_label = ctk.CTkLabel(
            emo_text,
            text="Neutral",
            font=("Segoe UI", 18, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            anchor="w",
        )
        self.emotion_label.pack(anchor="w")
        self.confidence_label = ctk.CTkLabel(
            emo_text,
            text="Confidence: 0%",
            font=("Segoe UI", 12),
            text_color=COLOR_TEXT_SECONDARY,
            anchor="w",
        )
        self.confidence_label.pack(anchor="w")

        # Confidence bar
        self.confidence_bar = ctk.CTkProgressBar(
            emo_card, height=6, corner_radius=3, progress_color=COLOR_ACCENT, fg_color=COLOR_BG
        )
        self.confidence_bar.set(0)
        self.confidence_bar.pack(fill="x", padx=14, pady=(0, 12))

        # Recent emotions
        recent_header = ctk.CTkFrame(left, fg_color="transparent")
        recent_header.pack(fill="x", padx=16, pady=(4, 2))
        ctk.CTkLabel(
            recent_header, text="Recent Emotions History", font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT_PRIMARY
        ).pack(side="left")

        self.recent_emotions_frame = ctk.CTkFrame(
            left, fg_color=COLOR_BG, corner_radius=12, border_color=COLOR_BORDER, border_width=1
        )
        self.recent_emotions_frame.pack(fill="x", padx=16, pady=(0, 16))
        
        self.recent_emotion_labels: list[ctk.CTkLabel] = []
        for _ in range(3):
            lbl = ctk.CTkLabel(
                self.recent_emotions_frame,
                text="—",
                font=("Segoe UI", 12),
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
            )
            lbl.pack(anchor="w", padx=14, pady=4)
            self.recent_emotion_labels.append(lbl)

    def _build_right_panel(self, parent) -> None:
        right = ctk.CTkFrame(parent, corner_radius=16, fg_color=COLOR_CARD, border_color=COLOR_BORDER, border_width=1)
        right.grid(row=0, column=1, sticky="nsew")

        # Title Label
        ctk.CTkLabel(
            right, text="🎵  Now Playing & Controls", font=("Segoe UI", 14, "bold"), text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w", padx=16, pady=(16, 6))

        # Center Container
        now_playing_container = ctk.CTkFrame(right, fg_color=COLOR_CARD_ALT, corner_radius=12, border_color=COLOR_BORDER, border_width=1)
        now_playing_container.pack(fill="x", padx=16, pady=8)

        # ── Album art ───────────────────────────────────────────────────
        self.album_art_label = ctk.CTkLabel(
            now_playing_container,
            text="🎵",
            width=140,
            height=140,
            fg_color=COLOR_BG,
            corner_radius=12,
            font=("Segoe UI", 56),
        )
        self.album_art_label.pack(pady=14)

        # ── Now Playing info ─────────────────────────────────────────────
        self.song_title_label = ctk.CTkLabel(
            now_playing_container,
            text="No track playing",
            font=("Segoe UI", 16, "bold"),
            text_color=COLOR_TEXT_PRIMARY,
            wraplength=280,
        )
        self.song_title_label.pack(padx=14, pady=(2, 0))
        
        self.song_artist_label = ctk.CTkLabel(
            now_playing_container,
            text="—",
            font=("Segoe UI", 12),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.song_artist_label.pack(pady=(0, 2))
        
        self.song_meta_label = ctk.CTkLabel(
            now_playing_container,
            text="",
            font=("Segoe UI", 11),
            text_color=COLOR_TEXT_SECONDARY,
        )
        self.song_meta_label.pack(pady=(0, 10))

        # ── Progress bar + times ─────────────────────────────────────────
        time_row = ctk.CTkFrame(right, fg_color="transparent")
        time_row.pack(fill="x", padx=16, pady=(4, 0))
        self.elapsed_label = ctk.CTkLabel(
            time_row, text="00:00", font=("Segoe UI", 11), text_color=COLOR_TEXT_SECONDARY
        )
        self.elapsed_label.pack(side="left")
        self.duration_label = ctk.CTkLabel(
            time_row, text="00:00", font=("Segoe UI", 11), text_color=COLOR_TEXT_SECONDARY
        )
        self.duration_label.pack(side="right")

        self.progress_slider = ctk.CTkSlider(
            right,
            from_=0,
            to=1,
            height=12,
            progress_color=COLOR_BUTTON,
            button_color=COLOR_BUTTON,
            button_hover_color=COLOR_BUTTON_HOVER,
            command=self._on_seek,
            number_of_steps=200,
        )
        self.progress_slider.set(0)
        self.progress_slider.pack(fill="x", padx=16, pady=(0, 10))
        self._seeking = False

        # ── Playback controls ────────────────────────────────────────────
        ctrl_row = ctk.CTkFrame(right, fg_color="transparent")
        ctrl_row.pack(pady=4)

        self.prev_btn = ctk.CTkButton(
            ctrl_row,
            text="⏮",
            width=36,
            height=36,
            corner_radius=18,
            font=("Segoe UI", 15),
            fg_color="#21262d",
            hover_color="#30363d",
            text_color=COLOR_TEXT_PRIMARY,
            command=self._on_previous,
        )
        self.play_pause_btn = ctk.CTkButton(
            ctrl_row,
            text="▶",
            width=46,
            height=46,
            corner_radius=23,
            font=("Segoe UI", 18, "bold"),
            fg_color=COLOR_BUTTON,
            hover_color=COLOR_BUTTON_HOVER,
            text_color="#000000",
            command=self._on_play_pause,
        )
        self.next_btn = ctk.CTkButton(
            ctrl_row,
            text="⏭",
            width=36,
            height=36,
            corner_radius=18,
            font=("Segoe UI", 15),
            fg_color="#21262d",
            hover_color="#30363d",
            text_color=COLOR_TEXT_PRIMARY,
            command=self._on_next,
        )
        self.prev_btn.pack(side="left", padx=12)
        self.play_pause_btn.pack(side="left", padx=12)
        self.next_btn.pack(side="left", padx=12)

        # ── Volume row ───────────────────────────────────────────────────
        vol_row = ctk.CTkFrame(right, fg_color="transparent")
        vol_row.pack(fill="x", padx=16, pady=8)
        
        self.mute_btn = ctk.CTkButton(
            vol_row,
            text="🔊",
            width=32,
            height=28,
            corner_radius=6,
            font=("Segoe UI", 13),
            fg_color="#21262d",
            hover_color="#30363d",
            text_color=COLOR_TEXT_PRIMARY,
            command=self._on_mute,
        )
        self.mute_btn.pack(side="left", padx=(0, 6))
        
        self.volume_slider = ctk.CTkSlider(
            vol_row,
            from_=0,
            to=1,
            height=12,
            progress_color=COLOR_ACCENT,
            button_color=COLOR_ACCENT,
            button_hover_color="#00b8cc",
            command=self._on_volume_change,
            number_of_steps=20,
        )
        self.volume_slider.set(self.player.volume)
        self.volume_slider.pack(side="left", fill="x", expand=True)

        # ── Upcoming queue ───────────────────────────────────────────────
        ctk.CTkLabel(
            right, text="Up Next In Queue", font=("Segoe UI", 12, "bold"), text_color=COLOR_TEXT_PRIMARY
        ).pack(anchor="w", padx=16, pady=(8, 2))
        
        self.queue_frame = ctk.CTkFrame(
            right, fg_color=COLOR_BG, corner_radius=12, border_color=COLOR_BORDER, border_width=1
        )
        self.queue_frame.pack(fill="x", padx=16, pady=(0, 16))
        
        self.queue_labels: list[ctk.CTkLabel] = []
        for _ in range(3):
            lbl = ctk.CTkLabel(
                self.queue_frame,
                text="—",
                font=("Segoe UI", 12),
                text_color=COLOR_TEXT_SECONDARY,
                anchor="w",
            )
            lbl.pack(anchor="w", padx=14, pady=5)
            self.queue_labels.append(lbl)

    # Camera lifecycle
    def pack(self, *args, **kwargs) -> None:
        self.frame.pack(*args, **kwargs)

    def start_camera(self) -> None:
        if self.running:
            return
        try:
            self._ensure_pipeline()
            self.webcam = Webcam()
            self.webcam.start()
        except Exception as exc:
            self.stop_camera(f"Startup failed: {exc}")
            logger.error(f"Camera startup failed: {exc}")
            return

        self.running = True
        self.start_btn.configure(state="disabled")
        self.stop_btn.configure(state="normal")
        self.status_label.configure(text="Looking for a face…")
        self._update_frame()

    def stop_camera(self, status: str = "Camera stopped.") -> None:
        self.running = False
        if self.webcam is not None:
            self.webcam.release()
            self.webcam = None
        self.start_btn.configure(state="normal")
        self.stop_btn.configure(state="disabled")
        self.video_label.configure(image=None, text="📷  Camera stopped")
        self.status_label.configure(text=status)

    def shutdown(self) -> None:
        self.executor.shutdown(wait=False, cancel_futures=True)
        self.player.cleanup()

    def _ensure_pipeline(self) -> None:
        if self.face_detector is None:
            logger.info("Loading face detector…")
            self.face_detector = HaarCascadeFaceDetector()
            logger.info("Face detector ready.")
        if self.emotion_detector is None:
            logger.info("Loading emotion detector…")
            self.emotion_detector = EmotionDetectorFactory.create()
            logger.info("Emotion detector ready.")

    # Frame update loop
    def _update_frame(self) -> None:
        if not self.running or self.webcam is None:
            return

        self._drain_result_queue()
        self._check_song_ended()

        frame = self.webcam.read_frame()
        if frame is None:
            self.status_label.configure(text="Camera frame was empty.")
            self.frame.after(60, self._update_frame)
            return

        frame, rgb_frame = self.processor.preprocess(frame)
        boxes = self.face_detector.detect_faces(rgb_frame)

        if boxes:
            box = boxes[0]
            label = f"{EMOTION_EMOJI.get(self.current_emotion, '')} {self.current_confidence:.0%}"
            self.face_detector.draw_box(frame, box, label)
            self.status_label.configure(text="Face detected.")
            self._submit_prediction_if_ready(rgb_frame, box)
        else:
            self.status_label.configure(text="No face detected. Face the camera clearly.")

        self._show_frame(frame)
        self._update_player_ui()
        self.frame.after(30, self._update_frame)

    # Prediction pipeline (thread-safe via queue)
    def _submit_prediction_if_ready(self, rgb_frame, box) -> None:
        if self._is_predicting:
            return
        now = monotonic()
        if now - self.last_emotion_check < config.EMOTION.UPDATE_INTERVAL:
            return
        self.last_emotion_check = now
        face = self.face_detector.crop_face(rgb_frame, box)
        self._is_predicting = True
        self.executor.submit(self._run_prediction, face.copy())

    def _run_prediction(self, face):
        """Runs in worker thread — puts result into queue for main thread."""
        try:
            result = self.emotion_detector.predict(face)
            self._result_queue.put(("ok", result))
        except Exception as exc:
            self._result_queue.put(("err", str(exc)))

    def _drain_result_queue(self) -> None:
        """Process all pending prediction results from the worker thread."""
        while not self._result_queue.empty():
            try:
                kind, payload = self._result_queue.get_nowait()
            except queue.Empty:
                break
            except Exception:
                self._result_queue.put(("err", traceback.format_exc()))
            self._is_predicting = False
            if kind == "err":
                self.status_label.configure(text=f"Detection error: {payload}")
                logger.warning(f"Emotion detection error: {payload}")
                continue
            self._process_prediction(payload)

    def _process_prediction(self, payload) -> None:
        emotion, confidence = payload
        smoothed = self.smoother.add(emotion)
        self.current_confidence = confidence

        # Update confidence UI
        self.confidence_label.configure(text=f"Confidence: {confidence:.0%}")
        self.confidence_bar.set(confidence)

        if confidence < config.EMOTION.CONFIDENCE_THRESHOLD:
            self.status_label.configure(text="Confidence too low — keep facing the camera.")
            self._stability_start = 0.0
            self._stable_emotion = smoothed
            return

        # 2-second stability check
        now = monotonic()
        if smoothed != self._stable_emotion or self._stability_start <= 0.0:
            self._stable_emotion = smoothed
            self._stable_confidence = confidence
            self._stability_start = now
            self._update_emotion_display(smoothed)
            return

        # Emotion has been stable — check if 2 seconds have elapsed
        if now - self._stability_start >= config.EMOTION.STABILITY_DURATION:
            if smoothed != self._last_triggered_emotion:
                self._last_triggered_emotion = smoothed
                self.current_emotion = smoothed
                self._stability_start = now  # reset so we don't fire again immediately
                self._on_emotion_stabilized(smoothed)

    def _update_emotion_display(self, emotion: str) -> None:
        emoji = EMOTION_EMOJI.get(emotion, "❓")
        self.emotion_emoji_label.configure(text=emoji)
        self.emotion_label.configure(text=emotion.capitalize())

    def _on_emotion_stabilized(self, emotion: str) -> None:
        """Called when emotion has been stable for 2 seconds."""
        logger.info(f"Stable emotion: {emotion}")
        self.status_label.configure(text=f"Emotion stable: {emotion.capitalize()} — loading music…")

        # Add to recent emotions list
        self._recent_emotions.insert(0, emotion)
        self._recent_emotions = self._recent_emotions[:5]
        self._refresh_recent_emotions_ui()

        # Recommend and queue songs
        try:
            # Fill queue with top recommendations
            top_songs = self.recommender.top_recommendations(emotion, limit=5)
            if not top_songs:
                self.status_label.configure(text="No songs found for this emotion.")
                return

            self.player.queue.clear()
            self.player.queue.load_songs(top_songs[1:])  # rest goes to queue

            # Play the top song immediately
            first_song = top_songs[0]
            self.recommender.history.add_song(first_song.filename)
            self.recommender.play_stats.record_play(first_song.filename)
            self.player.play(first_song)
            self._refresh_now_playing_ui(first_song)
            self._refresh_queue_ui()
            self.play_pause_btn.configure(text="⏸")
            self.status_label.configure(
                text=f"Playing: {first_song.title} — {emotion.capitalize()}"
            )
        except Exception as exc:
            logger.error(f"Failed to play song: {exc}")
            self.status_label.configure(text=f"Playback error: {exc}")

    # Player UI refresh
    def _update_player_ui(self) -> None:
        """Called every frame to refresh progress bar and timers."""
        song = self.player.current_song
        if song is None or song.duration <= 0:
            return
        elapsed = self.player.elapsed_seconds()
        frac = self.player.progress_fraction()

        self.elapsed_label.configure(text=_format_duration(elapsed))
        self.duration_label.configure(text=_format_duration(song.duration))

        if not self._seeking:
            self.progress_slider.set(frac)

    def _refresh_now_playing_ui(self, song: Song) -> None:
        self.song_title_label.configure(text=song.title)
        self.song_artist_label.configure(text=song.artist)

        meta_parts = []
        if song.album and song.album != "Unknown Album":
            meta_parts.append(song.album)
        if song.bitrate:
            meta_parts.append(f"{song.bitrate} kbps")
        self.song_meta_label.configure(text="  ·  ".join(meta_parts))

        # Cover art
        if song.cover_art:
            try:
                img = Image.open(io.BytesIO(song.cover_art)).resize((140, 140))
                ctk_img = ctk.CTkImage(light_image=img, dark_image=img, size=(140, 140))
                self.album_art_label.configure(image=ctk_img, text="")
                self._album_art_ref = ctk_img  # prevent GC
            except Exception as e:
                logger.warning(f"Could not render cover art: {e}")
                self.album_art_label.configure(image=None, text="🎵")
        else:
            self.album_art_label.configure(image=None, text="🎵")

        # Reset progress
        self.progress_slider.set(0)
        self.elapsed_label.configure(text="00:00")
        self.duration_label.configure(text=_format_duration(song.duration))

    def _refresh_queue_ui(self) -> None:
        upcoming = self.player.queue.peek_next(3)
        for i, lbl in enumerate(self.queue_labels):
            if i < len(upcoming):
                s = upcoming[i]
                lbl.configure(
                    text=f"{i + 1}.  {s.title}  —  {s.artist}",
                    text_color=COLOR_TEXT_PRIMARY,
                )
            else:
                lbl.configure(text="—", text_color=COLOR_TEXT_SECONDARY)

    def _refresh_recent_emotions_ui(self) -> None:
        for i, lbl in enumerate(self.recent_emotion_labels):
            if i < len(self._recent_emotions):
                em = self._recent_emotions[i]
                emoji = EMOTION_EMOJI.get(em, "")
                lbl.configure(
                    text=f"{emoji}  {em.capitalize()}",
                    text_color=COLOR_TEXT_PRIMARY,
                )
            else:
                lbl.configure(text="—", text_color=COLOR_TEXT_SECONDARY)

    # Auto-advance when track ends
    def _check_song_ended(self) -> None:
        if not self.player.check_song_ended():
            return
        current = self.player.current_song
        if current:
            self.recommender.song_completed(current)

        if self.player.queue.has_next():
            next_song = self.player.next()
            if next_song:
                self._refresh_now_playing_ui(next_song)
                self._refresh_queue_ui()
                self.play_pause_btn.configure(text="⏸")
                logger.info(f"Auto-advancing to: {next_song.title}")
        else:
            # Queue empty — recommend a new batch and play the first one
            try:
                top_songs = self.recommender.top_recommendations(self.current_emotion, limit=5)
                if top_songs:
                    self.player.queue.clear()
                    self.player.queue.load_songs(top_songs[1:])
                    next_song = top_songs[0]
                    self.player.play(next_song)
                    self._refresh_now_playing_ui(next_song)
                    self._refresh_queue_ui()
                    self.play_pause_btn.configure(text="⏸")
                    logger.info(f"Queue empty — auto-recommended: {next_song.title}")
            except Exception as exc:
                logger.error(f"Auto-recommendation failed: {exc}")

    # Control callbacks
    def _on_play_pause(self) -> None:
        if self.player.current_song is None:
            # Recommend a fresh playlist for the current emotion
            try:
                top_songs = self.recommender.top_recommendations(self.current_emotion, limit=5)
                if top_songs:
                    self.player.queue.clear()
                    self.player.queue.load_songs(top_songs[1:])
                    next_song = top_songs[0]
                    self.player.play(next_song)
                    self._refresh_now_playing_ui(next_song)
                    self._refresh_queue_ui()
                    self.play_pause_btn.configure(text="⏸")
            except Exception as exc:
                logger.error(f"Playback initiation failed: {exc}")
            return
        paused = self.controls.play_pause()
        self.play_pause_btn.configure(text="▶" if paused else "⏸")

    def _on_next(self) -> None:
        current = self.player.current_song
        if current:
            self.recommender.song_skipped(current)
        next_song = self.controls.next_track()
        if next_song:
            self._refresh_now_playing_ui(next_song)
            self._refresh_queue_ui()
            self.play_pause_btn.configure(text="⏸")
        else:
            # Queue is empty — load a new recommendation batch
            try:
                top_songs = self.recommender.top_recommendations(self.current_emotion, limit=5)
                if top_songs:
                    self.player.queue.clear()
                    self.player.queue.load_songs(top_songs[1:])
                    next_song = top_songs[0]
                    self.player.play(next_song)
                    self._refresh_now_playing_ui(next_song)
                    self._refresh_queue_ui()
                    self.play_pause_btn.configure(text="⏸")
            except Exception as exc:
                logger.error(f"Next track recommendation failed: {exc}")

    def _on_previous(self) -> None:
        prev_song = self.controls.previous_track()
        if prev_song:
            self._refresh_now_playing_ui(prev_song)
            self._refresh_queue_ui()
            self.play_pause_btn.configure(text="⏸")

    def _on_mute(self) -> None:
        muted = self.controls.mute()
        self.mute_btn.configure(text="🔇" if muted else "🔊")

    def _on_volume_change(self, value: float) -> None:
        self.controls.set_volume(value)

    def _on_seek(self, value: float) -> None:
        """Called while dragging the seek slider."""
        song = self.player.current_song
        if song and song.duration > 0:
            self._seeking = True
            target = value * song.duration
            self.player.seek(target)
            self._seeking = False

    # Frame rendering

    def _show_frame(self, frame) -> None:
        display_w, display_h = 580, 360
        display_frame = cv2.resize(frame, (display_w, display_h))
        display_frame = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(display_frame)
        self.video_image = ctk.CTkImage(
            light_image=img, dark_image=img, size=(display_w, display_h)
        )
        self.video_label.configure(image=self.video_image, text="")
