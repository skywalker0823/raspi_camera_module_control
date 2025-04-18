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

# 在 Flask app 之前添加全局變數
is_capturing = False
current_detections = []

app = Flask(__name__)
try:
    picam2 = Picamera2()
    config = picam2.create_video_configuration(main={"size": (640, 480)})
    picam2.configure(config)
    # 移除不支援的 Rotate 控制
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
        .controls { margin: 20px 0; }
        .detection-results {
            margin: 20px auto;
            max-width: 600px;
            text-align: left;
            padding: 10px;
            border: 1px solid #ccc;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Pi Camera Live Stream with YOLO Detection</h1>
        <div class="controls">
            <button onclick="toggleCapture()" id="captureBtn">開始拍攝</button>
        </div>
        <img class="stream" id="videoFeed" style="display: none;" src="{{ url_for('video_feed') }}" />
        <div class="detection-results" id="detectionResults">
            等待檢測結果...
        </div>
    </div>
    <script>
        let isCapturing = false;
        
        function toggleCapture() {
            isCapturing = !isCapturing;
            const btn = document.getElementById('captureBtn');
            const videoFeed = document.getElementById('videoFeed');
            
            if (isCapturing) {
                btn.textContent = '停止拍攝';
                videoFeed.style.display = 'block';
                fetch('/start_capture');
            } else {
                btn.textContent = '開始拍攝';
                videoFeed.style.display = 'none';
                fetch('/stop_capture');
            }
        }

        // 定期更新檢測結果
        setInterval(async () => {
            if (isCapturing) {
                const response = await fetch('/get_detections');
                const data = await response.json();
                const resultsDiv = document.getElementById('detectionResults');
                resultsDiv.innerHTML = '<h3>當前檢測結果：</h3>' + 
                    data.map(item => `${item.label} (信心度: ${item.confidence})`).join('<br>');
            }
        }, 500);
    </script>
</body>
</html>
"""

def generate_frames():
    global current_detections
    while True:
        if not is_capturing:
            time.sleep(0.1)
            continue
            
        # 捕獲圖像
        im = picam2.capture_array()
        
        # 確保圖像是RGB格式
        if im.shape[-1] == 4:  # 如果是RGBA格式
            im = cv2.cvtColor(im, cv2.COLOR_RGBA2RGB)
        elif len(im.shape) == 2:  # 如果是灰階圖像
            im = cv2.cvtColor(im, cv2.COLOR_GRAY2RGB)
        
        #顏色輸出錯誤處理
        im = cv2.cvtColor(im, cv2.COLOR_RGB2BGR)

        # 直接在這裡旋轉圖像
        im = cv2.rotate(im, cv2.ROTATE_180)
        
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

        # 更新檢測結果
        current_detections = []
        for result in results:
            boxes = result.boxes
            for box in boxes:
                conf = float(box.conf[0])
                cls = int(box.cls[0])
                label = f'{model.names[cls]}'
                current_detections.append({
                    'label': label,
                    'confidence': f'{conf:.2f}'
                })

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

@app.route('/start_capture')
def start_capture():
    global is_capturing
    is_capturing = True
    return {'status': 'success'}

@app.route('/stop_capture')
def stop_capture():
    global is_capturing
    is_capturing = False
    return {'status': 'success'}

@app.route('/get_detections')
def get_detections():
    return current_detections

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        if 'picam2' in locals():
            picam2.stop()
            picam2.close()
