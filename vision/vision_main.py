import cv2
import numpy as np
import time
from vision import (GestionnaireCamera, ConfigurateurCamera, AnalyseurPosition, DetecteurBouteille, DetecteurNiveau)



class VisionMain:
	def __init__(self):
		self.config= ConfigurateurVision()
		self.camera= GestionnaireCamera(self.config.id_camera)
                #Preallocation de buffer
		self.frame_buffer=np.zeros((self.config.height, self.config.width, 3),dtype=np.uint8)
		self.est_tournant=False
		self.dernier_resultat={'Autorisation_Remplissage':False, 'Arret_Convoyeur':False, 'Defaut_Systeme':False, 'Status': 'Init', 'Compensation':0, 'Niveau_Remplissage':0.0}
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

				self.dernier_resultat.update({
					
					
                		        'Autorisation_Remplissage': False,
                   	        	'Arret_Convoyeur': False,
                   			'Defaut_Systeme': False,
                		        'Status': "ATTENTE"
               			 })

				resultat=DetecteurBouteille.detecter(frame, self.config)
				self.dernier_resultat['Autorisation_Remplissage'] = False
		                self.dernier_resultat['Arret_Convoyeur'] = False
		                self.dernier_resultat['Defaut_Systeme'] = False
		                self.dernier_resultat['Niveau_Remplissage'] = 0.0
		                self.dernier_resultat['Status'] = "ATTENTE"
				if resultat['present']:
					print("Bouteille existe")
					print(f"Bouteille est positionée à {resultat['centre']}")
					resultat_niveau = DetecteurNiveau.verifier(frame,resultat['bbox'],self.config)


					self.dernier_resultat['Niveau_Remplissage']= resultat_niveau['pourcentage']

					if resultat_niveau['debordement']:
						
					        self.dernier_resultat['Autorisation_Remplissage'] = False
			                        self.dernier_resultat['Arret_Convoyeur'] = True
			                        self.dernier_resultat['Defaut_Systeme'] = True
			                        self.dernier_resultat['Niveau_Remplissage'] = 100.0
			                        self.dernier_resultat['Status'] = "DEBORDEMENT"
				        elif resultat_niveau['plein']:
                                                self.dernier_resultat['Autorisation_Remplissage'] = False
                                                self.dernier_resultat['Arret_Convoyeur'] = False
                                                self.dernier_resultat['Defaut_Systeme'] = False
                                                self.dernier_resultat['Niveau_Remplissage'] = 100.0
                                                self.dernier_resultat['Status'] = "Bouteille Pleine"
					else:
    						self.dernier_resultat['Autorisation_Remplissage'] = True
                                                self.dernier_resultat['Arret_Convoyeur'] = True
                                                self.dernier_resultat['Defaut_Systeme'] = False
                                                self.dernier_resultat['Niveau_Remplissage'] = 0.0
                                                self.dernier_resultat['Status'] = "En Cours de remplissage"




				else:
					self.dernier_resultat['Status']="Aucune bouteille détectée"


				cv2.imshow("Ligne de Production ", frame)
				if cv2.waitKey(1) & 0xFF ==ord('q'):
					break


		except Exception as e:
			print (f"Erreur :{e}")
		finally:
			self.arreter()








	def arreter(self):
		self.est_tournant=False
		self.camera.release()
		cv2.destroyAllWindows()


#TEST du module Vision
if __name__=="__main__":
	print("TEST du module Vision")
	systeme= VisionMain()
	try:
		if systeme.start():
			systeme.run()
		else:
			print("Echec de démarrage")

	except KeyboardInterrupt:
		print ("veuilley appuiyer sur Ctr C")
	except Exception as e:
		print(f" Ereur critique: {e}")
	finally:
		systeme.arreter()
