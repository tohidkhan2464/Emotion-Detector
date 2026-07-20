import time


class PeriodicTimer:
    def __init__(self, interval_seconds: float) -> None:
        self.interval_seconds = interval_seconds
        self.last_run = 0.0

    def ready(self) -> bool:
        return time.monotonic() - self.last_run >= self.interval_seconds

    def reset(self) -> None:
        self.last_run = time.monotonic()
