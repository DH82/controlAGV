from flask import Flask, request, Response

app = Flask(__name__)

# 스트리밍을 위한 버퍼. 이 버퍼에는 AGV로부터 받은 최신 이미지가 저장됩니다.
stream_buffer = None

@app.route('/process_image', methods=['POST'])
def process_image():
    global stream_buffer
    file = request.files['image']
    if not file:
        return "No image file provided", 400

    # 파일을 읽어 바로 스트리밍 버퍼에 저장
    stream_buffer = file.read()
    return "Image received", 200

def generate_stream():
    global stream_buffer
    while True:
        if stream_buffer:
            # 스트리밍 버퍼에서 이미지 데이터를 가져와 스트리밍 형식으로 변환
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + stream_buffer + b'\r\n')
            # 다음 프레임까지 잠시 대기
            time.sleep(0.1)

@app.route('/stream')
def stream():
    # generate_stream 함수를 통해 이미지 스트리밍
    return Response(generate_stream(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, threaded=True)
