# ============================================================
#  分级预警管理器 — core/alert_manager.py
#  负责：分级处置、截图存档、下发指令给 ESP32
# ============================================================
import os
import cv2
import threading
from datetime import datetime
from core.config import RECORD_DIR
from core.cmd_sender import CmdSender

# 违规类别 → 对应 ESP32 播报指令（只保留 2 个报警）
# 注意：类别名称必须与 YOLOv8 模型训练时的标签一致！
CMD_MAP = {
    "Fire":      "warn2",   # 火焰 → 请勿违规操作明火
    "Smoke":     "warn2",   # 烟雾 → 请勿违规操作明火
}

# 预警等级中文说明（只保留 2 个等级）
LEVEL_DESC = {
    2: "二级预警（中度风险）",
    3: "三级预警（重大风险）",
}


class AlertManager:
    """
    预警处置：
      1. 保存违规截图
      2. 通过 CmdSender 向对应 ESP32 下发语音播报指令
      3. 回调通知 UI 刷新（on_alert_cb）
    """

    def __init__(self, cmd_sender: CmdSender,
                 db=None, on_alert_cb=None):
        """
        cmd_sender : CmdSender 实例
        db         : Database 实例（可为 None）
        on_alert_cb: fn(event_dict) — 由 UI 监听，用于弹窗/列表刷新
        """
        self._sender     = cmd_sender
        self._db         = db
        self._on_alert   = on_alert_cb
        self._lock       = threading.Lock()
        os.makedirs(RECORD_DIR, exist_ok=True)

    def handle(self, device_ip: str, class_name: str,
               level: int, frame, detections: list):
        """由 AIEngine 的 on_alert 回调触发（在 AI 推理线程中）"""
        threading.Thread(
            target=self._process,
            args=(device_ip, class_name, level, frame, detections),
            daemon=True
        ).start()

    def _process(self, device_ip, class_name, level, frame, detections):
        """处理预警的后台线程函数（增强错误处理）"""
        try:
            ts  = datetime.now()
            ts_str = ts.strftime("%Y%m%d_%H%M%S")
    
            # 1. 保存截图（增加错误处理）
            img_path = ""
            try:
                img_path = os.path.join(
                    RECORD_DIR,
                    f"{ts_str}_{device_ip.replace('.','_')}_{class_name}.jpg"
                )
                # 确保目录存在
                os.makedirs(os.path.dirname(img_path), exist_ok=True)
                    
                # 检查 frame 是否有效
                if frame is None or frame.size == 0:
                    print(f"[Alert] 警告：帧数据为空，跳过截图保存")
                else:
                    cv2.imwrite(img_path, frame)
                    print(f"[Alert] 截图已保存：{img_path}")
            except Exception as e:
                print(f"[Alert] 截图保存失败：{e}")
                img_path = ""
    
            # 2. 构造事件字典
            event = {
                "ts":         ts.isoformat(timespec="seconds"),
                "device_ip":  device_ip,
                "class_name": class_name,
                "level":      level,
                "level_desc": LEVEL_DESC.get(level, ""),
                "img_path":   img_path,
                "conf":       max((d["conf"] for d in detections
                                   if d["class"] == class_name), default=0.0),
            }
    
            # 3. 写入数据库（如果数据库可用）
            if self._db:
                try:
                    self._db.insert_event(event)
                except Exception as e:
                    print(f"[AlertManager] 数据库写入失败：{e}")
    
            # 4. 下发 ESP32 指令
            cmd   = CMD_MAP.get(class_name, "warn2")
            try:
                self._sender.send(device_ip, cmd, level)
                print(f"[CmdSender] 指令已发送：{cmd} to {device_ip}")
            except Exception as e:
                print(f"[AlertManager] 指令发送失败：{e}")
    
            print(f"[Alert] {event['level_desc']} | {device_ip} | {class_name}")
    
            # 5. 通知 UI（在独立线程中）
            if self._on_alert:
                try:
                    self._on_alert(event)
                except Exception as e:
                    print(f"[AlertManager] UI 通知失败：{e}")
                        
        except Exception as e:
            print(f"[AlertManager] 处理异常：{type(e).__name__}: {e}")
