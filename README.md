# 機器人動作生成系統

使用 LLM (Ollama) 將自然語言指令轉換為機器人動作序列，並透過 TCP 傳送到 Raspberry Pi 控制的人形機器人。

## 專案結構

```
├── .env                    # 環境設定檔
├── README.md
├── dataset/
│   └── lang2motion.json    # 動作參考資料集
├── Robot_Window/           # Windows 端程式
│   ├── main.py                              # 主程式入口
│   ├── l1_llm_generate_action.py            # LLM 動作生成
│   └── l2_tcp_socket_translate_action_value.py  # TCP 傳送
└── Robot_Raspberry/        # Raspberry Pi 端程式
    └── pi_action.py        # 接收並執行動作
```

## 環境設定

### 1. 建立 `.env` 檔案

在專案根目錄建立 `.env` 檔案：

```env
# Ollama 設定 (如果沒有 GPU 可以留空)
OLLAMA_URL = "http://localhost:11434/api/generate"
OLLAMA_PORT = 11434
model = "qwen3:8b"

# Raspberry Pi 連線設定
PI_IP = "172.20.10.6"
PI_PORT = 8812
```

### 2. 參數說明

| 參數 | 說明 | 範例 |
|------|------|------|
| `OLLAMA_URL` | Ollama API 位址 | `http://localhost:11434/api/generate` |
| `OLLAMA_PORT` | Ollama 連接埠 | `11434` |
| `model` | 使用的 LLM 模型 | `qwen3:8b`, `llama3`, `mistral` |
| `PI_IP` | Raspberry Pi 的 IP 位址 | `172.20.10.6` |
| `PI_PORT` | Pi 監聽的連接埠 | `8812` |

## 安裝

### Windows 端

```bash
# 安裝 Python 套件
pip install requests python-dotenv
```

### Raspberry Pi 端

```bash
# 確保有安裝 Python 3
sudo apt update
sudo apt install python3
```

### Ollama (選用，需要 GPU)

```bash
# 安裝 Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 下載模型
ollama pull qwen3:8b
```

## 使用方式

### 步驟 1：啟動 Raspberry Pi 伺服器

在 Raspberry Pi 上執行：

```bash
cd Robot_Raspberry
python3 pi_action.py
```

輸出：
```
=== Pi 伺服器啟動 ===
等待連線中 (Port: 8812)...
```

### 步驟 2：啟動 Windows 主程式

在 Windows 上執行：

```bash
cd Robot_Window
python main.py
```

輸出：
```
偵測到 GPU
------------------------------
使用的模型：qwen3:8b
輸入 'exit' 可結束程式
------------------------------
```

### 步驟 3：輸入指令

```
User: 右手慢慢舉起

正在推理: '右手慢慢舉起' ...
回應: {"command": "右手緩慢舉起", "action_sequence": [[500,386,...], ...]}
生成了 20 幀動作
------------------------------------------------------------
動作序列預覽 (共 20 幀):
  幀 1: [500, 386, 501, 594, ...]
  幀 2: [500, 386, 501, 594, ...]
  ...
------------------------------------------------------------

是否傳送到機器人? (y/N): y
已連線至機器人 (172.20.10.6:8812)
已發送 20 幀數據至機器人
```

## 支援的指令範例

| 指令 | 說明 |
|------|------|
| `右手舉起` | 右手快速舉起 |
| `左手緩慢舉起` | 左手慢慢舉起 (較多幀數) |
| `雙手舉起` | 同時舉起雙手 |
| `蹲下` | 機器人蹲下 |
| `前進` | 向前走一步 |

## GPU 偵測邏輯

| GPU 狀態 | OLLAMA_URL | 行為 |
|----------|------------|------|
| ✅ 有 GPU | ✅ 已設定 | 正常使用 Ollama 推理 |
| ✅ 有 GPU | ❌ 未設定 | 顯示警告，無法推理 |
| ❌ 無 GPU | ✅ 已設定 | 使用 CPU 執行 Ollama |
| ❌ 無 GPU | ❌ 未設定 | 跳過 LLM，程式仍可執行 |

## 動作資料格式

每個動作由 16 個伺服馬達數值組成 (範圍 0-1000，500 為中位)：

```json
{
  "command": "右手舉起",
  "action_sequence": [
    [500, 386, 501, 594, 498, 574, 801, 725, 498, 613, 500, 404, 502, 424, 199, 276],
    [500, 386, 501, 594, 498, 574, 801, 725, 498, 613, 500, 404, 502, 424, 199, 380],
    ...
  ]
}
```

### 馬達索引對應

| 索引 | 部位 |
|------|------|
| 0 | 身體左右傾斜 |
| 1-4 | 左腿關節 |
| 5-6 | 軀幹/腰部 |
| 7 | 左手臂 (0=舉高, 1000=放下) |
| 8-11 | 右腿關節 |
| 12-14 | 頭部/頸部 |
| 15 | 右手臂 (0=放下, 1000=舉高) |

## 疑難排解

### 連線失敗
- 確認 Pi 和 Windows 在同一網路
- 檢查 `.env` 中的 `PI_IP` 是否正確
- 確認 Pi 上的 `pi_action.py` 正在執行

### Ollama 錯誤
- 確認 Ollama 服務已啟動：`ollama serve`
- 確認模型已下載：`ollama list`
- 檢查 `OLLAMA_URL` 設定

### 無法偵測 GPU
- 確認已安裝 NVIDIA 驅動程式
- 執行 `nvidia-smi` 確認 GPU 狀態

### Email資訊
- s11427602@gm.cyut.edu.tw
