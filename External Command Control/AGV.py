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
        response = requests.post("http://172.30.1.90:5000/process_image", files={"image": img_encoded.tobytes()})
        if response.status_code == 200:
            command = response.json().get("command")
            if command and command != "No QR code found":
                execute_command(command)
    cap.release()

def execute_command(command):
    if command == 'FORWARD':
        print('FORWARD')
        agv.go_ahead(10, timeout=3)
        time.sleep(0.5)
    elif command == 'LEFT':
        print('LEFT')
        agv.counterclockwise_rotation(1, timeout=3)
        time.sleep(0.5)
        agv.pan_right(10, timeout=1.8)
        time.sleep(0.5)
        agv.retreat(10, timeout=1.7)
        time.sleep(0.5)
    elif command == 'RIGHT':
        print('RIGHT')
        agv.clockwise_rotation(1, timeout=3)
        time.sleep(0.5)
        agv.pan_left(10, timeout=1.8)
        time.sleep(0.5)
        agv.retreat(10, timeout=1.7)
        time.sleep(0.5)
    elif command == 'STOP':
        agv.stop()
    elif command == 'COBOT':
        print('COBOT')
        agv.clockwise_rotation(1, timeout=3)
        time.sleep(0.5)
        agv.pan_left(10, timeout=4.3)
        time.sleep(0.5)
        agv.retreat(10, timeout=1.7)
        time.sleep(0.5)
    elif command == 'changkyu':
        print('1,1')
        agv.go_ahead(10, timeout=5.3)
        time.sleep(0.5)
        agv.pan_right(10, timeout=4.6)
        time.sleep(0.5)
        agv.retreat(10, timeout=2.1)
        time.sleep(0.5)
    elif command == 'parking':
        print('Parking')
        agv.clockwise_rotation(1, timeout=3)
        time.sleep(0.5)
        agv.go_ahead(10, timeout=3.5)
        time.sleep(0.5)
        agv.pan_left(10, timeout=6.2)
        time.sleep(0.5)
        agv.retreat(10, timeout=5.3)
        time.sleep(0.5)

if __name__ == '__main__':
    while True:
        capture_and_send()
