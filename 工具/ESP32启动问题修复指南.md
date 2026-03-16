# ESP32 无法自动运行 main.py 问题修复指南

## 问题现象

将文件上传到 ESP32 后，ESP32 **不能自动运行** `main.py`。

---

## 🔍 可能的原因

### 原因 1: **缺少 boot.py 文件** ❌

**MicroPython 启动顺序**:
```
1. _boot.py (固件内置，只读)
2. boot.py   (用户启动脚本，必需!)
3. main.py   (主程序，可选)
```

如果缺少 `boot.py`，ESP32 可能无法正常启动 `main.py`。

**解决方案**: ✅ 已创建 [`boot.py`](file://d:\桌面\中俄比赛\esp32\boot.py)

---

### 原因 2: **导入错误导致启动中断** ❌

`main.py` 中导入了多个模块：
```python
from wifi_manager   import WiFiManager
from camera_stream  import CameraStreamer
from audio_player   import AudioPlayer
from cmd_receiver   import CmdReceiver
from heartbeat      import Heartbeat
```

如果任何一个模块：
- 有语法错误
- 缺少依赖
- 文件损坏

都会导致启动过程中断。

**解决方案**: 使用诊断工具检查所有文件

---

### 原因 3: **文件上传不完整** ❌

上传过程中文件可能：
- 部分损坏
- 编码错误
- 行尾符不兼容（Windows CRLF vs Unix LF）

**解决方案**: 重新上传关键文件

---

## 🛠️ 完整修复步骤

### 步骤 1: 准备必要文件

确保以下文件在 `esp32/` 目录中：

**核心启动文件（必需）**:
- ✅ [`boot.py`](file://d:\桌面\中俄比赛\esp32\boot.py) - **新增！启动配置**
- ✅ [`main.py`](file://d:\桌面\中俄比赛\esp32\main.py) - 主程序
- ✅ [`config.py`](file://d:\桌面\中俄比赛\esp32\config.py) - 配置文件

**功能模块（必需）**:
- ✅ [`wifi_manager.py`](file://d:\桌面\中俄比赛\esp32\wifi_manager.py)
- ✅ [`camera_stream.py`](file://d:\桌面\中俄比赛\esp32\camera_stream.py)
- ✅ [`audio_player.py`](file://d:\桌面\中俄比赛\esp32\audio_player.py)
- ✅ [`cmd_receiver.py`](file://d:\桌面\中俄比赛\esp32\cmd_receiver.py)
- ✅ [`heartbeat.py`](file://d:\桌面\中俄比赛\esp32\heartbeat.py)

---

### 步骤 2: 上传文件到 ESP32

#### 方法 A: 使用 Thonny IDE（推荐）

1. **连接 ESP32**
   - USB 线连接电脑
   - Thonny → 工具 → 选项 → MicroPython
   - 选择正确的 COM 端口

2. **上传文件**
   ```
   按以下顺序上传：
   1. boot.py      ← 先上传启动配置
   2. config.py    ← 再上传配置
   3. 其他模块文件
   4. main.py      ← 最后上传主程序
   ```

3. **上传技巧**
   - 右键点击文件 → "保存到设备"
   - 或直接拖拽到 Thonny 的设备窗口
   - 确保文件名完全一致（区分大小写）

#### 方法 B: 使用 uPyCraft

1. 连接设备
2. 打开文件
3. 点击"上传"按钮
4. 选择保存到设备根目录

---

### 步骤 3: 验证文件完整性

#### 方式 1: 使用串口终端检查

1. 打开 Thonny 的 Shell 窗口
2. 按 `Ctrl+C` 中断当前运行
3. 输入以下命令：

```python
# 列出所有文件
import os
os.listdir()

# 检查 boot.py 是否存在
'main.py' in os.listdir()
'boot.py' in os.listdir()

# 查看文件大小（确认上传完整）
import os
for f in ['boot.py', 'main.py', 'config.py']:
    try:
        size = os.stat(f)[6]
        print(f"{f}: {size} bytes")
    except:
        print(f"{f}: 不存在!")
```

#### 方式 2: 运行诊断脚本

将 [`diagnose_esp32.py`](file://d:\桌面\中俄比赛\工具\diagnose_esp32.py) 上传到 ESP32 并运行：

```python
# 在 Thonny 中打开 diagnose_esp32.py
# 然后点击"运行"
```

诊断工具会自动检查：
- ✓ 所有关键文件是否存在
- ✓ 文件内容是否完整
- ✓ 系统资源状态
- ✓ 启动配置是否正确

---

### 步骤 4: 观察启动日志

**重启 ESP32**（按 RESET 键或断电重启），观察串口输出：

**正常启动日志**:
```
============================================================
[BOOT] CPU 频率：240MHz
[BOOT] 可用内存：XXXXX bytes
[BOOT] 文件系统文件数：XX
[BOOT] ✓ main.py 存在
[BOOT] ✓ config.py 存在
[BOOT] ✓ wifi_manager.py 存在
[BOOT] 系统初始化完成，准备加载 main.py...
============================================================
[WIFI] 正在连接 WiFi...
[WIFI] 已连接，IP: 192.168.137.121
[Camera] 初始化成功...
[MAIN] 系统启动完成，开始运行...
```

**异常启动日志示例**:

1. **ImportError**:
   ```
   Traceback (most recent call last):
     File "main.py", line 2, in <module>
   ImportError: no module named 'xxx'
   ```
   **解决**: 上传缺失的模块文件

2. **SyntaxError**:
   ```
     File "config.py", line 5
   SyntaxError: invalid syntax
   ```
   **解决**: 检查文件第 5 行的语法错误

3. **OSError** (文件不存在):
   ```
   OSError: [Errno 2] ENOENT
   ```
   **解决**: 重新上传对应文件

---

### 步骤 5: 手动测试 main.py

如果自动启动仍有问题，可以手动运行：

1. **连接串口**（Thonny Shell）
2. **按 Ctrl+C** 停止当前运行
3. **输入命令**:

```python
import main
```

或直接运行：

```python
exec(open('main.py').read())
```

观察输出错误信息。

---

## 📋 快速检查清单

上传前确认：

- [ ] `boot.py` 已创建并准备上传
- [ ] `main.py` 内容完整（107 行）
- [ ] `config.py` 配置正确（WiFi SSID、密码等）
- [ ] 所有模块文件都存在
- [ ] 文件格式为 UTF-8 编码
- [ ] 行尾符为 Unix 格式（LF）

上传后确认：

- [ ] 通过 `os.listdir()` 验证文件存在
- [ ] 文件大小与本地一致
- [ ] 重启后能看到 boot.py 的启动日志
- [ ] WiFi 连接成功
- [ ] 摄像头初始化成功
- [ ] 无报错信息

---

## 🔧 高级故障排除

### 问题：上传后仍然无法启动

**检查点 1**: 确认上传位置
```python
# 在 Thonny 中执行
import os
print(os.listdir())
```

确保文件在**设备根目录**，不是子文件夹中。

---

**检查点 2**: 清除旧文件
```python
# 删除可能有问题的旧文件
import os
try:
    os.remove('old_main.py')  # 替换为实际文件名
except:
    pass
```

---

**检查点 3**: 恢复出厂设置
```python
# 格式化 Flash（谨慎操作！）
import os
os.mount(machine.SDCard(), '/sd')  # 如果使用 SD 卡
# 或者通过按键进入下载模式重新烧录固件
```

---

**检查点 4**: 检查电源
- USB 供电不足可能导致启动失败
- 使用优质 USB 线（支持数据传输）
- 避免使用 USB 集线器，直接连接电脑

---

## 💡 预防措施

### 1. 使用版本控制

备份重要文件到电脑：
```
esp32/
├── boot.py          ← 备份
├── main.py          ← 备份
├── config.py        ← 备份
└── ...
```

### 2. 标准化上传流程

每次上传遵循：
1. 先上传 `boot.py`
2. 再上传配置文件
3. 然后上传模块
4. 最后上传 `main.py`
5. 重启验证

### 3. 保留调试接口

在 `main.py` 中添加：
```python
import sys

# 启动时打印版本信息
print(f"Running on {sys.platform}")
print(f"Python version: {sys.version}")
```

---

## 📞 需要帮助？

如果以上方法都无效，请提供：

1. **启动日志**（完整串口输出）
2. **错误信息**（截图或文字）
3. **文件列表**（`os.listdir()` 结果）
4. **使用的 IDE**（Thonny/uPyCraft/其他）
5. **ESP32 型号**（ESP32-S3/ESP32-CAM 等）

---

## 📚 相关文档

- [MicroPython 官方文档](https://docs.micropython.org/)
- [ESP32 快速入门](https://docs.micropython.org/en/latest/esp32/quickref.html)
- [视频流修复指南](file://d:\桌面\中俄比赛\工具\视频流修复指南.md)

---

**最后更新**: 2026-03-16  
**版本**: v1.0
