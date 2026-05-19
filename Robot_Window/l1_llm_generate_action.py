import requests
import json
import sys
import os
import subprocess
from dotenv import load_dotenv

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(SCRIPT_DIR) 

load_dotenv(os.path.join(PROJECT_ROOT, ".env"))

def check_gpu_available():
    try:
        result = subprocess.run(['nvidia-smi'], capture_output=True, text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False

class MotionGenerator:
    def __init__(self):
        self.has_gpu = check_gpu_available()
        self.ollama_url = os.getenv("OLLAMA_URL")
        self.model = os.getenv("model")
        
        if self.has_gpu:
            print("偵測到 GPU")
            if not self.ollama_url:
                print("警告未設定 OLLAMA_URL")
        else:
            print("未偵測到 GPU，跳過 Ollama 檢查")
        
        dataset_path = os.path.join(PROJECT_ROOT, "dataset", "lang2motion.json")
        with open(dataset_path, "r", encoding="utf-8") as f:
            self.reference_motions = json.load(f)

    def get_reference_examples(self):
        examples = []
        for motion in self.reference_motions[:5]:  
            examples.append(f"動作: \"{motion['command']}\" -> action_sequence 有 {len(motion['action_sequence'])} 幀，每幀 16 個伺服馬達數值 (0-1000)")
        return "\n".join(examples)

    def ask_llm(self, user_prompt):
        if not self.ollama_url:
            if self.has_gpu:
                print("有 GPU 但未設定 OLLAMA_URL")
            else:
                print("無 GPU 且未設定 Ollama，跳過 LLM 推理")
            return None
        
        print(f"正在推理: '{user_prompt}' ...")
        
        reference_examples = self.get_reference_examples()
        sample_motion = self.reference_motions[0]
        sample_json = json.dumps(sample_motion, ensure_ascii=False, indent=2)
        
        system_instruction = f"""
        你是一個機器人動作生成器。根據使用者的指令，**創造性地**生成機器人的動作序列。

        [伺服馬達配置 - 16 個馬達]
        索引 0: 身體左右傾斜 (500=直立, <500=左傾, >500=右傾)
        索引 1-4: 左腿關節 (髖、膝、踝等)
        索引 5-6: 軀幹/腰部
        索引 7: 左手臂主關節 (0=舉高, 500=平放, 1000=放下)
        索引 8-11: 右腿關節 (髖、膝、踝等)
        索引 12-14: 頭部/頸部
        索引 15: 右手臂主關節 (0=放下, 500=平放, 1000=舉高)

        [輸出格式]
        請輸出 JSON 格式：
        - "command": 動作名稱
        - "action_sequence": 動作序列陣列，每幀 16 個整數 (0-1000)

        [動作生成原則 - 重要！]
        1. **速度控制**：
           - "快速/急速/迅速" → 幀數少 (3-5幀)，每幀變化大 (50-100)
           - "緩慢/慢慢/輕柔" → 幀數多 (15-30幀)，每幀變化小 (10-25)
           - "正常" → 中等幀數 (8-12幀)
        
        2. **方向判斷**：
           - "舉起/抬起/向上" → 數值朝目標方向遞增或遞減（根據馬達配置）
           - "放下/降下/向下" → 數值朝反方向變化
           - 你需要根據起始位置和目標位置，決定數值是增加還是減少
        
        3. **創意生成**：
           - 不要直接複製範例，要根據語意**自行計算**合理的數值
           - 起始幀通常是標準站姿：[500,386,501,594,498,574,801,725,498,613,500,404,502,424,199,276]
           - 相鄰幀之間的變化要平滑自然

        [參考格式 - 僅供了解結構，不要照抄數值]
        {reference_examples}

        [格式範例]
        {sample_json}

        請根據使用者的指令，**自行判斷**動作方向、幅度和步數，生成獨特的動作序列。
        """

        payload = {
            "model": self.model,
            "prompt": f"{system_instruction}\n\n使用者指令: {user_prompt}",
            "stream": True, 
            "format": "json",
            "options": {
                "temperature": 0.7 
            }
        }
        
        full_response_text = ""
        
        try:
            print(f"回應:", end="", flush=True)
            
            with requests.post(self.ollama_url, json=payload, stream=True) as response:
                response.raise_for_status()
                for line in response.iter_lines():
                    if line:
                        decoded_line = line.decode('utf-8')
                        chunk_json = json.loads(decoded_line)
                        token = chunk_json.get("response", "")
                        sys.stdout.write(token)
                        sys.stdout.flush()
                        full_response_text += token
                        
            print() 
            cleaned_json_str = full_response_text.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned_json_str)

        except Exception as e:
            print(f"錯誤: {e}")
            return None

    def execute_command(self, user_text):
        """生成動作序列並返回"""
        result = self.ask_llm(user_text)
        
        if result and "action_sequence" in result:
            action_sequence = result["action_sequence"]
            print(f"生成了 {len(action_sequence)} 幀動作")
            return action_sequence
        else:
            print("無法解析動作序列")
            return None

if __name__ == "__main__":
    generator = MotionGenerator()

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

            generator.execute_command(user_input)

    except KeyboardInterrupt:
        print("偵測到強制中斷。")
    except Exception as e:
        print(f"系統錯誤: {e}")