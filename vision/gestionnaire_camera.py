import cv2

class GestionnaireCamera:
    def __init__(self, camera_id):
        self.camera_id = camera_id
        self.cap = None
        self.gstreamer_pipeline = (
            "nvarguscamerasrc ! "
            "video/x-raw(memory:NVMM), width=(int)1920, height=(int)1080, format=(string)NV12, framerate=(fraction)30/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, width=(int)1920, height=(int)1080, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! "
            "appsink"
        )

    def open(self):
        if isinstance(self.camera_id, int):
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if not self.cap.isOpened():
                print("Échec ouverture , on essaye GStreamer pour CSI...")
                self.cap = cv2.VideoCapture(self.gstreamer_pipeline, cv2.CAP_GSTREAMER)
        else:
            self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            return False
        
        ret, _ = self.cap.read()
        if not ret:
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
