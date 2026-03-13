# ============================================================
#  音频预警播报模块 — audio_player.py
#  硬件：MAX98357A I2S 功放
#  功能：根据指令从 PC 端流式接收并播放 WAV 音频
# ============================================================
import uasyncio as asyncio
import machine
import socket
from config import I2S_BCK_PIN, I2S_WS_PIN, I2S_DATA_PIN, AUDIO_RATE, WARN_CMD_MAP, PC_IP


class AudioPlayer:
    CHUNK = 1024  # 每次读取字节数
    AUDIO_PORT = 5603  # PC 端音频服务端口

    def __init__(self):
        self.i2s = machine.I2S(
            0,
            sck=machine.Pin(I2S_BCK_PIN),
            ws=machine.Pin(I2S_WS_PIN),
            sd=machine.Pin(I2S_DATA_PIN),
            mode=machine.I2S.TX,
            bits=16,
            format=machine.I2S.MONO,
            rate=AUDIO_RATE,
            ibuf=4096,
        )
        self._playing   = False
        self._stop_flag = False
        self._tcp_sock = None

    def _file_exists(self, path):
        """检查 PC 端文件是否存在（通过 TCP 询问）"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(3)
            sock.connect((PC_IP, self.AUDIO_PORT))
            request = f"CHECK:{path}\n".encode()
            sock.send(request)
            response = sock.recv(64).decode().strip()
            sock.close()
            return response == "EXISTS"
        except:
            return False

    async def play(self, wav_path: str, loop: bool = False):
        """从 PC 端流式接收并播放 WAV 文件；loop=True 时循环播放"""
        self._playing   = True
        self._stop_flag = False
        try:
            while True:
                # 连接 PC 端音频服务器
                try:
                    self._tcp_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    self._tcp_sock.settimeout(5)
                    print(f"[Audio] 正在请求：{wav_path}")
                    self._tcp_sock.connect((PC_IP, self.AUDIO_PORT))
                    
                    # 发送文件路径请求
                    request = f"{wav_path}\n".encode()
                    self._tcp_sock.send(request)
                    
                    # 接收文件头信息
                    header = b""
                    while b"\n" not in header:
                        chunk = self._tcp_sock.recv(1)
                        if not chunk:
                            raise Exception("连接断开")
                        header += chunk
                    
                    header_str = header.decode().strip()
                    if header_str.startswith("ERROR"):
                        print(f"[Audio] 服务器错误：{header_str}")
                        break
                    
                    if not header_str.startswith("SIZE:"):
                        print(f"[Audio] 无效的响应头：{header_str}")
                        break
                    
                    file_size = int(header_str.split(":")[1])
                    print(f"[Audio] 开始接收：{wav_path} ({file_size} bytes)")
                    
                    # 跳过 WAV 文件头（44 字节）
                    skipped = 0
                    while skipped < 44:
                        chunk = self._tcp_sock.recv(44 - skipped)
                        if not chunk:
                            break
                        skipped += len(chunk)
                    
                    # 循环读取并播放音频数据
                    total_received = 0
                    while True:
                        if self._stop_flag:
                            break
                        
                        # 从网络接收音频数据
                        buf = self._tcp_sock.recv(self.CHUNK)
                        if not buf:
                            break  # 文件结束
                        
                        total_received += len(buf)
                        
                        # 写入 I2S 播放
                        n = self.i2s.write(buf)
                        await asyncio.sleep_ms(5)  # 短暂延迟，避免缓冲区溢出
                    
                    print(f"[Audio] 播放完成：{total_received} bytes")
                    
                except Exception as e:
                    print(f"[Audio] 流式接收失败：{type(e).__name__}: {e}")
                finally:
                    if self._tcp_sock:
                        try:
                            self._tcp_sock.close()
                        except:
                            pass
                        self._tcp_sock = None
                
                if not loop or self._stop_flag:
                    break
                    
        except Exception as e:
            print(f"[Audio] 播放异常：{e}")
        finally:
            self._playing   = False
            self._stop_flag = False

    def stop(self):
        self._stop_flag = True

    async def handle_command(self, cmd: bytes, level: int = 1):
        """
        根据预警指令触发播放
        level 1: 单次播放
        level 2/3: 循环播放（需 PC 下发 stop 指令停止）
        """
        if cmd == b"stop":
            self.stop()
            return
        wav = WARN_CMD_MAP.get(cmd)
        if wav is None:
            print("[Audio] 未知指令:", cmd)
            return
        self.stop()
        await asyncio.sleep_ms(100)
        loop = (level >= 2)
        asyncio.create_task(self.play(wav, loop=loop))
