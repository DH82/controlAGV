import requests
import cv2
import time

def capture_and_send():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    
    if ret:
        _, img_encoded = cv2.imencode('.jpg', frame)
        img_bytes = img_encoded.tobytes()
        response = requests.post("http://172.30.1.89:5000/process_image", files={"image": img_bytes})
        
        if response.status_code == 200:
            print("Image sent successfully")
        else:
            print(f"Failed to send image. Status code: {response.status_code}")
    
    cap.release()

if __name__ == '__main__':
    while True:
        capture_and_send()
        time.sleep(1)