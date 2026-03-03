# ============================================================
#  心跳监测模块 — core/heartbeat_monitor.py
#  功能：接收 ESP32 UDP 心跳，维护设备在线表，超时标记离线
# ============================================================
import socket
import json
import threading
import time
from core.config import UDP_HB_PORT, DEVICE_TIMEOUT


class HeartbeatMonitor:
    """
    设备在线状态表：
      devices = {
        device_id: {
          "ip": str,
          "last_seen": float,
          "online": bool,
          "seq": int
        }
      }
    线程安全（读写加锁）。
    """

    def __init__(self, on_status_change=None):
        """
        on_status_change: fn(device_id, online: bool)
        """
        self.devices = {}
        self._lock   = threading.Lock()
        self._on_change = on_status_change
        self._running   = False
        self._thread    = None
        self._sock      = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    def start(self):
        self._sock.bind(("0.0.0.0", UDP_HB_PORT))
        self._sock.settimeout(1.0)
        self._running = True
        self._thread  = threading.Thread(target=self._recv_loop,
                                          daemon=True, name="HBMonitor")
        self._thread.start()
        # 启动超时检测线程
        threading.Thread(target=self._timeout_loop,
                         daemon=True, name="HBTimeout").start()
        print(f"[HBMonitor] 监听 UDP:{UDP_HB_PORT}")

    def stop(self):
        self._running = False
        self._sock.close()

    def get_devices(self):
        with self._lock:
            return dict(self.devices)

    def is_online(self, device_id):
        with self._lock:
            return self.devices.get(device_id, {}).get("online", False)

    def _recv_loop(self):
        while self._running:
            try:
                data, (ip, _) = self._sock.recvfrom(512)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                pkt = json.loads(data.decode())
            except Exception:
                continue
            if pkt.get("type") != "heartbeat":
                continue
            dev_id = pkt.get("device_id", ip)
            with self._lock:
                was_online = self.devices.get(dev_id, {}).get("online", False)
                self.devices[dev_id] = {
                    "ip":        ip,
                    "last_seen": time.time(),
                    "online":    True,
                    "seq":       pkt.get("seq", 0),
                }
                if not was_online and self._on_change:
                    self._on_change(dev_id, True)

    def _timeout_loop(self):
        while self._running:
            time.sleep(2)
            now = time.time()
            with self._lock:
                for dev_id, info in self.devices.items():
                    if info["online"] and now - info["last_seen"] > DEVICE_TIMEOUT:
                        info["online"] = False
                        print(f"[HBMonitor] 设备离线: {dev_id}")
                        if self._on_change:
                            self._on_change(dev_id, False)
