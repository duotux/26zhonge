# ============================================================
#  主窗口 — ui/main_window.py
#  蓝白工业风，五大功能区，中俄双语切换
# ============================================================
import threading
from PyQt5.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QTabWidget, QLabel, QStatusBar, QMessageBox, QApplication
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QObject
from PyQt5.QtGui import QFont, QIcon, QColor, QPalette

from ui.i18n import t, set_lang
from ui.monitor_tab  import MonitorTab
from ui.alert_tab    import AlertTab
from ui.stats_tab    import StatsTab
from ui.device_tab   import DeviceTab
from ui.settings_tab import SettingsTab


# 跨线程安全信号桥
class Bridge(QObject):
    alert_signal = pyqtSignal(dict)


class MainWindow(QMainWindow):
    def __init__(self, stream_receiver, ai_engine,
                 hb_monitor, cmd_sender, db):
        super().__init__()
        self._sr    = stream_receiver
        self._ai    = ai_engine
        self._hbm   = hb_monitor
        self._sender = cmd_sender
        self._db    = db
        self._bridge = Bridge()
        self._bridge.alert_signal.connect(self._on_alert_ui)

        self._apply_dark_theme()
        self._build_ui()
        self._setup_connections()

        # 注册预警回调（后端线程 → 信号 → UI 线程）
        from core.alert_manager import AlertManager
        self._alert_mgr = AlertManager(
            cmd_sender=self._sender,
            db=self._db,
            on_alert_cb=lambda ev: self._bridge.alert_signal.emit(ev),
        )
        self._ai.on_alert = self._alert_mgr.handle

        # 注册心跳状态变更回调
        self._hbm._on_change = self._on_device_status_change

        # 状态栏刷新
        self._sb_timer = QTimer(self)
        self._sb_timer.timeout.connect(self._update_statusbar)
        self._sb_timer.start(2000)

    # ── 界面构建 ─────────────────────────────────────────
    def _build_ui(self):
        self.setWindowTitle(t("app_title"))
        self.resize(1280, 820)
        self.setMinimumSize(960, 640)

        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # 顶部标题栏
        header = QLabel(t("app_title"))
        header.setFixedHeight(42)
        header.setAlignment(Qt.AlignCenter)
        header.setStyleSheet(
            "background:qlineargradient(x1:0,y1:0,x2:1,y2:0,"
            "stop:0 #0a1628, stop:1 #1a3a5c);"
            "color:#7ec8e3; font-size:18px; font-weight:bold; "
            "letter-spacing:2px;")
        root.addWidget(header)

        # 主标签页
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.North)
        self._tabs.setStyleSheet(
            "QTabWidget::pane{border:none;background:#0d1b2a;}"
            "QTabBar::tab{background:#1a2a3a;color:#7ec8e3;"
            "padding:7px 20px;font-size:13px;border-bottom:2px solid transparent;}"
            "QTabBar::tab:selected{background:#0d1b2a;color:#ffffff;"
            "border-bottom:2px solid #7ec8e3;}"
            "QTabBar::tab:hover{background:#0d1b2a;}")
        root.addWidget(self._tabs)

        # 实例化各功能页
        self._tab_monitor  = MonitorTab(self._sr, self._ai, self._hbm)
        self._tab_alert    = AlertTab(self._db)
        self._tab_stats    = StatsTab(self._db)
        self._tab_device   = DeviceTab(self._hbm, self._sender, self._db)
        self._tab_settings = SettingsTab(self._ai)

        self._tabs.addTab(self._tab_monitor,  t("tab_monitor"))
        self._tabs.addTab(self._tab_alert,    t("tab_alert"))
        self._tabs.addTab(self._tab_stats,    t("tab_stats"))
        self._tabs.addTab(self._tab_device,   t("tab_device"))
        self._tabs.addTab(self._tab_settings, t("tab_settings"))

        # 状态栏
        self._statusbar = QStatusBar()
        self._statusbar.setStyleSheet(
            "QStatusBar{background:#0a1628;color:#7ec8e3;font-size:11px;}")
        self.setStatusBar(self._statusbar)
        self._lbl_status = QLabel("系统就绪 / Система готова")
        self._lbl_status.setStyleSheet("color:#7ec8e3;")
        self._statusbar.addWidget(self._lbl_status)

        self._lbl_device_cnt = QLabel("设备: 0 在线")
        self._lbl_device_cnt.setStyleSheet("color:#00e676;")
        self._statusbar.addPermanentWidget(self._lbl_device_cnt)

    def _setup_connections(self):
        self._tab_settings.lang_changed.connect(self._on_lang_changed)
        self._tab_settings.conf_changed.connect(self._on_conf_changed)

    # ── 槽函数 ───────────────────────────────────────────
    def _on_alert_ui(self, event: dict):
        """预警事件到达 UI 线程"""
        self._tab_alert.add_event(event)
        level = event.get("level", 2)
        cls   = t(event.get("class_name", ""))
        dev   = event.get("device_ip", "")
        level_str = t(f"level_{level}")
        self._lbl_status.setText(
            f"⚠ [{level_str}] {cls}  @{dev}  {event.get('ts','')}")
        # 三级预警弹窗
        if level >= 3:
            QMessageBox.critical(
                self, f"【{level_str}】紧急预警",
                f"设备：{dev}\n违规类型：{cls}\n时间：{event.get('ts','')}\n\n"
                f"请立即处置！截图已保存：\n{event.get('img_path','')}")

    def _on_device_status_change(self, device_id: str, online: bool):
        """心跳状态变更（后端线程触发，不直接操作 UI）"""
        pass  # 设备页由定时器轮询刷新，此处仅打印日志

    def _on_lang_changed(self, lang: str):
        self.setWindowTitle(t("app_title"))
        self._tabs.setTabText(0, t("tab_monitor"))
        self._tabs.setTabText(1, t("tab_alert"))
        self._tabs.setTabText(2, t("tab_stats"))
        self._tabs.setTabText(3, t("tab_device"))
        self._tabs.setTabText(4, t("tab_settings"))
        for tab in [self._tab_monitor, self._tab_alert,
                    self._tab_stats, self._tab_device, self._tab_settings]:
            if hasattr(tab, "refresh_lang"):
                tab.refresh_lang()

    def _on_conf_changed(self, val: float):
        from core import config as cfg
        cfg.CONF_THRESHOLD = val

    def _update_statusbar(self):
        devices = self._hbm.get_devices()
        online  = sum(1 for d in devices.values() if d.get("online"))
        total   = len(devices)
        self._lbl_device_cnt.setText(
            f"设备: {online}/{total} 在线")

    # ── 主题 ─────────────────────────────────────────────
    def _apply_dark_theme(self):
        palette = QPalette()
        bg = QColor("#0d1b2a")
        fg = QColor("#cdd6f4")
        palette.setColor(QPalette.Window,          bg)
        palette.setColor(QPalette.WindowText,      fg)
        palette.setColor(QPalette.Base,            QColor("#1a2a3a"))
        palette.setColor(QPalette.AlternateBase,   QColor("#0d1b2a"))
        palette.setColor(QPalette.Text,            fg)
        palette.setColor(QPalette.Button,          QColor("#1a2a3a"))
        palette.setColor(QPalette.ButtonText,      fg)
        palette.setColor(QPalette.Highlight,       QColor("#1e3a5f"))
        palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
        QApplication.instance().setPalette(palette)
        QApplication.instance().setStyleSheet(
            "QPushButton{background:#1a3a5c;color:#7ec8e3;border:1px solid #1e3a5f;"
            "border-radius:4px;padding:4px 12px;}"
            "QPushButton:hover{background:#1e4a7c;}"
            "QPushButton:pressed{background:#0d2a4a;}"
            "QComboBox{background:#1a2a3a;color:#cdd6f4;border:1px solid #1e3a5f;"
            "border-radius:4px;padding:2px 6px;}"
            "QComboBox QAbstractItemView{background:#1a2a3a;color:#cdd6f4;"
            "selection-background-color:#1e3a5f;}"
            "QSpinBox,QDoubleSpinBox{background:#1a2a3a;color:#cdd6f4;"
            "border:1px solid #1e3a5f;border-radius:4px;padding:2px 4px;}"
            "QLabel{color:#cdd6f4;}"
            "QCheckBox{color:#cdd6f4;}"
            "QSlider::groove:horizontal{background:#1a2a3a;height:6px;"
            "border-radius:3px;}"
            "QSlider::handle:horizontal{background:#7ec8e3;width:14px;"
            "height:14px;margin:-4px 0;border-radius:7px;}"
            "QScrollBar:vertical{background:#0d1b2a;width:8px;}"
            "QScrollBar::handle:vertical{background:#1e3a5f;border-radius:4px;}")

    def closeEvent(self, event):
        self._sr.stop()
        self._hbm.stop()
        self._sender.close()
        event.accept()
