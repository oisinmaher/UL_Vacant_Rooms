from PySide6.QtWidgets import QApplication
from ui_display import UIDisplay


def main():
    app = QApplication([])
    window = UIDisplay()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
