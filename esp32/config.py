# ============================================================
#  ESP32 终端配置文件 — config.py
#  校园实验室安全智能管控系统
# ============================================================

# ---------- WiFi 连接配置 ----------
WIFI_SSID     = "ceshi123"   # PC 热点名称
WIFI_PASSWORD = "12345678"      # PC 热点密码

# ---------- 静态 IP 配置（避免 DHCP 导致 IP 漂移） ----------
STATIC_IP      = "192.168.137.121"
SUBNET_MASK    = "255.255.255.0"
GATEWAY        = "192.168.137.1"
DNS_SERVER     = "192.168.137.1"

# ---------- PC 端地址与端口 ----------
PC_IP          = "192.168.137.1"   # PC 热点网关即为 PC 本机地址
UDP_PORT       = 5600              # 视频帧上行（ESP32→PC）UDP 端口
TCP_PORT       = 5601              # 指令下行（PC→ESP32）TCP 端口
HEARTBEAT_PORT = 5602              # 心跳包端口（UDP）

# ---------- 摄像头配置（优化帧率和稳定性） ----------
CAM_FRAMESIZE  = 5     # FRAMESIZE_QVGA = 5 → 320×240（节省内存，提高帧率）
CAM_QUALITY    = 35    # JPEG 质量 0-63，增大数值降低大小，推荐 30-40（平衡质量和速度）
CAM_FPS        = 10    # 目标帧率（QVGA 分辨率下可达 10-15FPS）

# ---------- 音频配置（I2S → MAX98357A） ----------
I2S_BCK_PIN    = 41    # I2S 时钟引脚
I2S_WS_PIN     = 42    # I2S 字节时钟
I2S_DATA_PIN   = 40    # I2S 数据输出引脚
AUDIO_RATE     = 24000  # 采样率 24kHz（与音频文件一致）

# ---------- 预警指令映射（只保留 2 个报警） ----------
WARN_CMD_MAP = {
    b"warn2": "/audio/warn2.wav",   # 请勿违规操作明火
    b"warn3": "/audio/warn3.wav",   # 危险！无人值守
    b"warn2_ru": "/audio/warn2_ru.wav",
    b"warn3_ru": "/audio/warn3_ru.wav",
    b"stop":  None,                 # 停止当前播报
}

# ---------- 心跳间隔（秒） ----------
HEARTBEAT_INTERVAL = 2

# ---------- 帧分包大小（字节） ----------
CHUNK_SIZE = 1400   # UDP MTU 安全上限
