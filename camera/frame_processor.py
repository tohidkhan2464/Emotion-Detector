import config
import cv2


class FrameProcessor:
    def resize(
        self, frame, width: int = config.FRAME_WIDTH, height: int = config.FRAME_HEIGHT
    ):
        return cv2.resize(frame, (width, height))

    def flip(self, frame):
        return cv2.flip(frame, 1)

    def convert_rgb(self, frame):
        return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    def improve_brightness(self, frame, alpha: float = 1.1, beta: int = 10):
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=beta)

    def preprocess(self, frame, improve_brightness=False):
        frame = self.resize(frame)
        frame = self.flip(frame)
        detection_frame = frame
        if improve_brightness:
            detection_frame = self.improve_brightness(detection_frame)
        rgb_frame = self.convert_rgb(detection_frame)
        return frame, rgb_frame
