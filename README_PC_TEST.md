# YOLOv8 PC 摄像头实时测试程序使用说明

## 📋 功能特性

- ✅ **实时检测**: 使用 PC 摄像头进行实时目标检测
- ✅ **可视化显示**: 在视频上绘制检测框、类别和置信度
- ✅ **性能统计**: 实时显示 FPS、检测数量等统计信息
- ✅ **灵活控制**: 
  - 按 'q' 退出
  - 按 's' 截图
  - 按 '+'/'-' 调整置信度阈值
- ✅ **自动适配**: 支持不同类别的 YOLOv8 模型

## 🚀 快速开始

### 1. 安装依赖

在项目根目录执行：

```bash
pip install -r requirements_pc_test.txt
```

或手动安装：

```bash
pip install ultralytics opencv-python numpy
```

### 2. 准备模型

将训练好的 `.pt` 文件放在项目目录中，例如：
- `pc/yolov8n.pt` (默认路径)
- 或修改代码中的 `MODEL_PATH` 参数指向你的模型文件

### 3. 运行测试

```bash
python pc_camera_yolo_test.py
```

## 🎯 使用说明

### 快捷键

| 按键 | 功能 |
|------|------|
| `q` | 退出程序 |
| `s` | 截图保存（当前目录生成 screenshot_时间戳.jpg） |
| `+` 或 `=` | 提高置信度阈值（每次 +0.05） |
| `-` | 降低置信度阈值（每次 -0.05） |

### 参数调整

如果检测效果不理想，可以调整以下参数（在代码中）：

1. **置信度阈值** (`CONF_THRESHOLD`)
   - 范围：0.0 ~ 1.0
   - 默认：0.7
   - 调高：减少误检，但可能漏检
   - 调低：增加检出率，但可能误检

2. **摄像头 ID** (`CAMERA_ID`)
   - `0`: 默认摄像头
   - `1`: 第二个摄像头
   - `2`: 第三个摄像头

3. **窗口大小** (`WINDOW_SIZE`)
   - 默认：`(1280, 720)`
   - 可调整为其他分辨率

4. **模型选择**
   - `yolov8n.pt`: 最快，精度较低
   - `yolov8s.pt`: 平衡速度和精度
   - `yolov8m.pt`: 较慢，精度高
   - `yolov8l.pt`: 慢，高精度
   - `yolov8x.pt`: 最慢，最高精度

## 📊 输出说明

### 实时显示信息

- **左上角**: 性能统计（FPS、平均检测数等）
- **右上角**: 当前检测到的目标数量
- **每个目标**: 边界框 + 类别名称 + 置信度

### 截图保存

按 's' 键后，截图会保存在当前目录，文件名格式：
```
screenshot_1710604800.jpg
```

## 🔧 常见问题

### Q1: 无法打开摄像头

**解决方案**:
1. 检查摄像头是否已连接
2. 关闭其他可能占用摄像头的程序（如 Zoom、微信、QQ 等）
3. 尝试更改 `CAMERA_ID` 参数（0, 1, 2...）
4. 检查摄像头驱动是否已安装

### Q2: 检测速度很慢（FPS 低）

**优化建议**:
1. 使用更小的模型（如 yolov8n.pt）
2. 降低摄像头分辨率（修改 `WINDOW_SIZE`）
3. 确保 CPU/GPU 散热良好
4. 关闭其他占用资源的程序

### Q3: 检测效果不好

**改进方法**:
1. 调整置信度阈值（按 '+' 或 '-' 键）
2. 确保训练数据充足且质量好
3. 尝试更大的模型（yolov8m.pt 等）
4. 检查光照条件是否良好

### Q4: ModuleNotFoundError: No module named 'ultralytics'

**解决方案**:
```bash
pip install --upgrade pip
pip install ultralytics
```

如果下载速度慢，可以使用国内镜像：
```bash
pip install ultralytics -i https://pypi.tuna.tsinghua.edu.cn/simple
```

## 💡 进阶技巧

### 多摄像头测试

如果有多个摄像头，可以修改 `CAMERA_ID`:

```python
CAMERA_ID = 1  # 第二个摄像头
```

或使用 USB 外接摄像头：

```python
CAMERA_ID = 2  # 第三个摄像头
```

### 自定义模型路径

如果你的模型在其他位置：

```python
MODEL_PATH = 'YOLOv8 训练/best.pt'  # 修改为你的实际路径
```

### 批量测试图片

如果要测试静态图片而不是摄像头：

```python
import cv2
from ultralytics import YOLO

model = YOLO('pc/yolov8n.pt')
image = cv2.imread('test_image.jpg')
results = model(image)
results[0].show()
```

## 📝 与 ESP32 系统的区别

| 特性 | PC 测试程序 | ESP32 系统 |
|------|-----------|-----------|
| 摄像头 | PC 自带/USB 摄像头 | ESP32-CAM 模块 |
| 推理设备 | CPU/GPU | 无（仅传输，PC 端推理） |
| 网络 | 不需要 | 需要 WiFi 连接 |
| 实时性 | 高（本地处理） | 受网络影响 |
| 用途 | 开发调试 | 生产部署 |
| 功耗 | 高 | 低 |

## 🎓 下一步

测试通过后，可以将模型集成到完整系统中：

1. 将训练好的模型复制到 `pc/models/` 目录
2. 修改 `pc/core/config.py` 中的 `MODEL_PATH`
3. 运行完整系统：`python pc/main.py`

## 📞 技术支持

如遇到问题，请提供以下信息：

1. 完整的错误信息
2. Python 版本（`python --version`）
3. 已安装的包版本（`pip list`）
4. 操作系统版本
5. 摄像头型号

---

**作者**: AI Assistant  
**日期**: 2026-03-16  
**版本**: v1.0
