from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QTableWidget, QAbstractItemView


class InventoryTab:
    def __init__(self):
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)

        top = QHBoxLayout()
        self.inv_kw = QLineEdit()
        self.inv_kw.setPlaceholderText("搜索物料编码/名称")
        self.inv_wh = QComboBox()
        self.inv_wh.addItem("全部仓库", None)
        self.btn_add_wh = QPushButton("新增仓库")
        self.btn_add_loc = QPushButton("新增库位")
        self.btn_refresh_inv = QPushButton("刷新库存")
        top.addWidget(self.inv_kw)
        top.addWidget(self.inv_wh)
        top.addWidget(self.btn_add_wh)
        top.addWidget(self.btn_add_loc)
        top.addWidget(self.btn_refresh_inv)
        layout.addLayout(top)

        self.inv_table = QTableWidget()
        self.inv_table.setColumnCount(8)
        self.inv_table.setHorizontalHeaderLabels(
            ["仓库", "库位", "物料编码", "物料名称", "库存数量", "锁定数量", "均价", "更新时间"]
        )
        self.inv_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.inv_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.inv_table)
