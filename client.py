import socket
from os.path import isfile, getsize

import matplotlib.pyplot as plt
from collections import defaultdict
import matplotlib.dates as mdates
from datetime import datetime

conn_ip = "127.0.0.1"
conn_port = 8800

client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM) # TCP
client_socket.connect((conn_ip, conn_port))

client_socket.settimeout(30)  # 設定超時為 30 秒

def receive_message(conn):
    # Keep reading until the delimiter is found
    try:
        message = b""
        first_chunk = conn.recv(4096)
        if "[TABLE]".encode('utf-8') not in first_chunk:
            return first_chunk.decode('utf-8')
        
        message += first_chunk

        while True:
            chunk = conn.recv(4096)
            if not chunk:
                raise ConnectionError("Connection lost while receiving data")
            message += chunk
            if "[END]".encode('utf-8') in message:
                break
        return message.decode('utf-8').replace("[END]", '').replace("[TABLE]", '')
    except Exception:
        print("Receive message error.")
        return
        # client_socket.close()

try: 
    while True: 
        # Keep receiving and sending message with server. 
        # Different types of message have different tags, such as [EXIT], [INPUT], [CSV], [PLOT]
        # If the message does not have any tag, it will be displayed directly.
    
        recv_msg = receive_message(client_socket)
        
        if not recv_msg:
            print("Connection closed by the server.")
            break
        
        if recv_msg.find("[EXIT]") != -1:
            print(recv_msg.replace("[EXIT]", ''), end='')
            break
        
        if recv_msg.find("[CSV]") != -1:
            print(recv_msg.replace("[CSV]", '').replace("[INPUT]", ''), end='')
            
            filename = input().strip() 
            if not isfile(filename) or filename.find(".csv") == -1:
                print(f'File \'{filename}\' is not found or is not a csv file.')
                client_socket.send("[NOTFOUND]".encode('utf-8'))
            
            file_size = getsize(filename)
            # print(f'File \'{filename}\' found, file_size = {file_size}')
            client_socket.send(str(file_size).encode())
        
            # Wait for server response
            client_socket.recv(1024)
            print(f'Start transferring file...')

            with open(filename, 'rb') as f:
                while (chunk := f.read(1024)):
                    client_socket.send(chunk)
            print(f'File \'{filename}\' sent successfully.')
        
        elif recv_msg.find("[INPUT]") != -1:
            print(recv_msg.replace("[INPUT]", ''), end='')

            send_msg = input().strip()
            while len(send_msg) == 0:
                print("Input cannot be empty. Please enter again:", end=' ')
                send_msg = input().strip()

            if send_msg == "exit":
                break            
            client_socket.send(send_msg.encode('utf-8'))
        
        elif recv_msg.find("[PLOT]") != -1:
            print(recv_msg.replace("[PLOT]", ''), end='')  # 顯示訊息內容
            data = defaultdict(list)

            # 解析接收到的資料
            for line in recv_msg.split('\n'):
                line = line.strip()  # 去除首尾空白字符
                #print(f"line: {line}")
                if len(line) == 0:
                    continue  # 跳過空行
                # 確保這一行有兩個部分，避免格式錯誤
                if ',' in line:
                    key, value = line.split(',')
                    try:
                        data[key] = int(value)
                    except ValueError:
                        #print(f"警告: 無法將 '{value}' 轉換為數字")
                        continue  # 如果轉換失敗，跳過這一行
                else:
                    pass
            
            print(data)

            # 解析時間和對應的值
            times = [datetime.strptime(key, '%Y-%m-%d') for key in data.keys()]
            values = list(data.values())

            # 創建圖表
            fig, ax = plt.subplots()

            # 繪製時間對應的數值
            ax.plot(times, values, label="Visitors")

            # 設定日期格式
            ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d %H'))

            # 自動旋轉 x 軸標籤，避免重疊
            plt.xticks(rotation=45)

            # 顯示圖例
            ax.legend()

            # 顯示圖表
            plt.tight_layout()  # 防止標籤被裁剪
            plt.show()
        
        else:
            # message without any tag
            print(recv_msg, end='')
        
finally:
    print("Connection close.")
    client_socket.close()