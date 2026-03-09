from datetime import datetime

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from database import Database


class SupplierManagePage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()

        self.current_supplier_id = None
        self.is_creating = False
        self.available_columns = self._load_supplier_columns()

        self.init_ui()
        self.set_readonly_mode(True)
        self.load_suppliers()

    def _load_supplier_columns(self):
        rows = self.db.fetch_all(
            """
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema='public' AND table_name='suppliers'
            """
        )
        return {str(row[0]) for row in rows}

    def init_ui(self):
        main_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("供应商列表"))
        self.supplier_list = QListWidget()
        left_layout.addWidget(self.supplier_list)

        right_layout = QVBoxLayout()
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("添加")
        self.btn_edit = QPushButton("编辑")
        self.btn_save = QPushButton("保存")
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_save)
        btn_layout.addStretch()

        form_layout = QFormLayout()
        self.supplier_code_input = QLineEdit()
        self.supplier_name_input = QLineEdit()
        self.address_input = QLineEdit()
        self.contact_name_input = QLineEdit()
        self.contact_phone_input = QLineEdit()
        self.tax_no_input = QLineEdit()
        self.bank_name_input = QLineEdit()
        self.bank_account_input = QLineEdit()

        form_layout.addRow("供应商编码", self.supplier_code_input)
        form_layout.addRow("供应商名称", self.supplier_name_input)
        form_layout.addRow("地址", self.address_input)
        form_layout.addRow("联系人", self.contact_name_input)
        form_layout.addRow("电话", self.contact_phone_input)
        form_layout.addRow("税号", self.tax_no_input)
        form_layout.addRow("开户行", self.bank_name_input)
        form_layout.addRow("银行账号", self.bank_account_input)

        right_layout.addLayout(btn_layout)
        right_layout.addLayout(form_layout)
        right_layout.addStretch()

        main_layout.addLayout(left_layout, 1)
        main_layout.addLayout(right_layout, 2)
        self.setLayout(main_layout)

        self.supplier_list.itemSelectionChanged.connect(self.on_supplier_selected)
        self.btn_add.clicked.connect(self.add_supplier)
        self.btn_edit.clicked.connect(self.edit_supplier)
        self.btn_save.clicked.connect(self.save_supplier)

        # 历史库可能尚未加字段，界面可见但只读禁用，避免保存时报错。
        has_tax_no = "tax_no" in self.available_columns
        has_bank_name = "bank_name" in self.available_columns
        has_bank_account = "bank_account" in self.available_columns
        self.tax_no_input.setEnabled(has_tax_no)
        self.bank_name_input.setEnabled(has_bank_name)
        self.bank_account_input.setEnabled(has_bank_account)

    def set_readonly_mode(self, readonly: bool):
        widgets = [
            self.supplier_code_input,
            self.supplier_name_input,
            self.address_input,
            self.contact_name_input,
            self.contact_phone_input,
            self.tax_no_input,
            self.bank_name_input,
            self.bank_account_input,
        ]
        for widget in widgets:
            widget.setReadOnly(readonly)
        self.btn_save.setEnabled(not readonly)

    def _clear_form(self):
        self.supplier_code_input.clear()
        self.supplier_name_input.clear()
        self.address_input.clear()
        self.contact_name_input.clear()
        self.contact_phone_input.clear()
        self.tax_no_input.clear()
        self.bank_name_input.clear()
        self.bank_account_input.clear()

    def _next_supplier_code(self):
        code = "SUP" + datetime.now().strftime("%Y%m%d%H%M%S")
        exists = self.db.fetch_all("SELECT id FROM suppliers WHERE supplier_code=%s LIMIT 1", (code,))
        if exists:
            return code + "01"
        return code

    def _supplier_select_sql(self):
        tax_no_col = "tax_no" if "tax_no" in self.available_columns else "NULL AS tax_no"
        bank_name_col = "bank_name" if "bank_name" in self.available_columns else "NULL AS bank_name"
        bank_account_col = (
            "bank_account" if "bank_account" in self.available_columns else "NULL AS bank_account"
        )
        return f"""
            SELECT supplier_code,
                   supplier_name,
                   address,
                   contact_name,
                   contact_phone,
                   {tax_no_col},
                   {bank_name_col},
                   {bank_account_col}
            FROM suppliers
            WHERE id=%s
        """

    def load_suppliers(self):
        rows = self.db.fetch_all(
            """
            SELECT id, supplier_code, supplier_name
            FROM suppliers
            ORDER BY id DESC
            """
        )
        self.supplier_list.clear()
        for supplier_id, supplier_code, supplier_name in rows:
            text = f"{supplier_code or ''} - {supplier_name or ''}".strip(" -")
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, supplier_id)
            self.supplier_list.addItem(item)

        if rows:
            self.supplier_list.setCurrentRow(0)
        else:
            self.current_supplier_id = None
            self._clear_form()
            self.btn_edit.setEnabled(False)

    def on_supplier_selected(self):
        item = self.supplier_list.currentItem()
        if not item:
            self.current_supplier_id = None
            self._clear_form()
            self.btn_edit.setEnabled(False)
            return

        self.current_supplier_id = item.data(Qt.UserRole)
        self.btn_edit.setEnabled(True)
        self.is_creating = False
        self.set_readonly_mode(True)
        self.load_supplier_detail()

    def load_supplier_detail(self):
        if not self.current_supplier_id:
            self._clear_form()
            return

        rows = self.db.fetch_all(self._supplier_select_sql(), (self.current_supplier_id,))
        if not rows:
            self._clear_form()
            return

        row = rows[0]
        self.supplier_code_input.setText("" if row[0] is None else str(row[0]))
        self.supplier_name_input.setText("" if row[1] is None else str(row[1]))
        self.address_input.setText("" if row[2] is None else str(row[2]))
        self.contact_name_input.setText("" if row[3] is None else str(row[3]))
        self.contact_phone_input.setText("" if row[4] is None else str(row[4]))
        self.tax_no_input.setText("" if row[5] is None else str(row[5]))
        self.bank_name_input.setText("" if row[6] is None else str(row[6]))
        self.bank_account_input.setText("" if row[7] is None else str(row[7]))

    def add_supplier(self):
        self.current_supplier_id = None
        self.is_creating = True
        self.supplier_list.clearSelection()
        self._clear_form()
        self.supplier_code_input.setText(self._next_supplier_code())
        self.set_readonly_mode(False)
        self.supplier_name_input.setFocus()

    def edit_supplier(self):
        if not self.current_supplier_id:
            QMessageBox.warning(self, "提示", "请先选择供应商")
            return
        self.is_creating = False
        self.set_readonly_mode(False)
        self.supplier_name_input.setFocus()

    def _save_payload(self):
        payload = {
            "supplier_code": self.supplier_code_input.text().strip(),
            "supplier_name": self.supplier_name_input.text().strip(),
            "address": self.address_input.text().strip(),
            "contact_name": self.contact_name_input.text().strip(),
            "contact_phone": self.contact_phone_input.text().strip(),
        }
        if "tax_no" in self.available_columns:
            payload["tax_no"] = self.tax_no_input.text().strip()
        if "bank_name" in self.available_columns:
            payload["bank_name"] = self.bank_name_input.text().strip()
        if "bank_account" in self.available_columns:
            payload["bank_account"] = self.bank_account_input.text().strip()
        return payload

    def save_supplier(self):
        payload = self._save_payload()
        supplier_code = payload["supplier_code"]
        supplier_name = payload["supplier_name"]

        if not supplier_code:
            QMessageBox.warning(self, "提示", "供应商编码不能为空")
            return
        if not supplier_name:
            QMessageBox.warning(self, "提示", "供应商名称不能为空")
            return

        try:
            if self.is_creating:
                columns = list(payload.keys())
                values = [payload[key] for key in columns]
                placeholders = ",".join(["%s"] * len(columns))
                with self.db.conn.cursor() as cur:
                    cur.execute(
                        f"INSERT INTO suppliers ({','.join(columns)}) VALUES ({placeholders}) RETURNING id",
                        tuple(values),
                    )
                    self.current_supplier_id = cur.fetchone()[0]
                self.db.conn.commit()
                self.is_creating = False
            else:
                if not self.current_supplier_id:
                    QMessageBox.warning(self, "提示", "请先选择供应商")
                    return
                columns = list(payload.keys())
                values = [payload[key] for key in columns]
                set_clause = ", ".join([f"{col}=%s" for col in columns])
                self.db.execute(
                    f"UPDATE suppliers SET {set_clause} WHERE id=%s",
                    tuple(values + [self.current_supplier_id]),
                )
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"保存失败: {exc}")
            return

        self.set_readonly_mode(True)
        self.load_suppliers()
        self._select_current_supplier()
        QMessageBox.information(self, "提示", "保存成功")

    def _select_current_supplier(self):
        if not self.current_supplier_id:
            return
        for i in range(self.supplier_list.count()):
            item = self.supplier_list.item(i)
            if item and item.data(Qt.UserRole) == self.current_supplier_id:
                self.supplier_list.setCurrentRow(i)
                break
