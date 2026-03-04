from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLineEdit, QComboBox, QPushButton, QTableWidget, QAbstractItemView


class TransactionTab:
    def __init__(self):
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)

        top = QHBoxLayout()
        self.tx_kw = QLineEdit()
        self.tx_kw.setPlaceholderText("搜索物料编码/名称")
        self.tx_wh = QComboBox()
        self.tx_wh.addItem("全部仓库", None)
        self.btn_refresh_tx = QPushButton("刷新流水")
        top.addWidget(self.tx_kw)
        top.addWidget(self.tx_wh)
        top.addWidget(self.btn_refresh_tx)
        layout.addLayout(top)

        self.tx_table = QTableWidget()
        self.tx_table.setColumnCount(10)
        self.tx_table.setHorizontalHeaderLabels(["时间", "方向", "仓库", "库位", "物料编码", "物料名称", "数量", "结存前", "结存后", "单据号"])
        self.tx_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tx_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.tx_table)
