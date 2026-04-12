import cv2
import os
import subprocess
import time
import signal

class GestionnaireCamera:
    def __init__(self, camera_id=0):
        self.pipe_path = "/tmp/cam_pipe_fifo"
        self.cap = None
        self.gst_process = None
        
        # Configuration : On laisse GStreamer négocier la résolution native puis on convertit en 1280x720 BGR
        self.cmd = [
            "gst-launch-1.0",
            "nvarguscamerasrc", "sensor-id=0",
            "!", "video/x-raw(memory:NVMM)",
            "!", "nvvidconv", "flip-method=0",
            "!", "video/x-raw", "format=(string)BGR", "width=(int)1280", "height=(int)720",
            "!", "videoconvert",
            "!", "video/x-raw", "format=(string)BGR",
            "!", "filesink", "location=" + self.pipe_path
        ]

    def open(self):
        print("🚀 Lancement du mode 'Pipe Brut Forcé' (Subprocess)...")
        
        # 1. Nettoyage radical
        if os.path.exists(self.pipe_path):
            os.remove(self.pipe_path)
        
        # 2. Création du FIFO
        try:
            os.mkfifo(self.pipe_path)
        except OSError as e:
            print(f"❌ Erreur création FIFO: {e}")
            return False
        
        # 3. Lancement GStreamer EN ARRIÈRE PLAN
        print("   -> Démarrage du processus GStreamer...")
        self.gst_process = subprocess.Popen(
            self.cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid
        )
        
        # 4. Attente CRUCIALE (La caméra IMX219 met ~2-3s à initialiser le capteur)
        print("   -> Attente de stabilisation du capteur (3 secondes)...")
        time.sleep(3.0) 
        
        # Vérification si le processus est mort prématurément
        if self.gst_process.poll() is not None:
            stdout, stderr = self.gst_process.communicate()
            print("❌ ÉCHEC FATAL : GStreamer s'est arrêté immédiatement.")
            print("   --- Message d'erreur système ---")
            print(stderr.decode('utf-8'))
            print("   -------------------------------")
            return False
            
        # 5. Ouverture avec OpenCV (Lecture SIMPLE de fichier, PAS de GStreamer ici!)
        print("   -> Ouverture du pipe par OpenCV (Mode Standard)...")
        self.cap = cv2.VideoCapture(self.pipe_path)
        
        if not self.cap.isOpened():
            print("❌ ÉCHEC : OpenCV n'arrive pas à ouvrir le pipe.")
            self.release()
            return False
            
        # 6. Test de lecture (On essaie pendant 2 secondes)
        print("   -> Tentative de réception d'images...")
        for i in range(20): 
            ret, frame = self.cap.read()
            if ret and frame is not None:
                h, w = frame.shape[:2]
                print(f"✅ SUCCÈS TOTAL ! Image reçue : {w}x{h}")
                return True
            time.sleep(0.1)
            
        print("❌ ÉCHEC : Pipe ouvert mais aucune image ne vient (flux vide).")
        self.release()
        return False

    def read(self):
        if self.cap is None or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            ret, frame = self.cap.read() # Deuxième chance
        return frame

    def release(self):
        if self.cap:
            self.cap.release()
            self.cap = None
        if self.gst_process:
            try:
                # Tuer tout le groupe de processus proprement
                os.killpg(os.getpgid(self.gst_process.pid), signal.SIGKILL)
            except:
                pass
        if os.path.exists(self.pipe_path):
            try:
                os.remove(self.pipe_path)
            except:
                pass
        print("📷 Ressources caméra libérées.")
