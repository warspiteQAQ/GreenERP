import sys
from PySide6.QtWidgets import QApplication
from login import LoginWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)

    with open("ui/style.qss", "r") as f:
        app.setStyleSheet(f.read())

    window = LoginWindow()
    window.show()

    sys.exit(app.exec())