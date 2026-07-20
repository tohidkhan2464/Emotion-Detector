import config
from emotion_detection.hsemotion_detector import HSEmotionDetector
from utils.logger import get_logger

logger = get_logger("emotion_factory")


class EmotionDetectorFactory:
    @staticmethod
    def create():
        engine = config.EMOTION.ENGINE.lower()
        logger.info(f"Creating emotion detector: {engine}")

        if engine == "hsemotion":
            return HSEmotionDetector()

        raise ValueError(f"Unsupported emotion engine: {config.EMOTION.ENGINE}")
