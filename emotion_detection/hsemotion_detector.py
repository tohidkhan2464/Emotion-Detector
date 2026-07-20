import cv2
from hsemotion.facial_emotions import HSEmotionRecognizer
from emotion_detection.base_detector import BaseEmotionDetector
from emotion_detection.emotion_mapper import EmotionMapper
import numpy as np


class HSEmotionDetector(BaseEmotionDetector):
    def __init__(self, model_name="enet_b0_8_va_mtl"):
        self.mapper = EmotionMapper()
        self.model_name = model_name
        self.model = None

    def _load_model(self):
        if self.model is None:
            self.model = HSEmotionRecognizer(model_name=self.model_name)
        return self.model

    def predict(self, face) -> tuple[str, float]:
        model = self._load_model()
        print(face.shape)
        cv2.imshow("Face", cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
        cv2.imwrite("debug_face.jpg", cv2.cvtColor(face, cv2.COLOR_RGB2BGR))
        cv2.waitKey(1)

        raw, scores = model.predict_emotions(face, logits=False)
        scores = np.asarray(scores, dtype=np.float32)
        confidence = float(scores.max())

        return self.mapper.normalize(raw), confidence