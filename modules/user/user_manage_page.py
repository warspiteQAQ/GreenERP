from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTableWidget, QTableWidgetItem, QLabel,
    QListWidget, QListWidgetItem, QMessageBox, QDialog,
    QFormLayout, QCheckBox
)
from PySide6.QtCore import Qt
from database import Database
from ui.refresh_toast import show_refresh_success


class UserEditDialog(QDialog):
    def __init__(self, db: Database, user_id=None, parent=None):
        super().__init__(parent)
        self.db = db
        self.user_id = user_id
        self.setWindowTitle("编辑用户" if user_id else "新建用户")
        self.resize(460, 520)
        self.init_ui()
        self.load_roles()
        if self.user_id:
            self.load_user()

    def init_ui(self):
        layout = QVBoxLayout()

        form = QFormLayout()
        self.username_input = QLineEdit()
        self.real_name_input = QLineEdit()
        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.Password)
        self.active_check = QCheckBox("启用")
        self.active_check.setChecked(True)

        form.addRow("用户名", self.username_input)
        form.addRow("姓名", self.real_name_input)
        form.addRow("密码", self.password_input)
        form.addRow("状态", self.active_check)
        layout.addLayout(form)

        layout.addWidget(QLabel("角色选择"))
        self.role_list = QListWidget()
        layout.addWidget(self.role_list, 1)

        btns = QHBoxLayout()
        self.btn_ok = QPushButton("保存")
        self.btn_cancel = QPushButton("取消")
        btns.addStretch()
        btns.addWidget(self.btn_ok)
        btns.addWidget(self.btn_cancel)
        layout.addLayout(btns)

        self.setLayout(layout)
        self.btn_ok.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)

    def load_roles(self):
        self.role_list.clear()
        rows = self.db.fetch_all("SELECT id, role_name FROM roles ORDER BY id")
        for role_id, role_name in rows:
            item = QListWidgetItem(role_name)
            item.setData(Qt.UserRole, role_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.role_list.addItem(item)

    def load_user(self):
        rows = self.db.fetch_all(
            "SELECT username, COALESCE(real_name, ''), is_active FROM users WHERE id=%s",
            (self.user_id,)
        )
        if not rows:
            return

        username, real_name, is_active = rows[0]
        self.username_input.setText(username or "")
        self.real_name_input.setText(real_name or "")
        self.password_input.setPlaceholderText("留空表示不修改密码")
        self.active_check.setChecked(bool(is_active))

        role_rows = self.db.fetch_all(
            "SELECT role_id FROM user_roles WHERE user_id=%s",
            (self.user_id,)
        )
        role_ids = {str(v[0]) for v in role_rows}
        for i in range(self.role_list.count()):
            item = self.role_list.item(i)
            rid = str(item.data(Qt.UserRole))
            item.setCheckState(Qt.Checked if rid in role_ids else Qt.Unchecked)

    def get_selected_role_ids(self):
        role_ids = []
        for i in range(self.role_list.count()):
            item = self.role_list.item(i)
            if item.checkState() == Qt.Checked:
                role_ids.append(item.data(Qt.UserRole))
        return role_ids

    def save(self):
        username = self.username_input.text().strip()
        real_name = self.real_name_input.text().strip()
        password = self.password_input.text().strip()
        is_active = self.active_check.isChecked()

        if not username:
            QMessageBox.warning(self, "提示", "用户名不能为空")
            return
        if not self.user_id and not password:
            QMessageBox.warning(self, "提示", "新建用户必须输入密码")
            return

        try:
            if self.user_id:
                if password:
                    self.db.execute(
                        """
                        UPDATE users
                        SET username=%s, real_name=%s, password=%s, is_active=%s
                        WHERE id=%s
                        """,
                        (username, real_name, password, is_active, self.user_id)
                    )
                else:
                    self.db.execute(
                        """
                        UPDATE users
                        SET username=%s, real_name=%s, is_active=%s
                        WHERE id=%s
                        """,
                        (username, real_name, is_active, self.user_id)
                    )
                user_id = self.user_id
            else:
                self.db.execute(
                    """
                    INSERT INTO users (username, password, real_name, is_active)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (username, password, real_name, is_active)
                )
                user_id = self.db.fetch_all(
                    "SELECT id FROM users WHERE username=%s ORDER BY id DESC LIMIT 1",
                    (username,)
                )[0][0]

            self.db.execute("DELETE FROM user_roles WHERE user_id=%s", (user_id,))
            for role_id in self.get_selected_role_ids():
                self.db.execute(
                    "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                    (user_id, role_id)
                )
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"保存失败: {exc}")
            return

        self.accept()


class UserManagePage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.current_user_id = None
        self.init_ui()
        self.load_users()
        self.load_roles()

    def init_ui(self):
        layout = QVBoxLayout()

        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索用户名或姓名")
        self.btn_search = QPushButton("查询")
        self.btn_add_user = QPushButton("新建用户")
        self.btn_edit_user = QPushButton("编辑用户")
        self.btn_refresh = QPushButton("刷新")
        top.addWidget(self.search_input)
        top.addWidget(self.btn_search)
        top.addWidget(self.btn_add_user)
        top.addWidget(self.btn_edit_user)
        top.addWidget(self.btn_refresh)
        layout.addLayout(top)

        body = QHBoxLayout()

        self.user_table = QTableWidget()
        self.user_table.setColumnCount(4)
        self.user_table.setHorizontalHeaderLabels(["ID", "用户名", "姓名", "状态"])
        self.user_table.setColumnHidden(0, True)
        self.user_table.setSelectionBehavior(QTableWidget.SelectRows)
        body.addWidget(self.user_table, 3)

        right = QVBoxLayout()
        right.addWidget(QLabel("用户角色"))
        self.role_list = QListWidget()
        right.addWidget(self.role_list, 1)
        self.btn_save_roles = QPushButton("保存用户角色")
        right.addWidget(self.btn_save_roles)
        body.addLayout(right, 2)

        layout.addLayout(body)
        self.setLayout(layout)

        self.btn_search.clicked.connect(self.load_users)
        self.search_input.returnPressed.connect(self.load_users)
        self.btn_add_user.clicked.connect(self.add_user)
        self.btn_edit_user.clicked.connect(self.edit_user)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.user_table.itemSelectionChanged.connect(self.on_user_changed)
        self.btn_save_roles.clicked.connect(self.save_user_roles)

    def load_users(self):
        keyword = self.search_input.text().strip()
        query = """
            SELECT id, username, COALESCE(real_name, ''), is_active
            FROM users
            WHERE username ILIKE %s OR COALESCE(real_name, '') ILIKE %s
            ORDER BY id DESC
        """
        data = self.db.fetch_all(query, (f"%{keyword}%", f"%{keyword}%"))
        self.user_table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                if c == 3:
                    val = "启用" if val else "禁用"
                self.user_table.setItem(r, c, QTableWidgetItem(str(val)))

        if not data:
            self.current_user_id = None
            self.clear_role_checks()

    def load_roles(self):
        self.role_list.clear()
        roles = self.db.fetch_all("SELECT id, role_name FROM roles ORDER BY id")
        for role_id, role_name in roles:
            item = QListWidgetItem(role_name)
            item.setData(Qt.UserRole, role_id)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.role_list.addItem(item)

    def clear_role_checks(self):
        for i in range(self.role_list.count()):
            self.role_list.item(i).setCheckState(Qt.Unchecked)

    def get_current_user_id(self):
        row = self.user_table.currentRow()
        if row < 0:
            return None
        item = self.user_table.item(row, 0)
        return item.text() if item else None

    def add_user(self):
        dialog = UserEditDialog(self.db, parent=self)
        if dialog.exec():
            self.load_users()

    def edit_user(self):
        user_id = self.get_current_user_id()
        if not user_id:
            QMessageBox.warning(self, "提示", "请先选择用户")
            return
        dialog = UserEditDialog(self.db, user_id=user_id, parent=self)
        if dialog.exec():
            self.load_users()

    def on_user_changed(self):
        self.current_user_id = self.get_current_user_id()
        if not self.current_user_id:
            self.clear_role_checks()
            return

        self.clear_role_checks()
        rows = self.db.fetch_all(
            "SELECT role_id FROM user_roles WHERE user_id=%s",
            (self.current_user_id,)
        )
        role_ids = {str(v[0]) for v in rows}
        for i in range(self.role_list.count()):
            item = self.role_list.item(i)
            role_id = str(item.data(Qt.UserRole))
            item.setCheckState(Qt.Checked if role_id in role_ids else Qt.Unchecked)

    def save_user_roles(self):
        if not self.current_user_id:
            QMessageBox.warning(self, "提示", "请先选择用户")
            return

        selected_role_ids = []
        for i in range(self.role_list.count()):
            item = self.role_list.item(i)
            if item.checkState() == Qt.Checked:
                selected_role_ids.append(item.data(Qt.UserRole))

        self.db.execute("DELETE FROM user_roles WHERE user_id=%s", (self.current_user_id,))
        for role_id in selected_role_ids:
            self.db.execute(
                "INSERT INTO user_roles (user_id, role_id) VALUES (%s, %s)",
                (self.current_user_id, role_id)
            )
        QMessageBox.information(self, "提示", "用户角色已保存")

    def refresh_data(self):
        self.load_roles()
        self.load_users()
        show_refresh_success(self)
        self.on_user_changed()
