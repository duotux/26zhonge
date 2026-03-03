# ============================================================
#  视频流接收与重组模块 — core/stream_receiver.py
#
#  负责：
#    1. UDP 接收来自多个 ESP32 的分包 JPEG 帧
#    2. 按 frame_id 重组完整帧
#    3. OpenCV 解码 → 存入帧队列供 AI 消费
#    4. 支持多设备（device_id 按源 IP 区分）
# ============================================================
import socket
import struct
import threading
import time
import cv2
import numpy as np
from collections import defaultdict
from queue import Queue, Full
from core.config import UDP_VIDEO_PORT

MAGIC       = b'\xaa\xbb'
HEADER_SIZE = 8   # MAGIC(2) + FRAME_ID(2) + TOTAL(2) + IDX(2)
TIMEOUT_SEC = 1.0 # 超时未收齐的帧丢弃
MAX_QUEUE   = 4   # 每路设备帧队列深度，防内存溢出


class FrameAssembler:
    """单路设备的帧重组器"""
    def __init__(self):
        # {frame_id: {"total": N, "chunks": {idx: bytes}, "ts": float}}
        self._frames = {}

    def feed(self, frame_id, total, idx, payload):
        """
        喂入一个分包，若重组完成返回完整 JPEG bytes，否则返回 None
        """
        now = time.time()
        # 清理超时帧
        expired = [fid for fid, f in self._frames.items()
                   if now - f["ts"] > TIMEOUT_SEC]
        for fid in expired:
            del self._frames[fid]

        if frame_id not in self._frames:
            self._frames[frame_id] = {"total": total, "chunks": {}, "ts": now}
        frame = self._frames[frame_id]
        frame["chunks"][idx] = payload

        if len(frame["chunks"]) == frame["total"]:
            data = b"".join(frame["chunks"][i] for i in range(frame["total"]))
            del self._frames[frame_id]
            return data
        return None


class StreamReceiver:
    """
    多设备 UDP 视频流接收器。
    收到完整帧后 OpenCV 解码并放入 per-device 帧队列。
    外部通过 get_frame(device_ip) 获取最新帧。
    """

    def __init__(self, on_new_frame=None):
        """
        on_new_frame: 可选回调 fn(device_ip: str, frame: np.ndarray)
                      在接收线程中被调用，注意线程安全
        """
        self._sock        = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
        self._sock.bind(("0.0.0.0", UDP_VIDEO_PORT))
        self._sock.settimeout(1.0)

        self._assemblers  = defaultdict(FrameAssembler)  # ip → assembler
        self._queues      = defaultdict(lambda: Queue(MAX_QUEUE))  # ip → Queue
        self._on_new_frame = on_new_frame

        self._running     = False
        self._thread      = None

        # 统计
        self.stats = defaultdict(lambda: {"recv": 0, "drop": 0, "fps": 0.0,
                                           "_t0": time.time(), "_cnt": 0})

    # ── 公开 API ──────────────────────────────────────────
    def start(self):
        self._running = True
        self._thread  = threading.Thread(target=self._recv_loop,
                                          daemon=True, name="StreamRecv")
        self._thread.start()
        print(f"[StreamReceiver] 监听 UDP:{UDP_VIDEO_PORT}")

    def stop(self):
        self._running = False
        self._sock.close()

    def get_frame(self, device_ip: str):
        """非阻塞获取指定设备最新帧 (np.ndarray BGR)，无帧返回 None"""
        q = self._queues[device_ip]
        frame = None
        while not q.empty():
            frame = q.get_nowait()
        return frame

    def device_list(self):
        return list(self._queues.keys())

    # ── 内部逻辑 ─────────────────────────────────────────
    def _recv_loop(self):
        while self._running:
            try:
                data, (ip, _) = self._sock.recvfrom(65535)
            except socket.timeout:
                continue
            except OSError:
                break

            if len(data) < HEADER_SIZE or data[:2] != MAGIC:
                continue

            frame_id, total, idx = struct.unpack(">HHH", data[2:8])
            payload = data[HEADER_SIZE:]

            complete = self._assemblers[ip].feed(frame_id, total, idx, payload)
            if complete is None:
                continue

            # JPEG → BGR
            arr = np.frombuffer(complete, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            if frame is None:
                continue

            # 更新 FPS 统计
            s = self.stats[ip]
            s["recv"]  += 1
            s["_cnt"]  += 1
            elapsed = time.time() - s["_t0"]
            if elapsed >= 2.0:
                s["fps"]  = s["_cnt"] / elapsed
                s["_cnt"] = 0
                s["_t0"]  = time.time()

            # 放入队列（满了就丢最旧帧）
            q = self._queues[ip]
            if q.full():
                try:
                    q.get_nowait()
                    s["drop"] += 1
                except Exception:
                    pass
            try:
                q.put_nowait(frame)
            except Full:
                pass

            if self._on_new_frame:
                try:
                    self._on_new_frame(ip, frame)
                except Exception:
                    pass
