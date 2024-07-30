from flask import Flask, request, jsonify
import cv2
import numpy as np
import logging

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

def display_image_with_qr_code(img, decoded_text, points):
    if points is not None and decoded_text:
        points = np.int32(points).reshape(-1, 2)
        for j in range(points.shape[0]):
            cv2.line(img, tuple(points[j]), tuple(points[(j+1) % points.shape[0]]), (255,0,0), 5)
        cv2.putText(img, decoded_text, (points[0][0], points[0][1] - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255,0,0), 2)
        cv2.imshow("QR Code Detection", img)
        cv2.waitKey(1)

@app.route('/process_image', methods=['POST'])
def process_image():
    if request.files:
        file_str = request.files['image'].read()
        np_img = np.frombuffer(file_str, np.uint8)
        img = cv2.imdecode(np_img, cv2.IMREAD_COLOR)
        qr_code_detector = cv2.QRCodeDetector()
        decoded_text, points, _ = qr_code_detector.detectAndDecode(img)
        if points is not None and decoded_text:
            logging.info(f"QR Code detected: {decoded_text}")  # 읽은 정보 출력
            display_image_with_qr_code(img, decoded_text, points)
            return jsonify({"command": decoded_text})
        else:
            logging.info("No QR code or data found")
            return jsonify({"command": "No QR code found"})
    return jsonify({"error": "No image provided"}), 400

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)