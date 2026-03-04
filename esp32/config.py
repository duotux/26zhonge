# ============================================================
#  ESP32 终端配置文件 — config.py
#  校园实验室安全智能管控系统
# ============================================================

# ---------- WiFi 连接配置 ----------
WIFI_SSID     = "Xiaomi_DE8E"   # PC 热点名称
WIFI_PASSWORD = "123456789"      # PC 热点密码

# ---------- 静态 IP 配置（避免 DHCP 导致 IP 漂移） ----------
STATIC_IP      = "192.168.137.10"
SUBNET_MASK    = "255.255.255.0"
GATEWAY        = "192.168.137.1"
DNS_SERVER     = "192.168.137.1"

# ---------- PC 端地址与端口 ----------
PC_IP          = "192.168.137.1"   # PC 热点网关即为 PC 本机地址
UDP_PORT       = 5600              # 视频帧上行（ESP32→PC）UDP 端口
TCP_PORT       = 5601              # 指令下行（PC→ESP32）TCP 端口
HEARTBEAT_PORT = 5602              # 心跳包端口（UDP）

# ---------- 摄像头配置 ----------
CAM_FRAMESIZE  = 5     # FRAMESIZE_QVGA = 5 → 320×240
CAM_QUALITY    = 12    # JPEG 质量 0-63，数值越小质量越高，推荐 10-15
CAM_FPS        = 12    # 目标帧率

# ---------- 音频配置（I2S → MAX98357A） ----------
I2S_BCK_PIN    = 26    # I2S 时钟引脚
I2S_WS_PIN     = 25    # I2S 字节时钟
I2S_DATA_PIN   = 22    # I2S 数据输出引脚
AUDIO_RATE     = 8000  # 采样率 8kHz

# ---------- 预警指令映射 ----------
WARN_CMD_MAP = {
    b"warn1": "/audio/warn1.wav",   # 请规范佩戴护目镜和实验服
    b"warn2": "/audio/warn2.wav",   # 请勿违规操作明火
    b"warn3": "/audio/warn3.wav",   # 危险！无人值守
    b"warn1_ru": "/audio/warn1_ru.wav",  # 俄语版
    b"warn2_ru": "/audio/warn2_ru.wav",
    b"warn3_ru": "/audio/warn3_ru.wav",
    b"stop":  None,                 # 停止当前播报
}

# ---------- 心跳间隔（秒） ----------
HEARTBEAT_INTERVAL = 2

# ---------- 帧分包大小（字节） ----------
CHUNK_SIZE = 1400   # UDP MTU 安全上限
