from PySide6.QtWidgets import QApplication, QMainWindow
from PySide6.QtUiTools import QUiLoader
from PySide6.QtCore import QFile
from scrape_info import ScrapeInfo

class UIDisplay():
    def __init__(self):
        self.app = QApplication([])
        loader = QUiLoader()
        file = QFile("roomDisplay.ui")
        file.open(QFile.ReadOnly)
        self.window = loader.load(file)
        file.close()


        self.info = ScrapeInfo()
        self.building_cb = self.window.buildingCB
        self.day_cb = self.window.dayCB
        self.time_cb = self.window.timeCB
        self.submit_btn = self.window.submitBtn
        self.text_box = self.window.freeRoomsText

        self.submit_btn.clicked.connect(self.on_changed)

        self.text_box.setText("Enter info")
        self.window.show()
        self.app.exec()



    def on_changed(self):
        day = self.day_cb.currentText()
        time = self.time_cb.currentText()
        building = self.building_cb.currentText()
        if day[:6] == "Choose" or time[:6] == "Choose" or building[:6] == "Choose":
            self.window.freeRoomsText.setText("Fill all combo boxes")
        else:
            vacant_rooms = self.info.run(building, day, time)
            self.text_box.setText(vacant_rooms)




