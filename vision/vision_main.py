# -*- coding: utf-8 -*-
import cv2
import time
from .gestionnaire_camera import GestionnaireCamera
from .configurateur_vision import ConfigurateurVision
from .detecteur_bouteille import DetecteurBouteille
from .detecteur_niveau import DetecteurNiveau

class VisionMain:
    def __init__(self):
        self.config = ConfigurateurVision()
        self.camera = GestionnaireCamera(self.config.id_camera)
        self.detecteur_bouteille = DetecteurBouteille()
        self.detecteur_niveau = DetecteurNiveau()
        
        self.est_tournant = False
        self.dernier_log_hash = "" 

    def start(self):
        print("Initialisation du systeme de vision...")
        if not self.camera.open():
            raise RuntimeError("Echec critique : Impossible d'ouvrir la camera")
        self.est_tournant = True
        print("Systeme pret.")
        return True

    def run(self):
        if not self.est_tournant: return

        try:
            while self.est_tournant:
                debut_cycle = time.time()
                frame = self.camera.read()
                if frame is None:
                    time.sleep(0.01)
                    continue

                # Resize if necessary
                if frame.shape[1] != self.config.largeur or frame.shape[0] != self.config.hauteur:
                    frame = cv2.resize(frame, (self.config.largeur, self.config.hauteur))

                # 1. Detection
                res_bouteille = self.detecteur_bouteille.detecter(frame, self.config)
                
                res_niveau = {'pourcentage': 0.0, 'plein': False, 'debordement': False}
                if res_bouteille['present']:
                    res_niveau = self.detecteur_niveau.verifier(frame, res_bouteille['bbox'], self.config)

                # 2. Status Logic
                if not res_bouteille['present']:
                    status = "AUCUNE_BOUTEILLE"
                elif res_niveau.get('debordement'):
                    status = "DEBORDEMENT"
                elif res_niveau.get('plein'):
                    status = "BOUTEILLE_PLEINE"
                else:
                    status = "EN_REMPLISSAGE"

                # 3. Logging (Only print if changed to reduce spam)
                log_msg = "{} | Centre: {} | Niveau: {:.1f}%".format(
                    status, 
                    res_bouteille['centre'] if res_bouteille['centre'] else "N/A", 
                    res_niveau['pourcentage']
                )
                
                if log_msg != self.dernier_log_hash:
                    print(log_msg)
                    self.dernier_log_hash = log_msg

                # 4. Visualization
                if res_bouteille['present']:
                    x, y, w, h = res_bouteille['bbox']
                    
                    # Green Rectangle (Bottle) - Should be smooth now
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, status, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Red Rectangle (Liquid Level) - Should rise smoothly now
                    niveau_pct = res_niveau['pourcentage'] / 100.0
                    liq_h = int(h * niveau_pct)
                    rx, ry = x + 5, y + h - liq_h
                    rw, rh = w - 10, liq_h
                    
                    if rh > 0:
                        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), -1)

                cv2.imshow("Ligne de Production", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'): break

                # FPS Control
                dt = time.time() - debut_cycle
                if dt < 0.033: time.sleep(0.033 - dt)

        except Exception as e:
            print("Erreur : {}".format(e))
        finally:
            self.arreter()

    def arreter(self):
        self.est_tournant = False
        self.camera.release()
        cv2.destroyAllWindows()
