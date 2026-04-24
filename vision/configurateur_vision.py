# -*- coding: utf-8 -*-
import os
import sys
import yaml

class ConfigurateurVision:
    def __init__(self):
        dossier_courant = os.path.dirname(os.path.abspath(__file__))
        
        chemin_complet = os.path.join(os.path.dirname(dossier_courant), "vision_config.yaml")
        
        if not os.path.exists(chemin_complet):
            chemin_complet = os.path.join(dossier_courant, "vision_config.yaml")

        if not os.path.exists(chemin_complet):
            print("Fichier de configuration YAML introuvable dans: {}".format(chemin_complet))
            sys.exit(1)
            
        try:
            with open(chemin_complet, 'r') as f:
                donnees = yaml.safe_load(f)
                if not donnees:
                    raise ValueError("Le fichier YAML est vide")
                    
            cam = donnees['camera']
            self.id_camera = cam['id']
            self.largeur = cam['width']
            self.hauteur = cam['height']
            
            det = donnees['detection']
            self.surface_min_bouteille = det.get('surface_min_bouteille', 20000)
            self.noyau_flou = det.get('noyau_flou', 5)
            
            rempl = donnees.get('remplissage', {})
            self.seuil_plein = rempl.get('seuil_plein_pourcentage', 95.0)
            
            plc = donnees.get('plc', {})
            self.plc_ip = plc.get('ip_adress', plc.get('ip', '0.0.0.0')) 
            self.port = plc.get('port', 502)
            
            calib_raw = donnees.get('calibration', {})
            self.calibration = {
            'enabled': calib_raw.get('enabled', False),
            'area_min': calib_raw.get('area_min', 0),
            'area_max': calib_raw.get('area_max', 999999),
            'width_min': calib_raw.get('width_min', 0),
            'width_max': calib_raw.get('width_max', 999999),
            'height_min': calib_raw.get('height_min', 0),
            'height_max': calib_raw.get('height_max', 999999),
            'center_x_min': calib_raw.get('center_x_min', 0),
            'center_x_max': calib_raw.get('center_x_max', 999999),
            'top_edge_y_max': calib_raw.get('top_edge_y_max', 999999),
              }
        except Exception as e:
            erreur_message = "Erreur Configuration : {}".format(e)
            print(erreur_message)
            sys.exit(1)
