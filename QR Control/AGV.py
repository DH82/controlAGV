import requests
import cv2
from pymycobot.myagv import MyAgv
import time

agv = MyAgv("/dev/ttyAMA2", 115200)

def capture_and_send():
    cap = cv2.VideoCapture(0)
    ret, frame = cap.read()
    if ret:
        _, img_encoded = cv2.imencode('.jpg', frame)
        response = requests.post("http://172.30.1.89:5000/process_image", files={"image": img_encoded.tobytes()})
        if response.status_code == 200:
            command = response.json().get("command")
            if command and command != "No QR code found":
                execute_command(command)
    cap.release()

def execute_command(command):
    if command == 'FORWARD':
        agv.go_ahead(10)
    elif command == 'LEFT':
        agv.counterclockwise_rotation(rotate_left_speed=1,timeout=3)
    elif command == 'RIGHT':
        agv.clockwise_rotation(rotate_right_speed=1,timeout=3)
    elif command == 'STOP':
        agv.stop()
        time.sleep(5)
        agv.go_ahead(10)

if __name__ == '__main__':
    while True:
        capture_and_send()