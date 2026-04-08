import cv2
import numpy as np

class DetecteurBouteille:
    @staticmethod
    def detecter(frame, config):
        #  Conversion en niveaux de gris
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        #  Lissage (Gaussian Blur) 
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        #  DÉTECTION DE CONTOURS (CANNY)
        edges = cv2.Canny(blurred, 30, 100)
        
        #  Morphologie 
        # relier les pointillés des bords de la bouteille en un seul contour fermé
        kernel = np.ones((3,3), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=3) 
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=2) 
        
        # trouver les contours
        contours, _ = cv2.findContours(eroded_edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
            
        # Trier par aire
        biggest = sorted(contours, key=cv2.contourArea, reverse=True)[0]
        
        x, y, w, h = cv2.boundingRect(biggest)
        aire = cv2.contourArea(biggest)
        
        ratio = float(h) / float(w) if w > 0 else 0
        hull = cv2.convexHull(biggest)
        hull_area = cv2.contourArea(hull)
        solidite = float(aire) / hull_area if hull_area > 0 else 0

        # FILTRE 1 : tailles minimale
        if w < 20 or h < 40 or aire < 500: 
            
            return {'present': False, 'centre': None, 'bbox': None, 'aire': aire}

        # FILTRE 2 : ratio de forme (hauteur / largeur)
        if ratio < 1.5 or ratio > 8.0:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': aire}

        centre_x = x + (w // 2)
        centre_y = y + (h // 2)
        
        return {
            'present': True,
            'centre': (centre_x, centre_y),
            'bbox': (x, y, w, h),
            'aire': aire,
            'ratio': ratio,
        }
