# test_stream_only.py
import network
import uasyncio as asyncio
import time
from config import WIFI_SSID, WIFI_PASSWORD, STATIC_IP, SUBNET_MASK, GATEWAY, DNS_SERVER
from camera_stream import CameraStreamer

def connect_wifi_simple():
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    wlan.ifconfig((STATIC_IP, SUBNET_MASK, GATEWAY, DNS_SERVER))
    
    if not wlan.isconnected():
        print(f"[WiFi] 连接 {WIFI_SSID}...")
        wlan.connect(WIFI_SSID, WIFI_PASSWORD)
        for _ in range(10):
            if wlan.isconnected():
                break
            time.sleep(1)
    
    if wlan.isconnected():
        print(f"[WiFi] 连接成功 | IP: {wlan.ifconfig()[0]}")
        return True
    else:
        print("[WiFi] 连接失败！")
        return False

async def main():
    if not connect_wifi_simple():
        return

    streamer = CameraStreamer()
    try:
        await streamer.stream_loop()
    except KeyboardInterrupt:
        print("[Test] 停止视频流")
    finally:
        streamer.stop()
        print("[Test] 资源已释放")

if __name__ == "__main__":
    asyncio.run(main())