# ============================================================
#  ESP32 启动配置文件 — boot.py
#  校园实验室安全智能管控系统
# ============================================================
#
# MicroPython 启动顺序:
# 1. _boot.py (固件内置，不可修改)
# 2. boot.py (用户启动脚本，必须存在)
# 3. main.py (主程序，可选)
#
# 此文件负责:
# - 禁用 WiFi 省电模式
# - 设置 CPU 频率为最大
# - 启用垃圾回收调试（可选）
# - 打印系统信息
# ============================================================

import machine
import os
import gc

# ── 硬件初始化 ──────────────────────────────────────────────
# 设置 CPU 频率为最大值（提高性能）
try:
    machine.freq(240000000)  # 240 MHz
    print(f"[BOOT] CPU 频率：{machine.freq() // 1000000}MHz")
except:
    print("[BOOT] 无法设置 CPU 频率，使用默认值")

# ── 内存管理 ──────────────────────────────────────────────
# 启用垃圾回收
gc.enable()
gc.threshold(gc.mem_free() // 4 + gc.mem_alloc())

print(f"[BOOT] 可用内存：{gc.mem_free()} bytes")

# ── 文件系统检查 ─────────────────────────────────────────────
try:
    files = os.listdir()
    print(f"[BOOT] 文件系统文件数：{len(files)}")
    
    # 检查关键文件是否存在
    required_files = ['main.py', 'config.py', 'wifi_manager.py']
    for f in required_files:
        if f in files:
            print(f"[BOOT] ✓ {f} 存在")
        else:
            print(f"[BOOT] ✗ {f} 缺失!")
except Exception as e:
    print(f"[BOOT] 文件系统检查失败：{e}")

# ── 电源管理 ──────────────────────────────────────────────
# 关闭深度睡眠（我们需要持续运行）
# machine.lightsleep(False)

print("[BOOT] 系统初始化完成，准备加载 main.py...")
print("=" * 60)
