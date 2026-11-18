"""Clean PySide6 GUI for the UL vacant rooms app.

Layout:
  * Header: building / day / time pickers and a "Check availability" button.
  * Summary banner: rooms free for the whole chosen window.
  * Table: one row per room, one column per hour; cells show Free / Booked,
    with rooms free for the entire window highlighted with a star.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from scrape_info import DAYS, TIMES, ScrapeInfo

STYLESHEET = """
* { font-family: 'Segoe UI', 'Helvetica Neue', Arial, sans-serif; }
QMainWindow, QWidget { background-color: #f6f8fb; color: #232a35; }

#titleLabel { font-size: 20px; font-weight: 700; }
#subtitleLabel { font-size: 12px; color: #6b7688; }

QComboBox {
    background-color: #ffffff; border: 1px solid #d6dde8;
    border-radius: 8px; padding: 7px 12px; font-size: 13px; min-width: 160px;
}
QComboBox:focus { border: 2px solid #2f6fed; }
QComboBox::drop-down { border: none; width: 26px; }

#checkBtn {
    background-color: #2f6fed; color: #ffffff; border: none;
    border-radius: 8px; padding: 9px 22px; font-size: 14px; font-weight: 600;
}
#checkBtn:hover { background-color: #245cd1; }
#checkBtn:pressed { background-color: #1d4ab0; }
#checkBtn:disabled { background-color: #b9c6dd; }

QLabel#banner {
    background-color: #e8f1ff; border: 1px solid #c4d7fb;
    border-radius: 10px; padding: 10px 16px; font-size: 14px;
}
QLabel#banner[variant="good"] {
    background-color: #e6f6ec; border: 1px solid #b4e0c4;
}
QLabel#banner[variant="bad"] {
    background-color: #fdecec; border: 1px solid #f2c4c4;
}

