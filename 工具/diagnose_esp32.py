# ============================================================
#  ESP32 启动诊断工具
#  用于检查和修复 ESP32 无法自动运行的问题
# ============================================================
import os
import sys

print("=" * 60)
print("ESP32 启动问题诊断")
print("=" * 60)

# 1. 检查关键文件是否存在
print("\n1. 检查关键文件...")
required_files = {
    'boot.py': '启动配置文件（必需）',
    'main.py': '主程序入口（必需）',
    'config.py': '配置文件（必需）',
    'wifi_manager.py': 'WiFi 管理模块（必需）',
    'camera_stream.py': '摄像头流模块（必需）',
    'audio_player.py': '音频播放模块（必需）',
    'cmd_receiver.py': '指令接收模块（必需）',
    'heartbeat.py': '心跳模块（必需）'
}

missing_files = []
for filename, description in required_files.items():
    try:
        with open(filename, 'r') as f:
            print(f"  ✓ {filename}: {description}")
    except:
        print(f"  ✗ {filename}: {description} - 缺失!")
        missing_files.append(filename)

# 2. 检查 boot.py 内容
print("\n2. 检查 boot.py 内容...")
try:
    with open('boot.py', 'r') as f:
        content = f.read()
        if 'machine' in content and 'os' in content:
            print("  ✓ boot.py 包含必要的导入")
        else:
            print("  ⚠ boot.py 可能缺少必要代码")
except:
    print("  ✗ boot.py 不存在或无法读取")

# 3. 检查 main.py 内容
print("\n3. 检查 main.py 内容...")
try:
    with open('main.py', 'r') as f:
        content = f.read()
        
        # 检查是否有必要的导入
        checks = [
            ('uasyncio', '异步支持'),
            ('WiFiManager', 'WiFi 管理'),
            ('CameraStreamer', '摄像头流'),
            ('AudioPlayer', '音频播放'),
            ('CmdReceiver', '指令接收'),
            ('Heartbeat', '心跳功能'),
            ('if __name__', '主入口检查')
        ]
        
        for keyword, desc in checks:
            if keyword in content:
                print(f"  ✓ {desc}: {keyword}")
            else:
                print(f"  ✗ {desc}: {keyword} - 缺失!")
except Exception as e:
    print(f"  ✗ main.py 检查失败：{e}")

# 4. 检查 config.py
print("\n4. 检查 config.py 配置...")
try:
    with open('config.py', 'r') as f:
        content = f.read()
        
        configs = [
            ('WIFI_SSID', 'WiFi SSID'),
            ('WIFI_PASSWORD', 'WiFi 密码'),
            ('PC_IP', 'PC IP 地址'),
            ('CAM_FRAMESIZE', '摄像头分辨率'),
            ('AUDIO_RATE', '音频采样率')
        ]
        
        for keyword, desc in configs:
            if keyword in content:
                print(f"  ✓ {desc}: {keyword}")
            else:
                print(f"  ✗ {desc}: {keyword} - 缺失!")
except Exception as e:
    print(f"  ✗ config.py 检查失败：{e}")

# 5. 文件系统状态
print("\n5. 文件系统状态...")
try:
    files = os.listdir()
    print(f"  总文件数：{len(files)}")
    
    # 统计文件类型
    py_files = [f for f in files if f.endswith('.py')]
    print(f"  Python 文件：{len(py_files)}")
    
    # 检查存储空间
    try:
        stat = os.statvfs('/')
        free_space = stat[0] * stat[3]
        total_space = stat[0] * stat[2]
        print(f"  可用存储：{free_space // 1024} KB / {total_space // 1024} KB")
    except:
        print("  ⚠ 无法读取存储信息")
        
except Exception as e:
    print(f"  ✗ 文件系统检查失败：{e}")

# 6. 系统信息
print("\n6. 系统信息...")
try:
    import machine
    print(f"  平台：{sys.platform}")
    print(f"  MicroPython 版本：{sys.version}")
    print(f"  CPU 频率：{machine.freq() // 1000000} MHz")
    print(f"  可用内存：{__import__('gc').mem_free()} bytes")
except Exception as e:
    print(f"  ✗ 系统信息获取失败：{e}")

# 7. 诊断结论
print("\n" + "=" * 60)
print("诊断结论")
print("=" * 60)

if missing_files:
    print(f"\n❌ 发现缺失文件：{', '.join(missing_files)}")
    print("解决方案：使用 Thonny/uPyCraft 上传缺失文件到 ESP32")
else:
    print("\n✓ 所有关键文件都存在")
    
print("\n建议的检查步骤:")
print("1. 确认 boot.py 和 main.py 都已上传到 ESP32")
print("2. 通过串口连接 ESP32，观察启动日志")
print("3. 如果看到错误，根据错误信息修复对应文件")
print("4. 按 RESET 键重启 ESP32 测试")

print("\n" + "=" * 60)
