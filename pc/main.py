#!/usr/bin/env python3
# ============================================================
#  PC 端主程序入口 — main.py
#  校园实验室安全智能管控系统
#
#  运行：python main.py
#  依赖：pip install -r requirements.txt
# ============================================================
import sys
import os

# ==================== Qt插件修复 核心代码 ====================
# 使用 sys.prefix 直接获取虚拟环境根目录，避免路径错误
pyqt_plugins_path = os.path.join(
    sys.prefix,  # 直接指向 .venv 根目录
    "Lib", "site-packages", "PyQt5", "Qt5", "plugins"
)
# 强制设置Qt插件路径环境变量
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = pyqt_plugins_path
# ============================================================

# 确保以 pc/ 为工作目录，使相对路径正确
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont
# --------------- 后面的原有代码完全不变，无需修改 ---------------

from core.stream_receiver   import StreamReceiver
from core.heartbeat_monitor import HeartbeatMonitor
from core.cmd_sender        import CmdSender
from core.ai_engine         import AIEngine
from db.database            import Database
from ui.main_window         import MainWindow
from ui.i18n                import set_lang
from core.config            import DEFAULT_LANG, LOG_DIR, RECORD_DIR, DB_PATH


def main():
    # ── 创建必要目录 ─────────────────────────────────────
    for d in [LOG_DIR, RECORD_DIR, os.path.dirname(DB_PATH), "models"]:
        os.makedirs(d, exist_ok=True)

    # ── 初始化语言 ───────────────────────────────────────
    set_lang(DEFAULT_LANG)

    # ── 启动后端服务 ─────────────────────────────────────
    db         = Database()
    hb_monitor = HeartbeatMonitor()
    cmd_sender = CmdSender()
    stream_rcv = StreamReceiver()
    ai_engine  = AIEngine(lang=DEFAULT_LANG)

    stream_rcv.start()
    hb_monitor.start()

    # ── 启动 Qt 应用 ──────────────────────────────────────
    app = QApplication(sys.argv)
    app.setApplicationName("校园实验室安全管控系统")
    font = QFont("Microsoft YaHei", 10)
    app.setFont(font)

    win = MainWindow(
        stream_receiver=stream_rcv,
        ai_engine=ai_engine,
        hb_monitor=hb_monitor,
        cmd_sender=cmd_sender,
        db=db,
    )
    win.show()

    code = app.exec_()

    # ── 清理 ─────────────────────────────────────────────
    stream_rcv.stop()
    hb_monitor.stop()
    cmd_sender.close()

    sys.exit(code)


if __name__ == "__main__":
    main()
