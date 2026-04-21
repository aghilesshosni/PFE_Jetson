# -*- coding: utf-8 -*-
import cv2
import numpy as np

class DetecteurBouteille:
    @staticmethod
    def detecter(frame, config):
        # 1. PRE-PROCESSING: Enhance Contrast BEFORE detection
        # Transparent bottles often have low contrast. CLAHE boosts local contrast
        # without amplifying noise globally like normal histogram equalization.
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_gray = clahe.apply(gray)
        
        # 2. SMOOTHING: Use a slightly larger kernel to remove sensor noise
        # but keep edge details.
        blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)
        
        # 3. EDGE DETECTION: Adaptive Canny
        # For transparent objects, we need LOWER thresholds to catch faint reflections.
        # We use 20 and 60 instead of 30 and 100.
        edges = cv2.Canny(blurred, 20, 60)
        
        # 4. MORPHOLOGY: Aggressive Closing to Connect Broken Edges
        # Transparent bottles often have "dashed" lines on the sides.
        # We need to bridge these gaps.
        kernel = np.ones((5,5), np.uint8) # Larger kernel (5x5) bridges bigger gaps
        
        # Dilate first to expand edges
        dilated_edges = cv2.dilate(edges, kernel, iterations=3)
        # Erode to restore original thickness but keep them connected
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=2)
        
        # Optional: Second pass of closing if edges are still very fragmented
        # eroded_edges = cv2.morphologyEx(eroded_edges, cv2.MORPH_CLOSE, kernel)

        # 5. FIND CONTOURS
        contours, _ = cv2.findContours(eroded_edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) == 0:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
        
        # 6. SMART SORTING: Don't just take the biggest area.
        # Sometimes noise creates a huge blob. Look for the biggest object 
        # that ALSO fits the shape criteria.
        candidates = []
        
        for cnt in contours:
            aire = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)
            
            # Basic size filter first to ignore tiny noise
            if aire < 300 or w < 20 or h < 40:
                continue
                
            ratio = float(h) / float(w) if w > 0 else 0
            
            # Shape filter: Is it bottle-like?
            if 2 <= ratio <= 5:
                candidates.append((cnt, aire, x, y, w, h, ratio))
        
        if not candidates:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
            
        # Sort candidates by area (largest valid bottle first)
        candidates.sort(key=lambda k: k[1], reverse=True)
        best_candidate = candidates[0]
        
        biggest = best_candidate[0]
        aire = best_candidate[1]
        x, y, w, h = best_candidate[2], best_candidate[3], best_candidate[4], best_candidate[5]
        ratio = best_candidate[6]

        # Final Safety Checks (Optional, already filtered above but good for debug)
        if w < 20 or h < 40 or aire < 500: 
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
