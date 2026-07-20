from abc import ABC, abstractmethod


class BaseEmotionDetector(ABC):
    @abstractmethod
    def predict(self, face) -> tuple[str, float]:
        pass