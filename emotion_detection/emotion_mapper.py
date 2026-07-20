import config


class EmotionMapper:
    DEFAULT_MAPPING = {
        # Direct mappings
        "happy": "happy",
        "sad": "sad",
        "angry": "angry",
        "calm": "calm",
        # Neutral face → Calm music
        "neutral": "calm",
        # Fear usually benefits from calming music
        "fear": "calm",
        "fearful": "calm",
        # Surprise is usually high-arousal and positive/energetic
        "surprise": "happy",
        "surprised": "happy",
        # Disgust is negative high-arousal
        "disgust": "angry",
        "disgusted": "angry",
    }

    def __init__(self, mapping: dict[str, str] | None = None) -> None:
        # Use provided mapping or fall back to defaults (never use the JSON path here)
        self.mapping = mapping or self.DEFAULT_MAPPING

    def normalize(self, emotion: str) -> str:
        normalized = self.mapping.get(emotion.strip().lower(), "neutral")
        if normalized not in config.EMOTION.SUPPORTED:
            return "neutral"
        return normalized
