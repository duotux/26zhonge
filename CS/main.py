# ============================================================
#  ESP32 主程序入口 — main.py
#  校园实验室安全智能管控系统 · 终端固件
#
#  运行环境：MicroPython v1.22+ / ESP32-S3-N16R8
#  上电自动执行，协程并发：摄像头流 + 心跳 + 指令监听
# ============================================================
import uasyncio as asyncio
import time
import sys

from wifi_manager   import WiFiManager
from camera_stream  import CameraStreamer
from audio_player   import AudioPlayer
from cmd_receiver   import CmdReceiver
from heartbeat      import Heartbeat


# ── 全局单例 ──────────────────────────────────────────────
wifi    = WiFiManager()
streamer = None
player   = AudioPlayer()
hb       = Heartbeat(device_id="ESP32_01")


async def on_command(cmd: bytes, level: int):
    """指令回调：由 CmdReceiver 触发，交给 AudioPlayer 处理"""
    await player.handle_command(cmd, level)


async def main():
    # 1. 连接 WiFi（最多等待 30 秒）
    connected = wifi.connect(timeout=30)
    if not connected:
        print("[MAIN] WiFi 连接失败，60 秒后重启")
        await asyncio.sleep(60)
        import machine
        machine.reset()

    # 2. 初始化摄像头流
    global streamer
    streamer = CameraStreamer()

    # 3. 启动 TCP 指令服务器
    cmd_recv = CmdReceiver(on_command_cb=on_command)
    await cmd_recv.start()

    # 4. 并发启动：视频流 + 心跳 + WiFi 看门狗
    asyncio.create_task(streamer.stream_loop())
    asyncio.create_task(hb.beat_loop())
    asyncio.create_task(_wifi_watchdog())

    print("[MAIN] 系统启动完成，开始运行...")
    # 主循环保活
    while True:
        await asyncio.sleep(60)


async def _wifi_watchdog():
    """每 10 秒检测 WiFi，断线自动重连，恢复后重启摄像头流"""
    global streamer
    while True:
        await asyncio.sleep(10)
        if not wifi.ensure_connected():
            print("[WATCHDOG] WiFi 断线，等待重连...")
            if streamer:
                streamer.stop()
            # 等待 WiFi 恢复后重新创建流
            while not wifi.ensure_connected():
                await asyncio.sleep(3)
            streamer = CameraStreamer()
            asyncio.create_task(streamer.stream_loop())
            print("[WATCHDOG] WiFi 恢复，视频流已重启")


# ── 程序入口 ───────────────────────────────────────────────
try:
    asyncio.run(main())
except KeyboardInterrupt:
    print("[MAIN] 手动终止")
except Exception as e:
    print("[MAIN] 致命异常:", e)
    time.sleep(5)
    import machine
    machine.reset()
