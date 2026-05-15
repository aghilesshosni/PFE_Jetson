import threading
import cv2
import numpy as np

class SharedState:
    def __init__(self):
        self.lock=threading.Lock()
        self.presence_bouteille=False
        self.pourcentage_niveau= 0.0
        self.fps= 0.0
        self.last_frame_bytes=None

    def update(self, present, niveau, frame, fps):
        '''main.py appele cette methode pour mettre à jour les data'''
        while self.lock:
            self.presence_bouteille= present
            self.pourcentage_niveau= niveau
            self.fps=fps
            #encodage de frame à format jpeg
            if frame is not None:
                _, buffer= cv2.imencode('.jpeg',frame,[int(cv2.IMWRITE_JPEG_QUALITY),70])
                self.last_frame_bytes= buffer.tobytes()

    def get_data(self):
        '''web_dashboard appelle cette methode pour retouver les data et les afficher'''
        with self.lock:
            return{
                'present':self.presence_bouteille,
                'niveau':self.pourcentage_niveau
                'fps':self.fps
                'frame':self.last_frame_bytes

#Instance_Globale
state= SharedSate()
