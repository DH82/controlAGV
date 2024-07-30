import cv2
import requests
from pymycobot.myagv import MyAgv

agv = MyAgv("/dev/ttyAMA2", 115200)  # AGV 초기화 및 설정

def send_frame_to_server(frame):
    _, img_encoded = cv2.imencode('.jpg', frame)
    response = requests.post("http://172.30.1.20:5000/video", files={'video': img_encoded.tobytes()})
    return response.json()['command']

def execute_command(command):
    if command == "LEFT":
        agv.counterclockwise_rotation(10)
    elif command == "RIGHT":
        agv.clockwise_rotation(10)
    elif command == "FORWARD":
        agv.go_ahead(10)
    elif command == "STOP":
        agv.stop()

def main():
    cap = cv2.VideoCapture(0)  # 카메라 열기
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        command = send_frame_to_server(frame)
        execute_command(command)

if __name__ == '__main__':
    main()