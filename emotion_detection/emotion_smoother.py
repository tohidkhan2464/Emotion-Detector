from collections import Counter, deque


class EmotionSmoother:
    def __init__(self, window_size: int = 5) -> None:
        self.predictions = deque(maxlen=window_size)

    def add(self, emotion: str) -> str:
        self.predictions.append(emotion)
        return self.current()

    def current(self) -> str:
        if not self.predictions:
            return "neutral"
        return Counter(self.predictions).most_common(1)[0][0]

    def clear(self) -> None:
        self.predictions.clear()
