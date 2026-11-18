"""Clean GUI for the UL vacant-room finder.

Renders the structured report from ScrapeInfo.run() as a styled table with
a highlighted summary of rooms that are free for the whole period.
"""
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication, QComboBox, QFrame, QHBoxLayout, QHeaderView, QLabel,
    QMainWindow, QPushButton, QTableWidget, QTableWidgetItem,
    QVBoxLayout, QWidget,
)
from scrape_info import ScrapeInfo

PLACEHOLDER = "Choose…"


class UIDisplay(QMainWindow):
    def __init__(self):
        super().__init__()
        self.info = ScrapeInfo()
        self.setWindowTitle("UL Vacant Rooms")
        self.resize(920, 640)
        self.setMinimumSize(760, 560)
        self.setStyleSheet(STYLE)

        central = QWidget()
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 20, 20, 20)
        root.setSpacing(14)

        # --- Header -------------------------------------------------------
        title = QLabel("Vacant Rooms Finder")
        title.setObjectName("title")
        subtitle = QLabel("See which rooms in a UL building are free for the next three hours.")
        subtitle.setObjectName("subtitle")
        root.addWidget(title)
        root.addWidget(subtitle)

        # --- Options card -------------------------------------------------
        options = QFrame()
        options.setObjectName("card")
        opts = QVBoxLayout(options)
        opts.setContentsMargins(16, 14, 16, 14)
        opts.setSpacing(10)

        pickers = QHBoxLayout()
        pickers.setSpacing(16)
        self.building_cb = self._combo("Building",
                                       ["Choose Building…", "Computer Science Building"])
        self.day_cb = self._combo("Day", [PLACEHOLDER] + list(ScrapeInfo.DAYS))
        self.time_cb = self._combo("Start time", [PLACEHOLDER] + ScrapeInfo.TIMES)
        for box in (self.building_cb, self.day_cb, self.time_cb):
            pickers.addWidget(box)
        pickers.addStretch(1)

        self.search_btn = QPushButton("Show Vacant Rooms")
        self.search_btn.setObjectName("primary")
        self.search_btn.clicked.connect(self.on_search)

        self.refresh_btn = QPushButton("Refresh Data")
        self.refresh_btn.setToolTip("Re-scrape the timetable from the website")
        self.refresh_btn.setObjectName("secondary")
        self.refresh_btn.clicked.connect(self.on_refresh)

        pickers.addWidget(self.search_btn)
        pickers.addWidget(self.refresh_btn)
        opts.addLayout(pickers)
        root.addWidget(options)

        # --- Summary card -------------------------------------------------
        summary = QFrame()
        summary.setObjectName("card")
        summ = QVBoxLayout(summary)
        summ.setContentsMargins(16, 12, 16, 12)
        summ.setSpacing(4)
        self.summary_title = QLabel("Rooms free for the whole period")
        self.summary_title.setObjectName("fieldLabel")
        self.summary_rooms = QLabel("Pick a building, day and time, then press “Show Vacant Rooms”.")
        self.summary_rooms.setObjectName("summaryBody")
        self.summary_rooms.setWordWrap(True)
        summ.addWidget(self.summary_title)
        summ.addWidget(self.summary_rooms)
        root.addWidget(summary)

        # --- Results table ------------------------------------------------
        self.table = QTableWidget(0, 2)
        self.table.setHorizontalHeaderLabels(["Time", "Vacant rooms"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        root.addWidget(self.table, 1)

        self.setCentralWidget(central)
        self.statusBar().showMessage("Ready")

    # ------------------------------------------------------------------ UI
    @staticmethod
    def _combo(label, items):
        """A labelled combo box. Returns the wrapper widget; the actual
        QComboBox is available as ``.combo``."""
        box = QWidget()
        lay = QVBoxLayout(box)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(3)
        title = QLabel(label)
        title.setObjectName("fieldLabel")
        cb = QComboBox()
        cb.addItems(items)
        cb.setMinimumWidth(170)
        lay.addWidget(title)
        lay.addWidget(cb)
        box.combo = cb
        return box

    # ---------------------------------------------------------------- actions
    def on_search(self):
        building = self.building_cb.combo.currentText()
        day = self.day_cb.combo.currentText()
        time = self.time_cb.combo.currentText()

        missing = [name for box, name in (
            (self.building_cb, "building"), (self.day_cb, "day"), (self.time_cb, "time"),
        ) if box.combo.currentIndex() == 0]
        if missing:
            self.statusBar().showMessage(f"Please choose: {', '.join(missing)}.")
            self._set_summary("Please fill in all three choices above.", "summaryBody")
            return

        self._set_busy(True, f"Looking up {day} at {time}…")
        try:
            report = self.info.run(building, day, time)
            self._render(report)
            self.statusBar().showMessage(
                f"Showing {len(report['slots'])} hour slots on {day}, from {time}.")
        except Exception as exc:  # scrape failures, missing data, …
            self.statusBar().showMessage(f"Error: {exc}")
            self._set_summary(f"Could not fetch data: {exc}", "summaryBad")
        finally:
            self._set_busy(False)

    def on_refresh(self):
        if self.building_cb.combo.currentIndex() == 0:
            self.statusBar().showMessage("Choose a building first.")
            return
        building = self.building_cb.combo.currentText()
        day = self.day_cb.combo.currentText()
        time = self.time_cb.combo.currentText()
        if day == PLACEHOLDER or time == PLACEHOLDER:
            self.statusBar().showMessage("Choose a day and time first.")
            return
        self._set_busy(True, "Re-scraping timetable… this can take a while.")
        try:
            report = self.info.run(building, day, time, force_scrape=True)
            self._render(report)
            self.statusBar().showMessage("Timetable refreshed from the website.")
        except Exception as exc:
            self.statusBar().showMessage(f"Refresh failed: {exc}")
        finally:
            self._set_busy(False)

    # ----------------------------------------------------------------- render
    def _set_summary(self, text, style):
        self.summary_rooms.setText(text)
        self.summary_rooms.setObjectName(style)
        # objectName styling only takes effect after a re-polish
        self.summary_rooms.style().unpolish(self.summary_rooms)
        self.summary_rooms.style().polish(self.summary_rooms)

    def _render(self, report):
        if report["fully_free"]:
            self._set_summary("  ".join(report["fully_free"]), "summaryGood")
        else:
            self._set_summary("No room is free for the entire period.", "summaryBad")

        self.table.setRowCount(len(report["slots"]))
        bold = QFont()
        bold.setBold(True)
        for row, (time, rooms) in enumerate(report["slots"]):
            t_item = QTableWidgetItem(time)
            t_item.setFont(bold)
            self.table.setItem(row, 0, t_item)

            if rooms:
                r_item = QTableWidgetItem(",  ".join(rooms))
                r_item.setBackground(QColor("#e7f6ec"))
                r_item.setForeground(QColor("#1c7a3d"))
            else:
                r_item = QTableWidgetItem("— none —")
                r_item.setBackground(QColor("#fdecec"))
                r_item.setForeground(QColor("#b3261e"))
            self.table.setItem(row, 1, r_item)

        self.table.resizeRowsToContents()

    def _set_busy(self, busy, message=None):
        self.search_btn.setEnabled(not busy)
        self.refresh_btn.setEnabled(not busy)
        if message:
            self.statusBar().showMessage(message)


STYLE = """
QMainWindow, QWidget {
    background: #f4f6f8;
    color: #1f2933;
    font-size: 13px;
}
#title {
    font-size: 22px;
    font-weight: 700;
}
#subtitle {
    color: #5b6b7b;
}
#card {
    background: #ffffff;
    border: 1px solid #dde4ea;
    border-radius: 10px;
}
QComboBox {
    background: #ffffff;
    border: 1px solid #c9d4de;
    border-radius: 6px;
    padding: 6px 10px;
}
QComboBox:hover { border: 1px solid #7fa8d0; }
QComboBox::drop-down {
    border: none;
    width: 24px;
}
QPushButton {
    border: 1px solid #c9d4de;
    border-radius: 6px;
    padding: 7px 16px;
    background: #ffffff;
}
QPushButton:hover { background: #eef3f7; }
QPushButton:disabled { color: #9aa7b2; background: #f0f3f5; }
#primary {
    background: #2563a8;
    border: 1px solid #1e548c;
    color: #ffffff;
    font-weight: 600;
}
#primary:hover { background: #2d70ba; }
#primary:disabled { background: #9fb9d4; border: 1px solid #93aec9; }
#summaryBody { color: #5b6b7b; }
#summaryGood { color: #1c7a3d; font-weight: 700; font-size: 15px; }
#summaryBad  { color: #b3261e; font-weight: 600; }
#fieldLabel {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: #5b6b7b;
}
QTableWidget {
    background: #ffffff;
    alternate-background-color: #f7f9fb;
    border: 1px solid #dde4ea;
    border-radius: 10px;
    gridline-color: #e6ebf0;
    selection-background-color: #d4e5f7;
    selection-color: #1f2933;
}
QHeaderView::section {
    background: #eef2f6;
    color: #3e4c59;
    font-weight: 600;
    border: none;
    padding: 8px 10px;
}
QStatusBar {
    background: #ffffff;
    color: #5b6b7b;
    border-top: 1px solid #dde4ea;
}
"""


if __name__ == "__main__":
    app = QApplication([])
    window = UIDisplay()
    window.show()
    app.exec()
