# ============================================================
#  WiFi 连接管理 — wifi_manager.py
# ============================================================
import network
import time
from config import WIFI_SSID, WIFI_PASSWORD, STATIC_IP, SUBNET_MASK, GATEWAY, DNS_SERVER


class WiFiManager:
    def __init__(self):
        self.wlan = network.WLAN(network.STA_IF)
        self.connected = False

    def connect(self, timeout=20):
        self.wlan.active(True)
        self.wlan.ifconfig((STATIC_IP, SUBNET_MASK, GATEWAY, DNS_SERVER))
        if not self.wlan.isconnected():
            print("[WiFi] 正在连接:", WIFI_SSID)
            self.wlan.connect(WIFI_SSID, WIFI_PASSWORD)
            t = 0
            while not self.wlan.isconnected() and t < timeout:
                time.sleep(1)
                t += 1
                print(f"[WiFi] 等待连接... {t}s")
        self.connected = self.wlan.isconnected()
        if self.connected:
            print("[WiFi] 连接成功:", self.wlan.ifconfig())
        else:
            print("[WiFi] 连接超时，请检查热点配置")
        return self.connected

    def ensure_connected(self):
        """断网检测，自动重连"""
        if not self.wlan.isconnected():
            print("[WiFi] 断网，尝试重连...")
            self.connected = False
            self.connect()
        return self.wlan.isconnected()

    def ip(self):
        return self.wlan.ifconfig()[0]
