import json
import socket
import os
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR)  

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

class RobotDriver:
    def __init__(self):
        self.pi_ip = os.getenv("PI_IP")
        self.pi_port = int(os.getenv("PI_PORT"))
        
        self.sock = None
        self.is_connected = False

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.pi_ip, self.pi_port))
            self.is_connected = True
            print(f"已連線至機器人 ({self.pi_ip}:{self.pi_port})")
            return True
        except Exception as e:
            print(f"連線失敗: {e}")
            self.is_connected = False
            return False

    def disconnect(self):
        if self.sock:
            try:
                self.sock.close()
            except:
                pass
        self.is_connected = False
        print("已斷開連線")

    def send_trajectory(self, action_sequence, ask_before_send=True):
        if not action_sequence:
            print("沒有動作序列可傳送")
            return False

        print("-" * 60)
        print(f"動作序列預覽 (共 {len(action_sequence)} 幀):")
        for i, frame in enumerate(action_sequence[:]):  
            print(f"  幀 {i+1}: {frame}")
        print("-" * 60)

        # 詢問是否傳送
        if ask_before_send:
            try:
                user_input = input("\n是否傳送到機器人? (y/N): ").strip().lower()
                if user_input not in ['y', 'yes']:
                    print("已取消傳送")
                    return False
            except EOFError:
                print("跳過傳送")
                return False

        if not self.is_connected:
            if not self.connect():
                return False

        return self._send_data(action_sequence)

    def _send_data(self, action_sequence):
        try:
            trajectory_batch = []
            for frame in action_sequence:
                if len(frame) == 16:
                    frame_with_header = [500] + [int(v) for v in frame]
                    trajectory_batch.append(frame_with_header)
                else:
                    print(f"警告: 幀長度不正確 ({len(frame)}), 跳過")
            
            if not trajectory_batch:
                print("沒有有效的幀可傳送")
                return False

            json_str = json.dumps(trajectory_batch)
            message = json_str + "\n"
            
            self.sock.sendall(message.encode('utf-8'))
            print(f"已發送 {len(trajectory_batch)} 幀數據至機器人")
            return True
            
        except Exception as e:
            print(f"發送失敗: {e}")
            self.is_connected = False
            return False

    def send_single_frame(self, frame):
        return self.send_trajectory([frame], ask_before_send=False)


if __name__ == "__main__":
    driver = RobotDriver()
    print(f"機器人 IP: {driver.pi_ip}")
    print(f"機器人 Port: {driver.pi_port}")
    
    test_frame = [500, 386, 501, 594, 498, 574, 801, 725, 498, 613, 500, 404, 502, 424, 199, 276]
    driver.send_trajectory([test_frame])