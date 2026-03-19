# ============================================================
#  PC 端全局配置 — core/config.py
# ============================================================
import os

# ── 网络 ─────────────────────────────────────────────────
UDP_VIDEO_PORT   = 5600   # 接收 ESP32 视频帧
TCP_CMD_PORT     = 5601   # 向 ESP32 发送指令（每台设备一条连接）
UDP_HB_PORT      = 5602   # 接收心跳包
TCP_AUDIO_PORT   = 5603   # 音频文件流式传输

# ── AI 推理 ───────────────────────────────────────────────
MODEL_PATH       = "models/best.pt"   # 训练好的 YOLOv8n 权重
CONF_THRESHOLD   = 0.50   # 置信度阈值
CONSECUTIVE_FRAMES = 3    # 连续 N 帧触发预警

# 违规类别及其默认预警等级（只保留 2 个报警）
VIOLATION_LEVELS = {
    "open_fire":     2,   # 违规明火 → 二级预警
    "absent":        3,   # 人员离岗 → 三级预警（重大风险）
}

# ── 数据库 ────────────────────────────────────────────────
DB_PATH  = "db/lab_safety.db"

# ── 路径 ─────────────────────────────────────────────────
LOG_DIR      = "logs"
RECORD_DIR   = "records"    # 违规截图 / 视频片段保存路径
AUDIO_DIR    = "assets/audio"
AUDIO_FILES_PATH = os.path.join(os.path.dirname(__file__), "..", AUDIO_DIR)  # 音频文件目录

# ── 心跳超时（秒），超过则标记设备离线 ─────────────────────
DEVICE_TIMEOUT = 8

# ── 界面语言默认值（zh / ru） ─────────────────────────────
DEFAULT_LANG = "zh"
