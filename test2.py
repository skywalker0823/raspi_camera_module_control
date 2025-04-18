from flask import Flask, render_template_string, Response
from picamera2 import Picamera2
from ultralytics import YOLO
import io, time, os, subprocess
import cv2
import numpy as np

def release_camera():
    try:
        # 嘗試釋放可能佔用相機的程序
        subprocess.run(['sudo', 'pkill', '-f', 'libcamera'], check=False)
        subprocess.run(['sudo', 'systemctl', 'restart', 'libcamera'], check=False)
        time.sleep(1)  # 等待相機重置
    except Exception as e:
        print(f"相機釋放過程出錯: {e}")

# 在初始化相機前先釋放資源
release_camera()

# 載入 YOLO 模型
model = YOLO('yolov8n.pt')

app = Flask(__name__)
try:
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    # 設定相機轉向
    picam2.set_controls({"Rotate": 180})  # 180度旋轉
    picam2.start()
except Exception as e:
    print(f"相機初始化失敗: {e}")
    exit(1)

HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Pi Camera Stream with Object Detection</title>
    <style>
        .container { text-align: center; }
        .stream { max-width: 100%; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pi Camera Live Stream with YOLO Detection</h1>
        <img class="stream" src="{{ url_for('video_feed') }}" />
    </div>
</body>
</html>
"""

def generate_frames():
    while True:
        # 捕獲圖像
        im = picam2.capture_array()
        
        # 確保圖像是RGB格式
        if im.shape[-1] == 4:  # 如果是RGBA格式
            im = cv2.cvtColor(im, cv2.COLOR_RGBA2RGB)
        elif len(im.shape) == 2:  # 如果是灰階圖像
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
            
        # 執行 YOLO 物件識別
        results = model(im)
        
        # 在圖像上繪製識別結果
        for result in results:
            boxes = result.boxes
            for box in boxes:
                # 取得邊界框座標
                x1, y1, x2, y2 = map(int, box.xyxy[0])
                # 取得類別和信心度
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = f'{model.names[cls]} {conf:.2f}'
                
                # 繪製邊界框和標籤
                cv2.rectangle(im, (x1, y1), (x2, y2), (0, 255, 0), 2)
                cv2.putText(im, label, (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

        # 轉換為 JPEG
        ret, jpeg = cv2.imencode('.jpg', im)
        frame = jpeg.tobytes()
        
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        time.sleep(0.1)

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        if 'picam2' in locals():
            picam2.stop()
            picam2.close()
