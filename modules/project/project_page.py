from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from database import Database
from .project_dialog import ProjectDialog


class ProjectPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.init_ui()
        self.load_projects()

    def init_ui(self):
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入项目编码/名称/客户关键词")
        self.status_filter = QComboBox()
        self.status_filter.addItems(["全部", "新建", "进行中", "已完成", "已取消"])
        self.btn_add = QPushButton("新建")
        self.btn_edit = QPushButton("编辑")
        self.btn_refresh = QPushButton("刷新")

        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.status_filter)
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_edit)
        top_layout.addWidget(self.btn_refresh)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(
            ["ID", "项目编码", "项目名称", "客户", "状态", "开始日期", "结束日期", "创建时间"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.btn_add.clicked.connect(self.add_project)
        self.btn_edit.clicked.connect(self.edit_project)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.search_input.textChanged.connect(self.load_projects)
        self.status_filter.currentIndexChanged.connect(self.load_projects)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(self.table)
        self.setLayout(main_layout)

    def _build_filter(self):
        keyword = self.search_input.text().strip()
        status = self.status_filter.currentText()
        return keyword, status

    def load_projects(self):
        keyword, status = self._build_filter()
        like_kw = f"%{keyword}%"

        where_clauses = ["(project_code ILIKE %s OR project_name ILIKE %s OR customer_name ILIKE %s)"]
        params = [like_kw, like_kw, like_kw]

        if status != "全部":
            where_clauses.append("status = %s")
            params.append(status)

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT id, project_code, project_name, customer_name,
                   status, start_date, end_date, created_at
            FROM projects
            WHERE {where_sql}
            ORDER BY id DESC
        """
        data = self.db.fetch_all(query, tuple(params))

        self.table.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                self.table.setItem(
                    row_idx, col_idx, QTableWidgetItem("" if value is None else str(value))
                )

    def refresh_data(self):
        self.load_projects()

    def add_project(self):
        dialog = ProjectDialog()
        if dialog.exec():
            self.load_projects()

    def edit_project(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择一条记录")
            return

        project_id = self.table.item(row, 0).text()
        dialog = ProjectDialog(project_id)
        if dialog.exec():
            self.load_projects()
