from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent

FRAME_WIDTH = 1280
FRAME_HEIGHT = 720
class CAMERA:
    INDEX = 0
    WIDTH = 1280
    HEIGHT = 720
    FACE_DETECTION_EVERY_N_FRAMES = 3


class EMOTION:
    DETECTION_CONFIDENCE = 0.6
    CONFIDENCE_THRESHOLD = 0.5
    UPDATE_INTERVAL = 0.2  # high frequency to support stability calculations
    STABILITY_DURATION = 2.0  # seconds required for stability
    # ENGINE = "deepface"
    ENGINE = "hsemotion"
    SUPPORTED = [
        "happy",
        "sad",
        "angry",
        "neutral",
        "surprise",
        "fear",
        "disgust",
    ]


class PLAYER:
    MUSIC_FOLDER = BASE_DIR / "assets" / "songs"
    BACKEND = "pygame"


class DATABASE:
    DIR = BASE_DIR / "database"
    SONGS_CSV = DIR / "songs.csv"
    EMOTION_MAPPING_JSON = DIR / "emotion_mapping.json"
    HISTORY_JSON = DIR / "history.json"
    PLAY_STATS_JSON = DIR / "play_stats.json"
    PREFERENCES_JSON = DIR / "preferences.json"


class UI:
    WIDTH = 1200
    HEIGHT = 750
