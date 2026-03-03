# ============================================================
#  心跳包模块 — heartbeat.py
#  功能：定时向 PC 发送 UDP 心跳，携带设备状态
# ============================================================
import uasyncio as asyncio
import socket
import ujson
import time
from config import PC_IP, HEARTBEAT_PORT, HEARTBEAT_INTERVAL, STATIC_IP


class Heartbeat:
    def __init__(self, device_id: str = "ESP32_01"):
        self.device_id = device_id
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.pc_addr = (PC_IP, HEARTBEAT_PORT)
        self.running = False

    async def beat_loop(self):
        self.running = True
        seq = 0
        while self.running:
            payload = ujson.dumps({
                "type":      "heartbeat",
                "device_id": self.device_id,
                "ip":        STATIC_IP,
                "seq":       seq,
                "ts":        time.time(),
            }).encode()
            try:
                self.sock.sendto(payload, self.pc_addr)
            except Exception as e:
                print("[HB] 发送失败:", e)
            seq += 1
            await asyncio.sleep(HEARTBEAT_INTERVAL)

    def stop(self):
        self.running = False
        self.sock.close()
