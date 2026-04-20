# -*- coding: utf-8 -*-
import cv2
import numpy as np

class DetecteurNiveau:
    def __init__(self):
        self.dernier_niveau_stable = -1.0
        self.seuil_variation_pct = 1.5  

    def verifier(self, frame, bbox_bouteille, config):
        if not bbox_bouteille:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}

        x, y, w, h = bbox_bouteille
        
        if h <= 0 or w <= 0:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}
        
        margin_x = int(w * 0.15)
        margin_y = int(h * 0.05)
        
        # Ensure coordinates are within frame bounds
        h_frame, w_frame = frame.shape[:2]
        x1 = max(0, x + margin_x)
        x2 = min(w_frame, x + w - margin_x)
        y1 = max(0, y + margin_y)
        y2 = min(h_frame, y + h - margin_y)

        roi = frame[y1:y2, x1:x2]
        
        if roi.size == 0:
            return self._get_result_stable(0.0)

        roi_gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Use config values safely
        kernel_size = getattr(config, 'noyau_flou', 7)
        if kernel_size % 2 == 0: kernel_size += 1
        
        blurred = cv2.GaussianBlur(roi_gris, (kernel_size, kernel_size), 0)
        
        # Default threshold if not in config
        threshold_val = getattr(config, 'seuil_liquide', 40)
        (_, mask_liquide) = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask_open = cv2.morphologyEx(mask_liquide, cv2.MORPH_OPEN, kernel_morph)
        mask_open = cv2.morphologyEx(mask_open, cv2.MORPH_CLOSE, kernel_morph)

        contours, _ = cv2.findContours(mask_open.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return self._get_result_stable(0.0)
        
        min_area = (w * h) * 0.05
        valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        if not valid_contours:
            return self._get_result_stable(0.0)
            
        plus_grand_contour = max(valid_contours, key=cv2.contourArea)
        lx, ly, lw, lh = cv2.boundingRect(plus_grand_contour)
        
        hauteur_roi = roi.shape[0]
        if hauteur_roi == 0:
            return self._get_result_stable(0.0)

        pourcentage_brut = (lh / float(hauteur_roi)) * 100.0
        pourcentage_brut = max(0.0, min(100.0, pourcentage_brut))

        return self._get_result_stable(pourcentage_brut)

    def _get_result_stable(self, pourcentage_brut):
        if self.dernier_niveau_stable < 0:
            self.dernier_niveau_stable = pourcentage_brut
        else:
            if abs(pourcentage_brut - self.dernier_niveau_stable) > self.seuil_variation_pct:
                self.dernier_niveau_stable = pourcentage_brut

        seuil_plein = 95.0 
        est_plein = self.dernier_niveau_stable >= seuil_plein
        est_debordement = est_plein and (self.dernier_niveau_stable >= 98.0)

        return {
            'pourcentage': self.dernier_niveau_stable,
            'plein': est_plein,
            'debordement': est_debordement,
            'hauteur_liquide_px': int(self.dernier_niveau_stable * 0.01 * 100) 
        }
