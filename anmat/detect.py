"""Phát hiện khuôn mặt: ưu tiên YuNet (OpenCV DNN), dự phòng Haar cascade có sẵn."""
import os
import urllib.request

import cv2
import numpy as np

MODEL_URL = (
    "https://github.com/opencv/opencv_zoo/raw/main/models/"
    "face_detection_yunet/face_detection_yunet_2023mar.onnx"
)
CACHE_DIR = os.path.join(os.path.expanduser("~"), ".cache", "anmat")
MODEL_PATH = os.path.join(CACHE_DIR, "yunet.onnx")


def _ensure_model():
    if os.path.exists(MODEL_PATH) and os.path.getsize(MODEL_PATH) > 100_000:
        return MODEL_PATH
    try:
        os.makedirs(CACHE_DIR, exist_ok=True)
        print("[anmat] Đang tải model nhận diện mặt (~230KB, chỉ lần đầu)...")
        urllib.request.urlretrieve(MODEL_URL, MODEL_PATH)
        return MODEL_PATH
    except Exception as exc:  # không có mạng -> dùng Haar
        print(f"[anmat] Không tải được model ({exc}), chuyển sang Haar cascade.")
        return None


class FaceDetector:
    def __init__(self, threshold=0.6):
        self.threshold = threshold
        self.yunet = None
        path = _ensure_model()
        if path:
            try:
                self.yunet = cv2.FaceDetectorYN.create(path, "", (320, 320), threshold, 0.3, 5000)
            except Exception:
                self.yunet = None
        if self.yunet is None:
            self.haar = cv2.CascadeClassifier(
                os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
            )

    def detect(self, img):
        """Trả về list (x, y, w, h) các khuôn mặt."""
        h, w = img.shape[:2]
        if self.yunet is not None:
            self.yunet.setInputSize((w, h))
            _, faces = self.yunet.detect(img)
            if faces is None:
                return []
            return [tuple(int(v) for v in f[:4]) for f in faces]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        found = self.haar.detectMultiScale(gray, 1.1, 5, minSize=(24, 24))
        return [tuple(int(v) for v in f) for f in found]
