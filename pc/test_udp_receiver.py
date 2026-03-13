#!/usr/bin/env python3
# ============================================================
#  PC 端视频流测试接收器 — 用于单独测试 UDP 接收
#  使用方法：python test_udp_receiver.py
# ============================================================
import socket
import struct
import time
import cv2
import numpy as np
from collections import defaultdict

MAGIC = b'\xaa\xbb'
HEADER_SIZE = 8
TIMEOUT_SEC = 1.0

class FrameAssembler:
    """单路设备的帧重组器"""
    def __init__(self):
        self._frames = {}

    def feed(self, frame_id, total, idx, payload):
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


def test_receiver():
    """测试 UDP 视频流接收"""
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 1 << 20)
    sock.bind(("0.0.0.0", 5600))
    sock.settimeout(1.0)
    
    assembler = FrameAssembler()
    stats = {"recv": 0, "frames": 0, "start_time": time.time()}
    
    print("=" * 60)
    print("PC 端 UDP 视频流测试接收器")
    print("=" * 60)
    print(f"监听端口：UDP 5600")
    print(f"等待 ESP32 发送视频流...")
    print("按 Ctrl+C 停止")
    print("=" * 60)
    
    try:
        while True:
            try:
                data, (ip, port) = sock.recvfrom(65535)
            except socket.timeout:
                continue
            
            # 检查魔数
            if len(data) < HEADER_SIZE or data[:2] != MAGIC:
                continue
            
            # 解析头部
            frame_id, total, idx = struct.unpack(">HHH", data[2:8])
            payload = data[HEADER_SIZE:]
            
            stats["recv"] += 1
            
            # 重组帧
            complete = assembler.feed(frame_id, total, idx, payload)
            if complete is None:
                continue
            
            stats["frames"] += 1
            
            # 解码并显示
            arr = np.frombuffer(complete, dtype=np.uint8)
            frame = cv2.imdecode(arr, cv2.IMREAD_COLOR)
            
            if frame is not None:
                elapsed = time.time() - stats["start_time"]
                fps = stats["frames"] / elapsed if elapsed > 0 else 0
                
                print(f"[{time.strftime('%H:%M:%S')}] "
                      f"收到帧 #{stats['frames']} | "
                      f"尺寸：{frame.shape[1]}x{frame.shape[0]} | "
                      f"数据量：{len(complete)/1024:.1f} KB | "
                      f"平均 FPS: {fps:.1f} | "
                      f"源：{ip}:{port}")
                
                # 显示窗口
                cv2.putText(frame, f"FPS: {fps:.1f} | Packets: {stats['recv']}",
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.imshow("Test Video Stream", frame)
                
                # 按 Q 键退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
    
    except KeyboardInterrupt:
        print("\n用户停止测试")
    finally:
        sock.close()
        cv2.destroyAllWindows()
        
        elapsed = time.time() - stats["start_time"]
        print("=" * 60)
        print(f"测试统计:")
        print(f"  总数据包：{stats['recv']}")
        print(f"  完整帧数：{stats['frames']}")
        print(f"  平均 FPS: {stats['frames']/elapsed:.1f}" if elapsed > 0 else "  无数据")
        print("=" * 60)


if __name__ == "__main__":
    test_receiver()
