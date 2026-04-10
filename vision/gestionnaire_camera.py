import cv2

class GestionnaireCamera:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None

        self.gstreamer_pipeline = (
            "nvarguscamerasrc sensor-id=0 ! "
            "video/x-raw(memory:NVMM), width=1280, height=720, framerate=30/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, format=BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=BGR ! "
            "appsink drop=true"
        )

    def open(self):
        print("Ouverture caméra Jetson...")

        self.cap = cv2.VideoCapture(self.gstreamer_pipeline, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            print("Erreur: caméra non ouverte")
            return False

        print("Caméra OK")
        return True

    def read(self):
        if self.cap is None or not self.cap.isOpened():
            return None

        ret, frame = self.cap.read()
        if not ret:
            return None

        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
