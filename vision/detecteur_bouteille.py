# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time

class DetecteurBouteille:
    def __init__(self):
        # État interne pour la stabilité
        self.derniere_detection_valide = None
        self.temps_perte_detection = None
        self.seuil_temps_perte = 2.0  # Secondes de tolérance avant de dire "perdu"
        self.seuil_deplacement_px = 15 # Pixels min pour considérer un mouvement réel

    def detecter(self, frame, config):
        # 1. TRAITEMENT D'IMAGE (Inchangé, c'est la base)
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
            # Recherche du meilleur candidat
            candidates = []
            for cnt in contours:
                aire = cv2.contourArea(cnt)
                x, y, w, h = cv2.boundingRect(cnt)
                if aire < 1000 or w < 20 or h < 40: continue
                ratio = float(h) / float(w) if w > 0 else 0
                if 2.0 <= ratio <= 4.0:
                    candidates.append((cnt, aire, x, y, w, h, ratio))
            
            if not candidates:
                detection_brute = {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
            else:
                candidates.sort(key=lambda k: k[1], reverse=True)
                best = candidates[0]
                x, y, w, h = best[2], best[3], best[4], best[5]
                detection_brute = {
                    'present': True,
                    'centre': (x + w//2, y + h//2),
                    'bbox': (x, y, w, h),
                    'aire': best[1]
                }

        # 2. FILTRAGE TEMPOREL (La nouvelle logique)
        temps_actuel = time.time()
        
        if detection_brute['present']:
            # Si détecté maintenant : on met à jour la référence et on reset le timer de perte
            self.derniere_detection_valide = detection_brute
            self.temps_perte_detection = None
            
            # Optionnel : Filtrer les micro-mouvements du centre
            if self.derniere_detection_valide and self.derniere_detection_valide.get('centre_stable'):
                old_c = self.derniere_detection_valide['centre_stable']
                new_c = detection_brute['centre']
                if abs(old_c[0]-new_c[0]) < self.seuil_deplacement_px and abs(old_c[1]-new_c[1]) < self.seuil_deplacement_px:
                    # Mouvement trop faible, on garde l'ancien centre stable
                    detection_brute['centre_stable'] = old_c
                else:
                    detection_brute['centre_stable'] = new_c
            else:
                detection_brute['centre_stable'] = detection_brute['centre']
                
            return {
                'present': True,
                'centre': detection_brute['centre_stable'],
                'bbox': detection_brute['bbox'], # On garde la bbox brute ou stable selon besoin
                'aire': detection_brute['aire']
            }
        else:
            # Si NON détecté maintenant : on vérifie le timer
            if self.temps_perte_detection is None:
                self.temps_perte_detection = temps_actuel
            
            # Si perdu depuis moins de 2s, on retourne la DERNIÈRE valeur connue (Hold)
            if (temps_actuel - self.temps_perte_detection) < self.seuil_temps_perte:
                if self.derniere_detection_valide:
                    # On retourne une copie pour ne pas modifier l'original par erreur
                    return {
                        'present': True, # On ment volontairement pour la stabilité
                        'centre': self.derniere_detection_valide['centre_stable'],
                        'bbox': self.derniere_detection_valide['bbox'],
                        'aire': self.derniere_detection_valide['aire'],
                        'stable_hold': True # Flag optionnel pour savoir qu'on est en hold
                    }
            
            # Sinon, vraiment perdu
            self.derniere_detection_valide = None
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
