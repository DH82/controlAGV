import requests

def send_data():
    server_url = 'http://172.30.1.90:5000/command'
    while True:
        data = input("Enter data (coordinates as 'x,y' or a signal, type 'exit' to quit): ")
        if data.lower() == 'exit':
            break
        
        # 데이터 전송
        response = requests.post(server_url, json={'data': data})
        print("Response from server:", response.json())

if __name__ == "__main__":
    send_data()