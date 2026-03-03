# ============================================================
#  音频预警播报模块 — audio_player.py
#  硬件：MAX98357A I2S 功放
#  功能：根据指令播放对应 WAV 音频，支持等级控制
# ============================================================
import uasyncio as asyncio
import machine
import os
from config import I2S_BCK_PIN, I2S_WS_PIN, I2S_DATA_PIN, AUDIO_RATE, WARN_CMD_MAP


class AudioPlayer:
    CHUNK = 1024  # 每次读取字节数

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

    def _file_exists(self, path):
        try:
            os.stat(path)
            return True
        except OSError:
            return False

    async def play(self, wav_path: str, loop: bool = False):
        """播放 WAV 文件；loop=True 时循环，直到 stop() 被调用"""
        if not self._file_exists(wav_path):
            print("[Audio] 文件不存在:", wav_path)
            return
        self._playing   = True
        self._stop_flag = False
        try:
            while True:
                with open(wav_path, "rb") as f:
                    f.seek(44)  # 跳过 WAV 文件头
                    while True:
                        if self._stop_flag:
                            break
                        buf = f.read(self.CHUNK)
                        if not buf:
                            break
                        # 写入 I2S（非阻塞写，等待缓冲区有空间）
                        n = self.i2s.write(buf)
                        await asyncio.sleep_ms(10)
                if not loop or self._stop_flag:
                    break
        except Exception as e:
            print("[Audio] 播放异常:", e)
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
