import os
import sys
import yaml

class ConfigurateurVision:
    def __init__(self):
        dossier_courant = os.path.dirname(os.path.abspath(__file__))
        chemin_complet = os.path.join(dossier_courant, "vision_config.yaml")
        
        if not os.path.exists(chemin_complet):
            print("Fichier de configuration YAML introuvable")
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
            self.surface_min = det['surface_min_bouteille']
            self.noyau_flou = det['noyau_flou']
            
            rempl = donnees['remplissage']
            self.seuil_plein = rempl['seuil_plein_pourcentage']
            
            plc = donnees['plc']
            self.plc_ip = plc.get('ip_adress', plc.get('ip', '0.0.0.0')) 
            self.port = plc.get('port', 502)
            
        except Exception as e:
            erreur_message = "Erreur Inconnue : {}".format(e)
            print(erreur_message)
            sys.exit(1)
