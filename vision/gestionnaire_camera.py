# -*- coding: utf-8 -*-
import cv2

class GestionnaireCamera:
    def __init__(self, camera_id=0):
        self.camera_id = camera_id
        self.cap = None

        # Parametres JetsonHacks
        self.capture_width = 1920
        self.capture_height = 1080
        self.display_width = 1280   
        self.display_height = 720
        self.framerate = 30
        self.flip_method = 0       

    def gstreamer_pipeline(self):
        return (
            "nvarguscamerasrc sensor-id=%d ! "
            "video/x-raw(memory:NVMM), width=(int)%d, height=(int)%d, framerate=(fraction)%d/1 ! "
            "nvvidconv flip-method=%d ! "
            "video/x-raw, width=(int)%d, height=(int)%d, format=(string)BGRx ! "
            "videoconvert ! "
            "video/x-raw, format=(string)BGR ! appsink"
            % (
                self.camera_id,
                self.capture_width,
                self.capture_height,
                self.framerate,
                self.flip_method,
                self.display_width,
                self.display_height,
            )
        )

    def open(self):
        print("Initialisation camera (Methode Directe JetsonHacks)...")

        pipeline_str = self.gstreamer_pipeline()

        self.cap = cv2.VideoCapture(pipeline_str, cv2.CAP_GSTREAMER)

        if not self.cap.isOpened():
            print("ECHEC : Impossible d'ouvrir la camera avec le pipeline GStreamer.")
            return False

        print("Camera ouverte avec succes !")
        print("   -> Attente de la premiere image...")

        for i in range(30): 
            ret, frame = self.cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                # CORRECTION PYTHON 2.7 : Remplacement de f-string par .format()
                print("SUCCES : Flux actif ! Resolution recue : {}x{}".format(w, h))
                return True
            cv2.waitKey(10) 

        print("Attention : Camera ouverte mais aucune image recue apres 3s.")
        return True

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
        print("Camera relachee.")
