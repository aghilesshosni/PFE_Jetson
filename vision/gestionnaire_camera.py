import cv2
import os
import subprocess
import time
import signal
import fcntl

class GestionnaireCamera:
    def __init__(self, camera_id=0):
        self.pipe_path = "/tmp/jetson_cam_pipe_final"
        self.cap = None
        self.gst_process = None
        
        # Pipeline GStreamer standard
        self.cmd = [
            "gst-launch-1.0",
            "nvarguscamerasrc", "sensor-id=0",
            "!", "video/x-raw(memory:NVMM)",
            "!", "nvvidconv", "flip-method=0",
            "!", "video/x-raw,format=(string)BGRx,width=(int)1280,height=(int)720",
            "!", "videoconvert",
            "!", "video/x-raw,format=(string)BGR",
            "!", "filesink", "location=" + self.pipe_path, "sync=false"
        ]

    def open(self):
        print("🚀 Lancement mode FIFO avec astuce 'O_RDWR' (Anti-Deadlock)...")
        
        # 1. Nettoyage
        if os.path.exists(self.pipe_path):
            os.remove(self.pipe_path)
        try:
            os.mkfifo(self.pipe_path)
        except OSError as e:
            print(f"Erreur FIFO: {e}")
            return False
        
        # 2. Lancement GStreamer
        print("   -> Démarrage GStreamer...")
        self.gst_process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # Attendre que le process soit prêt (ou qu'il plante)
        time.sleep(1.0)
        if self.gst_process.poll() is not None:
            _, stderr = self.gst_process.communicate()
            print("❌ GStreamer a planté au démarrage:")
            print(stderr.decode('utf-8'))
            return False

        # 3. L'ASTUCE MAGIQUE : Ouvrir le FIFO en RDWR non-bloquant
        # Cela force l'ouverture immédiate des deux côtés (lecture/écriture)
        # et empêche le blocage infini de filesink et VideoCapture.
        print("   -> Application de l'astuce O_RDWR pour débloquer le flux...")
        try:
            fd = os.open(self.pipe_path, os.O_RDWR | os.O_NONBLOCK)
            # On garde le fd ouvert quelques ms puis on le ferme
            # Le simple fait d'avoir ouvert en RDWR a suffi à handshake
            time.sleep(0.2)
            os.close(fd)
            print("   -> Verrou FIFO brisé avec succès.")
        except Exception as e:
            print(f"⚠️ Astuce O_RDWR échouée: {e}")
            # On continue quand même, parfois ça marche sans

        # 4. Ouverture par OpenCV
        print("   -> Connexion OpenCV...")
        self.cap = cv2.VideoCapture(self.pipe_path)
        
        if not self.cap.isOpened():
            print("❌ ÉCHEC : OpenCV ne peut pas ouvrir le pipe.")
            self.release()
            return False
            
        # 5. Réception images (On patiente plus longtemps)
        print("   -> Attente du premier frame (peut prendre 3-4s)...")
        for i in range(60): # 6 secondes max
            ret, frame = self.cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"✅ SUCCÈS TOTAL ! Image reçue : {w}x{h}")
                return True
            time.sleep(0.1)
            
        print("❌ ÉCHEC : Aucun frame reçu après 6s.")
        self.release()
        return False

    def read(self):
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            ret, frame = self.cap.read()
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
        if self.gst_process:
            try:
                os.killpg(os.getpgid(self.gst_process.pid), signal.SIGKILL)
            except: pass
        if os.path.exists(self.pipe_path):
            try: os.remove(self.pipe_path)
            except: pass
        print("📷 Ressources libérées.")
