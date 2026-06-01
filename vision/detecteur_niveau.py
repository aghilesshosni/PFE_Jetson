# -*- coding: utf-8 -*-
import cv2
import numpy as np


class DetecteurNiveau:
    def __init__(self):
        self._historique        = []
        self._taille_historique = 10

    def verifier(self, frame, bbox_bouteille, config):
        x, y, w, h = bbox_bouteille

        if h <= 0 or w <= 0:
            return self._vide()
        if y + h > frame.shape[0] or x + w > frame.shape[1]:
            return self._vide()

        margin_x = int(w * 0.15)
        margin_y = int(h * 0.05)
        roi = frame[y + margin_y : y + h - margin_y,
                    x + margin_x : x + w - margin_x]

        if roi.size == 0:
            return self._vide()

        roi_gris = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        blurred  = cv2.GaussianBlur(roi_gris, (5, 5), 0)

        _, mask = cv2.threshold(
            blurred, 0, 255,
            cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)

        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        mask   = cv2.morphologyEx(mask, cv2.MORPH_OPEN,  kernel)
        mask   = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)

        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        if not contours:
            return self._build(self._lisser(0.0), config, h)

        plus_grand    = max(contours, key=cv2.contourArea)
        _, _, _, lh   = cv2.boundingRect(plus_grand)
        hauteur_utile = h - 2 * margin_y

        pct = float(np.clip((lh / float(hauteur_utile)) * 100.0,
                            0.0, 100.0))

        return self._build(self._lisser(pct), config, h)

    def _lisser(self, value):
        self._historique.append(value)
        if len(self._historique) > self._taille_historique:
            self._historique.pop(0)
        if not self._historique:
            return 0.0
        weights = list(range(1, len(self._historique) + 1))
        return (sum(v * w for v, w in zip(self._historique, weights))
                / sum(weights))

    def _vide(self):
        return {
            'pourcentage'       : 0.0,
            'plein'             : False,
            'debordement'       : False,
            'hauteur_liquide_px': 0,
            'hauteur_bouteille' : 0
        }

    def _build(self, pct, config, h):
        seuil = getattr(config, 'seuil_plein', 90.0)
        return {
            'pourcentage'       : round(pct, 1),
            'plein'             : pct >= seuil,
            'debordement'       : pct >= 99.0,
            'hauteur_liquide_px': int(pct),
            'hauteur_bouteille' : h
        }
