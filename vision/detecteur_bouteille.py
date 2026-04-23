# -*- coding: utf-8 -*-
import cv2
import numpy as np
import time

class DetecteurBouteille:
    def __init__(self):
        pass

    def detecter(self, frame, config):

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        enhanced_gray = clahe.apply(gray)
        
        blurred = cv2.GaussianBlur(enhanced_gray, (5, 5), 0)
        
        edges = cv2.Canny(blurred, 20, 60)
        
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
            
            if aire < 300 or w < 20 or h < 40:
                continue
                
            ratio = float(h) / float(w) if w > 0 else 0
            
            if 2 <= ratio <= 5:
                candidates.append((cnt, aire, x, y, w, h, ratio))
        
        if not candidates:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}
            
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
