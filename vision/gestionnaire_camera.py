import cv2

class GestionnaireCamera:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None
        
        self.gstreamer_pipeline = (
            "nvarguscamerasrc sensor-id=0 ! "
            "video/x-raw(memory:NVMM), width=(int)1280, height=(int)720, format=(string)NV12, framerate=(fraction)30/1 ! "
            "nvvidconv flip-method=0 ! "
            "video/x-raw, width=(int)1280, height=(int)720, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! "
            "appsink drop=true"
        )

    def open(self):
        print("Tentative d'ouverture de la caméra...")
        
        if isinstance(self.camera_id, int):
            print(f"Essai mode standard (ID: {self.camera_id})...")
            self.cap = cv2.VideoCapture(self.camera_id)
            
            if self.cap.isOpened():
                ret, _ = self.cap.read()
                if ret:
                    print("Succès : Mode Standard")
                    return True
                else:
                    self.cap.release()
        
        print("Échec mode standard. Bascule vers GStreamer (CSI)...")
        self.cap = cv2.VideoCapture(self.gstreamer_pipeline, cv2.CAP_GSTREAMER)
        
        if self.cap.isOpened():
            ret, _ = self.cap.read()
            if ret:
                print("Mode GStreamer (Jetson CSI)")
                return True
            else:
                print(" Attention : Flux ouvert mais lecture échouée.")
        
        print(" Impossible d'ouvrir la caméra.")
        return False

    def read(self):
        if self.cap is None or not self.cap.isOpened():
            return None
        
        ret, frame = self.cap.read()
        if not ret:
            ret, frame = self.cap.read()
            if not ret:
                return None
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        print("Caméra relâchée.")
