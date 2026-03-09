from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from database import Database


class MaterialDialog(QDialog):
    def __init__(self, material_id=None):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.material_id = material_id
        self.setWindowTitle("物料信息")
        self.resize(500, 400)
        self.ensure_material_supplier_table()
        self.init_ui()
        self.load_supplier_options()

        if self.material_id:
            self.load_data()

    def init_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # 基础信息
        self.tab_basic = QWidget()
        form = QFormLayout()

        self.code = QLineEdit()
        self.name = QLineEdit()
        self.material_type = QComboBox()
        self.material_type.addItems(["原材料", "成品", "生产件"])
        self.unit = QLineEdit()
        self.spec = QLineEdit()
        self.cost = QLineEdit()

        form.addRow("物料编码", self.code)
        form.addRow("物料名称", self.name)
        form.addRow("物料种类", self.material_type)
        form.addRow("单位", self.unit)
        form.addRow("规格", self.spec)
        form.addRow("标准成本", self.cost)
        self.tab_basic.setLayout(form)

        # 库存属性
        self.tab_stock = QWidget()
        stock_form = QFormLayout()
        self.safety_stock = QLineEdit()
        stock_form.addRow("安全库存", self.safety_stock)
        self.tab_stock.setLayout(stock_form)

        # 生产属性
        self.tab_prod = QWidget()
        prod_form = QFormLayout()
        self.is_produced = QCheckBox("是否自产")
        prod_form.addRow(self.is_produced)
        self.tab_prod.setLayout(prod_form)

        # 质量属性
        self.tab_quality = QWidget()
        quality_form = QFormLayout()
        self.inspection_required = QCheckBox("需要检验")
        quality_form.addRow(self.inspection_required)
        self.tab_quality.setLayout(quality_form)

        # 供应商
        self.tab_supplier = QWidget()
        supplier_layout = QVBoxLayout()
        supplier_action = QHBoxLayout()
        self.supplier_combo = QComboBox()
        self.btn_add_supplier = QPushButton("添加供应商")
        self.btn_remove_supplier = QPushButton("移除选中")
        supplier_action.addWidget(self.supplier_combo)
        supplier_action.addWidget(self.btn_add_supplier)
        supplier_action.addWidget(self.btn_remove_supplier)

        self.supplier_table = QTableWidget()
        self.supplier_table.setColumnCount(3)
        self.supplier_table.setHorizontalHeaderLabels(["ID", "供应商编码", "供应商名称"])
        self.supplier_table.setColumnHidden(0, True)
        self.supplier_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.supplier_table.setEditTriggers(QTableWidget.NoEditTriggers)

        supplier_layout.addLayout(supplier_action)
        supplier_layout.addWidget(self.supplier_table)
        self.tab_supplier.setLayout(supplier_layout)

        self.tabs.addTab(self.tab_basic, "基础信息")
        self.tabs.addTab(self.tab_stock, "库存属性")
        self.tabs.addTab(self.tab_prod, "生产属性")
        self.tabs.addTab(self.tab_quality, "质量属性")
        self.tabs.addTab(self.tab_supplier, "供应商")

        btn_layout = QHBoxLayout()
        self.btn_save = QPushButton("保存")
        self.btn_cancel = QPushButton("取消")
        btn_layout.addWidget(self.btn_save)
        btn_layout.addWidget(self.btn_cancel)

        layout.addWidget(self.tabs)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

        self.btn_save.clicked.connect(self.save)
        self.btn_cancel.clicked.connect(self.reject)
        self.btn_add_supplier.clicked.connect(self.add_supplier)
        self.btn_remove_supplier.clicked.connect(self.remove_supplier)

    def ensure_material_supplier_table(self):
        query = """
            CREATE TABLE IF NOT EXISTS material_suppliers (
                id SERIAL PRIMARY KEY,
                material_id INT NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
                supplier_id INT NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (material_id, supplier_id)
            )
        """
        self.db.execute(query)

    def load_supplier_options(self):
        self.supplier_combo.clear()
        suppliers = self.db.fetch_all(
            "SELECT id, supplier_code, supplier_name FROM suppliers ORDER BY id DESC"
        )
        for sid, code, name in suppliers:
            self.supplier_combo.addItem(f"{code} - {name}", sid)

    def add_supplier(self):
        supplier_id = self.supplier_combo.currentData()
        if supplier_id is None:
            QMessageBox.warning(self, "提示", "暂无可选供应商")
            return

        for row in range(self.supplier_table.rowCount()):
            item = self.supplier_table.item(row, 0)
            if item and item.text() == str(supplier_id):
                return

        current_text = self.supplier_combo.currentText()
        if " - " in current_text:
            supplier_code, supplier_name = current_text.split(" - ", 1)
        else:
            supplier_code, supplier_name = "", current_text

        row = self.supplier_table.rowCount()
        self.supplier_table.insertRow(row)
        self.supplier_table.setItem(row, 0, QTableWidgetItem(str(supplier_id)))
        self.supplier_table.setItem(row, 1, QTableWidgetItem(supplier_code))
        self.supplier_table.setItem(row, 2, QTableWidgetItem(supplier_name))

    def remove_supplier(self):
        selected_rows = sorted(
            {idx.row() for idx in self.supplier_table.selectedIndexes()}, reverse=True
        )
        for row in selected_rows:
            self.supplier_table.removeRow(row)

    def selected_supplier_ids(self):
        supplier_ids = []
        for row in range(self.supplier_table.rowCount()):
            item = self.supplier_table.item(row, 0)
            if item and item.text().strip():
                supplier_ids.append(int(item.text()))
        return supplier_ids

    def load_material_suppliers(self):
        self.supplier_table.setRowCount(0)
        rows = self.db.fetch_all(
            """
            SELECT s.id, s.supplier_code, s.supplier_name
            FROM material_suppliers ms
            JOIN suppliers s ON s.id = ms.supplier_id
            WHERE ms.material_id=%s
            ORDER BY ms.id
            """,
            (self.material_id,),
        )
        for supplier_id, supplier_code, supplier_name in rows:
            row = self.supplier_table.rowCount()
            self.supplier_table.insertRow(row)
            self.supplier_table.setItem(row, 0, QTableWidgetItem(str(supplier_id)))
            self.supplier_table.setItem(row, 1, QTableWidgetItem(supplier_code or ""))
            self.supplier_table.setItem(row, 2, QTableWidgetItem(supplier_name or ""))

    def load_data(self):
        query = """
            SELECT material_code,
                   material_name,
                   unit,
                   specification,
                   standard_cost,
                   safety_stock,
                   is_produced,
                   inspection_required,
                   material_type
            FROM materials
            WHERE id=%s
        """
        data = self.db.fetch_all(query, (self.material_id,))
        if data:
            row = data[0]
            self.code.setText(row[0] or "")
            self.name.setText(row[1] or "")
            self.unit.setText(row[2] or "")
            self.spec.setText(row[3] or "")
            self.cost.setText("" if row[4] is None else str(row[4]))
            self.safety_stock.setText("" if row[5] is None else str(row[5]))
            self.is_produced.setChecked(bool(row[6]))
            self.inspection_required.setChecked(bool(row[7]))

            material_type = row[8] if len(row) > 8 else None
            if material_type:
                idx = self.material_type.findText(str(material_type))
                self.material_type.setCurrentIndex(idx if idx >= 0 else 0)

        self.load_material_suppliers()

    def save(self):
        try:
            supplier_ids = self.selected_supplier_ids()
            with self.db.conn.cursor() as cur:
                if self.material_id:
                    query = """
                        UPDATE materials
                        SET material_code=%s, material_name=%s,
                            unit=%s, specification=%s,
                            standard_cost=%s, safety_stock=%s,
                            is_produced=%s, inspection_required=%s,
                            material_type=%s
                        WHERE id=%s
                    """
                    cur.execute(
                        query,
                        (
                            self.code.text(),
                            self.name.text(),
                            self.unit.text(),
                            self.spec.text(),
                            self.cost.text(),
                            self.safety_stock.text(),
                            self.is_produced.isChecked(),
                            self.inspection_required.isChecked(),
                            self.material_type.currentText(),
                            self.material_id,
                        ),
                    )
                    material_id = self.material_id
                else:
                    query = """
                        INSERT INTO materials
                        (material_code, material_name, unit,
                         specification, standard_cost,
                         safety_stock, is_produced,
                         inspection_required, material_type)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        RETURNING id
                    """
                    cur.execute(
                        query,
                        (
                            self.code.text(),
                            self.name.text(),
                            self.unit.text(),
                            self.spec.text(),
                            self.cost.text(),
                            self.safety_stock.text(),
                            self.is_produced.isChecked(),
                            self.inspection_required.isChecked(),
                            self.material_type.currentText(),
                        ),
                    )
                    material_id = cur.fetchone()[0]

                cur.execute("DELETE FROM material_suppliers WHERE material_id=%s", (material_id,))
                for supplier_id in supplier_ids:
                    cur.execute(
                        "INSERT INTO material_suppliers (material_id, supplier_id) VALUES (%s, %s)",
                        (material_id, supplier_id),
                    )
            self.db.conn.commit()
            self.accept()
        except Exception as e:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"保存失败：{e}")
