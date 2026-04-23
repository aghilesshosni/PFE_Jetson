# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time

class DetecteurBouteille:
    def __init__(self):
        # No state needed here; the logic is stateless and relies on config thresholds
        pass

    def detecter(self, frame, config):
        # 1. Pre-processing (CLAHE for transparent objects)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_gray = clahe.apply(gray)
        
        blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)
        
        # 2. Edge Detection
        edges = cv2.Canny(blurred, 20, 60)
        
        # 3. Morphology (Connect broken edges)
        kernel = np.ones((5,5), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=3)
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=2)

        contours, _ = cv2.findContours(eroded_edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
        
        candidates = []
        
        # Load calibration settings if available
        use_calibration = False
        calib = {}
        if hasattr(config, 'calibration') and config.calibration.get('enabled', False):
            use_calibration = True
            calib = config.calibration

        for cnt in contours:
            aire = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Basic Size Filter (Reject tiny noise immediately)
            if aire < 300 or w < 20 or h < 40:
                continue
                
            ratio = float(h) / float(w) if w > 0 else 0
            
            # Shape Filter (Must be bottle-like)
            if not (2 <= ratio <= 5):
                continue

            # --- NEW: STRICT CALIBRATION CHECKS ---
            if use_calibration:
                centre_x = x + (w // 2)
                top_edge_y = y
                
                # Check Area Range
                if not (calib.get('area_min', 0) <= aire <= calib.get('area_max', 999999)):
                    continue
                
                # Check Width/Height Range
                if not (calib.get('width_min', 0) <= w <= calib.get('width_max', 999999)):
                    continue
                if not (calib.get('height_min', 0) <= h <= calib.get('height_max', 999999)):
                    continue
                
                # Check Horizontal Position (Center X)
                if not (calib.get('center_x_min', 0) <= centre_x <= calib.get('center_x_max', 999999)):
                    continue
                
                # Check Vertical Alignment (Top Edge Y)
                # Real bottles sit near the top of the ROI (low Y value). 
                # Noise often floats lower (high Y value).
                if top_edge_y > calib.get('top_edge_y_max', 999999):
                    continue
            
            # If it passes all checks (or calibration is off), add to candidates
            candidates.append((cnt, aire, x, y, w, h, ratio))
        
        if not candidates:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
            
        # Sort by area (largest first)
        # Now, the "largest" will be the largest VALID bottle, not the largest noise.
        candidates.sort(key=lambda k: k[1], reverse=True)
        best_candidate = candidates[0]
        
        aire = best_candidate[1]
        x, y, w, h = best_candidate[2], best_candidate[3], best_candidate[4], best_candidate[5]
        
        centre_x = x + (w // 2)
        centre_y = y + (h // 2)
        
        return {
            'present': True,
            'centre': (centre_x, centre_y),
            'bbox': (x, y, w, h),
            'aire': aire
        }
