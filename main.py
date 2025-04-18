from flask import Flask, render_template, jsonify, Response
from picamera2 import Picamera2
from datetime import datetime
import os
import time

app = Flask(__name__)
RESULTS_FOLDER = 'results'

# 確保相機在程式開始時是關閉的
picam2 = None

def init_camera():
    global picam2
    if picam2 is None:
        picam2 = Picamera2()
        picam2.configure(picam2.create_preview_configuration())

if not os.path.exists(RESULTS_FOLDER):
    os.makedirs(RESULTS_FOLDER)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/record')
def record():
    global picam2
    try:
        init_camera()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{RESULTS_FOLDER}/video_{timestamp}.mp4"
        picam2.start_and_record_video(filename, duration=5)
        return jsonify({"status": "success", "filename": filename})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

@app.route('/videos')
def list_videos():
    videos = [f for f in os.listdir(RESULTS_FOLDER) if f.endswith('.mp4')]
    videos.sort(reverse=True)  # 最新的影片排在前面
    return jsonify(videos)

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=True)
    finally:
        if picam2:
            picam2.close()
