# ============================================================
#  视频流测试脚本 — 用于单独测试摄像头采集和 UDP 发送
#  使用方法：在 Thonny 中运行此文件，观察串口输出
# ============================================================
import socket
import camera
import uasyncio as asyncio
import struct
import time

# 配置参数
PC_IP = "192.168.137.1"
UDP_PORT = 5600
CHUNK_SIZE = 1400
MAGIC = b'\xaa\xbb'
HEADER_SIZE = 8

def _init_camera():
    """初始化摄像头（使用 ceshi.py 的成功配置）"""
    try:
        camera.deinit()
    except:
        pass
    
    print("[Camera] 正在初始化...")
    camera.init(0,
                format=camera.JPEG,
                framesize=camera.FRAME_VGA,  # 640x480
                quality=15,
                fb_location=camera.PSRAM)
    print("[Camera] 初始化成功！")
    return True

def _split_frame(frame_bytes, frame_id):
    """将一帧 JPEG 拆分为多个 UDP 包"""
    chunks = []
    total = (len(frame_bytes) + CHUNK_SIZE - 1) // CHUNK_SIZE
    for i in range(total):
        payload = frame_bytes[i * CHUNK_SIZE: (i + 1) * CHUNK_SIZE]
        header = MAGIC + struct.pack(">HHH", frame_id & 0xFFFF, total, i)
        chunks.append(header + payload)
    return chunks

async def test_stream():
    """测试视频流发送"""
    # 初始化摄像头
    cam_ok = _init_camera()
    if not cam_ok:
        print("[ERROR] 摄像头初始化失败！")
        return
    
    # 创建 UDP 套接字
    udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    pc_addr = (PC_IP, UDP_PORT)
    
    print(f"[INFO] 开始发送视频流到 {PC_IP}:{UDP_PORT}")
    print("[INFO] 按 Ctrl+C 停止")
    
    frame_id = 0
    sent_frames = 0
    total_bytes = 0
    
    try:
        while True:
            t0 = time.ticks_ms()
            
            # 捕获一帧
            buf = camera.capture()
            
            if buf and len(buf) > 0:
                # 拆分并发送
                chunks = _split_frame(buf, frame_id)
                for pkt in chunks:
                    udp_sock.sendto(pkt, pc_addr)
                    await asyncio.sleep_ms(1)  # 降低发送速率
                
                frame_id = (frame_id + 1) % 65536
                sent_frames += 1
                total_bytes += len(buf)
                
                elapsed = time.ticks_ms() - t0
                fps = 1000 / elapsed if elapsed > 0 else 0
                
                print(f"[STATS] 已发送：{sent_frames} 帧 | "
                      f"数据量：{total_bytes/1024:.1f} KB | "
                      f"当前 FPS: {fps:.1f}")
            
            # 控制帧率 ~10 FPS
            await asyncio.sleep(0.1)
            
    except KeyboardInterrupt:
        print("\n[INFO] 用户停止测试")
    finally:
        udp_sock.close()
        camera.deinit()
        print(f"[SUMMARY] 总共发送 {sent_frames} 帧，{total_bytes/1024:.1f} KB 数据")

# 运行测试
try:
    asyncio.run(test_stream())
except Exception as e:
    print(f"[ERROR] 测试失败：{e}")
    camera.deinit()
