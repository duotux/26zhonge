# ============================================================
#  台账统计页 — ui/stats_tab.py
#  matplotlib 柱状图 / 折线图 / 饼图嵌入 PyQt5
# ============================================================
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QSpinBox, QPushButton, QTabWidget
)
from PyQt5.QtCore import Qt
from ui.i18n import t

try:
    import matplotlib
    matplotlib.use("Qt5Agg")
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
    from matplotlib.figure import Figure
    import matplotlib.pyplot as plt
    plt.rcParams["font.family"] = ["Microsoft YaHei", "DejaVu Sans"]
    _MPL_OK = True
except ImportError:
    _MPL_OK = False


class ChartCanvas(FigureCanvas if _MPL_OK else QWidget):
    def __init__(self, parent=None):
        if _MPL_OK:
            self.fig = Figure(figsize=(6, 3.5), facecolor="#0d1b2a")
            super().__init__(self.fig)
            self.setParent(parent)
        else:
            super().__init__(parent)
            self._lbl = QLabel("请安装 matplotlib", self)

    def clear(self):
        if _MPL_OK:
            self.fig.clear()

    def draw_bar(self, labels, values, title=""):
        if not _MPL_OK:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor="#0d1b2a")
        colors = ["#7ec8e3" if v < max(values, default=1) * 0.7
                  else "#ff5252" for v in values]
        bars = ax.bar(labels, values, color=colors, edgecolor="#1e3a5f")
        ax.set_facecolor("#0d1b2a")
        ax.tick_params(colors="#7ec8e3", labelsize=9)
        ax.set_title(title, color="#7ec8e3", fontsize=10)
        for spine in ax.spines.values():
            spine.set_edgecolor("#1e3a5f")
        for bar, v in zip(bars, values):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.1,
                    str(v), ha="center", va="bottom", color="#cdd6f4", fontsize=8)
        self.fig.tight_layout()
        self.draw()

    def draw_line(self, x_labels, values, title=""):
        if not _MPL_OK:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor="#0d1b2a")
        ax.plot(x_labels, values, color="#7ec8e3", marker="o", linewidth=2)
        ax.fill_between(range(len(x_labels)), values,
                         alpha=0.15, color="#7ec8e3")
        ax.set_xticks(range(len(x_labels)))
        ax.set_xticklabels(x_labels, rotation=30, ha="right", fontsize=8)
        ax.tick_params(colors="#7ec8e3", labelsize=9)
        ax.set_title(title, color="#7ec8e3", fontsize=10)
        ax.set_facecolor("#0d1b2a")
        for spine in ax.spines.values():
            spine.set_edgecolor("#1e3a5f")
        self.fig.tight_layout()
        self.draw()

    def draw_pie(self, labels, values, title=""):
        if not _MPL_OK:
            return
        self.fig.clear()
        ax = self.fig.add_subplot(111, facecolor="#0d1b2a")
        colors = ["#00e676", "#ffab40", "#ff5252"][:len(labels)]
        wedges, texts, autotexts = ax.pie(
            values, labels=labels, colors=colors,
            autopct="%1.0f%%", startangle=140,
            textprops={"color": "#cdd6f4", "fontsize": 9})
        ax.set_title(title, color="#7ec8e3", fontsize=10)
        self.fig.tight_layout()
        self.draw()


class StatsTab(QWidget):
    def __init__(self, db, parent=None):
        super().__init__(parent)
        self._db = db
        self._build_ui()
        self.refresh_data()

    def _build_ui(self):
        vbox = QVBoxLayout(self)
        vbox.setContentsMargins(10, 10, 10, 10)

        bar = QHBoxLayout()
        bar.addWidget(QLabel(t("days_label") + ":"))
        self._spin = QSpinBox()
        self._spin.setRange(1, 90)
        self._spin.setValue(14)
        bar.addWidget(self._spin)
        btn = QPushButton("刷新 / Обновить")
        btn.clicked.connect(self.refresh_data)
        bar.addWidget(btn)
        bar.addStretch()
        vbox.addLayout(bar)

        self._tabs = QTabWidget()
        self._tabs.setStyleSheet(
            "QTabWidget::pane{border:1px solid #1e3a5f;background:#0d1b2a;}"
            "QTabBar::tab{background:#1a2a3a;color:#7ec8e3;padding:5px 12px;}"
            "QTabBar::tab:selected{background:#0d1b2a;color:#ffffff;}")

        self._canvas_bar  = ChartCanvas()
        self._canvas_line = ChartCanvas()
        self._canvas_pie  = ChartCanvas()

        self._tabs.addTab(self._canvas_bar,  t("chart_by_class"))
        self._tabs.addTab(self._canvas_line, t("chart_by_day"))
        self._tabs.addTab(self._canvas_pie,  t("chart_by_level"))
        vbox.addWidget(self._tabs)

    def refresh_data(self):
        days = self._spin.value()
        # 柱状图：按违规类型
        rows = self._db.stats_by_class(days)
        labels = [t(r["class_name"]) for r in rows]
        values = [r["cnt"] for r in rows]
        self._canvas_bar.draw_bar(labels, values, t("chart_by_class"))

        # 折线图：按日期
        rows2 = self._db.stats_by_day(days)
        xl = [r["day"][5:] for r in rows2]  # MM-DD
        yl = [r["cnt"] for r in rows2]
        self._canvas_line.draw_line(xl, yl, t("chart_by_day"))

        # 饼图：按等级
        lvl = self._db.stats_by_level(days)
        pl = [t(f"level_{k}") for k in sorted(lvl)]
        pv = [lvl[k] for k in sorted(lvl)]
        if pv:
            self._canvas_pie.draw_pie(pl, pv, t("chart_by_level"))

    def refresh_lang(self):
        self._tabs.setTabText(0, t("chart_by_class"))
        self._tabs.setTabText(1, t("chart_by_day"))
        self._tabs.setTabText(2, t("chart_by_level"))
        self.refresh_data()
