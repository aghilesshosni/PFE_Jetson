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
        # Preallocation de buffer
        self.frame_buffer = np.zeros((self.config.hauteur, self.config.largeur, 3), dtype=np.uint8)
        self.est_tournant = False
        self.dernier_resultat = {
            'Autorisation_Remplissage': False,
            'Arret_Convoyeur': False,
            'Defaut_Systeme': False,
            'Status': 'Init',
            'Compensation': 0,
            'Niveau_Remplissage': 0.0
        }

    def start(self):
        if not self.camera.open():
            raise RuntimeError("Echec de Camera")
        self.est_tournant = True
        return True

    def run(self):
        # Boucle infinie de traitement d'images
        if not self.est_tournant:
            return
        
        self.dernier_etat_affiche = None 

        try:
            while self.est_tournant:
                debut_cycle = time.time()
                frame = self.camera.read()
                
                if frame is None:
                    continue

                self.dernier_resultat.update({
                    'Autorisation_Remplissage': False,
                    'Arret_Convoyeur': False,
                    'Defaut_Systeme': False,
                    'Status': "AUCUNE_BOUTEILLE",
                    'Niveau_Remplissage': 0.0,
                    'Centre': None  
                })

                # Détecter
                resultat = DetecteurBouteille.detecter(frame, self.config)

                if resultat['present']:
                    # cas 1: bouteille détectée
                    centre = resultat['centre']
                    self.dernier_resultat['Centre'] = centre
                    
                    # Mise à jour du niveau
                    resultat_niveau = DetecteurNiveau.verifier(frame, resultat['bbox'], self.config)
                    self.dernier_resultat['Niveau_Remplissage'] = resultat_niveau['pourcentage']

                    if resultat_niveau.get('debordement', False):
                        self.dernier_resultat['Status'] = "DEBORDEMENT"
                        self.dernier_resultat['Autorisation_Remplissage'] = False
                        self.dernier_resultat['Arret_Convoyeur'] = True
                        self.dernier_resultat['Defaut_Systeme'] = True
                    elif resultat_niveau.get('plein', False):
                        self.dernier_resultat['Status'] = "BOUTEILLE_PLEINE"
                        self.dernier_resultat['Autorisation_Remplissage'] = False
                        self.dernier_resultat['Arret_Convoyeur'] = False
                        self.dernier_resultat['Defaut_Systeme'] = False
                    else:
                        self.dernier_resultat['Status'] = "EN_REMPLISSAGE"
                        self.dernier_resultat['Autorisation_Remplissage'] = True
                        self.dernier_resultat['Arret_Convoyeur'] = True
                        self.dernier_resultat['Defaut_Systeme'] = False

                    # Affichage seulement si l'état change
                    etat_actuel = f"{self.dernier_resultat['Status']} à {centre}"
                    if etat_actuel != self.dernier_etat_affiche:
                        print(f"Bouteille détectée : {etat_actuel} | Niveau: {self.dernier_resultat['Niveau_Remplissage']:.1f}%")
                        self.dernier_etat_affiche = etat_actuel

                else:
                    # cas 2: aucune bouteille
                    if self.dernier_etat_affiche != "AUCUNE_BOUTEILLE":
                        print("Aucune bouteille détectée")
                        self.dernier_etat_affiche = "AUCUNE_BOUTEILLE"

                #  Dessiner un rectangle si détection 
                if resultat['present']:
                    x, y, w, h = resultat['bbox']
                    cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                    cv2.putText(frame, self.dernier_resultat['Status'], (x, y - 10), 
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

                cv2.imshow("Ligne de Production", frame)

                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
                
        except Exception as e:
            print(f"Erreur critique dans la boucle : {e}")
            import traceback
            traceback.print_exc()
        finally:
            self.arreter()

    def arreter(self):
        self.est_tournant = False
        self.camera.release()
        cv2.destroyAllWindows()

# TEST du module Vision
if __name__ == "__main__":
    print("TEST du module Vision")
    systeme = VisionMain()
    try:
        if systeme.start():
            systeme.run()
        else:
            print("Echec de démarrage")
    except KeyboardInterrupt:
        print("veuillez appuyer sur Ctrl C")
    except Exception as e:
        print(f" Erreur critique: {e}")
    finally:
        systeme.arreter()
