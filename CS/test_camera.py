import camera
import time

try:
    # 填入你的ESP32-S3引脚配置
    camera.init(
        pin_pwdn=32, pin_reset=-1, pin_xclk=15,
        pin_sscb_sda=4, pin_sscb_scl=5,
        pin_d7=16, pin_d6=17, pin_d5=18, pin_d4=12,
        pin_d3=10, pin_d2=8, pin_d1=9, pin_d0=11,
        pin_vsync=6, pin_href=7, pin_pclk=13,
        xclk_freq_hz=20000000,
        frame_size=camera.FRAMESIZE_QVGA,
        fb_count=1
    )
    print("[Camera] 初始化成功！")
    # 尝试拍一张图验证
    buf = camera.capture()
    print(f"[Camera] 捕获成功，图片大小: {len(buf)} 字节")
    camera.deinit()
except Exception as e:
    print(f"[Camera] 初始化失败: {e}")