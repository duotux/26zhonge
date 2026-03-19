# ============================================================
#  PC 摄像头实时 YOLOv8 识别测试程序
#  用于在本地 PC 上测试训练好的模型识别效果
# ============================================================
import cv2
import numpy as np
from ultralytics import YOLO
import time
from collections import deque

class YOLOv8Tester:
    """YOLOv8 实时识别测试器"""
    
    def __init__(self, model_path='best.pt', conf_threshold=0.3):
        """
        初始化 YOLOv8 测试器
        
        Args:
            model_path: 模型权重文件路径
            conf_threshold: 置信度阈值
        """
        self.conf_threshold = conf_threshold
        
        # 加载模型
        print(f"[INFO] 正在加载模型：{model_path}")
        try:
            self.model = YOLO(model_path)
            print("[INFO] 模型加载成功 ✓")
        except Exception as e:
            print(f"[ERROR] 模型加载失败：{e}")
            raise
        
        # 获取类别名称
        self.class_names = list(self.model.names.values())
        
        # 生成不同颜色的色带（用于绘制边界框）
        np.random.seed(42)
        self.colors = np.random.randint(0, 255, size=(len(self.class_names), 3), dtype=np.uint8)
        
        # 性能统计
        self.fps_history = deque(maxlen=30)  # 记录最近 30 帧的 FPS
        self.detection_stats = {
            'total_frames': 0,
            'total_detections': 0,
            'start_time': time.time()
        }
    
    def detect_frame(self, frame):
        """
        对单帧进行目标检测
        
        Args:
            frame: BGR 图像 (numpy array)
            
        Returns:
            results: YOLO 检测结果
        """
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        return results[0]
    
    def draw_detections(self, frame, results):
        """
        在图像上绘制检测结果
        
        Args:
            frame: BGR 图像
            results: YOLO 检测结果
            
        Returns:
            annotated_frame: 绘制了结果的图像
        """
        annotated_frame = frame.copy()
        
        if results.boxes is None:
            return annotated_frame
        
        for box in results.boxes:
            # 获取边界框坐标
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            
            # 获取类别和置信度
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            
            # 只绘制超过阈值的检测
            if conf < self.conf_threshold:
                continue
            
            # 获取类别名称和颜色
            class_name = self.class_names[cls_id] if cls_id < len(self.class_names) else f"class_{cls_id}"
            color = [int(c) for c in self.colors[cls_id % len(self.colors)]]
            
            # 绘制边界框
            cv2.rectangle(annotated_frame, (x1, y1), (x2, y2), color, 2)
            
            # 绘制标签背景
            label = f"{class_name}: {conf:.2f}"
            (label_w, label_h), baseline = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)
            cv2.rectangle(annotated_frame, (x1, y1 - label_h - baseline - 5), 
                         (x1 + label_w, y1), color, -1)
            
            # 绘制标签文字
            cv2.putText(annotated_frame, label, (x1, y1 - 5), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # 更新统计
            self.detection_stats['total_detections'] += 1
        
        self.detection_stats['total_frames'] += 1
        return annotated_frame
    
    def draw_stats(self, frame):
        """
        在图像上绘制性能统计信息
        
        Args:
            frame: BGR 图像
            
        Returns:
            frame: 绘制了统计信息的图像
        """
        # 计算 FPS
        current_time = time.time()
        elapsed = current_time - self.detection_stats['start_time']
        
        if elapsed > 0:
            avg_fps = self.detection_stats['total_frames'] / elapsed
            avg_det = self.detection_stats['total_detections'] / max(1, self.detection_stats['total_frames'])
        else:
            avg_fps = 0
            avg_det = 0
        
        # 绘制统计信息背景
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (350, 120), (0, 0, 0), -1)
        cv2.addWeighted(overlay, 0.6, frame, 0.4, 0, frame)
        
        # 绘制统计文字
        stats_text = [
            f"FPS: {avg_fps:.1f}",
            f"平均检测：{avg_det:.2f} 个/帧",
            f"总帧数：{self.detection_stats['total_frames']}",
            f"总检测：{self.detection_stats['total_detections']}",
            f"置信度阈值：{self.conf_threshold}"
        ]
        
        y_offset = 25
        for i, text in enumerate(stats_text):
            cv2.putText(frame, text, (10, y_offset + i * 22), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return frame
    
    def run(self, camera_id=0, window_size=(1280, 720)):
        """
        运行实时检测
        
        Args:
            camera_id: 摄像头 ID（通常是 0）
            window_size: 窗口大小 (宽度，高度)
        """
        print(f"\n[INFO] 正在打开摄像头 {camera_id}...")
        cap = cv2.VideoCapture(camera_id)
        
        if not cap.isOpened():
            print("[ERROR] 无法打开摄像头!")
            print("[TIP] 请检查:")
            print("  1. 摄像头是否已连接")
            print("  2. 摄像头驱动是否已安装")
            print("  3. 是否有其他程序正在使用摄像头")
            return
        
        # 设置摄像头参数
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, window_size[0])
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, window_size[1])
        cap.set(cv2.CAP_PROP_FPS, 30)
        
        # 获取实际分辨率
        actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        actual_fps = int(cap.get(cv2.CAP_PROP_FPS))
        
        print(f"[INFO] 摄像头已打开 ✓")
        print(f"[INFO] 分辨率：{actual_width}x{actual_height} @ {actual_fps}fps")
        print(f"[INFO] 按 'q' 键退出，按 's' 键截图，按 '+'/'-' 调整阈值")
        print("=" * 60)
        
        # 创建显示窗口
        cv2.namedWindow('YOLOv8 实时检测 - PC 摄像头测试', cv2.WINDOW_NORMAL)
        cv2.resizeWindow('YOLOv8 实时检测 - PC 摄像头测试', window_size)
        
        frame_count = 0
        last_print_time = time.time()
        
        try:
            while True:
                # 读取帧
                ret, frame = cap.read()
                
                if not ret:
                    print("[WARNING] 无法读取帧，跳过...")
                    continue
                
                # 翻转图像（镜像效果，更自然）
                frame = cv2.flip(frame, 1)
                
                # 执行检测
                results = self.detect_frame(frame)
                
                # 绘制检测结果
                annotated_frame = self.draw_detections(frame, results)
                
                # 绘制统计信息
                annotated_frame = self.draw_stats(annotated_frame)
                
                # 显示当前检测到的目标数量
                if results.boxes is not None:
                    det_count = len(results.boxes)
                    cv2.putText(annotated_frame, f"检测到 {det_count} 个目标", 
                               (annotated_frame.shape[1] - 250, 30),
                               cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)
                
                # 显示图像
                cv2.imshow('YOLOv8 实时检测 - PC 摄像头测试', annotated_frame)
                
                # 处理键盘事件
                key = cv2.waitKey(1) & 0xFF
                
                if key == ord('q'):
                    print("\n[INFO] 用户退出")
                    break
                elif key == ord('s'):
                    # 截图保存
                    filename = f"screenshot_{int(time.time())}.jpg"
                    cv2.imwrite(filename, annotated_frame)
                    print(f"[INFO] 截图已保存：{filename}")
                elif key == ord('+') or key == ord('='):
                    # 提高置信度阈值
                    self.conf_threshold = min(0.95, self.conf_threshold + 0.05)
                    print(f"[INFO] 置信度阈值：{self.conf_threshold:.2f}")
                elif key == ord('-'):
                    # 降低置信度阈值
                    self.conf_threshold = max(0.1, self.conf_threshold - 0.05)
                    print(f"[INFO] 置信度阈值：{self.conf_threshold:.2f}")
                
                frame_count += 1
                
                # 每 60 秒打印一次统计
                current_time = time.time()
                if current_time - last_print_time >= 60:
                    elapsed = current_time - self.detection_stats['start_time']
                    avg_fps = frame_count / elapsed
                    print(f"\n[STATS] 运行时间：{elapsed:.0f}s | 平均 FPS: {avg_fps:.1f} | 总检测：{self.detection_stats['total_detections']}")
                    last_print_time = current_time
                    
        except KeyboardInterrupt:
            print("\n[INFO] 程序中断")
        
        finally:
            # 释放资源
            cap.release()
            cv2.destroyAllWindows()
            
            # 打印最终统计
            total_time = time.time() - self.detection_stats['start_time']
            print("\n" + "=" * 60)
            print("[最终统计]")
            print(f"  总运行时间：{total_time:.1f} 秒")
            print(f"  总处理帧数：{self.detection_stats['total_frames']}")
            print(f"  总检测目标：{self.detection_stats['total_detections']}")
            print(f"  平均 FPS: {self.detection_stats['total_frames']/total_time:.1f}")
            print(f"  平均每帧检测：{self.detection_stats['total_detections']/max(1, self.detection_stats['total_frames']):.2f} 个")
            print("=" * 60)