QTableWidget {
    background-color: #ffffff; border: 1px solid #d6dde8;
    border-radius: 10px; gridline-color: #edf0f5;
    font-size: 13px; selection-background-color: #d5e3fb;
}
QTableWidget::item { padding: 6px; }
QHeaderView::section {
    background-color: #eef2f8; color: #3c4657; font-weight: 600;
    border: none; border-bottom: 2px solid #d6dde8; padding: 8px;
}
QTableCornerButton::section { background-color: #eef2f8; border: none; }
#statusLabel { color: #6b7688; font-size: 12px; }
"""


class UIDisplay:
    def __init__(self):
        self.info = ScrapeInfo()
        self.app = QApplication.instance() or QApplication([])
        self.app.setStyleSheet(STYLESHEET)
        self.window = self._build_window()

    # ------------------------------------------------------------------ #
    # Construction
    # ------------------------------------------------------------------ #
    def _build_window(self):
        window = QMainWindow()
        window.setWindowTitle("UL Vacant Rooms")
        window.resize(880, 560)
        window.setMinimumSize(640, 440)

        central = QWidget()
        window.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(20, 18, 20, 14)
        root.setSpacing(12)

        # Header
        title = QLabel("UL Vacant Rooms")
        title.setObjectName("titleLabel")
        subtitle = QLabel("Which rooms are free over the next 3 hours?")
        subtitle.setObjectName("subtitleLabel")
        root.addWidget(title)
        root.addWidget(subtitle)

        # Form row
        form_row = QHBoxLayout()
        form_row.setSpacing(10)

        self.building_cb = QComboBox()
        self.building_cb.addItems(list(self.info.building_rooms))
        self.day_cb = QComboBox()
        self.day_cb.addItem("Choose day")
        self.day_cb.addItems(DAYS)
        self.time_cb = QComboBox()
        self.time_cb.addItem("Choose time")
        self.time_cb.addItems(TIMES)

        self.check_btn = QPushButton("Check availability")
        self.check_btn.setObjectName("checkBtn")
        self.check_btn.clicked.connect(self.on_check)

        for widget in (self.building_cb, self.day_cb, self.time_cb):
            form_row.addWidget(widget)
        form_row.addWidget(self.check_btn)
        form_row.addStretch(1)
        root.addLayout(form_row)

        # Summary banner
        self.banner = QLabel("Pick a day and a time, then check availability.")
        self.banner.setObjectName("banner")
        self.banner.setWordWrap(True)
        self.banner.setProperty("variant", "neutral")
        root.addWidget(self.banner)

        # Results table
        self.table = QTableWidget(0, 0)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(30)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setContextMenuPolicy(Qt.NoContextMenu)
        root.addWidget(self.table, 1)

        # Status
        self.status = QLabel("Ready.")
        self.status.setObjectName("statusLabel")
        root.addWidget(self.status)

        return window

    # ------------------------------------------------------------------ #
    # Behaviour
    # ------------------------------------------------------------------ #
    def on_check(self):
        building = self.building_cb.currentText()
        day = self.day_cb.currentText()
        time = self.time_cb.currentText()

        if "Choose" in (day, time):
            self._set_banner("Pick a day and a time first.", "bad")
            return

        self.check_btn.setEnabled(False)
        self.status.setText("Looking up the schedule…")
        self.app.processEvents()

        try:
            result = self.info.query(building, day, time)
        except Exception as exc:  # offline, no Chrome, network error…
            self.check_btn.setEnabled(True)
            self.status.setText("Lookup failed.")
            self._set_banner(f"Could not load the timetable: {exc}", "bad")
            QMessageBox.critical(
                self.window, "Error", f"Could not load the timetable:\n{exc}"
            )
            return

        self.check_btn.setEnabled(True)
        self._render(result)

    # ------------------------------------------------------------------ #
    # Rendering
    # ------------------------------------------------------------------ #
    def _set_banner(self, text, variant):
        self.banner.setText(text)
        self.banner.setProperty("variant", variant)
        self.banner.style().unpolish(self.banner)
        self.banner.style().polish(self.banner)

    @staticmethod
    def _cell(free, bold):
        item = QTableWidgetItem("Free" if free else "Booked")
        item.setTextAlignment(Qt.AlignCenter)
        if free:
            item.setBackground(QColor("#e6f6ec"))
            item.setForeground(QColor("#1a7f37"))
        else:
            item.setBackground(QColor("#fdecec"))
            item.setForeground(QColor("#c03030"))
        font = item.font()
        font.setBold(bold)
        item.setFont(font)
        return item

    def _render(self, result):
        rooms = sorted(self.info.building_rooms.get(result["building"], []))
        if not rooms:  # fall back to rooms seen in any slot
            rooms = sorted({room for slot in result["slots"] for room in slot})
        times = result["times"]
        always_free = set(result["always_free"])

        self.table.setColumnCount(1 + len(times))
        self.table.setHorizontalHeaderLabels(["Room"] + times)
        self.table.setColumnWidth(0, 120)
        self.table.setRowCount(len(rooms))

        for r, room in enumerate(rooms):
            star = room in always_free

            label = QTableWidgetItem(f"★ {room}" if star else room)
            font = label.font()
            font.setBold(star)
            label.setFont(font)
            if star:
                label.setBackground(QColor("#e8f1ff"))
            self.table.setItem(r, 0, label)

            for c, slot_rooms in enumerate(result["slots"]):
                self.table.setItem(r, c + 1, self._cell(room in slot_rooms, star))

        span = f"{times[0]}–{times[-1]}"
        if always_free:
            self._set_banner(
                f"Free for the full window ({span}): "
                + ", ".join(sorted(always_free)),
                "good",
            )
        else:
            self._set_banner(
                f"No room is free for the whole window ({span}).", "bad"
            )
        booked_count = len(rooms) - len(always_free)
        self.status.setText(
            f"{len(rooms)} rooms checked · {booked_count} booked at least once"
        )

    # ------------------------------------------------------------------ #
    # Entry point
    # ------------------------------------------------------------------ #
    def exec(self):
        self.window.show()
        return self.app.exec()


def run():
    return UIDisplay().exec()
