# 校园实验室安全智能管控系统
**中俄青少年人工智能创新大赛 · 高中组参赛作品**

---

## 项目简介

本系统采用 **PC + ESP32-S3 无线分布式架构**，实现校园理化生实验室的实时安全监测与智能预警。ESP32 负责视频采集与语音播报，PC 端运行 YOLOv8n 轻量化模型完成 AI 推理，通过纯局域网无线通信完成端到端闭环管控，无需外网，比赛演示零风险。

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│                  核心 AI 与管控层（PC）                   │
│  YOLOv8n推理 │ 分级预警 │ PyQt5管理后台 │ SQLite台账    │
└──────────────────────┬──────────────────────────────────┘
                       │ 纯局域网 WiFi（PC热点）
          ┌────────────┴────────────┐
          │  无线通信层              │
          │  UDP上行(视频) 5600      │
          │  TCP下行(指令) 5601      │
          │  UDP心跳     5602        │
          └────────────┬────────────┘
                       │
┌──────────────────────┴──────────────────────────────────┐
│                终端感知执行层（ESP32-S3）                  │
│  OV2640摄像头 │ JPEG压缩传输 │ MAX98357A语音播报          │
└─────────────────────────────────────────────────────────┘
```

---

## 目录结构

```
中俄比赛/
├── esp32/                      # MicroPython 固件
│   ├── config.py               # WiFi / 端口 / 摄像头 / 引脚配置
│   ├── wifi_manager.py         # WiFi连接 + 静态IP + 断线自动重连
│   ├── camera_stream.py        # OV2640采集 → JPEG分包 → UDP上行
│   ├── cmd_receiver.py         # TCP监听PC指令，解析预警命令
│   ├── audio_player.py         # I2S驱动MAX98357A，支持循环/单次播报
│   ├── heartbeat.py            # 定时UDP心跳，上报设备在线状态
│   └── main.py                 # uasyncio协程主入口
│
└── pc/                         # Python PC端
    ├── requirements.txt        # Python依赖清单
    ├── main.py                 # 程序入口
    ├── core/
    │   ├── config.py           # 全局配置（端口/阈值/违规类别）
    │   ├── stream_receiver.py  # UDP多设备帧重组 + OpenCV解码
    │   ├── heartbeat_monitor.py# 心跳接收，设备在/离线检测
    │   ├── cmd_sender.py       # TCP长连接，向ESP32下发指令
    │   ├── ai_engine.py        # YOLOv8n推理 + 连续帧确认 + 触发预警
    │   └── alert_manager.py    # 分级处置：截图存档+指令下发+通知UI
    ├── db/
    │   └── database.py         # SQLite：事件台账/设备管理/统计查询
    └── ui/
        ├── i18n.py             # 中/俄双语翻译（全局 t(key) 函数）
        ├── main_window.py      # 主窗口（蓝白工业风深色主题）
        ├── monitor_tab.py      # 实时监控（2×2多路，AI标注叠加）
        ├── alert_tab.py        # 预警管理（实时列表/处理/CSV导出）
        ├── stats_tab.py        # 台账统计（柱状图/折线图/饼图）
        ├── device_tab.py       # 设备管理（在线状态/手动下发指令）
        └── settings_tab.py     # 系统设置（语言/阈值/音量/备份）
```

---

## 硬件清单

| 硬件 | 型号 | 说明 |
|------|------|------|
| 主控板 | ESP32-S3-N16R8 | 双核，8MB PSRAM，支持硬件JPEG压缩 |
| 摄像头 | OV2640 200万像素 | 硬件JPEG压缩，320×240@12FPS |
| 音频功放 | MAX98357A I2S | 3W/4Ω扬声器，I2S接口驱动 |
| 供电 | 5V/2A Type-C | 独立供电，严禁用电脑USB口 |
| PC | Windows i5及以上 | 带WiFi，运行AI推理与管控后台 |

---

## 快速开始

### 1. ESP32 端部署

```
① 安装 Thonny IDE，连接 ESP32-S3
② 将 esp32/ 目录下所有 .py 文件上传到 ESP32 根目录
③ 将语音文件（8kHz 16bit Mono WAV）上传到 ESP32 的 /audio/ 目录
   warn1.wav — 请规范佩戴护目镜和实验服
   warn2.wav — 请勿违规操作明火
   warn3.wav — 危险！实验区域无人值守
   warn1_ru.wav / warn2_ru.wav / warn3_ru.wav（俄语版）
④ 修改 esp32/config.py 中的热点名称、密码、PC_IP
⑤ 重启 ESP32，上电自动运行
```

### 2. PC 端部署

```bash
# 安装依赖
cd 中俄比赛/pc
pip install -r requirements.txt

# 将训练好的 YOLOv8n 权重放置到
# pc/models/lab_safety.pt
# （首次无权重时自动加载 yolov8n.pt 进行演示）

# 开启 PC WiFi 热点（名称和密码与 config.py 一致）

# 启动系统
python main.py
```

### 3. 无线通信端口说明

| 方向 | 协议 | 端口 | 内容 |
|------|------|------|------|
| ESP32 → PC | UDP | 5600 | JPEG 视频帧（AA BB 分包头） |
| PC → ESP32 | TCP | 5601 | `WARN:warn1:1\n` 格式指令 |
| ESP32 → PC | UDP | 5602 | JSON 心跳包（含设备ID/IP/序号） |

---

## 核心检测目标

| 违规类型 | 预警等级 | 处置动作 |
|----------|----------|----------|
| 未戴护目镜 / 未穿实验服 / 未戴手套 | 一级 | 界面标注 + ESP32单次语音提醒 |
| 违规明火操作 / 人员离岗 | 二级 | 持续声光提醒 + ESP32循环播报 |
| 危化品混放 / 违规废液倾倒 / 非授权人员 | 三级 | 紧急弹窗 + 全终端播报 + 截图存档 |

---

## AI 模型训练说明

```
1. 自主拍摄本校实验室违规场景，标注数量 ≥ 2000 张
2. 使用 LabelImg / Roboflow 完成 YOLO 格式标注
3. 数据增强：翻转、裁剪、亮度调整
4. 训练命令（在 pc/ 目录下）：
   yolo train model=yolov8n.pt data=dataset/lab.yaml epochs=100 imgsz=320
5. 将最佳权重 best.pt 复制为 models/lab_safety.pt
```

---

## 开发环境

- **ESP32 端**：MicroPython v1.22+ / Arduino IDE（二选一）
- **PC 端**：Python 3.9+ / PyQt5 / ultralytics / OpenCV / matplotlib
- **数据库**：SQLite3（Python内置，无需额外安装）
- **通信**：纯局域网，无外网依赖

---

## 开发团队分工建议

| 角色 | 职责 |
|------|------|
| 算法与PC端负责人 | 数据集制作、模型训练、AI推理逻辑 |
| ESP32硬件负责人 | 硬件搭建、底层驱动、无线通信调试 |
| 上位机与文档负责人 | PyQt5界面、数据库、文档与演示视频 |
