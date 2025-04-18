sudo apt install libcamera-dev python3-libcamera

# 若尚未建立 venv，建立一個可讀取系統套件的 venv
python3 -m venv venv --system-site-packages
source venv/bin/activate

# 安裝 picamera2（若尚未安裝）
pip install -r requirements.txt
