import cv2

class GestionnaireCamera:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            return False
        return True

    def read(self):
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
