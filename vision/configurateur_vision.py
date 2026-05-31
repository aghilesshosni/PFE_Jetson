# -*- coding: utf-8 -*-
import os
import sys
import yaml


class ConfigurateurVision:
    def __init__(self):
        dossier_courant = os.path.dirname(os.path.abspath(__file__))
        chemin_complet  = os.path.join(os.path.dirname(dossier_courant), "vision_config.yaml")

        if not os.path.exists(chemin_complet):
            chemin_complet = os.path.join(dossier_courant, "vision_config.yaml")
        if not os.path.exists(chemin_complet):
            print("Fichier de configuration YAML introuvable: {}".format(chemin_complet))
            sys.exit(1)

        try:
            with open(chemin_complet, 'r') as f:
                donnees = yaml.safe_load(f)
            if not donnees:
                raise ValueError("Le fichier YAML est vide")

            self.id_camera = donnees['camera']['id']
            self.largeur   = donnees['camera']['width']
            self.hauteur   = donnees['camera']['height']

            self.surface_min_bouteille = donnees.get('detection', {}).get('surface_min_bouteille', 10000)
            self.seuil_plein           = donnees.get('remplissage', {}).get('seuil_plein_pourcentage', 90.0)

            vision = donnees.get('vision', {})
            self.crop_x_start = vision.get('crop_x_start', 250)
            self.crop_x_end   = vision.get('crop_x_end',   450)

        except Exception as e:
            print("Erreur Configuration: {}".format(e))
            sys.exit(1)
