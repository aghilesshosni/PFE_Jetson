import cv2
import numpy as np
import time
from vision import (GestionnaireCamera, ConfigurateurCamera, AnalyseurPosition, DetecteurBouteille, DetecteurNiveau)



class VisionMain:
	def __init__(self):
		self.config= ConfigurateurCamera()
		self.camera= GestionnaireCamera(camera_id=0)
                #Preallocation de buffer
		self.frame_buffer=np.zeros((self.ConfigurateurCamera.height, self.ConfigurateurCamera.width, 3),dtype=np.uint8)
		self.est_tournant=False
		self.dernier_resultat={'Autorisée':'False', 'Compensation':'0'}
	def start():
		if not self.camera.open():
			raise RuntimeError("Echec de Camera")
		self.est_tournant=True 