def main():
    """主函数"""
    print("=" * 60)
    print("YOLOv8 PC 摄像头实时识别测试程序")
    print("=" * 60)
    print()
    
    # 配置参数（与 __init__ 默认值保持一致）
    MODEL_PATH = './last.pt'  # 模型路径（已修改为 best.pt）
    CONF_THRESHOLD = 0.3  # 置信度阈值（已修改为 0.5）
    CAMERA_ID = 0  # 摄像头 ID
    WINDOW_SIZE = (1280, 720)  # 窗口大小
    
    print(f"模型路径：{MODEL_PATH}")
    print(f"置信度阈值：{CONF_THRESHOLD}")
    print(f"摄像头 ID: {CAMERA_ID}")
    print(f"窗口大小：{WINDOW_SIZE[0]}x{WINDOW_SIZE[1]}")
    print()
    print("使用说明:")
    print("  - 按 'q' 键退出")
    print("  - 按 's' 键截图")
    print("  - 按 '+' 键提高置信度阈值")
    print("  - 按 '-' 键降低置信度阈值")
    print("=" * 60)
    print()
    
    # 创建测试器并运行
    try:
        tester = YOLOv8Tester(model_path=MODEL_PATH, conf_threshold=CONF_THRESHOLD)
        tester.run(camera_id=CAMERA_ID, window_size=WINDOW_SIZE)
    except Exception as e:
        print(f"\n[ERROR] 程序运行失败：{e}")
        print("\n可能的解决方案:")
        print("  1. 检查模型文件是否存在")
        print("  2. 确认已安装 ultralytics 库：pip install ultralytics")
        print("  3. 确认已安装 opencv-python：pip install opencv-python")
        print("  4. 检查摄像头连接")


if __name__ == "__main__":
    main()
