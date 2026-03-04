from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QFormLayout, QLineEdit, QPushButton,
    QHBoxLayout, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from database import Database


class ProjectPickerDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("选择项目")
        self.resize(700, 420)
        self.init_ui()
        self.load_projects()

    def init_ui(self):
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入项目编码/名称/客户关键词")
        self.btn_search = QPushButton("筛选")
        self.btn_search.clicked.connect(self.on_search)
        top_layout.addWidget(self.keyword_input)
        top_layout.addWidget(self.btn_search)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(
            ["ID", "项目编码", "项目名称", "客户", "状态"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        bottom_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel.clicked.connect(self.reject)
        bottom_layout.addStretch()
        bottom_layout.addWidget(self.btn_ok)
        bottom_layout.addWidget(self.btn_cancel)
        layout.addLayout(bottom_layout)

        self.setLayout(layout)

    def load_projects(self):
        keyword = self.keyword_input.text().strip()
        like_kw = f"%{keyword}%"
        query = """
            SELECT id, project_code, project_name, customer_name, status
            FROM projects
            WHERE project_code ILIKE %s OR project_name ILIKE %s OR customer_name ILIKE %s
            ORDER BY id DESC
        """
        data = self.db.fetch_all(query, (like_kw, like_kw, like_kw))
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

    def on_search(self):
        self.load_projects()

    def accept_selection(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择一个项目")
            return
        self.accept()

    def selected_project(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        pid = self.table.item(row, 0).text()
        code = self.table.item(row, 1).text()
        name = self.table.item(row, 2).text()
        return pid, code, name


class OrderDialog(QDialog):
    def __init__(self, order_id=None):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.order_id = order_id
        self.project_id = None
        self.setWindowTitle("订单")
        self.resize(520, 320)
        self.init_ui()

        if self.order_id:
            self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.project_code = QLineEdit()
        self.project_code.setReadOnly(True)
        self.project_name = QLineEdit()
        self.project_name.setReadOnly(True)
        self.btn_pick_project = QPushButton("选择项目")

        project_layout = QHBoxLayout()
        project_layout.addWidget(self.project_code)
        project_layout.addWidget(self.btn_pick_project)

        form.addRow("项目编号", project_layout)
        form.addRow("项目名称", self.project_name)

        self.order_code = QLineEdit()
        self.order_name = QLineEdit()
        self.amount = QLineEdit()
        self.status = QComboBox()
        self.status.addItems(["新建", "进行中", "已完成", "已取消"])

        form.addRow("订单编号", self.order_code)
        form.addRow("订单名称", self.order_name)
        form.addRow("金额", self.amount)
        form.addRow("状态", self.status)

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
        self.btn_pick_project.clicked.connect(self.pick_project)

    def pick_project(self):
        dialog = ProjectPickerDialog(self.db, self)
        if not dialog.exec():
            return
        selected = dialog.selected_project()
        if not selected:
            return
        self.project_id, code, name = selected
        self.project_code.setText(code)
        self.project_name.setText(name)

    def load_data(self):
        query = """
            SELECT o.project_id, p.project_code, p.project_name,
                   o.order_code, o.order_name, o.amount, o.status
            FROM orders o
            JOIN projects p ON o.project_id = p.id
            WHERE o.id=%s
        """
        data = self.db.fetch_all(query, (self.order_id,))
        if not data:
            return
        row = data[0]
        self.project_id = str(row[0]) if row[0] is not None else None
        self.project_code.setText(row[1] or "")
        self.project_name.setText(row[2] or "")
        self.order_code.setText(row[3] or "")
        self.order_name.setText(row[4] or "")
        self.amount.setText("" if row[5] is None else str(row[5]))
        status = row[6] or "新建"
        idx = self.status.findText(status)
        self.status.setCurrentIndex(idx if idx >= 0 else 0)

        self.btn_pick_project.setEnabled(False)

    def save(self):
        if not self.project_id:
            QMessageBox.warning(self, "提示", "请选择项目")
            return

        if self.order_id:
            query = """
                UPDATE orders
                SET order_code=%s, order_name=%s, amount=%s, status=%s
                WHERE id=%s
            """
            self.db.execute(query, (
                self.order_code.text(),
                self.order_name.text(),
                self.amount.text(),
                self.status.currentText(),
                self.order_id
            ))
        else:
            query = """
                INSERT INTO orders
                (project_id, order_code, order_name, amount, status)
                VALUES (%s,%s,%s,%s,%s)
            """
            self.db.execute(query, (
                self.project_id,
                self.order_code.text(),
                self.order_name.text(),
                self.amount.text(),
                self.status.currentText()
            ))

        self.accept()
