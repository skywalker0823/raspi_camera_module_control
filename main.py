from flask import Flask, render_template, jsonify
from picamera2 import Picamera2
from datetime import datetime
import os

app = Flask(__name__)
picam2 = Picamera2()

RESULTS_FOLDER = 'results'
if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record')
def record():
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{RESULTS_FOLDER}/video_{timestamp}.mp4"
    picam2.start_and_record_video(filename, duration=5)
    return jsonify({"status": "success", "filename": filename})

@app.route('/videos')
def list_videos():
    videos = [f for f in os.listdir(RESULTS_FOLDER) if f.endswith('.mp4')]
    return jsonify(videos)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
