import cv2

def gstreamer_pipeline(
    sensor_id=0,
    capture_width=1280,
    capture_height=720,
    display_width=1280,
    display_height=720,
    framerate=30,
    flip_method=0,
):
    return (
        f"nvarguscamerasrc sensor-id={sensor_id} ! "
        f"video/x-raw(memory:NVMM), width=(int){capture_width}, height=(int){capture_height}, framerate=(fraction){framerate}/1 ! "
        f"nvvidconv flip-method={flip_method} ! "
        f"video/x-raw, width=(int){display_width}, height=(int){display_height} ! "
        f"videoconvert ! video/x-raw, format=(string)BGR ! appsink"
    )

def show_camera():
    window_title = "Waveshare CSI Camera Test"
    pipeline_str = gstreamer_pipeline(flip_method=0)
    
    print("📷 Pipeline utilisé:")
    print(pipeline_str)
    print("\n⏳ Tentative d'ouverture (peut prendre 3-5 secondes)...")
    
    # Création de l'instance
    video_capture = cv2.VideoCapture(pipeline_str, cv2.CAP_GSTREAMER)
    
    if not video_capture.isOpened():
        print("❌ ÉCHEC : Unable to open camera (isOpened=False)")
        print("   -> Confirmation que ton OpenCV ne peut pas parler directement à GStreamer.")
        print("   -> La méthode du FIFO Pipe (subprocess) sera OBLIGATOIRE.")
        return

    print("✅ SUCCÈS : Caméra ouverte ! Attente de la première image...")
    
    # On attend patiemment la première image (la caméra IMX219 est lente)
    for i in range(50): # 5 secondes max
        ret, frame = video_capture.read()
        if ret and frame is not None:
            h, w = frame.shape[:2]
            print(f"🎉 IMAGE REÇUE ! Résolution: {w}x{h}")
            break
        if i % 10 == 0:
            print(f"   ... attente ({i/10}s)")
        cv2.waitKey(100)
    else:
        print("⚠️ Ouvert mais aucune image reçue après 5s.")

    try:
        while True:
            ret, frame = video_capture.read()
            if not ret or frame is None:
                continue
            
            cv2.imshow(window_title, frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
    finally:
        video_capture.release()
        cv2.destroyAllWindows()
        print("Caméra fermée.")

if __name__ == "__main__":
    show_camera()
