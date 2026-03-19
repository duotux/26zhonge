# ============================================================
#  YOLOv8 模型诊断工具
#  用于检查模型文件、类别配置和检测能力
# ============================================================
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'pc'))

print("=" * 60)
print("YOLOv8 模型诊断工具")
print("=" * 60)
print()

# 1. 检查模型文件
print("1. 检查模型文件...")
model_paths = [
    'pc/models/best.pt',
    'models/best.pt',
    'pc/yolov8n.pt',
    'yolov8n.pt'
]

found_model = None
for path in model_paths:
    if os.path.exists(path):
        print(f"  ✓ 找到模型：{path} ({os.path.getsize(path) / 1024:.1f} KB)")
        found_model = path
        break

if not found_model:
    print("  ✗ 未找到任何模型文件!")
    print("  请确认模型文件位置:")
    print("    - pc/models/best.pt")
    print("    - models/best.pt")
    sys.exit(1)

# 2. 加载模型并检查类别
print("\n2. 加载模型并检查类别...")
try:
    from ultralytics import YOLO
    model = YOLO(found_model)
    print(f"  ✓ 模型加载成功")
    print(f"  模型类型：{model.type}")
    print(f"  类别数量：{len(model.names)}")
    
    # 打印所有类别
    print("\n  模型包含的类别:")
    for cls_id, cls_name in model.names.items():
        print(f"    [{cls_id}] {cls_name}")
        
except Exception as e:
    print(f"  ✗ 模型加载失败：{e}")
    sys.exit(1)

# 3. 检查配置文件
print("\n3. 检查配置文件...")
try:
    from core.config import VIOLATION_LEVELS, CONF_THRESHOLD, CONSECUTIVE_FRAMES
    
    print(f"  ✓ 配置加载成功")
    print(f"  置信度阈值：{CONF_THRESHOLD}")
    print(f"  连续帧数：{CONSECUTIVE_FRAMES}")
    
    print("\n  配置的违规类别:")
    for cls_name, level in VIOLATION_LEVELS.items():
        print(f"    - {cls_name} → 等级 {level}")
        
except Exception as e:
    print(f"  ✗ 配置加载失败：{e}")
    sys.exit(1)

# 4. 检查类别匹配
print("\n4. 检查模型类别与配置匹配...")
model_classes = set(model.names.values())
config_classes = set(VIOLATION_LEVELS.keys())

print(f"  模型类别：{model_classes}")
print(f"  配置类别：{config_classes}")

missing_in_config = config_classes - model_classes
missing_in_model = model_classes - config_classes

if missing_in_config:
    print(f"  ⚠ 配置中有但模型中没有的类别：{missing_in_config}")
    
if missing_in_model:
    print(f"  ⚠ 模型中有但配置中没有的类别：{missing_in_model}")
    print("     这些类别的检测将被忽略！")

# 检查火焰类别
fire_classes_in_model = [c for c in model_classes if 'fire' in c.lower() or 'flame' in c.lower()]
fire_classes_in_config = [c for c in config_classes if 'fire' in c.lower() or 'flame' in c.lower()]

print(f"\n  火焰相关类别:")
print(f"    模型中：{fire_classes_in_model if fire_classes_in_model else '无'}")
print(f"    配置中：{fire_classes_in_config if fire_classes_in_config else '无'}")

# 检查是否有 Fire 或 open_fire
has_fire_in_model = any('fire' in c.lower() for c in model_classes)
has_fire_in_config = any('fire' in c.lower() for c in config_classes) or 'open_fire' in config_classes

if has_fire_in_model and not has_fire_in_config:
    print("  ⚠️  警告：模型检测到火焰类别，但配置中没有对应类别！")
    print("     需要在 pc/core/config.py 的 VIOLATION_LEVELS 中添加 Fire 或 open_fire")

# 5. 测试推理（可选）
print("\n5. 测试推理（需要摄像头）...")
try:
    import cv2
    cap = cv2.VideoCapture(0)
    
    if cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print("  ✓ 摄像头打开成功")
            
            # 执行一次推理
            results = model(frame, conf=CONF_THRESHOLD, verbose=False)
            
            if results[0].boxes is not None:
                detections = []
                for box in results[0].boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    name = model.names.get(cls_id, str(cls_id))
                    detections.append((name, conf))
                
                if detections:
                    print(f"  ✓ 检测到 {len(detections)} 个目标:")
                    for name, conf in detections[:5]:
                        print(f"    - {name} (置信度：{conf:.2f})")
                else:
                    print("  ℹ 未检测到任何目标（可能是正常情况）")
            else:
                print("  ℹ 未检测到任何目标（可能是正常情况）")
            
            cap.release()
        else:
            print("  ✗ 无法读取摄像头画面")
    else:
        print("  ℹ 无摄像头或无法打开")
        
except Exception as e:
    print(f"  ⚠ 摄像头测试跳过：{e}")

# 6. 诊断结论
print("\n" + "=" * 60)
print("诊断结论")
print("=" * 60)

issues = []

if missing_in_model:
    issues.append(f"模型缺少配置中的类别：{missing_in_config}")

# 检查火焰类别是否匹配
has_fire_in_model = any('fire' in c.lower() for c in model_classes)
has_fire_in_config = any('fire' in c.lower() for c in config_classes) or 'open_fire' in config_classes
if has_fire_in_model and not has_fire_in_config:
    issues.append("模型有火焰类别但配置中没有 'Fire' 或 'open_fire'")

if CONF_THRESHOLD > 0.4:
    issues.append(f"置信度阈值过高 ({CONF_THRESHOLD})，建议降低到 0.25-0.35")

if CONSECUTIVE_FRAMES > 3:
    issues.append(f"连续帧数过多 ({CONSECUTIVE_FRAMES})，建议减少到 2-3")

if issues:
    print("\n❌ 发现以下问题:")
    for issue in issues:
        print(f"  - {issue}")
    print("\n建议修复后重新运行程序")
else:
    print("\n✅ 未发现明显问题")
    print("\n如果仍然无法检测火焰，请:")
    print("  1. 确保摄像头视野中有清晰的火焰")
    print("  2. 检查光照条件是否良好")
    print("  3. 观察控制台输出，查看是否有 DEBUG 信息")
    print("  4. 尝试使用 pc_camera_yolo_test.py 直接测试")

print("\n" + "=" * 60)
