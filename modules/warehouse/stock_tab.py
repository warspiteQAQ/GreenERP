from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLineEdit,
    QComboBox,
    QPushButton,
    QSplitter,
    QLabel,
    QTableWidget,
    QAbstractItemView,
)


class StockTab:
    def __init__(self):
        self.widget = QWidget()
        layout = QVBoxLayout(self.widget)

        top = QHBoxLayout()
        self.doc_kw = QLineEdit()
        self.doc_kw.setPlaceholderText("搜索单号")
        self.doc_type = QComboBox()
        self.doc_type.addItem("全部类型", None)
        for t in ["purchase_in", "sale_out", "production_in", "production_out", "transfer_in", "transfer_out"]:
            self.doc_type.addItem(t, t)
        self.btn_add_doc = QPushButton("新增单据")
        self.btn_add_item = QPushButton("新增明细")
        self.btn_del_item = QPushButton("删除明细")
        self.btn_post = QPushButton("单据过账")
        self.btn_refresh_doc = QPushButton("刷新单据")
        top.addWidget(self.doc_kw)
        top.addWidget(self.doc_type)
        top.addWidget(self.btn_add_doc)
        top.addWidget(self.btn_add_item)
        top.addWidget(self.btn_del_item)
        top.addWidget(self.btn_post)
        top.addWidget(self.btn_refresh_doc)
        layout.addLayout(top)

        split = QSplitter(Qt.Horizontal)

        left = QWidget()
        left_layout = QVBoxLayout(left)
        left_layout.addWidget(QLabel("出入库单据"))
        self.doc_table = QTableWidget()
        self.doc_table.setColumnCount(8)
        self.doc_table.setHorizontalHeaderLabels(["ID", "单据号", "类型", "仓库", "状态", "业务日期", "来源", "创建时间"])
        self.doc_table.setColumnHidden(0, True)
        self.doc_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.doc_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.doc_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.doc_table.setContextMenuPolicy(Qt.CustomContextMenu)
        left_layout.addWidget(self.doc_table)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.addWidget(QLabel("单据明细"))
        self.item_table = QTableWidget()
        self.item_table.setColumnCount(9)
        self.item_table.setHorizontalHeaderLabels(["ID", "物料编码", "物料名称", "库位", "数量", "单价", "采购明细", "订单明细", "备注"])
        self.item_table.setColumnHidden(0, True)
        self.item_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.item_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.item_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        right_layout.addWidget(self.item_table)

        split.addWidget(left)
        split.addWidget(right)
        split.setStretchFactor(0, 2)
        split.setStretchFactor(1, 3)
        layout.addWidget(split)
