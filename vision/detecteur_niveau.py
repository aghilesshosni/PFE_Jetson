# -*- coding: utf-8 -*-
import cv2
import numpy as np

class DetecteurNiveau:

    @staticmethod
    def verifier(frame, bbox_bouteille, config):
        x, y, w, h = bbox_bouteille
        
        # Verification des limites
        if h <= 0 or w <= 0 or y + h > frame.shape[0] or x + w > frame.shape[1]:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}
        
        # 1. Decoupage ROI (Region Of Interest)
        # On ajoute une petite marge interne pour éviter de détecter les bords de la bouteille elle-même
        margin_x = int(w * 0.15)
        margin_y = int(h * 0.05)
        roi = frame[y+margin_y:y+h-margin_y, x+margin_x:x+w-margin_x]
        
        if roi.size == 0:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}

        # 2. Conversion en niveaux de gris
        roi_gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # 3. Lissage (Gaussian Blur) - Comme dans l'article Agmanic
        kernel_size = getattr(config, 'noyau_flou', 7)
        if kernel_size % 2 == 0:
            kernel_size += 1
        blurred = cv2.GaussianBlur(roi_gris, (kernel_size, kernel_size), 0)
        
        # 4. Seuillage (Thresholding)
        # ASTUCE: Au lieu d'une valeur fixe (30), on peut utiliser Otsu pour s'adapter à la lumière
        # Mais pour rester simple et proche de l'article, on garde une valeur fixe ou légèrement adaptative
        threshold_val = getattr(config, 'seuil_liquide', 40) 
        (_, mask_liquide) = cv2.threshold(blurred, threshold_val, 255, cv2.THRESH_BINARY_INV)
        
        # 5. Morphologie (Opening) - CRUCIAL pour casser les liens avec le goulot/reflets
        kernel_morph = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask_open = cv2.morphologyEx(mask_liquide, cv2.MORPH_OPEN, kernel_morph)
        
        # Optionnel: Une petite fermeture pour combler les trous dans le liquide
        mask_open = cv2.morphologyEx(mask_open, cv2.MORPH_CLOSE, kernel_morph)

        # 6. Trouver les contours
        contours, _ = cv2.findContours(mask_open.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if not contours:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}
        
        # 7. TRIER LES CONTOURS PAR AIRE (La clé de la méthode Agmanic)
        # On ne prend pas juste le max, on filtre d'abord les trop petits (bruit)
        min_area = (w * h) * 0.05  # Le liquide doit faire au moins 5% de la surface
        valid_contours = [c for c in contours if cv2.contourArea(c) > min_area]
        
        if not valid_contours:
            return {'pourcentage': 0.0, 'plein': False, 'debordement': False}
            
        # On prend le PLUS GRAND contour valide (c'est presque toujours le liquide)
        plus_grand_contour = max(valid_contours, key=cv2.contourArea)
        
        # 8. Calcul de la hauteur et du pourcentage
        lx, ly, lw, lh = cv2.boundingRect(plus_grand_contour)
        
        # Le pourcentage est basé sur la hauteur du contour par rapport à la hauteur TOTALE de la bouteille (h)
        # Note: Comme on a rogné la ROI avec des marges, on doit compenser ou accepter une approx
        pourcentage = (lh / float(h - 2*margin_y)) * 100.0
        
        # Limites de sécurité
        pourcentage = max(0.0, min(100.0, pourcentage))
        
        # Recuperation du seuil de plein
        seuil_plein = getattr(config, 'seuil_plein', 95.0)
        
        # Determination de l'etat
        est_debordement = False
        est_plein = False
        
        if pourcentage >= seuil_plein:
            est_plein = True
            # On considère débordement seulement si le contour touche presque le haut de la ROI
            if ly < 5: 
                est_debordement = True

        return {
            'pourcentage': pourcentage,
            'plein': est_plein,
            'debordement': est_debordement,
            'hauteur_liquide_px': lh,
            'hauteur_bouteille': h
        }
