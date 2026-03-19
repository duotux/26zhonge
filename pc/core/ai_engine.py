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
                          CONSECUTIVE_FRAMES, VIOLATION_LEVELS, RECORD_DIR,
                          PERSON_MODEL_PATH, PERSON_CONF_THRESHOLD, PERSON_CLASSES,
                          PERSON_ABSENT_SEC)

try:
    from ultralytics import YOLO
    _YOLO_OK = True
except ImportError:
    _YOLO_OK = False
    print("[AIEngine] 警告：未安装 ultralytics，以 Demo 模式运行")

# 违规类别多语言标签（包含人员检测）
# 注意：类别名称必须与 YOLOv8 模型训练时的标签一致！
CLASS_LABELS = {
    "Fire":  {"zh": "火焰",       "ru": "Огонь"},
    "Smoke": {"zh": "烟雾",       "ru": "Дым"},
    "Person": {"zh": "人员",      "ru": "Человек"},
}

# 预警等级 → (BGR 颜色，中文标题)（只保留 2 个等级）
LEVEL_STYLE = {
    2: ((0, 140, 255), "二级预警"),
    3: ((0, 0, 255),   "三级预警"),
}


class AIEngine:
    """
    多设备 AI 推理引擎（支持双模型）。
    - 主模型：检测 Fire 和 Smoke
    - 人员模型：检测 Person（离岗检测）
    
    每路设备独立计数器，连续 CONSECUTIVE_FRAMES 帧确认后触发预警回调。
    on_alert(device_ip, class_name, level, frame_bgr, boxes)
    """

    def __init__(self, on_alert=None, lang="zh"):
        self.lang = lang
        self.on_alert = on_alert
        self._model = None          # 主模型（Fire + Smoke）
        self._person_model = None   # 人员检测模型
        self._lock  = threading.Lock()
        # 每路设备的连续帧计数 {ip: {class_name: count}}
        self._consec = defaultdict(lambda: defaultdict(int))
        # 已触发（冷却中）的违规 {ip: {class_name: last_trigger_ts}}
        self._cooldown = defaultdict(dict)
        # 人员离岗计时器 {ip: last_person_seen_time}
        self._person_absent_timer = defaultdict(lambda: None)
        self.COOLDOWN_SEC = 8   # 同一违规 8 秒内不重复触发
        self.PERSON_ABSENT_SEC = PERSON_ABSENT_SEC  # 人员消失 30 秒后触发警报（从配置读取）
        self._load_models()

    def _load_models(self):
        """加载双模型：主模型 + 人员检测模型"""
        if not _YOLO_OK:
            return
                
        # 加载主模型（Fire + Smoke）
        path = MODEL_PATH
        if not os.path.exists(path):
            print(f"[AIEngine] 自训练权重不存在，加载 yolov8n.pt 演示")
            path = "yolov8n.pt"
        self._model = YOLO(path)
        print(f"[AIEngine] 主模型加载完成：{path}")
            
        # 加载人员检测模型（COCO 预训练）
        person_path = PERSON_MODEL_PATH
        if os.path.exists(person_path):
            try:
                self._person_model = YOLO(person_path)
                print(f"[AIEngine] 人员检测模型加载完成：{person_path}")
            except Exception as e:
                print(f"[AIEngine] 人员模型加载失败：{e}")
                self._person_model = None
        else:
            print(f"[AIEngine] 人员模型文件不存在：{person_path}")
            self._person_model = None

    def infer(self, device_ip: str, frame: np.ndarray):
        """
        推理一帧，返回标注后的图像和检测结果列表。
        result_list: [{"class": str, "conf": float, "box": [x1,y1,x2,y2], "level": int}]
        使用双模型：主模型检测 Fire/Smoke，人员模型检测 Person
        """
        if self._model is None and self._person_model is None:
            return frame, []

        annotated = frame.copy()
        detections = []
        detected_classes = set()
        
        # 调试：统计所有检测结果
        all_detections = []

        # ========== 1. 主模型推理（Fire + Smoke） ==========
        if self._model is not None:
            with self._lock:
                results = self._model(frame, conf=CONF_THRESHOLD,
                                       verbose=False, stream=False)

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

                    # 只绘制标注框，不添加文字标注
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

                    detections.append({"class": name, "conf": conf,
                                        "box": [x1, y1, x2, y2], "level": level})
                    detected_classes.add(name)
        
        # ========== 2. 人员模型推理（Person） ==========
        if self._person_model is not None:
            with self._lock:
                person_results = self._person_model(frame, conf=PERSON_CONF_THRESHOLD,
                                                    classes=PERSON_CLASSES,
                                                    verbose=False, stream=False)
            
            # 更新人员出现时间
            current_time = time.time()
            person_detected = False
            
            for r in person_results:
                if r.boxes is None:
                    continue
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf   = float(box.conf[0])
                    # COCO 数据集类别 0 是 person
                    name = "Person"
                    
                    # 调试：记录人员检测结果
                    all_detections.append({"name": name, "conf": conf})
                    
                    # 检查是否配置了人员检测
                    if name not in VIOLATION_LEVELS:
                        continue
                    
                    x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                    level  = VIOLATION_LEVELS.get(name, 1)
                    color  = LEVEL_STYLE[level][0]

                    # 只绘制标注框，不添加文字标注
                    cv2.rectangle(annotated, (x1, y1), (x2, y2), color, 2)

                    detections.append({"class": name, "conf": conf,
                                        "box": [x1, y1, x2, y2], "level": level})
                    detected_classes.add(name)
                    person_detected = True
            
            # 人员离岗逻辑：记录最后看到人员的时间
            if person_detected:
                # 检测到人员，重置计时器和计数器
                self._person_absent_timer[device_ip] = current_time
                self._consec[device_ip]["Person"] = 0  # 重置连续帧计数
            else:
                # 未检测到人员，开始计时
                # 只有之前看到过人（计时器不为 None）才开始计时
                if self._person_absent_timer[device_ip] is not None:
                    # 之前看到过人，计算消失时长
                    absent_duration = current_time - self._person_absent_timer[device_ip]
                    
                    # 只有超过 30 秒才触发警报
                    if absent_duration >= self.PERSON_ABSENT_SEC:
                        # 使用连续帧确认（防止误报）
                        self._consec[device_ip]["Person"] += 1
                        if self._consec[device_ip]["Person"] >= CONSECUTIVE_FRAMES:
                            self._consec[device_ip]["Person"] = 0
                            print(f"[ALERT] 人员离岗 {absent_duration:.1f}秒，触发警报！")
                            self._maybe_alert(device_ip, "Person", annotated, detections)
                # 如果这是第一次启动且没检测到人，不触发警报（等待首次检测到人来启动计时器）
        
        # 调试：打印检测结果（每 10 帧打印一次）
        if len(all_detections) > 0 and len(detections) == 0:
            print(f"[DEBUG] 检测到 {len(all_detections)} 个目标，但无违规类别:")
            for det in all_detections[:5]:  # 只显示前 5 个
                print(f"  - {det['name']} (置信度：{det['conf']:.2f})")
        elif len(detections) > 0:
            print(f"[AI] 检测到违规行为：{detections}")

        # 连续帧计数 + 预警触发（不包括 Person，Person 有独立的离岗计时逻辑）
        for cls in detected_classes:
            # 人员离岗检测不使用连续帧触发，而是使用离岗计时器
            if cls == "Person":
                continue  # 跳过人员的连续帧触发
            
            self._consec[device_ip][cls] += 1
            if self._consec[device_ip][cls] >= CONSECUTIVE_FRAMES:
                self._consec[device_ip][cls] = 0
                self._maybe_alert(device_ip, cls, annotated, detections)
        
        # 未检测到的类别重置计数（Person 的重置由离岗逻辑处理）
        for cls in list(self._consec[device_ip].keys()):
            if cls not in detected_classes and cls != "Person":
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
