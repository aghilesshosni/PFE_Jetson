# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time

class DetecteurBouteille:

    def detecter(self, frame, config):
       # 1. Convert to Gray
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 2. NOISE REDUCTION (Crucial for IMX219)
        # Use a slightly stronger blur to kill the sensor noise first
        blurred = cv2.GaussianBlur(gray, (7, 7), 0)
        
        # 3. DIGITAL SHARPENING (The "Webcam Effect")
        # Create an unsharp mask to enhance edges lost due to the cheap lens
        # Formula: Sharpened = Original + (Original - Blurred) * Amount
        gaussian_blur_for_sharp = cv2.GaussianBlur(blurred, (0, 0), 3.0)
        sharpened = cv2.addWeighted(blurred, 1.5, gaussian_blur_for_sharp, -0.5, 0)
        
        # Optional: Apply CLAHE now on the SHARPENED image to boost local contrast
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
        enhanced = clahe.apply(sharpened)

        # 4. Edge Detection on the SHARPENED image
        # Lower thresholds because our edges are now artificially stronger
        edges = cv2.Canny(enhanced, 20, 60)
        
        # 5. Morphology (Connect the broken edges caused by blur)
        kernel = np.ones((5,5), np.uint8)
        dilated_edges = cv2.dilate(edges, kernel, iterations=3)
        eroded_edges = cv2.erode(dilated_edges, kernel, iterations=2)
        
        contours, _ = cv2.findContours(eroded_edges.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                
        if len(contours) == 0:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
        
        candidates = []
        
        for cnt in contours:
            aire = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)
            
            # CHANGE 3: Significantly higher minimum area
            # Was: 300 -> Now: 2000 (Adjust based on your camera distance)
            if aire < 2000 or w < 30 or h < 60: 
                continue
                
            ratio = float(h) / float(w) if w > 0 else 0
            
            # Your tuned ratio (Good job on this!)
            if 2.0 <= ratio <= 4.0:
                candidates.append((cnt, aire, x, y, w, h, ratio))
        
        if not candidates:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
            
        # Pick the largest valid candidate
        candidates.sort(key=lambda k: k[1], reverse=True)
        best_candidate = candidates[0]
        
        # ... (rest of the code remains same)
        biggest = best_candidate[0]
        aire = best_candidate[1]
        x, y, w, h = best_candidate[2], best_candidate[3], best_candidate[4], best_candidate[5]
        ratio = best_candidate[6]

        centre_x = x + (w // 2)
        centre_y = y + (h // 2)
        
        return {
            'present': True,
            'centre': (centre_x, centre_y),
            'bbox': (x, y, w, h),
            'aire': aire,
            'ratio': ratio,
        }
