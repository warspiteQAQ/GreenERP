from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QComboBox, QTableWidget, QTableWidgetItem,
    QMessageBox, QSplitter, QDialog, QLabel, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from database import Database
from .order_dialog import OrderDialog
from modules.material.material_dialog import MaterialDialog


class MaterialPickerDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("选择物料")
        self.resize(720, 420)
        self.init_ui()
        self.load_materials()

    def init_ui(self):
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入物料编码/名称关键词")
        self.btn_search = QPushButton("筛选")
        self.btn_search.clicked.connect(self.on_search)
        top_layout.addWidget(self.keyword_input)
        top_layout.addWidget(self.btn_search)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "物料编码", "物料名称", "单位"])
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

    def load_materials(self):
        keyword = self.keyword_input.text().strip()
        like_kw = f"%{keyword}%"
        query = """
            SELECT id, material_code, material_name, unit
            FROM materials
            WHERE material_code ILIKE %s OR material_name ILIKE %s
            ORDER BY id DESC
        """
        data = self.db.fetch_all(query, (like_kw, like_kw))
        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

    def on_search(self):
        self.load_materials()

    def accept_selection(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择一个物料")
            return
        self.accept()

    def selected_material(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        mid = self.table.item(row, 0).text()
        code = self.table.item(row, 1).text()
        name = self.table.item(row, 2).text()
        unit = self.table.item(row, 3).text()
        return mid, code, name, unit


class OrderDetailDialog(QDialog):
    def __init__(self, material_info, parent=None, detail=None):
        super().__init__(parent)
        self.material_info = material_info
        self.detail = detail
        self.setWindowTitle("订单明细")
        self.resize(420, 220)
        self.init_ui()

        if self.detail:
            self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()

        form_layout = QVBoxLayout()
        material_line = QLabel(
            f"{self.material_info['code']} - {self.material_info['name']} ({self.material_info['unit']})"
        )
        form_layout.addWidget(QLabel("物料"))
        form_layout.addWidget(material_line)

        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("数量"))
        self.qty = QDoubleSpinBox()
        self.qty.setDecimals(4)
        self.qty.setMinimum(0.0001)
        self.qty.setMaximum(999999999)
        self.qty.setValue(1.0)
        qty_layout.addWidget(self.qty)
        form_layout.addLayout(qty_layout)

        price_layout = QHBoxLayout()
        price_layout.addWidget(QLabel("单价"))
        self.price = QDoubleSpinBox()
        self.price.setDecimals(4)
        self.price.setMinimum(0)
        self.price.setMaximum(999999999)
        self.price.setValue(0)
        price_layout.addWidget(self.price)
        form_layout.addLayout(price_layout)

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addLayout(form_layout)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def load_data(self):
        self.qty.setValue(float(self.detail.get("quantity", 1)))
        price_val = self.detail.get("unit_price")
        self.price.setValue(float(price_val) if price_val is not None else 0)

    def values(self):
        return self.qty.value(), self.price.value()


class OrderPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.current_order_id = None
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("输入订单/项目关键词")
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
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels(
            ["ID", "订单编号", "订单名称", "项目ID", "项目编号", "项目名称", "金额", "状态", "创建时间"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setColumnHidden(3, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)

        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(7)
        self.detail_table.setHorizontalHeaderLabels(
            ["ID", "物料ID", "物料编码", "物料名称", "数量", "单价", "金额"]
        )
        self.detail_table.setColumnHidden(0, True)
        self.detail_table.setColumnHidden(1, True)
        self.detail_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.detail_table.setEditTriggers(QTableWidget.NoEditTriggers)

        detail_btn_layout = QHBoxLayout()
        self.btn_add_detail = QPushButton("添加物料")
        self.btn_new_material = QPushButton("新建物料")
        self.btn_edit_detail = QPushButton("编辑明细")
        self.btn_delete_detail = QPushButton("删除明细")
        detail_btn_layout.addWidget(self.btn_add_detail)
        detail_btn_layout.addWidget(self.btn_new_material)
        detail_btn_layout.addWidget(self.btn_edit_detail)
        detail_btn_layout.addWidget(self.btn_delete_detail)
        detail_btn_layout.addStretch()

        detail_layout = QVBoxLayout()
        detail_layout.addWidget(self.detail_table)
        detail_layout.addLayout(detail_btn_layout)
        detail_widget = QWidget()
        detail_widget.setLayout(detail_layout)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(self.table)
        left_widget.setLayout(left_layout)

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(left_widget)
        splitter.addWidget(detail_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        self.btn_add.clicked.connect(self.add_order)
        self.btn_edit.clicked.connect(self.edit_order)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.search_input.textChanged.connect(self.load_orders)
        self.status_filter.currentIndexChanged.connect(self.load_orders)
        self.table.itemSelectionChanged.connect(self.on_order_selection_changed)

        self.btn_add_detail.clicked.connect(self.add_detail)
        self.btn_new_material.clicked.connect(self.new_material)
        self.btn_edit_detail.clicked.connect(self.edit_detail)
        self.btn_delete_detail.clicked.connect(self.delete_detail)

        main_layout.addLayout(top_layout)
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)

    def _build_filter(self):
        keyword = self.search_input.text().strip()
        status = self.status_filter.currentText()
        return keyword, status

    def load_orders(self):
        keyword, status = self._build_filter()
        like_kw = f"%{keyword}%"

        where_clauses = [
            "(o.order_code ILIKE %s OR o.order_name ILIKE %s "
            "OR p.project_code ILIKE %s OR p.project_name ILIKE %s)"
        ]
        params = [like_kw, like_kw, like_kw, like_kw]

        if status != "全部":
            where_clauses.append("o.status = %s")
            params.append(status)

        where_sql = " AND ".join(where_clauses)
        query = f"""
            SELECT o.id, o.order_code, o.order_name,
                   p.id, p.project_code, p.project_name,
                   o.amount, o.status, o.created_at
            FROM orders o
            JOIN projects p ON o.project_id = p.id
            WHERE {where_sql}
            ORDER BY o.id DESC
        """
        data = self.db.fetch_all(query, tuple(params))

        self.table.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                self.table.setItem(
                    row_idx, col_idx, QTableWidgetItem("" if value is None else str(value))
                )

        if not data:
            self.current_order_id = None
            self.detail_table.setRowCount(0)

    def refresh_data(self):
        self.load_orders()
        if self.current_order_id:
            self.load_order_details()

    def add_order(self):
        dialog = OrderDialog()
        if dialog.exec():
            self.load_orders()

    def edit_order(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择一条记录")
            return

        order_id = self.table.item(row, 0).text()
        dialog = OrderDialog(order_id)
        if dialog.exec():
            self.load_orders()

    def on_order_selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            self.current_order_id = None
            self.detail_table.setRowCount(0)
            return

        self.current_order_id = self.table.item(row, 0).text()
        self.load_order_details()

    def load_order_details(self):
        if not self.current_order_id:
            return
        query = """
            SELECT od.id, m.id, m.material_code, m.material_name,
                   od.quantity, od.unit_price
            FROM order_details od
            JOIN materials m ON od.material_id = m.id
            WHERE od.order_id = %s
            ORDER BY od.id DESC
        """
        data = self.db.fetch_all(query, (self.current_order_id,))
        self.detail_table.setRowCount(len(data))
        for r, row in enumerate(data):
            amount = None
            if row[4] is not None and row[5] is not None:
                amount = float(row[4]) * float(row[5])
            display_row = list(row) + [amount]
            for c, val in enumerate(display_row):
                self.detail_table.setItem(
                    r, c, QTableWidgetItem("" if val is None else str(val))
                )

    def add_detail(self):
        if not self.current_order_id:
            QMessageBox.warning(self, "提示", "请先选择订单")
            return
        picker = MaterialPickerDialog(self.db, self)
        if not picker.exec():
            return
        selected = picker.selected_material()
        if not selected:
            return
        mid, code, name, unit = selected
        dialog = OrderDetailDialog(
            {"id": mid, "code": code, "name": name, "unit": unit}, self
        )
        if not dialog.exec():
            return
        qty, price = dialog.values()
        self.db.execute(
            """
            INSERT INTO order_details
            (order_id, material_id, quantity, unit_price)
            VALUES (%s,%s,%s,%s)
            """,
            (self.current_order_id, mid, qty, price)
        )
        self.load_order_details()

    def new_material(self):
        dialog = MaterialDialog()
        if dialog.exec():
            self.add_detail()

    def edit_detail(self):
        row = self.detail_table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择一条明细")
            return

        detail_id = self.detail_table.item(row, 0).text()
        mid = self.detail_table.item(row, 1).text()
        code = self.detail_table.item(row, 2).text()
        name = self.detail_table.item(row, 3).text()
        qty = self.detail_table.item(row, 4).text()
        price = self.detail_table.item(row, 5).text()
        unit = ""
        unit_rows = self.db.fetch_all(
            "SELECT unit FROM materials WHERE id=%s",
            (mid,)
        )
        if unit_rows:
            unit = unit_rows[0][0] or ""

        detail = {"quantity": qty, "unit_price": price}
        dialog = OrderDetailDialog(
            {"id": mid, "code": code, "name": name, "unit": unit}, self, detail
        )
        if not dialog.exec():
            return
        new_qty, new_price = dialog.values()
        self.db.execute(
            """
            UPDATE order_details
            SET quantity=%s, unit_price=%s
            WHERE id=%s
            """,
            (new_qty, new_price, detail_id)
        )
        self.load_order_details()

    def delete_detail(self):
        row = self.detail_table.currentRow()
        if row < 0:
            return
        detail_id = self.detail_table.item(row, 0).text()
        self.db.execute("DELETE FROM order_details WHERE id=%s", (detail_id,))
        self.load_order_details()
