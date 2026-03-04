from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QPushButton, QMessageBox
from PySide6.QtCore import Qt
from database import Database
from ui.main_window import MainWindow

class LoginWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ERP系统登录")
        self.setFixedSize(400, 300)

        layout = QVBoxLayout()

        self.title = QLabel("GLDG 企业ERP系统")
        self.title.setAlignment(Qt.AlignCenter)
        self.title.setStyleSheet("font-size:22px;font-weight:bold;")

        self.username = QLineEdit()
        self.username.setPlaceholderText("用户名")

        self.password = QLineEdit()
        self.password.setPlaceholderText("密码")
        self.password.setEchoMode(QLineEdit.Password)

        self.login_btn = QPushButton("登录")
        self.login_btn.clicked.connect(self.login)

        layout.addWidget(self.title)
        layout.addWidget(self.username)
        layout.addWidget(self.password)
        layout.addWidget(self.login_btn)

        self.setLayout(layout)

    def login(self):
        db = Database()
        conn = db.connect()

        query = "SELECT username FROM users WHERE username=%s AND password=%s"
        # result = db.fetch_all(query, (self.username.text(), self.password.text()))
        result = True

        if result:
            self.main = MainWindow(self.username.text())
            self.main.show()
            self.close()
        else:
            QMessageBox.warning(self, "错误", "用户名或密码错误")