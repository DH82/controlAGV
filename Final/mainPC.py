from flask import Flask, request, jsonify, Response
import cv2
import numpy as np
import logging
import time
import requests
import queue
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
logging.basicConfig(level=logging.INFO)

# 전역 변수
stream_buffer = None
command_queue = queue.Queue()  # 명령을 저장할 큐
qr_detected = False  # QR 코드 감지 상태
detected_qr = None  # 감지된 QR 코드 데이터
x, y = 0, 0  # Initialize global variables for coordinates

def send_data(data):
    server_url = 'http://172.30.1.55:8080/robot/set_AGV'
    try:
        response = requests.post(server_url, json={'position': data})
        response.raise_for_status()  # Raise an HTTPError for bad responses
        try:
            response_data = response.json()
            print("Response from server:", response_data)
        except ValueError as e:
            print("Error parsing JSON response:", e)
            print("Raw response content:", response.text)
    except requests.exceptions.RequestException as e:
        print("Server request error:", e)

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
        send_data(decoded_text)
        return img, decoded_text
    return img, None

@app.route('/process_image', methods=['POST'])
def process_image():
    global stream_buffer
    try:
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
    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return jsonify({"error": "Failed to process image"}), 500

@app.route('/command', methods=['POST'])
def command():
    global qr_detected, stream_buffer, detected_qr, x, y
    data = request.json.get('data', '')

    if ',' in data:
        try:
            x, y = map(int, data.split(','))  # 좌표를 정수로 변환
            response_message = f"Received coordinates: (X: {x}, Y: {y})"
            logging.info(response_message)
            command_queue.put('changkyu')
            logging.info('changkyu')
            # 초기 QR 코드 확인
            qr_detected = False
            while not qr_detected:
                time.sleep(1)
            
            # 첫 번째 FORWARD 명령 실행
            for i in range(x-1):
                qr_detected = False
                while not qr_detected:
                    time.sleep(1)
                if detected_qr == f'({i+1},1)':
                    logging.info('FORWARD')
                    command_queue.put('FORWARD')
                    time.sleep(3)  # AGV가 움직일 시간을 확보
            
            # LEFT 명령 실행
            command_queue.put('LEFT')
            logging.info('LEFT')
            time.sleep(10)  # AGV가 움직일 시간을 확보
            
            # 세 번째 FORWARD 명령 실행
            for j in range(y-1):
                qr_detected = False
                while not qr_detected:
                    time.sleep(1)
                if detected_qr == f'({x},{j+1})':
                    logging.info('FORWARD')
                    command_queue.put('FORWARD')
                    time.sleep(3)  # AGV가 움직일 시간을 확보

        except ValueError as e:
            response_message = f"Invalid data format for coordinates. Ensure you enter integer values. Error: {e}"
            logging.error(response_message)
            return jsonify({"error": response_message}), 400
        except Exception as e:
            logging.error(f"Unexpected error: {e}")
            return jsonify({"error": "Unexpected error occurred"}), 500
    else:
        response_message = f"Received signal: {data}"
        logging.info(response_message)

        try:
            if data == '1':
                command_queue.put('LEFT')
                logging.info('LEFT')
                time.sleep(10)  # AGV가 움직일 시간을 확보

                for i in range(x-1):
                    qr_detected = False
                    while not qr_detected:
                        time.sleep(1)
                    if detected_qr == f'({x-i},{y})':
                        logging.info('FORWARD')
                        command_queue.put('FORWARD')
                        time.sleep(3)  # AGV가 움직일 시간을 확보

                command_queue.put('LEFT')
                logging.info('LEFT')
                time.sleep(10)  # AGV가 움직일 시간을 확보

                # 세 번째 FORWARD 명령 실행
                for j in range(y-1):
                    qr_detected = False
                    while not qr_detected:
                        time.sleep(1)
                    if detected_qr == f'(1,{y-j})':
                        logging.info('FORWARD')
                        command_queue.put('FORWARD')
                        time.sleep(3)  # AGV가 움직일 시간을 확보

                command_queue.put('COBOT')
                logging.info('COBOT')
                time.sleep(10)  # AGV가 움직일 시간을 확보

            elif data == '2':
                command_queue.put('parking')
                logging.info('parking')
                time.sleep(10)  # AGV가 움직일 시간을 확보
            elif data == '3':
                pass
            return jsonify({"message": response_message}), 200
        except Exception as e:
            logging.error(f"Error processing command {data}: {e}")
            return jsonify({"error": f"Failed to process command {data}"}), 500

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