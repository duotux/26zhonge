# ============================================================
#  系统设置页 — ui/settings_tab.py
# ============================================================
import shutil, os
from datetime import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QFormLayout, QComboBox,
    QDoubleSpinBox, QSlider, QPushButton, QLabel,
    QGroupBox, QHBoxLayout, QFileDialog, QMessageBox
)
from PyQt5.QtCore import Qt, pyqtSignal
from ui.i18n import t, set_lang, current_lang
from core.config import DB_PATH, RECORD_DIR


class SettingsTab(QWidget):
    lang_changed  = pyqtSignal(str)   # 语言切换信号
    conf_changed  = pyqtSignal(float) # 阈值变更信号

    def __init__(self, ai_engine=None, parent=None):
        super().__init__(parent)
        self._ai = ai_engine
        self._build_ui()

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(20, 20, 20, 20)
        vbox.setSpacing(16)

        # ── 界面语言 ────────────────────────────────────
        grp_lang = QGroupBox(t("lang_label"))
        grp_lang.setStyleSheet(self._grp_style())
        form_lang = QFormLayout(grp_lang)
        self._cmb_lang = QComboBox()
        self._cmb_lang.addItems(["中文", "Русский"])
        self._cmb_lang.setCurrentIndex(0 if current_lang() == "zh" else 1)
        self._cmb_lang.currentIndexChanged.connect(self._on_lang_change)
        form_lang.addRow(t("lang_label") + ":", self._cmb_lang)
        vbox.addWidget(grp_lang)

        # ── AI 推理阈值 ──────────────────────────────────
        grp_ai = QGroupBox(t("conf_label"))
        grp_ai.setStyleSheet(self._grp_style())
        form_ai = QFormLayout(grp_ai)
        self._spin_conf = QDoubleSpinBox()
        self._spin_conf.setRange(0.3, 0.99)
        self._spin_conf.setSingleStep(0.05)
        self._spin_conf.setValue(0.70)
        self._spin_conf.valueChanged.connect(self._on_conf_change)
        form_ai.addRow(t("conf_label") + ":", self._spin_conf)
        vbox.addWidget(grp_ai)

        # ── 播报音量 ─────────────────────────────────────
        grp_vol = QGroupBox(t("vol_label"))
        grp_vol.setStyleSheet(self._grp_style())
        h = QHBoxLayout(grp_vol)
        self._slider_vol = QSlider(Qt.Horizontal)
        self._slider_vol.setRange(0, 100)
        self._slider_vol.setValue(80)
        self._lbl_vol = QLabel("80%")
        self._slider_vol.valueChanged.connect(
            lambda v: self._lbl_vol.setText(f"{v}%"))
        h.addWidget(self._slider_vol)
        h.addWidget(self._lbl_vol)
        vbox.addWidget(grp_vol)

        # ── 数据备份 ─────────────────────────────────────
        grp_bak = QGroupBox(t("backup_label"))
        grp_bak.setStyleSheet(self._grp_style())
        hbak = QHBoxLayout(grp_bak)
        btn_bak = QPushButton(t("btn_backup"))
        btn_bak.setFixedWidth(120)
        btn_bak.clicked.connect(self._do_backup)
        hbak.addWidget(btn_bak)
        hbak.addStretch()
        vbox.addWidget(grp_bak)

        # ── 当前角色 ─────────────────────────────────────
        grp_role = QGroupBox(t("role_label"))
        grp_role.setStyleSheet(self._grp_style())
        form_role = QFormLayout(grp_role)
        self._cmb_role = QComboBox()
        self._cmb_role.addItems([t("role_admin"), t("role_teacher"), t("role_viewer")])
        form_role.addRow(t("role_label") + ":", self._cmb_role)
        vbox.addWidget(grp_role)

        vbox.addStretch()

    # ── 回调 ─────────────────────────────────────────────
    def _on_lang_change(self, idx):
        lang = "zh" if idx == 0 else "ru"
        set_lang(lang)
        if self._ai:
            self._ai.set_lang(lang)
        self.lang_changed.emit(lang)

    def _on_conf_change(self, val):
        self.conf_changed.emit(val)

    def _do_backup(self):
        ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
        dst, _ = QFileDialog.getSaveFileName(
            self, "选择备份位置",
            f"lab_backup_{ts}.db", "SQLite DB (*.db)")
        if not dst:
            return
        try:
            shutil.copy2(DB_PATH, dst)
            QMessageBox.information(self, "备份成功", f"已备份到：\n{dst}")
        except Exception as e:
            QMessageBox.critical(self, "备份失败", str(e))

    def refresh_lang(self):
        self._cmb_role.setItemText(0, t("role_admin"))
        self._cmb_role.setItemText(1, t("role_teacher"))
        self._cmb_role.setItemText(2, t("role_viewer"))

    @staticmethod
    def _grp_style():
        return ("QGroupBox{border:1px solid #1e3a5f;border-radius:6px;"
                "color:#7ec8e3;font-size:13px;margin-top:8px;padding:8px;}"
                "QGroupBox::title{subcontrol-origin:margin;left:10px;}")
