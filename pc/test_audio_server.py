#!/usr/bin/env python3
# ============================================================
#  PC 端音频文件测试工具
#  用于验证 AudioServer 是否正常工作
# ============================================================
import socket
import sys
import os

# 确保在正确的目录
os.chdir(os.path.dirname(os.path.abspath(__file__)))

def test_audio_server():
    """测试音频服务器"""
    print("=" * 60)
    print("PC 端音频服务器测试工具")
    print("=" * 60)
    
    # 检查音频目录
    audio_dir = "assets/audio"
    if not os.path.exists(audio_dir):
        print(f"❌ 错误：音频目录不存在 - {audio_dir}")
        return False
    
    print(f"\n✓ 音频目录：{audio_dir}")
    
    # 列出所有 WAV 文件
    wav_files = [f for f in os.listdir(audio_dir) if f.endswith('.wav')]
    
    if not wav_files:
        print(f"⚠️  警告：未找到任何 WAV 文件")
        print(f"   请将音频文件放入 {audio_dir}/ 目录")
    else:
        print(f"✓ 找到 {len(wav_files)} 个 WAV 文件:")
        for f in wav_files:
            size = os.path.getsize(os.path.join(audio_dir, f))
            print(f"   - {f} ({size} bytes)")
    
    # 测试连接
    print("\n正在测试端口 5603...")
    try:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        sock.connect(('127.0.0.1', 5603))
        
        # 测试请求一个文件
        test_file = "/audio/" + (wav_files[0] if wav_files else "test.wav")
        print(f"测试请求：{test_file}")
        
        sock.send(test_file.encode() + b"\n")
        
        # 接收响应
        response = b""
        while b"\n" not in response:
            chunk = sock.recv(1)
            if not chunk:
                break
            response += chunk
        
        print(f"响应：{response.decode().strip()}")
        
        if response.startswith(b"SIZE:"):
            print("✓ 服务器响应正常！")
            
            # 尝试接收少量数据
            data = sock.recv(1024)
            if data:
                print(f"✓ 成功接收到 {len(data)} bytes 音频数据")
        else:
            print("⚠️  服务器响应异常")
        
        sock.close()
        
    except ConnectionRefusedError:
        print("❌ 连接被拒绝！AudioServer 可能未启动")
        print("   请运行：python main.py")
        return False
    except socket.timeout:
        print("❌ 连接超时！")
        return False
    except Exception as e:
        print(f"❌ 测试失败：{e}")
        return False
    
    print("\n" + "=" * 60)
    print("✓ 音频服务器测试通过！")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_audio_server()
    sys.exit(0 if success else 1)
