# ============================================================
#  摄像头采集 & UDP 视频流上传模块 — camera_stream.py
#  硬件：OV2640 + ESP32-S3，JPEG 硬件压缩
#  协议：UDP 分包上行，帧头格式见下
# ============================================================
#
#  帧分包格式（每个 UDP 包）：
#  [ MAGIC(2B) | FRAME_ID(2B) | TOTAL_CHUNKS(2B) | CHUNK_IDX(2B) | PAYLOAD ]
#  MAGIC = 0xAA 0xBB
#
import socket
import camera          # MicroPython ESP32 camera 驱动
import uasyncio as asyncio
import struct
import time
from config import PC_IP, UDP_PORT, CAM_FRAMESIZE, CAM_QUALITY, CHUNK_SIZE, CAM_FPS

MAGIC = b'\xaa\xbb'
HEADER_SIZE = 8  # MAGIC(2) + FRAME_ID(2) + TOTAL(2) + IDX(2)

# 增加摄像头初始化锁，避免并发重复初始化
camera_init_lock = False

def _init_camera(retry=3):
    """带重试机制的摄像头初始化（兼容不同 ESP32-CAM 模块）"""
    global camera_init_lock
    if camera_init_lock:
        return False
    camera_init_lock = True
    try:
        # 先释放旧资源
        try:
            camera.deinit()
        except:
            pass
        
        # 重试初始化（使用 ceshi.py 的成功配置，移除 fb_location 参数）
        for i in range(retry):
            try:
                # 使用 FRAME_VGA 分辨率，不指定 fb_location（提高兼容性）
                camera.init(0,
                            format=camera.JPEG,
                            framesize=camera.FRAME_VGA,  # 640x480
                            quality=CAM_QUALITY)
                print("[Camera] 初始化成功，分辨率 640×480 JPEG")
                camera_init_lock = False
                return True
            except Exception as e:
                # 打印详细错误类型，便于调试
                print(f"[Camera] 初始化重试 {i+1}/{retry} 失败：{type(e).__name__}: {e}")
                time.sleep(0.5)
        
        # 如果标准初始化失败，尝试最低分辨率
        print("[Camera] 尝试降低分辨率到 QVGA...")
        try:
            camera.init(0,
                        format=camera.JPEG,
                        framesize=camera.FRAME_QVGA,  # 320x240
                        quality=20)  # 降低质量
            print("[Camera] 降级初始化成功，分辨率 320×240 JPEG")
            camera_init_lock = False
            return True
        except Exception as e:
            print(f"[Camera] 降级初始化也失败：{type(e).__name__}: {e}")
        
        camera_init_lock = False
        return False
    except Exception as e:
        print(f"[Camera] 初始化致命错误：{type(e).__name__}: {e}")
        camera_init_lock = False
        return False

def _split_frame(frame_bytes, frame_id):
    """将一帧 JPEG 拆分为多个 UDP 包"""
    chunks = []
    total = (len(frame_bytes) + CHUNK_SIZE - 1) // CHUNK_SIZE
    for i in range(total):
        payload = frame_bytes[i * CHUNK_SIZE: (i + 1) * CHUNK_SIZE]
        header = MAGIC + struct.pack(">HHH", frame_id & 0xFFFF, total, i)
        chunks.append(header + payload)
    return chunks

class CameraStreamer:
    def __init__(self):
        self.udp_sock = None
        self.pc_addr  = (PC_IP, UDP_PORT)
        self.frame_id = 0
        self.running  = False
        # 延迟初始化摄像头，避免资源抢占
        self.cam_ready = False

    async def init_resources(self):
        """异步初始化资源（避免阻塞主线程）"""
        if self.udp_sock is None:
            self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # 异步初始化摄像头（带重试）
        # 【仅修复这行】移除不支持的 to_thread，同步调用初始化函数
        self.cam_ready = _init_camera()
        if not self.cam_ready:
            print("[Camera] 资源初始化失败，将在5秒后重试")
            await asyncio.sleep(5)
            # 【仅修复这行】移除不支持的 to_thread，同步调用初始化函数
            self.cam_ready = _init_camera()

    async def stream_loop(self):
        """协程：持续采集并发送视频帧（增强容错 + 内存管理）"""
        self.running = True
        # 先初始化资源
        await self.init_resources()
        if not self.cam_ready:
            print("[Camera] 最终初始化失败，退出流循环")
            self.running = False
            return
    
        target_interval = 1.0 / CAM_FPS  # 使用配置文件中的 FPS
        gc_collect_count = 0
            
        while self.running:
            t0 = time.ticks_ms()
            try:
                # 捕获单帧异常（不终止整个循环）
                buf = None
                try:
                    buf = camera.capture()
                except Exception as e:
                    print(f"[Camera] 单帧采集失败：{type(e).__name__}: {e}")
                    await asyncio.sleep_ms(50)
                    continue
    
                if buf and len(buf) > 0:
                    chunks = _split_frame(buf, self.frame_id)
                    sent_count = 0
                        
                    # 分批发送，降低 UDP 发包速率
                    for idx, pkt in enumerate(chunks):
                        try:
                            self.udp_sock.sendto(pkt, self.pc_addr)
                            sent_count += 1
                            # 每发送 5 个包短暂延迟，避免网络拥塞
                            if idx % 5 == 0:
                                await asyncio.sleep_ms(2)
                        except Exception as e:
                            # 静默失败，避免过多打印占用串口
                            pass
                        await asyncio.sleep_ms(1)  # 防止 UDP 拥塞
                        
                    # 只有成功发送部分数据才计数
                    if sent_count > len(chunks) * 0.5:  # 超过 50% 成功
                        self.frame_id = (self.frame_id + 1) % 65536
                        
                    # 显式释放缓冲区
                    del chunks
                    del buf
                        
                    # 定期垃圾回收（每 10 帧一次）
                    gc_collect_count += 1
                    if gc_collect_count >= 10:
                        import gc
                        gc.collect()
                        gc_collect_count = 0
    
            except Exception as e:
                print(f"[Camera] 流循环异常（非致命）: {type(e).__name__}: {e}")
                # 发生异常时强制垃圾回收
                import gc
                gc.collect()
    
            # 动态调整等待时间，保证帧率稳定
            elapsed = (time.ticks_ms() - t0) / 1000.0
            wait = max(0, target_interval - elapsed)
            await asyncio.sleep(wait)

    def stop(self):
        """安全停止流并释放资源（关键：避免资源泄漏）"""
        self.running = False
        self.cam_ready = False
        # 关闭UDP套接字
        if self.udp_sock:
            try:
                self.udp_sock.close()
            except:
                pass
            self.udp_sock = None
        # 释放摄像头资源
        try:
            camera.deinit()
        except:
            pass
        global camera_init_lock
        camera_init_lock = False
        print("[Camera] 资源已安全释放")