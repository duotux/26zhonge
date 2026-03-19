# ============================================================
#  AI 推理引擎 — core/ai_engine.py
#  YOLOv8n 实时检测实验室违规行为
#  依赖：ultralytics >= 8.0
# ============================================================
import cv2
import numpy as np
import threading
import time
import os
from collections import defaultdict
from datetime import datetime
from core.config import (MODEL_PATH, CONF_THRESHOLD,
                          CONSECUTIVE_FRAMES, VIOLATION_LEVELS, RECORD_DIR)

try:
    from ultralytics import YOLO
    _YOLO_OK = True
except ImportError:
    _YOLO_OK = False
    print("[AIEngine] 警告：未安装 ultralytics，以 Demo 模式运行")

# 违规类别多语言标签（只保留 2 个报警）
# 注意：类别名称必须与 YOLOv8 模型训练时的标签一致！
CLASS_LABELS = {
    "Fire":  {"zh": "火焰",       "ru": "Огонь"},
    "Smoke": {"zh": "烟雾",       "ru": "Дым"},
}

# 预警等级 → (BGR 颜色，中文标题)（只保留 2 个等级）
LEVEL_STYLE = {
    2: ((0, 140, 255), "二级预警"),
    3: ((0, 0, 255),   "三级预警"),
}


class AIEngine:
    """
    多设备 AI 推理引擎。
    每路设备独立计数器，连续 CONSECUTIVE_FRAMES 帧确认后触发预警回调。
    on_alert(device_ip, class_name, level, frame_bgr, boxes)
    """

    def __init__(self, on_alert=None, lang="zh"):
        self.lang = lang
        self.on_alert = on_alert
        self._model = None
        self._lock  = threading.Lock()
        # 每路设备的连续帧计数 {ip: {class_name: count}}
        self._consec = defaultdict(lambda: defaultdict(int))
        # 已触发（冷却中）的违规 {ip: {class_name: last_trigger_ts}}
        self._cooldown = defaultdict(dict)
        self.COOLDOWN_SEC = 8   # 同一违规 8 秒内不重复触发
        self._load_model()

    def _load_model(self):
        if not _YOLO_OK:
            return
        path = MODEL_PATH
        if not os.path.exists(path):
            print(f"[AIEngine] 自训练权重不存在，加载 yolov8n.pt 演示")
            path = "yolov8n.pt"
        self._model = YOLO(path)
        print(f"[AIEngine] 模型加载完成: {path}")

    def infer(self, device_ip: str, frame: np.ndarray):
        """
        推理一帧，返回标注后的图像和检测结果列表。
        result_list: [{"class": str, "conf": float, "box": [x1,y1,x2,y2], "level": int}]
        """
        if self._model is None:
            return frame, []

        with self._lock:
            results = self._model(frame, conf=CONF_THRESHOLD,
                                   verbose=False, stream=False)

        annotated = frame.copy()
        detections = []
        detected_classes = set()
        
        # 调试：统计所有检测结果
        all_detections = []

        for r in results:
            if r.boxes is None:
                continue
            for box in r.boxes:
                cls_id = int(box.cls[0])
                conf   = float(box.conf[0])
                name   = self._model.names.get(cls_id, str(cls_id))
                
                # 调试：记录所有检测到的目标
                all_detections.append({"name": name, "conf": conf})
                
                # 只处理配置中的违规类别
                if name not in VIOLATION_LEVELS:
                    # 调试：打印未配置的类别（仅当检测到火焰时）
                    if "fire" in name.lower() or "flame" in name.lower():
                        print(f"[DEBUG] 检测到火焰但未配置：{name} (置信度：{conf:.2f})")
                    continue
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                level  = VIOLATION_LEVELS.get(name, 1)
                color  = LEVEL_STYLE[level][0]
                label  = CLASS_LABELS.get(name, {}).get(self.lang, name)

                # 绘制标注框
                cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)
                cv2.putText(annotated,
                            f"{label} {conf:.0%}",
                            (x1, max(y1 - 8, 0)),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)

                detections.append({"class": name, "conf": conf,
                                    "box": [x1, y1, x2, y2], "level": level})
                detected_classes.add(name)
        
        # 调试：打印检测结果（每 10 帧打印一次）
        if len(all_detections) > 0 and len(detections) == 0:
            print(f"[DEBUG] 检测到 {len(all_detections)} 个目标，但无违规类别:")
            for det in all_detections[:5]:  # 只显示前 5 个
                print(f"  - {det['name']} (置信度：{det['conf']:.2f})")
        elif len(detections) > 0:
            print(f"[AI] 检测到违规行为：{detections}")

        # 连续帧计数 + 预警触发
        for cls in detected_classes:
            self._consec[device_ip][cls] += 1
            if self._consec[device_ip][cls] >= CONSECUTIVE_FRAMES:
                self._consec[device_ip][cls] = 0
                self._maybe_alert(device_ip, cls, annotated, detections)
        # 未检测到的类别重置计数
        for cls in list(self._consec[device_ip].keys()):
            if cls not in detected_classes:
                self._consec[device_ip][cls] = 0

        return annotated, detections

    def _maybe_alert(self, device_ip, class_name, frame, detections):
        now = time.time()
        last = self._cooldown[device_ip].get(class_name, 0)
        if now - last < self.COOLDOWN_SEC:
            return
        self._cooldown[device_ip][class_name] = now
        level = VIOLATION_LEVELS.get(class_name, 1)
        print(f"[AIEngine] 触发预警 device={device_ip} "
              f"class={class_name} level={level}")
        if self.on_alert:
            self.on_alert(device_ip, class_name, level, frame.copy(), detections)

    def set_lang(self, lang: str):
        self.lang = lang
