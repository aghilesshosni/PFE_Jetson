import cv2
import numpy as np

class DetecteurNiveau:
	#Detecter le niveau de liquide en analysant le contour du liquide
	@staticmethod
	def verifier(frame,bbox_bouteille,config):
		x, y, w, h=bbow_bouteille
		if h<=0 OR w<=0 or y+h>frame.shape[0] or x+w>frame.shape[1]:
			return {'pourcentage':0.0, 'plein': False, 'debordement': False}
		#Decoupage Region Of Interest
		roi=frame[y:y+h, x:x+w]
		
		#Conversion en gris
		roi_gris=cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

		#Lissage (Gaussian Blur)
		kernel_size=getattr(config, 'noyau_flou',7)
		if kernel_size %2==0 :
			kernel_size=kernal_size+1
		blurred =cv2.GaussianBlur(roi_gris,(kernel_size, kernel_size),0)
		
		#Seuillage(Thresholding)
		(_, mask_liquide)=cv2.threshold(blurred, 30, 255, cv2.THRESH_BINARY_INV)

		#Morphologie(Opening)
		kernel_morph=cv2.getStructuringElement(cv2.MORPH.RECT,(5,5))
		mask_open=cv2.morphologyEx(mask_liquide,cv2.MORPH_OPEN, kernel_morph)

		#Trouver les contours
		contours, _=cv2.findContours(mask_open.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
		
		if not contours:
			return{'pourcentage':0.0,'plein':False, 'debordement': False}

		#Trier par aire
		plus_grand_contour=max(contours, key=cv2.contourArea)
		aire_liquide=cv2.contourArea(plus_grand_contour)

		if aire_liquide <100:
			return {'pourcentage':0.0, 'pleine':False, 'debordement':False}
		
		lx, ly, lw, lh= cv2.boundingRect(plus_grand_contour)

		pourcentage=(lh/float(h))*100.0

		seuil_plein=getattr(config, 'seuil_plein', 95.0)
		if pourcentage>=seuil_plein:
			est_debordement=True


		return{
			'pourcentage':pourcentage,
			'plein':est_plein,
			'debordement': est_debordement,
			'hauteur_liquide_px':lh,
			'hauteur_bouteille': h
			}
