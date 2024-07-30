import requests
import json
import serial
from pymodbus.client.sync import ModbusSerialClient
import time

plc_address = 10
serial_port = "COM6"
baud_rate = 9600
parity = serial.PARITY_NONE
stop_bits = serial.STOPBITS_ONE
data_bits = 8
state_address = 0x0005
data_address = 0x000A

client = ModbusSerialClient(method='rtu', port=serial_port, baudrate=baud_rate,
                            parity=parity, stopbits=stop_bits, bytesize=data_bits)
mod_connect = client.connect()

modbus_status = 0
x = 0
y = 0

def send_data(modbus_status, x, y):
    print('데이터 전송')
    server_url = 'http://172.30.1.16:5000/command'
    if modbus_status == 1:
        data = f'{x}, {y}'
        print(f'좌표 전송 {data}')
        
    elif modbus_status == 2:
        data = f'{1}'  # 'y' 값이 필요 없으면 0 또는 다른 값으로 대체
        print(f'테이블 이동 {data}')
        client.write_register(address=state_address, value=0, unit=plc_address)
        
    elif modbus_status == 3:
        data = f'{2}'  # 'y' 값이 필요 없으면 0 또는 다른 값으로 대체
        print(f'테이블 이동 {data}')
        client.write_register(address=state_address, value=0, unit=plc_address)
        
    else:
        data = None
    
    if data:
        response = requests.post(server_url, json={'data': data})
        
        try:
            response_data = response.json()
            print("Response from server:", response_data)
        except json.JSONDecodeError:
            print("Response from server is not in JSON format or is empty.")
        except requests.RequestException as e:
            print(f"An error occurred: {e}")
            
def state_reset():
    client.write_register(address=state_address, value=0, unit=plc_address)
        

if mod_connect:
    while True:
        start = client.read_holding_registers(address=state_address, count=1, unit=plc_address)
        point = client.read_holding_registers(address=data_address, count=2, unit=plc_address)
        modbus_status = start.registers[0]
        x = point.registers[0]
        y = point.registers[1]
        print(modbus_status)
        
        if modbus_status == 1:
            print(f'첫경우 {x,y}')
            send_data(modbus_status, x, y)
            state_reset()
            continue    
            
                    
        elif modbus_status == 2:
            print(f'둘째경우 {x}')
            send_data(modbus_status, x, y)
            state_reset()
            continue
            
        elif modbus_status == 3:
            print("복귀")
            send_data(modbus_status, x, y)
            state_reset()
            continue
            
            
        print('0')
        client.write_register(address=state_address, value=0, unit=plc_address)
        
                
        time.sleep(1)        
        