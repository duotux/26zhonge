# ============================================================
#  预警管理页 — ui/alert_tab.py
# ============================================================
import csv, os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QLabel, QComboBox, QCheckBox, QFileDialog,
    QMessageBox, QHeaderView, QAbstractItemView
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor
from ui.i18n import t

LEVEL_BG  = {1: QColor("#1a2a1a"), 2: QColor("#2a2000"), 3: QColor("#2a0000")}
LEVEL_FG  = {1: QColor("#00e676"), 2: QColor("#ffab40"), 3: QColor("#ff5252")}
COL_TIME, COL_DEV, COL_TYPE, COL_LVL, COL_CONF, COL_ST = range(6)


class AlertTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self._db = db
        self._all_events = []
        self._build_ui()
        self._load_from_db()

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(10, 10, 10, 10)

        bar = QHBoxLayout()
        self._cb_uh = QCheckBox(t("unhandled"))
        self._cb_uh.stateChanged.connect(self._refresh_table)
        bar.addWidget(self._cb_uh)

        bar.addWidget(QLabel(t("col_level") + ":"))
        self._cmb = QComboBox()
        self._cmb.addItems(["全部 / Все", t("level_1"), t("level_2"), t("level_3")])
        self._cmb.currentIndexChanged.connect(self._refresh_table)
        bar.addWidget(self._cmb)
        bar.addStretch()

        self._btn_handle = QPushButton(t("btn_handle"))
        self._btn_handle.setFixedWidth(120)
        self._btn_handle.clicked.connect(self._handle_selected)
        bar.addWidget(self._btn_handle)

        self._btn_export = QPushButton(t("btn_export"))
        self._btn_export.setFixedWidth(100)
        self._btn_export.clicked.connect(self._export_csv)
        bar.addWidget(self._btn_export)
        vbox.addLayout(bar)

        self._table = QTableWidget(0, 6)
        self._table.setHorizontalHeaderLabels([
            t("col_time"), t("col_device"), t("col_type"),
            t("col_level"), "Conf", t("col_status")
        ])
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setAlternatingRowColors(False)
        self._table.setStyleSheet(
            "QTableWidget{background:#0d1b2a;color:#cdd6f4;"
            "gridline-color:#1e3a5f;border:1px solid #1e3a5f;}"
            "QHeaderView::section{background:#1a2a3a;color:#7ec8e3;"
            "border:1px solid #1e3a5f;padding:4px;}")
        vbox.addWidget(self._table)

    def _load_from_db(self):
        self._all_events = self._db.query_events(days=30, limit=500)
        self._refresh_table()

    def _refresh_table(self):
        lvl_filter = self._cmb.currentIndex()   # 0=all,1=1,2=2,3=3
        uh_only    = self._cb_uh.isChecked()
        rows = [e for e in self._all_events
                if (lvl_filter == 0 or e["level"] == lvl_filter)
                and (not uh_only or not e["handled"])]
        self._table.setRowCount(len(rows))
        for r, ev in enumerate(rows):
            vals = [ev["ts"], ev["device_ip"],
                    t(ev["class_name"]), t(f"level_{ev['level']}"),
                    f"{ev.get('conf',0):.0%}",
                    t("handled") if ev["handled"] else t("unhandled")]
            bg = LEVEL_BG.get(ev["level"], QColor("#0d1b2a"))
            fg = LEVEL_FG.get(ev["level"], QColor("#cdd6f4"))
            for c, v in enumerate(vals):
                item = QTableWidgetItem(str(v))
                item.setBackground(bg)
                item.setForeground(fg)
                item.setData(Qt.UserRole, ev.get("id"))
                self._table.setItem(r, c, item)
        self._table.scrollToTop()

    def add_event(self, event: dict):
        """由主程序预警回调调用，线程安全 - 使用信号槽机制"""
        # 检查是否在 UI 线程中执行
        import threading
        if threading.current_thread() is threading.main_thread():
            # 在 UI 线程中，直接更新
            self._all_events.insert(0, event)
            if len(self._all_events) > 500:
                self._all_events = self._all_events[:500]
            try:
                self._refresh_table()
            except Exception as e:
                print(f"[AlertTab] UI 更新失败：{e}")
        else:
            # 不在 UI 线程中，通过信号安全更新（由 main_window 的 Bridge 处理）
            # 这里不应该直接调用，应该由 main_window 的信号机制处理
            pass

    def _handle_selected(self):
        rows = set(i.row() for i in self._table.selectedItems())
        for r in rows:
            eid = self._table.item(r, 0).data(Qt.UserRole)
            if eid:
                self._db.mark_handled(eid, user="teacher")
        self._load_from_db()

    def _export_csv(self):
        path, _ = QFileDialog.getSaveFileName(
            self, "导出报表", "alerts.csv", "CSV (*.csv)")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["时间", "设备IP", "违规类型", "等级", "置信度", "状态"])
            for ev in self._all_events:
                w.writerow([ev["ts"], ev["device_ip"],
                             t(ev["class_name"]),
                             t(f"level_{ev['level']}"),
                             f"{ev.get('conf',0):.0%}",
                             "已处理" if ev["handled"] else "未处理"])
        QMessageBox.information(self, "导出成功", f"已保存到\n{path}")

    def refresh_lang(self):
        self._table.setHorizontalHeaderLabels([
            t("col_time"), t("col_device"), t("col_type"),
            t("col_level"), "Conf", t("col_status")
        ])
        self._btn_handle.setText(t("btn_handle"))
        self._btn_export.setText(t("btn_export"))
        self._cmb.setItemText(1, t("level_1"))
        self._cmb.setItemText(2, t("level_2"))
        self._cmb.setItemText(3, t("level_3"))
        self._refresh_table()
