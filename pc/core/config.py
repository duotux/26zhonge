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
# 主模型：用于火焰和烟雾检测
MODEL_PATH       = "models/best.pt"   # 训练好的 YOLOv8n 权重
CONF_THRESHOLD   = 0.6   # 置信度阈值（降低到 0.25 以提高检测灵敏度）
CONSECUTIVE_FRAMES = 2    # 连续 N 帧触发预警（减少到 2 帧加快响应）

# 人员检测模型：使用 YOLOv8n COCO 预训练模型
PERSON_MODEL_PATH = "yolov8n.pt"  # COCO 预训练模型（检测人员）
PERSON_CONF_THRESHOLD = 0.6      # 人员检测置信度阈值
PERSON_CLASSES = [0]  # COCO 数据集中 'person' 的类别索引
PERSON_ABSENT_SEC = 30  # 人员消失持续时间（秒），超过后触发警报

# 违规类别及其默认预警等级（只保留 2 个报警）
# 注意：类别名称必须与 YOLOv8 模型训练时的标签一致！
VIOLATION_LEVELS = {
    "Fire":          2,   # 火焰 → 二级预警（模型输出的实际类别名）
    "Smoke":         2,   # 烟雾 → 二级预警（模型输出的实际类别名）
    "Person":        3,   # 人员离岗 → 三级预警（重大风险）
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
