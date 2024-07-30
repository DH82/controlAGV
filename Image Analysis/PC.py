from flask import Flask, request, jsonify
import cv2
import numpy as np
import threading

app = Flask(__name__)

# 초록색 범위 정의
lower_green = np.array([70, 60, 30])
upper_green = np.array([100, 255, 255])

# 실시간 영상 처리
@app.route('/video', methods=['POST'])
def process_video():
    video_file = request.files['video'].read()
    nparr = np.fromstring(video_file, np.uint8)
    frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(frame, lower_green, upper_green)

    # 명령 결정 로직
    command = determine_command(mask)
    return jsonify({'command': command})

def determine_command(mask):
    if np.any(mask):
        left_half = np.sum(mask[:, :mask.shape[1]//2])
        right_half = np.sum(mask[:, mask.shape[1]//2:])
        if left_half > right_half:
            return "LEFT"
        elif right_half > left_half:
            return "RIGHT"
        else:
            return "FORWARD"
    else:
        return "STOP"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)