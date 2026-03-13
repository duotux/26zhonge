# ============================================================
#  ESP32-CAM 硬件诊断脚本
#  用于检测摄像头硬件连接和初始化问题
# ============================================================
import camera
import time

print("=" * 60)
print("ESP32-CAM 硬件诊断工具")
print("=" * 60)

# 测试不同的初始化参数组合
configs = [
    {
        "name": "配置 1: VGA + JPEG (无 fb_location)",
        "params": {"format": camera.JPEG, "framesize": camera.FRAME_VGA}
    },
    {
        "name": "配置 2: QVGA + JPEG (无 fb_location)",
        "params": {"format": camera.JPEG, "framesize": camera.FRAME_QVGA}
    },
    {
        "name": "配置 3: VGA + JPEG + PSRAM",
        "params": {"format": camera.JPEG, "framesize": camera.FRAME_VGA, "fb_location": camera.PSRAM}
    },
    {
        "name": "配置 4: QVGA + JPEG + PSRAM",
        "params": {"format": camera.JPEG, "framesize": camera.FRAME_QVGA, "fb_location": camera.PSRAM}
    },
    {
        "name": "配置 5: CIF + JPEG (最低分辨率)",
        "params": {"format": camera.JPEG, "framesize": camera.FRAME_CIF}
    },
]

success_config = None

for i, config in enumerate(configs, 1):
    print(f"\n正在测试 [{config['name']}]...")
    try:
        # 先释放旧资源
        try:
            camera.deinit()
        except:
            pass
        
        time.sleep(0.5)
        
        # 尝试初始化
        camera.init(0, **config["params"])
        print(f"✓ 初始化成功！")
        
        # 尝试捕获一帧
        print("  正在测试捕获图像...")
        buf = camera.capture()
        
        if buf and len(buf) > 0:
            print(f"✓ 捕获成功！图像大小：{len(buf)} 字节")
            success_config = config["name"]
            
            # 保存测试图像
            try:
                with open("diag_test.jpg", "wb") as f:
                    f.write(buf)
                print("✓ 测试图像已保存为 'diag_test.jpg'")
            except Exception as e:
                print(f"✗ 保存失败：{e}")
        else:
            print("✗ 捕获失败：返回空数据")
        
        # 释放摄像头
        camera.deinit()
        
        if buf and len(buf) > 0:
            break  # 成功后退出
            
    except Exception as e:
        print(f"✗ 初始化失败：{type(e).__name__}: {e}")
        try:
            camera.deinit()
        except:
            pass

print("\n" + "=" * 60)
if success_config:
    print(f"诊断结果：找到可用配置 - {success_config}")
    print("建议：在 camera_stream.py 中使用此配置")
else:
    print("诊断结果：所有配置都失败！")
    print("可能原因:")
    print("  1. 摄像头未正确连接")
    print("  2. 摄像头硬件损坏")
    print("  3. 电源供电不足")
    print("  4. 引脚配置错误")
    print("\n建议检查:")
    print("  - 重新插拔摄像头排线")
    print("  - 检查 5V/3.3V 电源连接")
    print("  - 确认是 OV2640 摄像头")
print("=" * 60)
