from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget,
    QWidget, QFormLayout, QLineEdit,
    QPushButton, QHBoxLayout, QCheckBox, QComboBox
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
        self.init_ui()

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

        self.tabs.addTab(self.tab_basic, "基础信息")
        self.tabs.addTab(self.tab_stock, "库存属性")
        self.tabs.addTab(self.tab_prod, "生产属性")
        self.tabs.addTab(self.tab_quality, "质量属性")

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

    def save(self):
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
            self.db.execute(query, (
                self.code.text(),
                self.name.text(),
                self.unit.text(),
                self.spec.text(),
                self.cost.text(),
                self.safety_stock.text(),
                self.is_produced.isChecked(),
                self.inspection_required.isChecked(),
                self.material_type.currentText(),
                self.material_id
            ))
        else:
            query = """
                INSERT INTO materials
                (material_code, material_name, unit,
                 specification, standard_cost,
                 safety_stock, is_produced,
                 inspection_required, material_type)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
            """
            self.db.execute(query, (
                self.code.text(),
                self.name.text(),
                self.unit.text(),
                self.spec.text(),
                self.cost.text(),
                self.safety_stock.text(),
                self.is_produced.isChecked(),
                self.inspection_required.isChecked(),
                self.material_type.currentText()
            ))

        self.accept()
