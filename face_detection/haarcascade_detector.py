import config
from face_detection.utils import clip_box, expand_box
import cv2


class HaarCascadeFaceDetector:
    def __init__(
        self, min_detection_confidence: float = config.EMOTION.DETECTION_CONFIDENCE
    ) -> None:
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)
        if self.detector.empty():
            raise RuntimeError(f"Could not load OpenCV face cascade: {cascade_path}")

        self.min_neighbors = max(3, round(min_detection_confidence * 8))

    def detect_faces(self, rgb_frame) -> list[tuple[int, int, int, int]]:
        height, width = rgb_frame.shape[:2]
        gray_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_RGB2GRAY)
        detections = self.detector.detectMultiScale(
            gray_frame,
            scaleFactor=1.1,
            minNeighbors=self.min_neighbors,
            minSize=(60, 60),
        )

        return [clip_box(tuple(map(int, box)), width, height) for box in detections]

    def crop_face(self, frame, box: tuple[int, int, int, int], padding: float = 1.25):
        height, width = frame.shape[:2]
        x, y, w, h = expand_box(box, width, height, padding)
        return frame[y : y + h, x : x + w]

    def draw_box(self, frame, box: tuple[int, int, int, int], label: str | None = None):

        x, y, w, h = box
        cv2.rectangle(frame, (x, y), (x + w, y + h), (40, 220, 90), 2)
        if label:
            cv2.putText(
                frame,
                label,
                (x, max(20, y - 8)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (40, 220, 90),
                2,
            )
        return frame
