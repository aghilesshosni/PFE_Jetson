# -*- coding: utf-8 -*-
import cv2
import numpy as np


class DetecteurNiveau:
    def __init__(self):
        self._historique = []
        self._taille_historique = 12
        self._frames_sans_liquide = 0
        self._seuil_absence = 8  # need 8 consecutive empty frames to report 0

    def verifier(self, frame, bbox_bouteille, config):
        x, y, w, h = bbox_bouteille

        if h <= 0 or w <= 0:
            return self._vide()
        if y + h > frame.shape[0] or x + w > frame.shape[1]:
            return self._vide()

        # ── ROI margins ───────────────────────────────────────────────────────
        margin_x = int(w * 0.18)

        # If bbox starts at y=0 (snapped to top), use fixed pixel margin
        # instead of percentage to avoid eating too much of the bottle
        if y < 10:
            margin_top = 30  # fixed 30px for neck when bbox is full-frame
        else:
            margin_top = int(h * 0.15)

        margin_bot = int(h * 0.02)

        rx1, rx2 = x + margin_x,   x + w - margin_x
        ry1, ry2 = y + margin_top,  y + h - margin_bot

        if rx2 - rx1 < 5 or ry2 - ry1 < 5:
            return self._vide()

        roi   = frame[ry1:ry2, rx1:rx2]
        roi_h = ry2 - ry1

        # ── HSV color mask for pink/magenta liquid ────────────────────────────
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)

        # Widen the ranges to catch dim/dark pink under poor lighting
        mask1 = cv2.inRange(hsv,
            np.array([0,   35, 30]),
            np.array([20, 255, 255]))

        mask2 = cv2.inRange(hsv,
            np.array([145, 35, 30]),
            np.array([180, 255, 255]))

        liquid_mask = cv2.bitwise_or(mask1, mask2)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        liquid_mask = cv2.morphologyEx(liquid_mask, cv2.MORPH_OPEN,  kernel, iterations=2)
        liquid_mask = cv2.morphologyEx(liquid_mask, cv2.MORPH_CLOSE, kernel, iterations=4)
        # ── Check liquid presence ─────────────────────────────────────────────
        liquid_pixels = cv2.countNonZero(liquid_mask)
        min_pixels = int(roi_h * (rx2 - rx1) * 0.015)

        if liquid_pixels < min_pixels:
            self._frames_sans_liquide += 1
            if self._frames_sans_liquide >= self._seuil_absence:
                # Only reset after N consecutive empty frames
                self._historique.clear()
                self._frames_sans_liquide = 0
                return self._vide()
            else:
                # Hold last known value during brief detection gaps
                return self._build(
                    self._historique[-1] if self._historique else 0.0,
                    config
                )

        # Liquid detected — reset absence counter
        self._frames_sans_liquide = 0

        # ── Find topmost liquid row ───────────────────────────────────────────
        surface_y = None
        for row in range(roi_h):
            if np.any(liquid_mask[row, :] > 0):
                surface_y = row
                break

        if surface_y is None:
            return self._build(self._lisser(0.0), config)

        liquid_px   = roi_h - surface_y
        pourcentage = float(np.clip((liquid_px / roi_h) * 100.0, 0.0, 100.0))

        return self._build(self._lisser(pourcentage), config)

    def _lisser(self, value: float) -> float:
        self._historique.append(value)
        if len(self._historique) > self._taille_historique:
            self._historique.pop(0)
        weights = list(range(1, len(self._historique) + 1))
        return sum(v * w for v, w in zip(self._historique, weights)) / sum(weights)

    def _vide(self):
        return {'pourcentage': 0.0, 'plein': False, 'debordement': False,
                'hauteur_liquide_px': 0, 'hauteur_bouteille': 0}

    def _build(self, pct, config):
        seuil = getattr(config, 'seuil_plein', 90.0)
        return {'pourcentage': round(pct, 1),
                'plein': pct >= seuil,
                'debordement': pct >= 99.0,
                'hauteur_liquide_px': int(pct),
                'hauteur_bouteille': 100}
