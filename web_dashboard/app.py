import os
import sys
import time
import threading
from flask import Flask, render_template, Response, jsonify

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_state import state

app = Flask(__name__)

def generer_frames():
    '''methode pour MJPEG streaming'''
    while True:
        data = state.get_data()
        if data['last_frame_bytes']:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + data['last_frame_bytes'] + b'\r\n')
        else:
            time.sleep(0.1)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(generer_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/api/status')
def get_status():
    data = state.get_data()
    return jsonify({
        'niveau': data['pourcentage_niveau'], 
        'presence': data['presence_bouteille'], 
        'fps': data['fps']
    })

def start_dashboard_thread():
    def run_flask():
        app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)
        
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
