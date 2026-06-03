# -*- coding: utf-8 -*-
import cv2
import numpy as np


class DetecteurBouteille:
    def __init__(self):
        pass

    def detecter(self, frame, config):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)

        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)

        edges = cv2.Canny(blurred, 20, 60)

        kernel  = np.ones((5, 5), np.uint8)
        dilated = cv2.dilate(edges,  kernel, iterations=3)
        eroded = cv2.erode(dilated, kernel, iterations=2)

        contours, _ = cv2.findContours(
            eroded, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return {'present': False, 'centre': None,
                    'bbox': None, 'aire': 0}

        candidates = []
        for cnt in contours:
            aire = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)

            if aire < 300 or w < 20 or h < 40:
                continue

            ratio = float(h) / float(w) if w > 0 else 0
            if not (3 <= ratio <= 5.5):
                continue

            candidates.append((cnt, aire, x, y, w, h))

        if not candidates:
            return {'present': False, 'centre': None,
                    'bbox': None, 'aire': 0}

        candidates.sort(key=lambda k: k[1], reverse=True)
        _, aire, x, y, w, h = candidates[0]

        surface_min = getattr(config, 'surface_min_bouteille', 10000)
        if aire < surface_min:
            return {'present': False, 'centre': None,
                    'bbox': None, 'aire': 0}

        return {
            'present': True,
            'centre': (x + w // 2, y + h // 2),
            'bbox' : (x, y, w, h),
            'aire' : aire
        }
