# -*- coding: utf-8 -*-
import cv2
import numpy as np


class DetecteurBouteille:
    def __init__(self):
        pass

    def detecter(self, frame, config):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        blurred = cv2.bilateralFilter(gray, d=9, sigmaColor=75, sigmaSpace=75)
        _, thresholded = cv2.threshold(blurred, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)

        kernel = np.ones((7, 7), np.uint8)
        closed_edges = cv2.morphologyEx(thresholded, cv2.MORPH_CLOSE, kernel)
        opened_edges = cv2.morphologyEx(closed_edges, cv2.MORPH_OPEN, kernel)

        contours, _ = cv2.findContours(opened_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if len(contours) == 0:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}

        h_frame, w_frame = frame.shape[:2]
        MAX_BOTTLE_AREA = h_frame * w_frame * 0.90

        candidates = []
        for cnt in contours:
            aire = cv2.contourArea(cnt)
            x, y, w, h = cv2.boundingRect(cnt)

            if aire < 1000 or w < 30 or h < 50:
                continue
            if aire > MAX_BOTTLE_AREA:
                continue

            ratio = float(h) / float(w) if w > 0 else 0
            if not (1.3 <= ratio <= 6.0):
                continue

            candidates.append((cnt, aire, x, y, w, h, ratio))

        if not candidates:
            return {'present': False, 'centre': None, 'bbox': None, 'aire': 0}

        candidates.sort(key=lambda k: k[1], reverse=True)
        best = candidates[0]
        aire = best[1]
        x, y, w, h = best[2], best[3], best[4], best[5]

        bottom_edge = y + h
        if (h_frame - bottom_edge) < int(h_frame * 0.15):
            h = h_frame - y

        if y < int(h_frame * 0.05):
            h = h + y
            y = 0

        centre_x = x + (w // 2)
        centre_y = y + (h // 2)

        return {
            'present': True,
            'centre': (centre_x, centre_y),
            'bbox': (x, y, w, h),
            'aire': aire
        }
