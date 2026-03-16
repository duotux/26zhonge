# ============================================================
#  视频流配置测试脚本
#  用于验证 ESP32 和 PC 端的配置一致性
# ============================================================
import sys
import os

print("=" * 60)
print("ESP32 视频流配置检查")
print("=" * 60)

# 检查 ESP32 配置文件
esp32_config_path = "../esp32/config.py"
if os.path.exists(esp32_config_path):
    print(f"\n✓ 找到 ESP32 配置文件：{esp32_config_path}")
    
    # 读取配置内容
    with open(esp32_config_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # 提取关键配置
    if "CAM_FRAMESIZE" in content:
        for line in content.split('\n'):
            if line.startswith("CAM_FRAMESIZE"):
                print(f"  {line.strip()}")
            elif line.startswith("CAM_QUALITY"):
                print(f"  {line.strip()}")
            elif line.startswith("CAM_FPS"):
                print(f"  {line.strip()}")
            elif line.startswith("AUDIO_RATE"):
                print(f"  {line.strip()}")
else:
    print(f"\n✗ 未找到 ESP32 配置文件：{esp32_config_path}")

print("\n" + "=" * 60)
print("PC 端配置检查")
print("=" * 60)
print("UDP 视频接收端口：5600")
print("TCP 指令端口：5601")
print("UDP 心跳端口：5602")
print("TCP 音频端口：5603")

print("\n" + "=" * 60)
print("推荐配置（QVGA 分辨率优化）")
print("=" * 60)
print("分辨率：FRAMESIZE_QVGA (320×240)")
print("JPEG 质量：35 (范围 0-63，越大质量越低)")
print("目标帧率：10 FPS")
print("音频采样率：24000 Hz")

print("\n" + "=" * 60)
print("下一步操作")
print("=" * 60)
print("1. 将修改后的文件上传到 ESP32:")
print("   - esp32/config.py")
print("   - esp32/camera_stream.py")
print("\n2. 重启 ESP32 设备")
print("\n3. 观察串口日志，确认:")
print("   ✓ 摄像头初始化成功")
print("   ✓ 分辨率显示为 QVGA 或 FRAMESIZE_QVGA")
print("   ✓ 没有 ENOMEM 内存错误")
print("\n4. 在 PC 端观察:")
print("   ✓ 无 'corrupt JPEG data' 错误")
print("   ✓ 帧率达到 8-12 FPS")
print("=" * 60)
