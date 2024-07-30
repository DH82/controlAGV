from flask import Flask, request, jsonify, Response
import cv2
import numpy as np
import logging
import time

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 전역 변수
stream_buffer = None
current_command = None

def process_qr_code(img):
    qr_code_detector = cv2.QRCodeDetector()
    decoded_text, points, _ = qr_code_detector.detectAndDecode(img)
    if points is not None and decoded_text:
        logging.info(f"QR Code detected: {decoded_text}")
        points = np.int32(points).reshape(-1, 2)
        for j in range(points.shape[0]):
            cv2.line(img, tuple(points[j]), tuple(points[(j+1) % points.shape[0]]), (255,0,0), 5)
        cv2.putText(img, decoded_text, (points[0][0], points[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
        return img, decoded_text
    return img, None

@app.route('/process_image', methods=['POST'])
def process_image():
    global current_command
    if 'image' in request.files:
        file_str = request.files['image'].read()
        np_img = np.frombuffer(file_str, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        img, decoded_text = process_qr_code(img)
        _, stream_buffer = cv2.imencode('.jpg', img)
        if decoded_text:
            return jsonify({"command": decoded_text})
        else:
            logging.info("No QR code or data found")
            return jsonify({"command": "No QR code found"})
    return jsonify({"error": "No image provided"}), 400

@app.route('/command', methods=['POST'])
def command():
    data = request.json.get('data', '')
    if ',' in data:
        # ','를 기준으로 좌표를 추정
        try:
            x, y = map(int, data.split(','))  # 좌표를 정수로 변환
            response_message = f"Received coordinates: (X: {x}, Y: {y})"
        except ValueError:
            response_message = "Invalid data format for coordinates. Ensure you enter integer values."
            return jsonify({"error": response_message}), 400
    else:
        # 좌표가 아닌 단일 값(신호)로 추정
        response_message = f"Received signal: {data}"

    logging.info(response_message)
    return jsonify({"message": response_message})


def generate_stream():
    global stream_buffer
    while True:
        if stream_buffer is not None:
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + stream_buffer.tobytes() + b'\r\n')
            time.sleep(0.1)

@app.route('/stream')
def stream():
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)