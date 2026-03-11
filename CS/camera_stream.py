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
from config import PC_IP, UDP_PORT, CAM_FRAMESIZE, CAM_QUALITY, CHUNK_SIZE


MAGIC = b'\xaa\xbb'
HEADER_SIZE = 8  # MAGIC(2) + FRAME_ID(2) + TOTAL(2) + IDX(2)


def _init_camera():
    camera.init(0,
                format=camera.JPEG,
                framesize=CAM_FRAMESIZE,
                quality=CAM_QUALITY,
                fb_location=camera.PSRAM)
    print("[Camera] 初始化成功，分辨率 320×240 JPEG")


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
        self.udp_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pc_addr  = (PC_IP, UDP_PORT)
        self.frame_id = 0
        self.running  = False
        _init_camera()

    async def stream_loop(self):
        """协程：持续采集并发送视频帧"""
        self.running = True
        target_interval = 1.0 / 12  # 12 FPS
        while self.running:
            t0 = time.ticks_ms()
            try:
                buf = camera.capture()
                if buf:
                    chunks = _split_frame(buf, self.frame_id)
                    for pkt in chunks:
                        self.udp_sock.sendto(pkt, self.pc_addr)
                        await asyncio.sleep_ms(1)  # 防止 UDP 发送过快丢包
                    self.frame_id = (self.frame_id + 1) % 65536
            except Exception as e:
                print("[Camera] 采集异常:", e)
            elapsed = (time.ticks_ms() - t0) / 1000.0
            wait = max(0, target_interval - elapsed)
            await asyncio.sleep(wait)

    def stop(self):
        self.running = False
        self.udp_sock.close()
        camera.deinit()
