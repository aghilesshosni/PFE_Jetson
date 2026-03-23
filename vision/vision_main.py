import cv2
import numpy as np
import time
from vision import (GestionnaireCamera, ConfigurateurCamera, AnalyseurPosition, DetecteurBouteille, DetecteurNiveau)



class VisionMain:
	def __init__(self):
		self.config= ConfigurateurCamera()
		self.camera= GestionnaireCamera(camera_id=0)
                #Preallocation de buffer
		self.frame_buffer=np.zeros((self.Config.height, self.Config.width, 3),dtype=np.uint8)
		self.est_tournant=False
		self.dernier_resultat={'Autorisation_Remplissage':'False', 'Arret_Convoyeur':False, 'Defaut_Systeme':False, 'Status': 'Init', 'Compensation':0, 'Niveau_Remplissage':0.0}
	def start(self):
		if not self.camera.open():
			raise RuntimeError("Echec de Camera")
		self.est_tournant=True 

	def run(self):
		#Boucle infinie de traitement d'images
		if not self.est_tournant:
			return
		try:
			while self.est_tournant:
				debut_cycle=time.time()
				frame=self.camera.read()
				if frame is None:
					continue
			resultat=DetecteurBouteille.detecter(frame, self.config)
			if resultat['present']:
				print("Bouteille existe")
				print(f"Bouteille est positionée à {resultat['centre']}")

		except Exception as e:
			print (f"Erreur :{e}]")
		finally:
			self.arreter()








	def arreter(self):
		self.est_tournant=False
		self.camera.release()
		cv2.destroyAllWindows()
