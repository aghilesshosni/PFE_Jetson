import cv2

class GestionnaireCamera:
    def __init__(self, camera_id):
        # On s'attend à recevoir un entier (l'ID) directement ici
        self.camera_id = camera_id
        self.cap = None

    def open(self):
        self.cap = cv2.VideoCapture(self.camera_id)
        if not self.cap.isOpened():
            return False
        # Note: largeur/hauteur ne sont pas accessibles ici car on a passé un int, pas l'objet config complet
        # Si tu veux régler la résolution, il faudra passer l'objet config entier ou les valeurs en args supplémentaires.
        # Pour l'instant, on laisse les valeurs par défaut de la webcam pour éviter l'erreur.
        return True

    def read(self):
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None
        return frame

    def release(self):
        if self.cap is not None:
            self.cap.release()
