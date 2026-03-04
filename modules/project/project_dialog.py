from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QComboBox, QDateEdit
)
from PySide6.QtCore import QDate
from database import Database


class ProjectDialog(QDialog):
    def __init__(self, project_id=None):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.project_id = project_id
        self.setWindowTitle("项目")
        self.resize(520, 320)
        self.init_ui()

        if self.project_id:
            self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.code = QLineEdit()
        self.name = QLineEdit()
        self.customer = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["新建", "进行中", "已完成", "已取消"])
        self.start_date = QDateEdit()
        self.start_date.setCalendarPopup(True)
        self.start_date.setDate(QDate.currentDate())
        self.end_date = QDateEdit()
        self.end_date.setCalendarPopup(True)
        self.end_date.setDate(QDate.currentDate())

        form.addRow("项目编码", self.code)
        form.addRow("项目名称", self.name)
        form.addRow("客户", self.customer)
        form.addRow("状态", self.status)
        form.addRow("开始日期", self.start_date)
        form.addRow("结束日期", self.end_date)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(form)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

    def load_data(self):
        query = """
            SELECT project_code, project_name, customer_name,
                   status, start_date, end_date
            FROM projects
            WHERE id=%s
        """
        data = self.db.fetch_all(query, (self.project_id,))
        if not data:
            return
        row = data[0]
        self.code.setText(row[0] or "")
        self.name.setText(row[1] or "")
        self.customer.setText(row[2] or "")
        status = row[3] or "新建"
        idx = self.status.findText(status)
        self.status.setCurrentIndex(idx if idx >= 0 else 0)

        if row[4]:
            self.start_date.setDate(QDate.fromString(str(row[4]), "yyyy-MM-dd"))
        if row[5]:
            self.end_date.setDate(QDate.fromString(str(row[5]), "yyyy-MM-dd"))

    def save(self):
        start_date = self.start_date.date().toString("yyyy-MM-dd")
        end_date = self.end_date.date().toString("yyyy-MM-dd")

        if self.project_id:
            query = """
                UPDATE projects
                SET project_code=%s, project_name=%s, customer_name=%s,
                    status=%s, start_date=%s, end_date=%s
                WHERE id=%s
            """
            self.db.execute(query, (
                self.code.text(),
                self.name.text(),
                self.customer.text(),
                self.status.currentText(),
                start_date,
                end_date,
                self.project_id
            ))
        else:
            query = """
                INSERT INTO projects
                (project_code, project_name, customer_name, status, start_date, end_date)
                VALUES (%s,%s,%s,%s,%s,%s)
            """
            self.db.execute(query, (
                self.code.text(),
                self.name.text(),
                self.customer.text(),
                self.status.currentText(),
                start_date,
                end_date
            ))

        self.accept()
