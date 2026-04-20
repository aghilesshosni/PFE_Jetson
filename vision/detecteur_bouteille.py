# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time

class DetecteurBouteille:
    def __init__(self):
        self.derniere_detection_valide = None
        self.temps_perte_detection = None
        self.seuil_temps_perte = 2.0
        self.seuil_deplacement_px = 10
        self.dernier_centre_stable = None 

    def detecter(self, frame, config):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_gray = clahe.apply(gray)
        
        blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)
        edges = cv2.Canny(blurred, 30, 70)
        
        kernel = np.ones((5,5), np.uint8) 
        dilated_edges = cv2.dilate(edges, kernel, iterations=2)
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=1)
        
        contours, _ = cv2.findContours(eroded_edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            detection_brute = {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
        else:
            candidates = []
            for cnt in contours:
                aire = cv2.contourArea(cnt)
                x, y, w, h = cv2.boundingRect(cnt)
            
                if aire < 1000 or w < 20 or h < 40:
                    continue
                
                ratio = float(h) / float(w) if w > 0 else 0
            
                if 2 <= ratio <= 4.0:
                    candidates.append((cnt, aire, x, y, w, h, ratio))
        
            if not candidates:
                detection_brute = {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
            else:
                candidates.sort(key=lambda k: k[1], reverse=True)
                best = candidates[0]
        
                # Fixed variable name error here
                aire = best[1]
                x, y, w, h = best[2], best[3], best[4], best[5]
                detection_brute = { 
                    'present': True, 
                    'centre': (x + w//2, y + h//2), 
                    'bbox': (x, y, w, h), 
                    'aire': best[1] 
                }

        temps_actuel = time.time()

        if detection_brute['present']:
            # --- A. Gestion de la présence (Debouncing 2s) ---
            self.derniere_detection_valide = detection_brute
            self.temps_perte_detection = None
            
            # --- B. Gestion du centre (Hystérésis spatiale) ---
            centre_actuel = detection_brute['centre']
            
            if self.dernier_centre_stable is None:
                self.dernier_centre_stable = centre_actuel
                centre_a_renvoyer = centre_actuel
            else:
                dx = abs(centre_actuel[0] - self.dernier_centre_stable[0])
                dy = abs(centre_actuel[1] - self.dernier_centre_stable[1])
                
                if dx < self.seuil_deplacement_px and dy < self.seuil_deplacement_px:
                    centre_a_renvoyer = self.dernier_centre_stable
                else:
                    self.dernier_centre_stable = centre_actuel
                    centre_a_renvoyer = centre_actuel
            
            return {
                'present': True,
                'centre': centre_a_renvoyer,      
                'bbox': detection_brute['bbox'],  
                'aire': detection_brute['aire']
            }

        else:
            # --- C. Cas où la bouteille n'est PAS détectée ---
            if self.temps_perte_detection is None:
                self.temps_perte_detection = temps_actuel
            
            if (temps_actuel - self.temps_perte_detection) < self.seuil_temps_perte:
                if self.derniere_detection_valide:
                    return {
                        'present': True, 
                        'centre': self.dernier_centre_stable, 
                        'bbox': self.derniere_detection_valide['bbox'],
                        'aire': self.derniere_detection_valide['aire']
                    }
            
            self.derniere_detection_valide = None
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}












