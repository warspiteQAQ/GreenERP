from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton

from ui.refresh_toast import show_refresh_success


class QuotationPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("报价管理模块")
        self.label.setStyleSheet("font-size:20px;font-weight:bold;")
        self.btn_refresh = QPushButton("刷新")
        self.btn_refresh.clicked.connect(self.refresh_data)
        layout.addWidget(self.label)
        layout.addWidget(self.btn_refresh)
        layout.addStretch()
        self.setLayout(layout)

    def refresh_data(self):
        self.label.setText("报价管理模块")
        show_refresh_success(self)
