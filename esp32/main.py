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
    try:
        await player.handle_command(cmd, level)
    except Exception as e:
        print("[CMD] 指令处理异常:", e)


async def main():
    # 1. 连接 WiFi（最多等待 30 秒）
    connected = wifi.connect(timeout=30)
    if not connected:
        print("[MAIN] WiFi 连接失败，60 秒后重启")
        await asyncio.sleep(60)
        import machine
        machine.reset()

    # 2. 初始化摄像头流（延迟初始化，避免资源竞争）
    global streamer
    streamer = CameraStreamer()

    # 3. 启动 TCP 指令服务器
    cmd_recv = CmdReceiver(on_command_cb=on_command)
    await cmd_recv.start()

    # 4. 并发启动：视频流 + 心跳 + WiFi 看门狗（降低启动并发压力）
    await asyncio.sleep(1)  # 给系统1秒缓冲
    asyncio.create_task(streamer.stream_loop())
    await asyncio.sleep(0.5)
    asyncio.create_task(hb.beat_loop())
    asyncio.create_task(_wifi_watchdog())

    print("[MAIN] 系统启动完成，开始运行...")
    # 主循环保活
    while True:
        await asyncio.sleep(60)


async def _wifi_watchdog():
    """每 10 秒检测 WiFi，断线自动重连（优化摄像头重启逻辑）"""
    global streamer
    while True:
        await asyncio.sleep(10)
        if not wifi.ensure_connected():
            print("[WATCHDOG] WiFi 断线，等待重连...")
            # 安全停止摄像头（增加延迟，确保资源释放）
            if streamer:
                streamer.stop()
                await asyncio.sleep(1)  # 等待1秒释放资源
            # 等待 WiFi 恢复
            retry_count = 0
            while not wifi.ensure_connected() and retry_count < 20:
                await asyncio.sleep(3)
                retry_count += 1
            # WiFi恢复后重新初始化摄像头
            if wifi.ensure_connected():
                streamer = CameraStreamer()
                await asyncio.sleep(0.5)
                asyncio.create_task(streamer.stream_loop())
                print("[WATCHDOG] WiFi 恢复，视频流已重启")
            else:
                print("[WATCHDOG] WiFi 重连失败，将在30秒后重试")


# ── 程序入口（优化异常处理，避免串口乱码）──────────────────────
if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        # 中文转ASCII，避免串口编码乱码导致的异常
        print("[MAIN] Manual stop (用户手动终止)")
    except Exception as e:
        # 捕获所有异常并简化输出，避免串口解析错误
        print(f"[MAIN] Fatal error: {str(e)}")
        # 安全释放资源
        if streamer:
            streamer.stop()
        hb.stop()
        time.sleep(5)
        # 重启设备
        import machine
        machine.reset()