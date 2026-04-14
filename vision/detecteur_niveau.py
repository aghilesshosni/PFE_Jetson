import cv2
import numpy as np

class DetecteurNiveau:

    @staticmethod
    def verifier(frame, bbox_bouteille, config):
        x, y, w, h = bbox_bouteille
        
        if h <= 0 or w <= 0 or y + h > frame.shape[0] or x + w > frame.shape[1]:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}
        
        # 1. Decoupage ROI (Region Of Interest)
        margin_x = int(w * 0.15)
        margin_y = int(h * 0.05)
        roi = frame[y+margin_y:y+h-margin_y, x+margin_x:x+w-margin_x]
        
        if roi.size == 0:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}

        roi_gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        kernel_size = getattr(config, 'noyau_flou', 7)
        if kernel_size % 2 == 0:
            kernel_size += 1
        blurred = cv2.GaussianBlur(roi_gris, (kernel_size, kernel_size), 0)
        
        # 4. Seuillage (Thresholding)
        threshold_val = getattr(config, 'seuil_liquide', 40) 
        (_, mask_liquide) = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        # 5. Morphologie (Opening) - CRUCIAL pour casser les liens avec le goulot/reflets
        kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask_open = cv2.morphologyEx(mask_liquide, cv2.MORPH_OPEN, kernel_morph)
        
        mask_open = cv2.morphologyEx(mask_open, cv2.MORPH_CLOSE, kernel_morph)

        # 6. Trouver les contours
        contours, _ = cv2.findContours(mask_open.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}
        
        # 7. TRIER LES CONTOURS PAR AIRE (La cle de la methode Agmanic)
        min_area = (w * h) * 0.05  
        valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        if not valid_contours:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}
            
        # On prend le PLUS GRAND contour valide (c'est presque toujours le liquide)
        plus_grand_contour = max(valid_contours, key=cv2.contourArea)
        
        # 8. Calcul de la hauteur et du pourcentage
        lx, ly, lw, lh = cv2.boundingRect(plus_grand_contour)
        
        # Le pourcentage est base sur la hauteur du contour par rapport a la hauteur TOTALE de la bouteille (h)
        pourcentage = (lh / float(h - 2*margin_y)) * 100.0
        
        pourcentage = max(0.0, min(100.0, pourcentage))
        
        seuil_plein = getattr(config, 'seuil_plein', 95.0)
        
        est_debordement = False
        est_plein = False
        
        if pourcentage >= seuil_plein:
            est_plein = True
            if ly < 5: 
                est_debordement = True

        return {
            'pourcentage': pourcentage,
            'plein': est_plein,
            'debordement': est_debordement,
            'hauteur_liquide_px': lh,
            'hauteur_bouteille': h
        }
