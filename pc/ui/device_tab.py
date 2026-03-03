# ============================================================
#  设备管理页 — ui/device_tab.py
# ============================================================
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QHeaderView, QAbstractItemView, QMessageBox
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QColor
from ui.i18n import t
import time

COL_IP, COL_ID, COL_LOC, COL_LAST, COL_STATUS = range(5)
ONLINE_COLOR  = QColor("#00e676")
OFFLINE_COLOR = QColor("#ff5252")


class DeviceTab(QWidget):
    def __init__(self, hb_monitor, cmd_sender, db, parent=None):
        super().__init__(parent)
        self._hbm    = hb_monitor
        self._sender = cmd_sender
        self._db     = db
        self._build_ui()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(3000)

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(10, 10, 10, 10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel("指令 / Команда:"))
        self._cmb_cmd = QComboBox()
        self._cmb_cmd.addItems(["warn1", "warn2", "warn3", "stop"])
        bar.addWidget(self._cmb_cmd)

        bar.addWidget(QLabel(t("col_level") + ":"))
        self._cmb_lvl = QComboBox()
        self._cmb_lvl.addItems(["1", "2", "3"])
        bar.addWidget(self._cmb_lvl)

        self._btn_send = QPushButton(t("btn_send_warn"))
        self._btn_send.clicked.connect(self._send_to_selected)
        bar.addWidget(self._btn_send)

        self._btn_stop = QPushButton(t("btn_send_stop"))
        self._btn_stop.clicked.connect(self._stop_all)
        bar.addWidget(self._btn_stop)
        bar.addStretch()
        vbox.addLayout(bar)

        self._table = QTableWidget(0, 5)
        self._table.setHorizontalHeaderLabels([
            t("col_ip"), "Device ID", t("col_location"),
            t("col_last_seen"), "Status"
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setStyleSheet(
            "QTableWidget{background:#0d1b2a;color:#cdd6f4;"
            "gridline-color:#1e3a5f;border:1px solid #1e3a5f;}"
            "QHeaderView::section{background:#1a2a3a;color:#7ec8e3;"
            "border:1px solid #1e3a5f;padding:4px;}")
        vbox.addWidget(self._table)

        lbl = QLabel("* 选中设备行后点击「手动播报」可向该终端下发指令")
        lbl.setStyleSheet("color:#7ec8e3; font-size:11px;")
        vbox.addWidget(lbl)

    def _refresh(self):
        devices = self._hbm.get_devices()
        self._table.setRowCount(len(devices))
        for r, (dev_id, info) in enumerate(devices.items()):
            online = info.get("online", False)
            last_ts = info.get("last_seen", 0)
            last_str = time.strftime("%H:%M:%S", time.localtime(last_ts)) if last_ts else "-"
            vals = [info.get("ip", ""), dev_id,
                    info.get("location", "-"), last_str,
                    t("device_online") if online else t("device_offline")]
            fg = ONLINE_COLOR if online else OFFLINE_COLOR
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setForeground(fg)
                item.setData(Qt.UserRole, info.get("ip", ""))
                self._table.setItem(r, c, item)

    def _send_to_selected(self):
        rows = set(i.row() for i in self._table.selectedItems())
        if not rows:
            QMessageBox.information(self, "提示", "请先选中设备行")
            return
        cmd   = self._cmb_cmd.currentText()
        level = int(self._cmb_lvl.currentText())
        for r in rows:
            ip = self._table.item(r, 0).data(Qt.UserRole)
            if ip:
                self._sender.send(ip, cmd, level)

    def _stop_all(self):
        devices = self._hbm.get_devices()
        ips = [info["ip"] for info in devices.values() if info.get("online")]
        self._sender.send_all(ips, "stop", 0)

    def refresh_lang(self):
        self._table.setHorizontalHeaderLabels([
            t("col_ip"), "Device ID", t("col_location"),
            t("col_last_seen"), "Status"
        ])
        self._btn_send.setText(t("btn_send_warn"))
        self._btn_stop.setText(t("btn_send_stop"))
