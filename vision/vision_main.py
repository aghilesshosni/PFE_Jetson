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
        if not self.est_tournant:
            return

        from shared_state import state

        crop_x_start = self.config.crop_x_start
        crop_x_end   = self.config.crop_x_end

        try:
            while self.est_tournant:
                debut_cycle = time.time()

                frame = self.camera.read()
                if frame is None:
                    time.sleep(0.01)
                    continue

                if frame.shape[1] != self.config.largeur or frame.shape[0] != self.config.hauteur:
                    frame = cv2.resize(frame, (self.config.largeur, self.config.hauteur))

                frame_cropped = frame[:, crop_x_start:crop_x_end]
                cv2.rectangle(frame, (crop_x_start, 0), (crop_x_end, frame.shape[0]), (255, 0, 255), 2)

                res_bouteille = self.detecteur_bouteille.detecter(frame_cropped, self.config)

                if res_bouteille['present'] and res_bouteille['aire'] < self.config.surface_min_bouteille:
                    res_bouteille = {'present': False, 'centre': None, 'bbox': None, 'aire': 0}

                if res_bouteille['present'] and res_bouteille['centre']:
                    cx, cy = res_bouteille['centre']
                    res_bouteille['centre'] = (cx + crop_x_start, cy)

                    bx, by, bw, bh = res_bouteille['bbox']
                    res_bouteille['bbox'] = (bx + crop_x_start, by, bw, bh)

                res_niveau = {'pourcentage': 0.0, 'plein': False, 'debordement': False}
                if res_bouteille['present']:
                    res_niveau = self.detecteur_niveau.verifier(frame, res_bouteille['bbox'], self.config)

                if not res_bouteille['present']:
                    status      = "AUCUNE_BOUTEILLE"
                    final_level = 0.0
                    final_present = False
                elif res_niveau.get('debordement'):
                    status      = "DEBORDEMENT"
                    final_level = res_niveau['pourcentage']
                    final_present = True
                elif res_niveau.get('plein'):
                    status      = "BOUTEILLE_PLEINE"
                    final_level = res_niveau['pourcentage']
                    final_present = True
                else:
                    status      = "EN_REMPLISSAGE"
                    final_level = res_niveau['pourcentage']
                    final_present = True

                fps_val = 1.0 / max(time.time() - debut_cycle, 0.001)
                state.update(
                    present=final_present,
                    level=final_level,
                    frame=frame,
                    fps=fps_val,
                    status=status,
                )

                log_msg = "{} | Centre: {} | Niveau: {:.1f}% | BBox: {} | Aire: {}".format(
                    status,
                    res_bouteille['centre'] if res_bouteille['centre'] else "N/A",
                    final_level,
                    res_bouteille['bbox']   if res_bouteille['bbox']   else "N/A",
                    int(res_bouteille['aire']),
                )
                if log_msg != self.dernier_log_hash:
                    logger.info(log_msg)
                    self.dernier_log_hash = log_msg

                if res_bouteille['present']:
                    x, y, w, h = res_bouteille['bbox']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, status, (x, y - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                    niveau_pct = final_level / 100.0
                    liq_h = int(h * niveau_pct)
                    rx, ry = x + 5, y + h - liq_h
                    rw, rh = w - 10, liq_h
                    if rh > 0:
                        cv2.rectangle(frame, (rx, ry), (rx + rw, ry + rh), (0, 0, 255), -1)

                cv2.imshow("Ligne de Production", frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                dt = time.time() - debut_cycle
                if dt < 0.033:
                    time.sleep(0.033 - dt)

        except Exception as e:
            logger.error("Erreur Critique Vision: {}".format(e))
            import traceback
            traceback.print_exc()
        finally:
            self.arreter()

    def arreter(self):
        self.est_tournant = False
        self.camera.release()
        cv2.destroyAllWindows()
