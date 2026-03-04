from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QLabel,
    QListWidget, QListWidgetItem, QMessageBox
)
from PySide6.QtCore import Qt
from database import Database


class RoleManagePage(QWidget):
    MODULE_PERMISSIONS = [
        "报价管理",
        "订单管理",
        "物料管理",
        "用户管理",
        "角色管理",
    ]

    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.current_role_id = None
        self.init_ui()
        self.ensure_permissions_seeded()
        self.load_roles()
        self.load_permissions()

    def init_ui(self):
        layout = QVBoxLayout()

        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索角色名")
        self.btn_search = QPushButton("查询")
        self.btn_add_role = QPushButton("新增角色")
        self.btn_refresh = QPushButton("刷新")
        top.addWidget(self.search_input)
        top.addWidget(self.btn_search)
        top.addWidget(self.btn_add_role)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        body = QHBoxLayout()

        self.role_table = QTableWidget()
        self.role_table.setColumnCount(2)
        self.role_table.setHorizontalHeaderLabels(["ID", "角色名"])
        self.role_table.setColumnHidden(0, True)
        self.role_table.setSelectionBehavior(QTableWidget.SelectRows)
        body.addWidget(self.role_table, 3)

        right = QVBoxLayout()
        right.addWidget(QLabel("模块权限"))
        self.permission_list = QListWidget()
        right.addWidget(self.permission_list, 1)
        self.btn_save_permissions = QPushButton("保存角色权限")
        right.addWidget(self.btn_save_permissions)
        body.addLayout(right, 2)

        layout.addLayout(body)
        self.setLayout(layout)

        self.btn_search.clicked.connect(self.load_roles)
        self.search_input.returnPressed.connect(self.load_roles)
        self.role_table.itemSelectionChanged.connect(self.on_role_changed)
        self.btn_save_permissions.clicked.connect(self.save_role_permissions)
        self.btn_add_role.clicked.connect(self.add_role)
        self.btn_refresh.clicked.connect(self.refresh_data)

    def ensure_permissions_seeded(self):
        existing = self.db.fetch_all("SELECT permission_name FROM permissions")
        exists = {v[0] for v in existing}
        for name in self.MODULE_PERMISSIONS:
            if name not in exists:
                self.db.execute(
                    "INSERT INTO permissions (permission_name) VALUES (%s)",
                    (name,)
                )

    def load_roles(self):
        keyword = self.search_input.text().strip()
        rows = self.db.fetch_all(
            """
            SELECT id, role_name
            FROM roles
            WHERE role_name ILIKE %s
            ORDER BY id DESC
            """,
            (f"%{keyword}%",)
        )
        self.role_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.role_table.setItem(r, c, QTableWidgetItem(str(val)))

        if not rows:
            self.current_role_id = None
            self.clear_permission_checks()

    def load_permissions(self):
        self.permission_list.clear()
        rows = self.db.fetch_all("SELECT id, permission_name FROM permissions ORDER BY id")
        for permission_id, permission_name in rows:
            item = QListWidgetItem(permission_name)
            item.setData(Qt.UserRole, permission_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.permission_list.addItem(item)

    def clear_permission_checks(self):
        for i in range(self.permission_list.count()):
            self.permission_list.item(i).setCheckState(Qt.Unchecked)

    def on_role_changed(self):
        row = self.role_table.currentRow()
        if row < 0:
            self.current_role_id = None
            self.clear_permission_checks()
            return

        role_id_item = self.role_table.item(row, 0)
        self.current_role_id = role_id_item.text() if role_id_item else None
        self.clear_permission_checks()
        if not self.current_role_id:
            return

        rows = self.db.fetch_all(
            "SELECT permission_id FROM role_permissions WHERE role_id=%s",
            (self.current_role_id,)
        )
        permission_ids = {str(v[0]) for v in rows}
        for i in range(self.permission_list.count()):
            item = self.permission_list.item(i)
            permission_id = str(item.data(Qt.UserRole))
            item.setCheckState(Qt.Checked if permission_id in permission_ids else Qt.Unchecked)

    def save_role_permissions(self):
        if not self.current_role_id:
            QMessageBox.warning(self, "提示", "请先选择角色")
            return

        selected_permission_ids = []
        for i in range(self.permission_list.count()):
            item = self.permission_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_permission_ids.append(item.data(Qt.UserRole))

        self.db.execute("DELETE FROM role_permissions WHERE role_id=%s", (self.current_role_id,))
        for permission_id in selected_permission_ids:
            self.db.execute(
                "INSERT INTO role_permissions (role_id, permission_id) VALUES (%s, %s)",
                (self.current_role_id, permission_id)
            )
        QMessageBox.information(self, "提示", "角色权限已保存")

    def add_role(self):
        role_name = self.search_input.text().strip()
        if not role_name:
            QMessageBox.warning(self, "提示", "请先在搜索框输入角色名后再新增")
            return
        try:
            self.db.execute("INSERT INTO roles (role_name) VALUES (%s)", (role_name,))
            self.load_roles()
            QMessageBox.information(self, "提示", "角色已新增")
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"新增失败: {exc}")

    def refresh_data(self):
        self.load_permissions()
        self.load_roles()
        self.on_role_changed()
