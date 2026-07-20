import config
import cv2
from utils.logger import get_logger

logger = get_logger("webcam")


class Webcam:
    def __init__(
        self,
        camera_index: int = config.CAMERA.INDEX,
        width: int = config.CAMERA.WIDTH,
        height: int = config.CAMERA.HEIGHT,
    ) -> None:
        self.camera_index = camera_index
        self.width = width
        self.height = height
        self.capture = None
        self.backend_name = "default"

    def start(self):
        logger.info("Opening camera...")

        backends = [
            ("default", cv2.CAP_ANY),
            ("DirectShow", cv2.CAP_DSHOW),
            ("Media Foundation", cv2.CAP_MSMF),
        ]
        errors = []

        for backend_name, backend in backends:
            capture = cv2.VideoCapture(self.camera_index, backend)
            opened = capture.isOpened()
            logger.info(f"{backend_name} opened: {opened}")

            if opened:
                self.capture = capture
                self.backend_name = backend_name
                break

            capture.release()
            errors.append(backend_name)

        if self.capture is None:
            tried = ", ".join(errors)
            raise RuntimeError(
                f"Could not open webcam index {self.camera_index}. Tried: {tried}"
            )

        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        logger.info(f"Camera opened with {self.backend_name}")

    def read_frame(self):
        if self.capture is None:
            raise RuntimeError("Webcam has not been started.")

        ok, frame = self.capture.read()
        if not ok:
            return None
        return frame

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
            self.capture = None
            logger.info("Camera released.")
