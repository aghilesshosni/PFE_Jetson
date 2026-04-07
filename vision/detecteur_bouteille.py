import cv2
import numpy as np

class DetecteurBouteille:
    @staticmethod
    def detecter(frame, config):
        # Conversion en echelles de GRIS pour chercher une forme
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Lissage (Gaussian Blur)
        blurred = cv2.GaussianBlur(gray, (config.noyau_flou, config.noyau_flou), 0)
        
        # Seuillage (Thresholding)
        # Correction: cv.THRESH_BINARY_INT n'existe pas -> cv2.THRESH_BINARY_INV
        (_, mask) = cv2.threshold(blurred, 40, 255, cv2.THRESH_BINARY_INV)
        
        contours, hierarchy = cv2.findContours(mask.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return {
                'present': False,
                'centre': None,
                'bbox': None,
                'aire': 0
            }
            
        biggest = sorted(contours, key=cv2.contourArea, reverse=True)[0]
        
        # Recuperer Rectangle globale
        x, y, w, h = cv2.boundingRect(biggest)
        aire = cv2.contourArea(biggest)
        
        # Filtrage par taille
        if w < 30 or h < 50 or aire < config.surface_min:
            return {
                'present': False,
                'centre': None,
                'bbox': None,
                'aire': aire
            }
            
        centre_x = x + (w // 2)
        centre_y = y + (h // 2)
        
        return {
            'present': True,
            'centre': (centre_x, centre_y),
            'bbox': (x, y, w, h),
            'aire': aire
        }


