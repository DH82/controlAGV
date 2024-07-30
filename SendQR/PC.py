from flask import Flask, request, jsonify, Response
import cv2
import numpy as np
import logging
import time
import queue

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# 전역 변수
stream_buffer = None
command_queue = queue.Queue()  # 명령을 저장할 큐
qr_detected = False  # QR 코드 감지 상태
detected_qr = None  # 감지된 QR 코드 데이터

# QR 코드 감지 및 처리 함수
def process_qr_code(img):
    global detected_qr, qr_detected
    qr_code_detector = cv2.QRCodeDetector()
    decoded_text, points, _ = qr_code_detector.detectAndDecode(img)
    if points is not None and decoded_text:
        logging.info(f"QR Code detected: {decoded_text}")
        detected_qr = decoded_text
        qr_detected = True
        points = np.int32(points).reshape(-1, 2)
        for j in range(points.shape[0]):
            cv2.line(img, tuple(points[j]), tuple(points[(j+1) % points.shape[0]]), (255, 0, 0), 5)
        cv2.putText(img, decoded_text, (points[0][0], points[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        return img, decoded_text
    return img, None

@app.route('/process_image', methods=['POST'])
def process_image():
    global stream_buffer
    if 'image' in request.files:
        file_str = request.files['image'].read()
        np_img = np.frombuffer(file_str, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        img, decoded_text = process_qr_code(img)
        _, stream_buffer = cv2.imencode('.jpg', img)
        if decoded_text:
            response = {"command": decoded_text}
        else:
            logging.info("No QR code or data found")
            response = {"command": "No QR code found"}
    else:
        response = {"error": "No image provided"}

    if not command_queue.empty():
        response["command"] = command_queue.get()  # 큐에서 명령을 가져와서 전달

    return jsonify(response), 400 if "error" in response else 200

@app.route('/command', methods=['POST'])
def command():
    global qr_detected, stream_buffer, detected_qr
    data = request.json.get('data', '')
    if ',' in data:
        try:
            x, y = map(int, data.split(','))  # 좌표를 정수로 변환
            response_message = f"Received coordinates: (X: {x}, Y: {y})"
            command_queue.put('changkyu')
            
            # 초기 QR 코드 확인
            qr_detected = False
            while not qr_detected:
                if stream_buffer is not None:
                    if detected_qr == '(1,1)':
                        qr_detected = True
                    time.sleep(1)
            
            # 첫 번째 FORWARD 명령 실행
            for i in range(x):
                command_queue.put('FORWARD')
                time.sleep(3)  # AGV가 움직일 시간을 확보
                qr_detected = False
                while not qr_detected:
                    if stream_buffer is not None:
                        if detected_qr == '('+str(x+1)+',1)':
                            qr_detected = True
                        time.sleep(1)
            
            
            # LEFT 명령 실행
            command_queue.put('LEFT')
            time.sleep(10)  # AGV가 움직일 시간을 확보
            
            # 세 번째 FORWARD 명령 실행
            for j in range(y):
                command_queue.put('FORWARD')
                qr_detected = False
                while not qr_detected:
                    if stream_buffer is not None:
                        if detected_qr == '(x'+str(y+1)+')':
                            qr_detected = True
                        time.sleep(1)

        except ValueError:
            response_message = "Invalid data format for coordinates. Ensure you enter integer values."
            return jsonify({"error": response_message}), 400
    else:
        response_message = f"Received signal: {data}"
        logging.info(response_message)
        return jsonify({"message": response_message}), 400

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
