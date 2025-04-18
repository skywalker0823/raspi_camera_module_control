from flask import Flask, render_template, jsonify
from picamera2 import Picamera2
import time

app = Flask(__name__)
picam2 = Picamera2()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/capture')
def capture():
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    filename = f"capture_{timestamp}.jpg"
    picam2.start_and_capture_file(filename)
    return jsonify({"status": "success", "filename": filename})

@app.route('/record')
def record():
    timestamp = time.strftime('%Y%m%d-%H%M%S')
    filename = f"video_{timestamp}.mp4"
    picam2.start_and_record_video(filename, duration=5)
    return jsonify({"status": "success", "filename": filename})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

