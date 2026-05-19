import socket
import json
import sqlite3
import os
from datetime import datetime

HOST = '0.0.0.0'
PORT = 8812

# 儲存路徑
SAVE_PATH = "/home/pi/Desktop/Robot1_Aciton/"

def save_action_group(table_widget, chinese=False):
    if len(table_widget) == 0:
        if chinese:
            print('動作列表是空的哦，沒有能保存的')
        else:
            print('The action list is empty, nothing to save')
        return None

    now = datetime.now()
    filename = f"{now.year}_{now.month}_{now.day}_{now.hour}_{now.minute}_{now.second}.d6a"
    path = os.path.join(SAVE_PATH, filename)
    
    if os.path.isfile(path):
        os.remove(path)

    try:
        conn = sqlite3.connect(path)
        c = conn.cursor()
        
        c.execute('''CREATE TABLE ActionGroup(
            [Index] INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL ON CONFLICT FAIL UNIQUE ON CONFLICT ABORT,
            Time INT,
            Servo1 INT,
            Servo2 INT,
            Servo3 INT,
            Servo4 INT,
            Servo5 INT,
            Servo6 INT,
            Servo7 INT,
            Servo8 INT,
            Servo9 INT,
            Servo10 INT,
            Servo11 INT,
            Servo12 INT,
            Servo13 INT,
            Servo14 INT,
            Servo15 INT,
            Servo16 INT);''')
        
        for row in table_widget:
            insert_sql = "INSERT INTO ActionGroup(Time, Servo1, Servo2, Servo3, Servo4, Servo5, Servo6, Servo7, Servo8, Servo9, Servo10, Servo11, Servo12, Servo13, Servo14, Servo15, Servo16) VALUES ("
            insert_sql += ", ".join(map(str, row))
            insert_sql += ");"
            c.execute(insert_sql)
        
        conn.commit()
        conn.close()
        print(f"動作檔案已儲存: {path}")
        return path
    except Exception as e:
        print(f"儲存錯誤: {e}")
        return None

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server.bind((HOST, PORT))
        server.listen(1)
        print(f"=== Pi 伺服器啟動 ===\n等待連線中 (Port: {PORT})...")

        while True:
            conn, addr = server.accept()
            print(f"連線成功! 來自: {addr}")

            buffer = ""
            while True:
                try:
                    data = conn.recv(4096)
                    if not data:
                        break
                    
                    buffer += data.decode('utf-8')

                    if "\n" in buffer:
                        messages = buffer.split("\n")
                        
                        for msg in messages[:-1]:
                            if not msg: continue
                            
                            try:
                                trajectory = json.loads(msg)
                                print(f"收到軌跡數據，共 {len(trajectory)} 幀")
                                
                                for i, frame in enumerate(trajectory):
                                    print(f"Frame {i}: {frame}")
                                
                                saved_path = save_action_group(trajectory, chinese=True)
                                if saved_path:
                                    print(f"已自動儲存軌跡到: {saved_path}")
                                    
                            except json.JSONDecodeError:
                                print("JSON 解析錯誤")
                        
                        buffer = messages[-1]

                except Exception as e:
                    print(f"傳輸錯誤: {e}")
                    break
            
            print("連線斷開，重新等待...")
            conn.close()

    except KeyboardInterrupt:
        print("伺服器關閉。")
    finally:
        server.close()

if __name__ == "__main__":
    start_server()
