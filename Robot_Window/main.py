from l1_llm_generate_action import MotionGenerator
from l2_tcp_socket_translate_action_value import RobotDriver

generator = MotionGenerator()
driver = RobotDriver()

print("-" * 30)
print(f"使用的模型：{generator.model}")
print("輸入 'exit' 可結束程式")
print("-" * 30)

try:
    while True:
        user_input = input("\nUser: ").strip()

        if not user_input:
            continue

        if user_input.lower() in ['exit', 'quit', 'q']:
            break

        action_sequence = generator.execute_command(user_input)
        
        if action_sequence:
            driver.send_trajectory(action_sequence)

except KeyboardInterrupt:
    print("偵測到強制中斷。")
except Exception as e:
    print(f"系統錯誤: {e}")