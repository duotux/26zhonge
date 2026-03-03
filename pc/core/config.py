# ============================================================
#  PC 端全局配置 — core/config.py
# ============================================================
import os

# ── 网络 ─────────────────────────────────────────────────
UDP_VIDEO_PORT   = 5600   # 接收 ESP32 视频帧
TCP_CMD_PORT     = 5601   # 向 ESP32 发送指令（每台设备一条连接）
UDP_HB_PORT      = 5602   # 接收心跳包

# ── AI 推理 ───────────────────────────────────────────────
MODEL_PATH       = "models/lab_safety.pt"   # 训练好的 YOLOv8n 权重
CONF_THRESHOLD   = 0.70   # 置信度阈值
CONSECUTIVE_FRAMES = 3    # 连续 N 帧触发预警

# 违规类别及其默认预警等级
VIOLATION_LEVELS = {
    "no_goggles":    1,   # 未戴护目镜
    "no_labcoat":    1,   # 未穿实验服
    "no_gloves":     1,   # 未戴手套
    "open_fire":     2,   # 违规明火
    "absent":        2,   # 人员离岗
    "hazmat_mix":    3,   # 危化品混放
    "waste_pour":    3,   # 违规倾倒废液
    "unauthorized":  3,   # 非授权人员
}

# ── 数据库 ────────────────────────────────────────────────
DB_PATH  = "db/lab_safety.db"

# ── 路径 ─────────────────────────────────────────────────
LOG_DIR      = "logs"
RECORD_DIR   = "records"    # 违规截图 / 视频片段保存路径
AUDIO_DIR    = "assets/audio"

# ── 心跳超时（秒），超过则标记设备离线 ─────────────────────
DEVICE_TIMEOUT = 8

# ── 界面语言默认值（zh / ru） ─────────────────────────────
DEFAULT_LANG = "zh"
