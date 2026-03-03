# ============================================================
#  TCP 指令下发模块 — core/cmd_sender.py
#  功能：向指定 ESP32 终端发送预警指令（TCP 可靠传输）
# ============================================================
import socket
import threading
import time
from core.config import TCP_CMD_PORT


class CmdSender:
    """
    维护与每台 ESP32 的 TCP 长连接，
    断线自动重连，支持多设备并发下发。
    """

    def __init__(self):
        self._conns = {}     # device_ip → socket
        self._locks = {}     # device_ip → Lock
        self._lock  = threading.Lock()

    def send(self, device_ip: str, cmd: str, level: int = 1) -> bool:
        """
        发送指令。
        cmd: 指令名，如 warn1 / warn2 / warn3 / stop
        level: 预警等级 1-3
        返回是否发送成功。
        """
        msg = f"WARN:{cmd}:{level}\n".encode()
        with self._lock:
            if device_ip not in self._locks:
                self._locks[device_ip] = threading.Lock()
        lk = self._locks[device_ip]
        with lk:
            sock = self._get_conn(device_ip)
            if sock is None:
                return False
            try:
                sock.sendall(msg)
                ack = sock.recv(8)
                return ack.strip() == b"ACK"
            except Exception as e:
                print(f"[CmdSender] 发送失败 {device_ip}: {e}")
                self._close_conn(device_ip)
                return False

    def send_all(self, devices: list, cmd: str, level: int = 1):
        """广播指令到多台设备（多线程并发）"""
        threads = []
        for ip in devices:
            t = threading.Thread(target=self.send, args=(ip, cmd, level),
                                 daemon=True)
            t.start()
            threads.append(t)
        for t in threads:
            t.join(timeout=2)

    def close(self):
        with self._lock:
            for s in self._conns.values():
                try:
                    s.close()
                except Exception:
                    pass
            self._conns.clear()

    # ── 内部 ─────────────────────────────────────────────
    def _get_conn(self, ip: str):
        if ip in self._conns:
            return self._conns[ip]
        return self._connect(ip)

    def _connect(self, ip: str):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(3)
            s.connect((ip, TCP_CMD_PORT))
            self._conns[ip] = s
            print(f"[CmdSender] 已连接 {ip}:{TCP_CMD_PORT}")
            return s
        except Exception as e:
            print(f"[CmdSender] 连接失败 {ip}: {e}")
            return None

    def _close_conn(self, ip: str):
        s = self._conns.pop(ip, None)
        if s:
            try:
                s.close()
            except Exception:
                pass
