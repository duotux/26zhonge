# ============================================================
#  实时监控页 — ui/monitor_tab.py
#  最多同时显示 4 路 ESP32 摄像头画面（2×2 网格）
#  AI 推理标注框直接叠加在画面上
# ============================================================
import cv2
import numpy as np
from PyQt5.QtWidgets import (QWidget, QGridLayout, QLabel,
                              QSizePolicy, QVBoxLayout, QHBoxLayout)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QImage, QPixmap, QFont, QColor
from ui.i18n import t


# 每路画面的最大显示尺寸
DISPLAY_W, DISPLAY_H = 480, 360


def bgr_to_pixmap(frame: np.ndarray) -> QPixmap:
    h, w, ch = frame.shape
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    img = QImage(rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(img)


class CameraCell(QWidget):
    """单路摄像头显示单元"""

    def __init__(self, slot_idx: int, parent=None):
        super().__init__(parent)
        self.slot_idx  = slot_idx
        self.device_ip = None
        self._online   = False

        self.setFixedSize(DISPLAY_W, DISPLAY_H + 30)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # 标题栏
        self.title_lbl = QLabel(f"  通道 {slot_idx + 1}  —  {t('no_signal')}")
        self.title_lbl.setFixedHeight(24)
        self.title_lbl.setStyleSheet(
            "background:#1a2a3a; color:#7ec8e3; font-size:12px; "
            "border-radius:3px; padding-left:6px;")
        layout.addWidget(self.title_lbl)

        # 画面区域
        self.video_lbl = QLabel()
        self.video_lbl.setFixedSize(DISPLAY_W, DISPLAY_H)
        self.video_lbl.setAlignment(Qt.AlignCenter)
        self.video_lbl.setStyleSheet("background:#0d1b2a; border:1px solid #1e3a5f;")
        layout.addWidget(self.video_lbl)

        self._show_no_signal()

    def _show_no_signal(self):
        blank = np.zeros((DISPLAY_H, DISPLAY_W, 3), dtype=np.uint8)
        cv2.putText(blank, t("no_signal"),
                    (DISPLAY_W // 2 - 60, DISPLAY_H // 2),
                    cv2.FONT_HERSHEY_SIMPLEX, 1.2, (60, 80, 100), 2)
        self.video_lbl.setPixmap(bgr_to_pixmap(blank))

    def set_device(self, ip: str):
        self.device_ip = ip
        self._update_title()

    def set_online(self, online: bool):
        self._online = online
        self._update_title()
        if not online:
            self._show_no_signal()

    def _update_title(self):
        status = t("device_online") if self._online else t("device_offline")
        color  = "#00e676" if self._online else "#ff5252"
        ip_str = self.device_ip or t("no_signal")
        self.title_lbl.setText(f"  通道 {self.slot_idx + 1}  |  {ip_str}")
        self.title_lbl.setStyleSheet(
            f"background:#1a2a3a; color:{color}; font-size:12px; "
            f"border-radius:3px; padding-left:6px;")

    def update_frame(self, frame: np.ndarray, fps: float = 0.0):
        """更新画面，frame 已含 AI 标注"""
        scaled = cv2.resize(frame, (DISPLAY_W, DISPLAY_H))
        # 右上角叠加 FPS
        cv2.putText(scaled, f"FPS:{fps:.1f}",
                    (DISPLAY_W - 90, 20),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 100), 1)
        self.video_lbl.setPixmap(bgr_to_pixmap(scaled))


class MonitorTab(QWidget):
    """实时监控页，2×2 网格，支持 1-4 路设备"""

    def __init__(self, stream_receiver, ai_engine,
                 hb_monitor, parent=None):
        super().__init__(parent)
        self._sr  = stream_receiver
        self._ai  = ai_engine
        self._hbm = hb_monitor
        self._cells = []       # List[CameraCell]
        self._ip_slot = {}     # ip → slot_idx

        self._build_ui()

        # 刷新定时器，30ms ≈ 33 FPS 上限
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(30)

    def _build_ui(self):
        grid = QGridLayout(self)
        grid.setContentsMargins(8, 8, 8, 8)
        grid.setSpacing(6)
        for i in range(4):
            cell = CameraCell(i)
            self._cells.append(cell)
            grid.addWidget(cell, i // 2, i % 2)

    def _refresh(self):
        """每帧刷新：从 StreamReceiver 拉最新帧 → AIEngine 推理 → 更新画面"""
        devices = self._sr.device_list()
        # 注册新设备到空闲槽位
        for ip in devices:
            if ip not in self._ip_slot and len(self._ip_slot) < 4:
                slot = len(self._ip_slot)
                self._ip_slot[ip] = slot
                self._cells[slot].set_device(ip)

        for ip, slot in self._ip_slot.items():
            cell    = self._cells[slot]
            online  = self._hbm.is_online(
                self._hbm.devices.get(ip, {}).get("device_id", ip) or ip
            ) if hasattr(self._hbm, "devices") else True
            # 若任意设备心跳刚更新也视为在线
            dev_info = self._hbm.devices if hasattr(self._hbm, "devices") else {}
            for did, info in dev_info.items():
                if info.get("ip") == ip:
                    online = info.get("online", False)
                    break

            cell.set_online(online)
            if not online:
                continue

            frame = self._sr.get_frame(ip)
            if frame is None:
                continue
            stats = self._sr.stats.get(ip, {})
            fps   = stats.get("fps", 0.0)
            annotated, _ = self._ai.infer(ip, frame)
            cell.update_frame(annotated, fps)

    def refresh_lang(self):
        for cell in self._cells:
            cell._update_title()
