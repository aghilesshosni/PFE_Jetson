import os
import sys
import time
import threading
from flask import Flask, render_template, Response, jsonify

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared_state import state

app = Flask(__name__)

def generer_frames():
    """MJPEG streaming — throttled, non-blocking"""
    while True:
        try:
            data = state.get_data()
            frame_bytes = data['last_frame_bytes']
            if frame_bytes:
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n'
                       + frame_bytes + b'\r\n')
            time.sleep(0.1)  # hard cap at 10fps
        except GeneratorExit:
            break
        except Exception:
            time.sleep(0.1)
            continue

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/video_feed')
def video_feed():
    return Response(
        generer_frames(),
        mimetype='multipart/x-mixed-replace; boundary=frame',
        headers={
            'Cache-Control': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': '0',
            'Connection': 'close',   # ← key: don't keep connection alive forever
        }
    )

@app.route('/api/status')
def get_status():
    data = state.get_data()
    return jsonify({
        'niveau':    data['pourcentage_niveau'],
        'level':     data['pourcentage_niveau'],
        'presence':  data['presence_bouteille'],
        'present':   data['presence_bouteille'],
        'fps':       data['fps'],
        'status':    data['status'],
        'timestamp': data['timestamp'],
    })

def start_dashboard_thread():
    def run_flask():
        # threaded=True lets Flask handle video + API simultaneously
        # without one blocking the other
        app.run(
            host='0.0.0.0',
            port=5000,
            debug=False,
            use_reloader=False,
            threaded=True      # ← critical for MJPEG + API to coexist
        )
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
