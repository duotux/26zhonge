# ============================================================
#  PC 端音频文件服务模块 — core/audio_server.py
#  功能：通过 TCP 将音频文件流式传输到 ESP32
# ============================================================
import socket
import threading
import os
from core.config import AUDIO_FILES_PATH

class AudioFileServer:
    """
    音频文件服务器
    监听 TCP 端口，接收 ESP32 的音频请求，并发送 WAV 文件数据
    """
    
    def __init__(self, port=5603):
        self.port = port
        self._sock = None
        self._running = False
        
    def start(self):
        """启动音频文件服务"""
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.bind(('0.0.0.0', self.port))
        self._sock.listen(5)
        self._sock.settimeout(1.0)
        self._running = True
        
        print(f"[AudioServer] 启动于端口 {self.port}")
        print(f"[AudioServer] 音频目录：{AUDIO_FILES_PATH}")
        
        # 启动服务线程
        thread = threading.Thread(target=self._serve_loop, daemon=True)
        thread.start()
        
    def stop(self):
        """停止服务"""
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except:
                pass
                
    def _serve_loop(self):
        """服务主循环"""
        while self._running:
            try:
                client_sock, addr = self._sock.accept()
                # 为每个客户端创建独立线程
                thread = threading.Thread(
                    target=self._handle_client,
                    args=(client_sock, addr),
                    daemon=True
                )
                thread.start()
            except socket.timeout:
                continue
            except Exception as e:
                if self._running:
                    print(f"[AudioServer] 接受连接失败：{e}")
    
    def _handle_client(self, sock, addr):
        """处理单个客户端请求"""
        try:
            sock.settimeout(5.0)
            # 接收请求的文件路径
            request = sock.recv(256).decode('utf-8').strip()
            
            if not request:
                return
            
            # 处理路径：支持两种格式
            # 1. "/audio/warn1.wav" (Unix 风格)
            # 2. "audio/warn1.wav" (相对路径)
            # 统一转换为 Windows 路径："assets\audio\warn1.wav"
            rel_path = request.lstrip('/')  # 移除开头的 /
            
            # 构建完整文件路径
            file_path = os.path.join(AUDIO_FILES_PATH, rel_path.replace('/', os.sep))
            
            # 检查文件是否存在
            if not os.path.exists(file_path):
                print(f"[AudioServer] 文件不存在：{file_path}")
                sock.send(b"ERROR:FILE_NOT_FOUND")
                return
            
            # 发送文件信息（文件大小）
            file_size = os.path.getsize(file_path)
            header = f"SIZE:{file_size}\n".encode()
            sock.send(header)
            
            # 读取并发送文件内容
            with open(file_path, 'rb') as f:
                while True:
                    chunk = f.read(4096)  # 每次发送 4KB
                    if not chunk:
                        break
                    sock.sendall(chunk)
                    
            print(f"[AudioServer] 已发送：{file_path} ({file_size} bytes)")
            
        except Exception as e:
            print(f"[AudioServer] 客户端 {addr} 处理失败：{e}")
        finally:
            try:
                sock.close()
            except:
                pass
