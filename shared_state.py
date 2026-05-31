# -*- coding: utf-8 -*-
import threading
import cv2
import time


class SharedState:
    def __init__(self):
        self._lock = threading.Lock()
        self._present = False
        self._level = 0.0
        self._frame = None
        self._fps = 0.0
        self._status = "AUCUNE_BOUTEILLE"
        self._timestamp = time.time()

    def update(self, present, level, frame, fps, status):
        if frame is not None:
            small = cv2.resize(frame, (320, 240))
            _, buffer = cv2.imencode('.jpg', small, [cv2.IMWRITE_JPEG_QUALITY, 30])
            frame_bytes = buffer.tobytes()
        else:
            frame_bytes = None

        with self._lock:
            self._present = present
            self._level = level
            self._fps = fps
            self._status = status
            self._frame = frame_bytes
            self._timestamp = time.time()

    def get_data(self):
        with self._lock:
            return {
                'presence_bouteille': self._present,
                'pourcentage_niveau': round(self._level, 1),
                'last_frame_bytes': self._frame,
                'fps': round(self._fps, 1),
                'status': self._status,
                'timestamp': self._timestamp,
            }


state = SharedState()
