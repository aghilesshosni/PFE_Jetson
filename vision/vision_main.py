import cv2
import numpy as np
import time
from gestionnaire_camera import GestionnaireCamera
from configurateur_vision import ConfigurateurVision
from detecteur_bouteille import DetecteurBouteille
from detecteur_niveau import DetecteurNiveau

class VisionMain:
    def __init__(self):
        self.config = ConfigurateurVision()
        self.camera = GestionnaireCamera(self.config.id_camera)
        
        # Preallocation du buffer 
        self.frame_buffer = np.zeros(
            (self.config.hauteur, self.config.largeur, 3),
            dtype=np.uint8
        )
        
        self.est_tournant = False
        
        # Etat initial
        self.dernier_resultat = {
            'Autorisation_Remplissage': False,
            'Arret_Convoyeur': False,
            'Defaut_Systeme': False,
            'Status': 'Init',
            'Compensation': 0,
            'Niveau_Remplissage': 0.0,
            'Centre': None
        }

    def start(self):
        print("Initialisation du systeme de vision...")
        if not self.camera.open():
            raise RuntimeError("Echec critique : Impossible d'ouvrir la camera")
        self.est_tournant = True
        print("Camera active. Demarrage de la boucle...")
        return True

    def run(self):
        if not self.est_tournant:
            return

        # Pour eviter de spammer le terminal 
        self.dernier_etat_affiche = None 

        try:
            while self.est_tournant:
                debut_cycle = time.time()

                frame = self.camera.read()

                if frame is None:
                    time.sleep(0.01)
                    continue

                if frame.shape[1] != self.config.largeur or frame.shape[0] != self.config.hauteur:
                    frame = cv2.resize(frame, (self.config.largeur, self.config.hauteur))

                # REinitialisation par dEfaut 
                self.dernier_resultat.update({
                    'Autorisation_Remplissage': False,
                    'Arret_Convoyeur': False,
                    'Defaut_Systeme': False,
                    'Status': "AUCUNE_BOUTEILLE",
                    'Niveau_Remplissage': 0.0,
                    'Centre': None
                })

                resultat = DetecteurBouteille.detecter(frame, self.config)

                if resultat['present']:
                    # CAS 1 : BOUTEILLE DETECTEE
                    centre = resultat['centre']
                    self.dernier_resultat['Centre'] = centre
                    
                    resultat_niveau = DetecteurNiveau.verifier(
                        frame, 
                        resultat['bbox'], 
                        self.config
                    )
                    self.dernier_resultat['Niveau_Remplissage'] = resultat_niveau['pourcentage']

                    if resultat_niveau.get('debordement', False):
                        status = "DEBORDEMENT"
                        self.dernier_resultat.update({
                            'Autorisation_Remplissage': False, 
                            'Arret_Convoyeur': True, 
                            'Defaut_Systeme': True
                        })
                        
                    elif resultat_niveau.get('plein', False):
                        status = "BOUTEILLE_PLEINE"
                        self.dernier_resultat.update({
                            'Autorisation_Remplissage': False, 
                            'Arret_Convoyeur': False, 
                            'Defaut_Systeme': False
                        })
                        
                    else:
                        status = "EN_REMPLISSAGE"
                        self.dernier_resultat.update({
                            'Autorisation_Remplissage': True, 
                            'Arret_Convoyeur': True, 
                            'Defaut_Systeme': False
                        })

                    self.dernier_resultat['Status'] = status

                    etat_actuel = "{} @ {}".format(status, centre)
                    
                    if etat_actuel != self.dernier_etat_affiche:
                        print("{} | Centre: {} | Niveau: {:.1f}%".format(
                            status, 
                            centre, 
                            self.dernier_resultat['Niveau_Remplissage']
                        ))
                        self.dernier_etat_affiche = etat_actuel

                    # Affichage
                    x, y, w, h = resultat['bbox']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(
                        frame, 
                        self.dernier_resultat['Status'], 
                        (x, y - 10), 
                        cv2.FONT_HERSHEY_SIMPLEX, 
                        0.6, 
                        (0, 255, 0), 
                        2
                    )

                else:
                    if self.dernier_etat_affiche != "AUCUNE_BOUTEILLE":
                        print("Aucune bouteille detectee")
                        self.dernier_etat_affiche = "AUCUNE_BOUTEILLE"

                cv2.imshow("Ligne de Production", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break

                temps_cycle = time.time() - debut_cycle
                if temps_cycle < 0.033:
                    time.sleep(0.033 - temps_cycle)

        except Exception as e:
            print("Erreur critique dans la boucle : {}".format(e))
            import traceback
            traceback.print_exc()
        finally:
            self.arreter()

    def arreter(self):
        print("Arret du systeme...")
        self.est_tournant = False
        self.camera.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    print("TEST Vision System Jetson")
    systeme = VisionMain()

    try:
        if systeme.start():
            systeme.run()
    except KeyboardInterrupt:
        print(" Arret manuel (Ctrl+C)")
    except Exception as e:
        print("Erreur fatale au demarrage : {}".format(e))
    finally:
        systeme.arreter()
