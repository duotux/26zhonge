# ============================================================
#  TCP 指令接收模块 — cmd_receiver.py
#  功能：监听 PC 下发的 TCP 指令，解析后回调处理函数
#
#  指令帧格式（纯文本行，\n 结尾）：
#    WARN:<cmd>:<level>\n
#    e.g.  WARN:warn1:1\n  WARN:stop:0\n
# ============================================================
import uasyncio as asyncio
import socket
from config import TCP_PORT


class CmdReceiver:
    def __init__(self, on_command_cb):
        """
        on_command_cb: async fn(cmd: bytes, level: int)
        """
        self.on_command = on_command_cb
        self._server    = None
        self.running    = False

    async def start(self):
        self.running = True
        srv = asyncio.start_server(self._handle_client, "0.0.0.0", TCP_PORT)
        self._server = await srv
        print(f"[CMD] TCP 指令服务器监听端口 {TCP_PORT}")

    async def _handle_client(self, reader, writer):
        addr = writer.get_extra_info("peername")
        print(f"[CMD] PC 连接: {addr}")
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                line = line.strip()
                if line.startswith(b"WARN:"):
                    parts = line.split(b":")
                    if len(parts) >= 3:
                        cmd   = parts[1]
                        level = int(parts[2])
                        print(f"[CMD] 收到指令: {cmd}  等级: {level}")
                        asyncio.create_task(self.on_command(cmd, level))
                        writer.write(b"ACK\n")
                        await writer.drain()
        except Exception as e:
            print("[CMD] 客户端异常:", e)
        finally:
            writer.close()
            await writer.wait_closed()
