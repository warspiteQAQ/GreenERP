
from datetime import datetime

from PySide6.QtCore import Qt, QDate, QEvent
from PySide6.QtGui import QColor, QBrush
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QMessageBox,
    QSplitter,
    QDialog,
    QFormLayout,
    QDoubleSpinBox,
    QSpinBox,
    QDateEdit,
    QMenu,
    QTreeWidget,
    QTreeWidgetItem,
    QFileDialog,
)

from database import Database


class OrderPickerDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("选择订单")
        self.resize(760, 420)
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索订单号/订单名称")
        self.btn_search = QPushButton("查询")
        self.btn_search.clicked.connect(self.load_orders)
        self.search_input.returnPressed.connect(self.load_orders)
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.btn_search)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "订单号", "订单名称", "状态", "创建时间"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        bottom = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel.clicked.connect(self.reject)
        bottom.addStretch()
        bottom.addWidget(self.btn_ok)
        bottom.addWidget(self.btn_cancel)
        layout.addLayout(bottom)

    def load_orders(self):
        kw = self.search_input.text().strip()
        like_kw = f"%{kw}%"
        rows = self.db.fetch_all(
            """
            SELECT id, order_code, order_name, status, created_at
            FROM orders
            WHERE order_code ILIKE %s OR order_name ILIKE %s
            ORDER BY id DESC
            """,
            (like_kw, like_kw),
        )
        self.table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
        if rows:
            self.table.selectRow(0)

    def selected_order_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.text() if item else None

    def accept_selection(self):
        if not self.selected_order_id():
            QMessageBox.warning(self, "提示", "请选择订单")
            return
        self.accept()


class QuoteEditDialog(QDialog):
    def __init__(self, current_quote=None, parent=None):
        super().__init__(parent)
        self.current_quote = current_quote or {}
        self.setWindowTitle("录入信息")
        self.resize(460, 320)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.supplier_name_input = QLineEdit(self.current_quote.get("supplier_name") or "")
        self.purchase_link_input = QLineEdit(self.current_quote.get("purchase_link") or "")

        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(4)
        self.price_input.setMinimum(0)
        self.price_input.setMaximum(999999999)
        self.price_input.setValue(float(self.current_quote.get("quote_unit_price") or 0))

        self.lead_days_input = QSpinBox()
        self.lead_days_input.setMinimum(0)
        self.lead_days_input.setMaximum(9999)
        self.lead_days_input.setValue(int(self.current_quote.get("lead_time_days") or 0))

        self.tax_rate_input = QDoubleSpinBox()
        self.tax_rate_input.setDecimals(2)
        self.tax_rate_input.setMinimum(0)
        self.tax_rate_input.setMaximum(100)
        self.tax_rate_input.setValue(float(self.current_quote.get("tax_rate") or 0))

        self.freight_input = QDoubleSpinBox()
        self.freight_input.setDecimals(4)
        self.freight_input.setMinimum(0)
        self.freight_input.setMaximum(999999999)
        self.freight_input.setValue(float(self.current_quote.get("freight") or 0))

        self.valid_until = QDateEdit()
        self.valid_until.setCalendarPopup(True)
        self.valid_until.setDisplayFormat("yyyy-MM-dd")
        self.valid_until.setDate(QDate.currentDate())
        valid_until = self.current_quote.get("valid_until")
        if valid_until:
            qd = QDate.fromString(str(valid_until), "yyyy-MM-dd")
            if qd.isValid():
                self.valid_until.setDate(qd)

        form.addRow("供应商名称", self.supplier_name_input)
        form.addRow("购买链接", self.purchase_link_input)
        form.addRow("报价单价", self.price_input)
        form.addRow("交期(天)", self.lead_days_input)
        form.addRow("税率(%)", self.tax_rate_input)
        form.addRow("运费", self.freight_input)
        form.addRow("有效期", self.valid_until)
        layout.addLayout(form)

        bottom = QHBoxLayout()
        self.btn_ok = QPushButton("保存")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        bottom.addStretch()
        bottom.addWidget(self.btn_ok)
        bottom.addWidget(self.btn_cancel)
        layout.addLayout(bottom)

    def values(self):
        return {
            "supplier_name": self.supplier_name_input.text().strip(),
            "purchase_link": self.purchase_link_input.text().strip(),
            "quote_unit_price": self.price_input.value(),
            "lead_time_days": self.lead_days_input.value(),
            "tax_rate": self.tax_rate_input.value(),
            "freight": self.freight_input.value(),
            "valid_until": self.valid_until.date().toString("yyyy-MM-dd"),
        }


class CostAccountingDialog(QDialog):
    def __init__(self, current_cost=0, current_drawing_path="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("成本核算")
        self.resize(520, 180)
        self.current_cost = current_cost
        self.current_drawing_path = current_drawing_path or ""
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.cost_input = QDoubleSpinBox()
        self.cost_input.setDecimals(4)
        self.cost_input.setMinimum(0)
        self.cost_input.setMaximum(999999999)
        self.cost_input.setValue(float(self.current_cost or 0))

        drawing_layout = QHBoxLayout()
        self.drawing_path_input = QLineEdit(self.current_drawing_path)
        self.btn_pick_drawing = QPushButton("选择图纸")
        self.btn_pick_drawing.clicked.connect(self.pick_drawing)
        drawing_layout.addWidget(self.drawing_path_input)
        drawing_layout.addWidget(self.btn_pick_drawing)

        form.addRow("标准成本", self.cost_input)
        form.addRow("图纸路径", drawing_layout)
        layout.addLayout(form)

        bottom = QHBoxLayout()
        self.btn_ok = QPushButton("保存")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)
        bottom.addStretch()
        bottom.addWidget(self.btn_ok)
        bottom.addWidget(self.btn_cancel)
        layout.addLayout(bottom)

    def pick_drawing(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图纸")
        if file_path:
            self.drawing_path_input.setText(file_path)

    def values(self):
        return {
            "standard_cost": self.cost_input.value(),
            "drawing_path": self.drawing_path_input.text().strip(),
        }


class InquiryPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.current_inquiry_id = None
        self.current_item_id = None
        self.current_item_material_id = None
        self.current_item_is_quoteable = False
        self.init_ui()
        self.load_inquiries()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索询价单号/来源订单号")
        self.btn_search = QPushButton("查询")
        self.btn_create = QPushButton("订单询价")
        self.btn_refresh = QPushButton("刷新")

        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.btn_search)
        top_layout.addWidget(self.btn_create)
        top_layout.addWidget(self.btn_refresh)
        main_layout.addLayout(top_layout)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("询价单"))
        self.inquiry_table = QTableWidget()
        self.inquiry_table.setColumnCount(6)
        self.inquiry_table.setHorizontalHeaderLabels(
            ["ID", "询价单号", "来源订单", "状态", "截止日期", "创建时间"]
        )
        self.inquiry_table.setColumnHidden(0, True)
        self.inquiry_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.inquiry_table.setSelectionMode(QTableWidget.SingleSelection)
        self.inquiry_table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.inquiry_table)

        mid_widget = QWidget()
        mid_layout = QVBoxLayout(mid_widget)
        mid_layout.addWidget(QLabel("物料详情(树)"))
        self.item_tree = QTreeWidget()
        self.item_tree.setColumnCount(10)
        self.item_tree.setHeaderLabels(
            [
                "ID",
                "订单明细ID",
                "物料ID",
                "物料编码",
                "物料名称",
                "需求数量",
                "状态",
                "中标供应商",
                "中标单价",
                "成本核算",
            ]
        )
        self.item_tree.setColumnHidden(0, True)
        self.item_tree.setColumnHidden(1, True)
        self.item_tree.setColumnHidden(2, True)
        self.item_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        mid_layout.addWidget(self.item_tree)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("供应商及报价"))

        action_layout = QHBoxLayout()
        self.btn_edit_quote = QPushButton("录入信息")
        self.btn_auto_pick = QPushButton("自动选最低价")
        self.btn_refresh_quote = QPushButton("刷新报价")
        action_layout.addWidget(self.btn_edit_quote)
        action_layout.addWidget(self.btn_auto_pick)
        action_layout.addWidget(self.btn_refresh_quote)
        right_layout.addLayout(action_layout)

        self.quote_table = QTableWidget()
        self.quote_table.setColumnCount(9)
        self.quote_table.setHorizontalHeaderLabels(
            [
                "报价行ID",
                "供应商ID",
                "供应商",
                "购买链接",
                "报价单价",
                "交期(天)",
                "有效期",
                "中标",
                "税率",
            ]
        )
        self.quote_table.setColumnHidden(0, True)
        self.quote_table.setColumnHidden(1, True)
        self.quote_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.quote_table.setSelectionMode(QTableWidget.SingleSelection)
        self.quote_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.quote_table.setContextMenuPolicy(Qt.CustomContextMenu)
        right_layout.addWidget(self.quote_table)

        splitter.addWidget(left_widget)
        splitter.addWidget(mid_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        splitter.setStretchFactor(2, 4)
        main_layout.addWidget(splitter)

        self.btn_search.clicked.connect(self.load_inquiries)
        self.search_input.returnPressed.connect(self.load_inquiries)
        self.btn_create.clicked.connect(self.create_from_order)
        self.btn_refresh.clicked.connect(self.refresh_data)

        self.inquiry_table.itemSelectionChanged.connect(self.on_inquiry_changed)
        self.item_tree.itemSelectionChanged.connect(self.on_item_changed)
        self.item_tree.customContextMenuRequested.connect(self.show_item_context_menu)

        self.btn_edit_quote.clicked.connect(self.edit_quote)
        self.btn_auto_pick.clicked.connect(self.auto_pick_lowest)
        self.btn_refresh_quote.clicked.connect(self.load_quotes)
        self.quote_table.customContextMenuRequested.connect(self.show_quote_context_menu)
        self.quote_table.viewport().installEventFilter(self)
        self._set_quote_actions_enabled(False)

    def eventFilter(self, obj, event):
        if obj is self.quote_table.viewport() and event.type() == QEvent.MouseButtonPress:
            pos = event.position().toPoint() if hasattr(event, "position") else event.pos()
            idx = self.quote_table.indexAt(pos)
            if not idx.isValid():
                self.quote_table.clearSelection()
                self.quote_table.setCurrentCell(-1, -1)
        return super().eventFilter(obj, event)

    def _set_quote_actions_enabled(self, enabled):
        self.btn_edit_quote.setEnabled(enabled)
        self.btn_auto_pick.setEnabled(enabled)

    def _gen_inquiry_code(self):
        return "IQ" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    def _set_tree_item_style(self, item: QTreeWidgetItem, node_type: str):
        # node_type: parent_production / child_quoteable / child_selected / normal_quoteable / normal_selected / inventory / disabled
        if node_type == "parent_production":
            fg = QBrush(QColor("#5c6b7a"))
            bg = QBrush(QColor("#f4f6f8"))
        elif node_type == "inventory":
            fg = QBrush(QColor("#664d03"))
            bg = QBrush(QColor("#fff3cd"))
        elif node_type in ("child_selected", "normal_selected"):
            fg = QBrush(QColor("#0f5132"))
            bg = QBrush(QColor("#d1e7dd"))
        elif node_type in ("child_quoteable", "normal_quoteable"):
            fg = QBrush(QColor("#084298"))
            bg = QBrush(QColor("#e7f1ff"))
        else:
            fg = QBrush(QColor("#6c757d"))
            bg = QBrush(QColor("#f8f9fa"))

        for col in range(self.item_tree.columnCount()):
            item.setForeground(col, fg)
            item.setBackground(col, bg)

    def load_inquiries(self):
        kw = self.search_input.text().strip()
        like_kw = f"%{kw}%"
        rows = self.db.fetch_all(
            """
            SELECT io.id, io.inquiry_code, o.order_code, io.status, io.inquiry_deadline, io.created_at
            FROM inquiry_orders io
            LEFT JOIN orders o ON io.source_order_id = o.id
            WHERE io.inquiry_code ILIKE %s OR COALESCE(o.order_code, '') ILIKE %s
            ORDER BY io.id DESC
            """,
            (like_kw, like_kw),
        )
        self.inquiry_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.inquiry_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

        if rows:
            self.inquiry_table.selectRow(0)
        else:
            self.current_inquiry_id = None
            self.current_item_id = None
            self.current_item_material_id = None
            self.current_item_is_quoteable = False
            self.item_tree.clear()
            self.quote_table.setRowCount(0)
            self._set_quote_actions_enabled(False)

    def on_inquiry_changed(self):
        row = self.inquiry_table.currentRow()
        if row < 0:
            self.current_inquiry_id = None
            self.current_item_id = None
            self.current_item_material_id = None
            self.current_item_is_quoteable = False
            self.item_tree.clear()
            self.quote_table.setRowCount(0)
            self._set_quote_actions_enabled(False)
            return

        inquiry_id_item = self.inquiry_table.item(row, 0)
        self.current_inquiry_id = inquiry_id_item.text() if inquiry_id_item else None
        self.load_items()

    def load_items(self):
        if not self.current_inquiry_id:
            self.item_tree.clear()
            return

        source_rows = self.db.fetch_all(
            "SELECT source_order_id FROM inquiry_orders WHERE id=%s",
            (self.current_inquiry_id,),
        )
        if not source_rows:
            self.item_tree.clear()
            return

        source_order_id = source_rows[0][0]
        order_details = self.db.fetch_all(
            """
            SELECT od.id,
                   od.material_id,
                   od.quantity,
                   m.material_code,
                   m.material_name,
                   COALESCE(m.material_type, '') AS material_type,
                   m.standard_cost
            FROM order_details od
            JOIN materials m ON od.material_id = m.id
            WHERE od.order_id=%s
            ORDER BY od.id
            """,
            (source_order_id,),
        )
        inquiry_rows = self.db.fetch_all(
            """
            SELECT ioi.id,
                   ioi.source_order_detail_id,
                   ioi.material_id,
                   m.material_code,
                   m.material_name,
                   ioi.required_qty,
                   ioi.status,
                   COALESCE(s.supplier_name, ''),
                   ioi.selected_unit_price,
                   m.standard_cost
            FROM inquiry_order_items ioi
            JOIN materials m ON ioi.material_id = m.id
            LEFT JOIN suppliers s ON ioi.selected_supplier_id = s.id
            WHERE ioi.inquiry_order_id=%s
            ORDER BY ioi.id
            """,
            (self.current_inquiry_id,),
        )

        inquiry_map = {}
        for row in inquiry_rows:
            inquiry_map[(str(row[1]), str(row[2]))] = row

        self.item_tree.clear()
        first_quoteable_item = None

        for detail_id, root_material_id, root_qty, root_code, root_name, root_type, root_cost in order_details:
            if root_type == "生产件":
                root = QTreeWidgetItem([
                    "",
                    str(detail_id),
                    str(root_material_id),
                    f"🧩 生产件 {root_code or ''}",
                    root_name or "",
                    "" if root_qty is None else str(root_qty),
                    "父项-不询价",
                    "",
                    "",
                    "" if root_cost is None else str(root_cost),
                ])
                root.setData(0, Qt.UserRole, None)
                root.setData(1, Qt.UserRole, str(root_material_id))
                root.setData(2, Qt.UserRole, False)
                self._set_tree_item_style(root, "parent_production")
                self.item_tree.addTopLevelItem(root)

                components = self.db.fetch_all(
                    """
                    SELECT mc.component_material_id,
                           mc.quantity,
                           m.material_code,
                           m.material_name,
                           m.standard_cost
                    FROM material_components mc
                    JOIN materials m ON mc.component_material_id = m.id
                    WHERE mc.parent_material_id=%s
                    ORDER BY mc.id
                    """,
                    (root_material_id,),
                )
                for comp_mid, comp_ratio, comp_code, comp_name, comp_cost in components:
                    key = (str(detail_id), str(comp_mid))
                    inquiry_item = inquiry_map.get(key)
                    if inquiry_item:
                        inquiry_id = str(inquiry_item[0])
                        req_qty = inquiry_item[5]
                        status = inquiry_item[6]
                        status_text = "使用库存" if status == "inventory" else status
                        supplier_name = inquiry_item[7]
                        selected_price = inquiry_item[8]
                        standard_cost = inquiry_item[9]
                        quoteable = status != "inventory"
                    else:
                        inquiry_id = ""
                        req_qty = float(root_qty or 0) * float(comp_ratio or 0)
                        status = "未生成"
                        status_text = status
                        supplier_name = ""
                        selected_price = ""
                        standard_cost = comp_cost
                        quoteable = False

                    child = QTreeWidgetItem([
                        inquiry_id,
                        str(detail_id),
                        str(comp_mid),
                        f"🔹 子料 {comp_code or ''}",
                        comp_name or "",
                        "" if req_qty is None else str(req_qty),
                        status_text or "",
                        supplier_name or "",
                        "" if selected_price is None else str(selected_price),
                        "" if standard_cost is None else str(standard_cost),
                    ])
                    child.setData(0, Qt.UserRole, inquiry_id or None)
                    child.setData(1, Qt.UserRole, str(comp_mid))
                    child.setData(2, Qt.UserRole, quoteable)
                    if status == "inventory":
                        child_style = "inventory"
                    elif selected_price not in (None, "", "None"):
                        child_style = "child_selected"
                    elif quoteable:
                        child_style = "child_quoteable"
                    else:
                        child_style = "disabled"
                    self._set_tree_item_style(child, child_style)
                    root.addChild(child)
                    if quoteable and first_quoteable_item is None:
                        first_quoteable_item = child
                root.setExpanded(True)
            else:
                key = (str(detail_id), str(root_material_id))
                inquiry_item = inquiry_map.get(key)
                if inquiry_item:
                    inquiry_id = str(inquiry_item[0])
                    req_qty = inquiry_item[5]
                    status = inquiry_item[6]
                    status_text = "使用库存" if status == "inventory" else status
                    supplier_name = inquiry_item[7]
                    selected_price = inquiry_item[8]
                    standard_cost = inquiry_item[9]
                    quoteable = status != "inventory"
                else:
                    inquiry_id = ""
                    req_qty = root_qty
                    status = "未生成"
                    status_text = status
                    supplier_name = ""
                    selected_price = ""
                    standard_cost = root_cost
                    quoteable = False

                top = QTreeWidgetItem([
                    inquiry_id,
                    str(detail_id),
                    str(root_material_id),
                    f"📦 物料 {root_code or ''}",
                    root_name or "",
                    "" if req_qty is None else str(req_qty),
                    status_text or "",
                    supplier_name or "",
                    "" if selected_price is None else str(selected_price),
                    "" if standard_cost is None else str(standard_cost),
                ])
                top.setData(0, Qt.UserRole, inquiry_id or None)
                top.setData(1, Qt.UserRole, str(root_material_id))
                top.setData(2, Qt.UserRole, quoteable)
                if status == "inventory":
                    top_style = "inventory"
                elif selected_price not in (None, "", "None"):
                    top_style = "normal_selected"
                elif quoteable:
                    top_style = "normal_quoteable"
                else:
                    top_style = "disabled"
                self._set_tree_item_style(top, top_style)
                self.item_tree.addTopLevelItem(top)
                if quoteable and first_quoteable_item is None:
                    first_quoteable_item = top

        if first_quoteable_item:
            self.item_tree.setCurrentItem(first_quoteable_item)
        else:
            self.current_item_id = None
            self.current_item_material_id = None
            self.current_item_is_quoteable = False
            self.quote_table.setRowCount(0)
            self._set_quote_actions_enabled(False)

    def on_item_changed(self):
        item = self.item_tree.currentItem()
        if not item:
            self.current_item_id = None
            self.current_item_material_id = None
            self.current_item_is_quoteable = False
            self.quote_table.setRowCount(0)
            self._set_quote_actions_enabled(False)
            return

        item_id = item.data(0, Qt.UserRole)
        material_id = item.data(1, Qt.UserRole)
        quoteable = bool(item.data(2, Qt.UserRole))

        self.current_item_id = str(item_id) if item_id else None
        self.current_item_material_id = str(material_id) if material_id else None
        self.current_item_is_quoteable = quoteable
        self._set_quote_actions_enabled(quoteable)

        if quoteable:
            self.load_quotes()
        else:
            self.quote_table.setRowCount(0)

    def load_quotes(self):
        if not self.current_item_id or not self.current_inquiry_id or not self.current_item_is_quoteable:
            self.quote_table.setRowCount(0)
            return

        rows = self.db.fetch_all(
            """
            SELECT sqi.id,
                   sq.supplier_id,
                   s.supplier_name,
                   COALESCE(sqi.purchase_link, ''),
                   sqi.quote_unit_price,
                   sqi.lead_time_days,
                   sq.valid_until,
                   sqi.is_selected,
                   sqi.tax_rate
            FROM supplier_quote_items sqi
            JOIN supplier_quotes sq ON sq.id = sqi.supplier_quote_id
            JOIN suppliers s ON s.id = sq.supplier_id
            WHERE sq.inquiry_order_id = %s
              AND sqi.inquiry_item_id = %s
            ORDER BY sqi.quote_unit_price ASC, COALESCE(sqi.lead_time_days, 999999) ASC, sqi.id ASC
            """,
            (self.current_inquiry_id, self.current_item_id),
        )

        self.quote_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            values = list(row)
            values[7] = "是" if row[7] else "否"
            for c, val in enumerate(values):
                self.quote_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

    def show_item_context_menu(self, pos):
        clicked = self.item_tree.itemAt(pos)
        if not clicked:
            return
        if not clicked.isSelected():
            self.item_tree.clearSelection()
            clicked.setSelected(True)
            self.item_tree.setCurrentItem(clicked)

        inquiry_item_id = clicked.data(0, Qt.UserRole)
        quoteable = bool(clicked.data(2, Qt.UserRole))

        menu = QMenu(self)
        action_use_inventory = menu.addAction("使用库存（无需询价）")
        action_cost = menu.addAction("成本核算")
        action_use_inventory.setEnabled(bool(inquiry_item_id) and quoteable)
        chosen = menu.exec(self.item_tree.viewport().mapToGlobal(pos))
        if chosen == action_use_inventory:
            self.mark_use_inventory()
        elif chosen == action_cost:
            self.edit_item_cost_accounting()

    def edit_item_cost_accounting(self):
        item = self.item_tree.currentItem()
        if not item:
            return
        material_id = item.data(1, Qt.UserRole)
        if not material_id:
            QMessageBox.warning(self, "提示", "当前节点没有物料，无法进行成本核算")
            return

        material_rows = self.db.fetch_all(
            "SELECT standard_cost FROM materials WHERE id=%s",
            (material_id,),
        )
        current_cost = material_rows[0][0] if material_rows else 0
        drawing_rows = self.db.fetch_all(
            """
            SELECT file_path
            FROM material_drawings
            WHERE material_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (material_id,),
        )
        current_drawing_path = drawing_rows[0][0] if drawing_rows else ""

        dialog = CostAccountingDialog(current_cost=current_cost, current_drawing_path=current_drawing_path, parent=self)
        if not dialog.exec():
            return

        values = dialog.values()
        drawing_path = values["drawing_path"]
        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    "UPDATE materials SET standard_cost=%s WHERE id=%s",
                    (values["standard_cost"], material_id),
                )
                if drawing_path:
                    file_name = drawing_path.replace("\\", "/").split("/")[-1]
                    cur.execute(
                        """
                        SELECT id
                        FROM material_drawings
                        WHERE material_id=%s AND file_path=%s
                        LIMIT 1
                        """,
                        (material_id, drawing_path),
                    )
                    exists = cur.fetchone()
                    if not exists:
                        cur.execute(
                            """
                            INSERT INTO material_drawings (material_id, file_name, file_path)
                            VALUES (%s,%s,%s)
                            """,
                            (material_id, file_name, drawing_path),
                        )
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"保存成本核算失败: {exc}")
            return

        item.setText(9, str(values["standard_cost"]))
        QMessageBox.information(self, "提示", "成本核算已保存，并同步到物料管理")

    def _sync_inquiry_order_status(self):
        if not self.current_inquiry_id:
            return
        summary = self.db.fetch_all(
            """
            SELECT COUNT(*),
                   SUM(CASE WHEN status IN ('selected', 'inventory') THEN 1 ELSE 0 END)
            FROM inquiry_order_items
            WHERE inquiry_order_id=%s
            """,
            (self.current_inquiry_id,),
        )
        total_count = int(summary[0][0]) if summary else 0
        done_count = int(summary[0][1] or 0) if summary else 0
        if total_count > 0 and done_count == total_count:
            self.db.execute(
                "UPDATE inquiry_orders SET status='selected', updated_at=NOW() WHERE id=%s",
                (self.current_inquiry_id,),
            )
        else:
            self.db.execute(
                "UPDATE inquiry_orders SET status='quoted', updated_at=NOW() WHERE id=%s",
                (self.current_inquiry_id,),
            )

    def mark_use_inventory(self):
        if not self.current_item_id:
            QMessageBox.warning(self, "提示", "请先选择可询价条目")
            return
        if not self.current_item_is_quoteable:
            QMessageBox.warning(self, "提示", "当前条目不可设置为使用库存")
            return
        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    "UPDATE supplier_quote_items SET is_selected=FALSE WHERE inquiry_item_id=%s",
                    (self.current_item_id,),
                )
                cur.execute(
                    """
                    UPDATE inquiry_order_items
                    SET status='inventory',
                        selected_quote_item_id=NULL,
                        selected_supplier_id=NULL,
                        selected_unit_price=NULL,
                        updated_at=NOW()
                    WHERE id=%s
                    """,
                    (self.current_item_id,),
                )
            self.db.conn.commit()
            self._sync_inquiry_order_status()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"设置使用库存失败: {exc}")
            return

        QMessageBox.information(self, "提示", "已标记为使用库存，该条目后续无需采购")
        self.load_quotes()
        self.load_items()
        self.load_inquiries()

    def show_quote_context_menu(self, pos):
        row = self.quote_table.rowAt(pos.y())
        if row < 0:
            return
        if not self.quote_table.item(row, 0).isSelected():
            self.quote_table.selectRow(row)

        menu = QMenu(self)
        action_force = menu.addAction("强制选中该条目")
        chosen = menu.exec(self.quote_table.viewport().mapToGlobal(pos))
        if chosen == action_force:
            self.force_select_quote()

    def force_select_quote(self):
        if not self.current_item_id or not self.current_inquiry_id or not self.current_item_is_quoteable:
            QMessageBox.warning(self, "提示", "请选择可询价的子物料节点")
            return
        selected = self._selected_quote_row()
        if not selected or not selected.get("quote_item_id") or not selected.get("supplier_id"):
            QMessageBox.warning(self, "提示", "请先选中一条报价记录")
            return

        price_text = selected.get("quote_unit_price")
        if price_text in (None, "", "None"):
            QMessageBox.warning(self, "提示", "该条目没有报价单价，不能强制选中")
            return

        try:
            forced_price = float(price_text)
            quote_item_id = int(selected["quote_item_id"])
            supplier_id = int(selected["supplier_id"])
        except Exception:
            QMessageBox.warning(self, "提示", "当前条目数据无效，无法强制选中")
            return

        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    "UPDATE supplier_quote_items SET is_selected=FALSE WHERE inquiry_item_id=%s",
                    (self.current_item_id,),
                )
                cur.execute(
                    "UPDATE supplier_quote_items SET is_selected=TRUE WHERE id=%s",
                    (quote_item_id,),
                )
                cur.execute(
                    """
                    UPDATE inquiry_order_items
                    SET selected_quote_item_id=%s,
                        selected_supplier_id=%s,
                        selected_unit_price=%s,
                        status='selected',
                        updated_at=NOW()
                    WHERE id=%s
                    """,
                    (quote_item_id, supplier_id, forced_price, self.current_item_id),
                )

                summary = self.db.fetch_all(
                    """
                    SELECT COUNT(*),
                           SUM(CASE WHEN status IN ('selected', 'inventory') THEN 1 ELSE 0 END)
                    FROM inquiry_order_items
                    WHERE inquiry_order_id=%s
                    """,
                    (self.current_inquiry_id,),
                )
                total_count = int(summary[0][0]) if summary else 0
                selected_count = int(summary[0][1] or 0) if summary else 0
                if total_count > 0 and selected_count == total_count:
                    cur.execute(
                        "UPDATE inquiry_orders SET status='selected', updated_at=NOW() WHERE id=%s",
                        (self.current_inquiry_id,),
                    )
                else:
                    cur.execute(
                        "UPDATE inquiry_orders SET status='quoted', updated_at=NOW() WHERE id=%s",
                        (self.current_inquiry_id,),
                    )
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"强制选中失败: {exc}")
            return

        QMessageBox.information(self, "提示", "已强制选中当前报价条目")
        self.load_quotes()
        self.load_items()
        self.load_inquiries()

    def create_from_order(self):
        picker = OrderPickerDialog(self.db, self)
        if not picker.exec():
            return

        order_id = picker.selected_order_id()
        if not order_id:
            return

        exists = self.db.fetch_all(
            "SELECT id, inquiry_code FROM inquiry_orders WHERE source_order_id=%s ORDER BY id DESC LIMIT 1",
            (order_id,),
        )
        if exists:
            QMessageBox.information(self, "提示", f"该订单已生成询价单: {exists[0][1]}")
            self.load_inquiries()
            return

        details = self.db.fetch_all(
            """
            SELECT od.id,
                   od.material_id,
                   od.quantity,
                   COALESCE(m.material_type, '') AS material_type
            FROM order_details od
            JOIN materials m ON od.material_id = m.id
            WHERE od.order_id=%s
            ORDER BY od.id
            """,
            (order_id,),
        )
        if not details:
            QMessageBox.warning(self, "提示", "该订单没有明细，无法生成询价单")
            return

        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO inquiry_orders
                    (inquiry_code, source_order_id, status, remark)
                    VALUES (%s,%s,'inquiring','由订单自动生成')
                    RETURNING id
                    """,
                    (self._gen_inquiry_code(), order_id),
                )
                inquiry_id = cur.fetchone()[0]

                inserted_count = 0
                for detail_id, material_id, qty, material_type in details:
                    qty_val = float(qty or 0)
                    if material_type == "生产件":
                        cur.execute(
                            """
                            SELECT component_material_id, quantity
                            FROM material_components
                            WHERE parent_material_id=%s
                            ORDER BY id
                            """,
                            (material_id,),
                        )
                        components = cur.fetchall()
                        for component_material_id, component_qty in components:
                            comp_qty = qty_val * float(component_qty or 0)
                            if comp_qty <= 0:
                                continue
                            cur.execute(
                                """
                                INSERT INTO inquiry_order_items
                                (inquiry_order_id, source_order_detail_id, material_id, required_qty, status)
                                VALUES (%s,%s,%s,%s,'pending')
                                """,
                                (inquiry_id, detail_id, component_material_id, comp_qty),
                            )
                            inserted_count += 1
                    else:
                        cur.execute(
                            """
                            INSERT INTO inquiry_order_items
                            (inquiry_order_id, source_order_detail_id, material_id, required_qty, status)
                            VALUES (%s,%s,%s,%s,'pending')
                            """,
                            (inquiry_id, detail_id, material_id, qty_val),
                        )
                        inserted_count += 1

                if inserted_count <= 0:
                    raise ValueError("订单不存在可询价物料，请先维护生产件BOM或普通物料明细")

                cur.execute(
                    """
                    UPDATE orders
                    SET status='进行中'
                    WHERE id=%s
                    """,
                    (order_id,),
                )

            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"生成询价单失败: {exc}")
            return

        QMessageBox.information(
            self,
            "提示",
            "询价单已生成。生产件仅展示结构不询价，请在子物料节点上录入供应商信息与报价。",
        )
        self.load_inquiries()

    def _selected_quote_row(self):
        row = self.quote_table.currentRow()
        if row < 0:
            return None
        quote_item_id = self.quote_table.item(row, 0)
        supplier_id = self.quote_table.item(row, 1)
        current_price = self.quote_table.item(row, 4)
        current_lead_days = self.quote_table.item(row, 5)
        current_valid_until = self.quote_table.item(row, 6)
        current_tax_rate = self.quote_table.item(row, 8)
        current_supplier_name = self.quote_table.item(row, 2)
        current_purchase_link = self.quote_table.item(row, 3)
        return {
            "quote_item_id": quote_item_id.text() if quote_item_id else None,
            "supplier_id": supplier_id.text() if supplier_id else None,
            "supplier_name": current_supplier_name.text() if current_supplier_name else None,
            "purchase_link": current_purchase_link.text() if current_purchase_link else None,
            "quote_unit_price": current_price.text() if current_price else None,
            "lead_time_days": current_lead_days.text() if current_lead_days else None,
            "valid_until": current_valid_until.text() if current_valid_until else None,
            "tax_rate": current_tax_rate.text() if current_tax_rate else None,
        }

    def edit_quote(self):
        if (
            not self.current_inquiry_id
            or not self.current_item_id
            or not self.current_item_material_id
            or not self.current_item_is_quoteable
        ):
            QMessageBox.warning(self, "提示", "请选择可询价的子物料节点")
            return

        selected = self._selected_quote_row() or {}

        dialog = QuoteEditDialog(selected, self)
        if not dialog.exec():
            return
        values = dialog.values()
        supplier_name = values["supplier_name"]
        if not supplier_name:
            QMessageBox.warning(self, "提示", "供应商名称不能为空")
            return

        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    "SELECT id FROM suppliers WHERE supplier_name=%s ORDER BY id DESC LIMIT 1",
                    (supplier_name,),
                )
                supplier_row = cur.fetchone()
                if supplier_row:
                    supplier_id = supplier_row[0]
                else:
                    supplier_code = "SP" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
                    cur.execute(
                        """
                        INSERT INTO suppliers (supplier_code, supplier_name, status)
                        VALUES (%s, %s, 'active')
                        RETURNING id
                        """,
                        (supplier_code, supplier_name),
                    )
                    supplier_id = cur.fetchone()[0]

                cur.execute(
                    """
                    SELECT id
                    FROM supplier_quotes
                    WHERE inquiry_order_id=%s AND supplier_id=%s AND status='submitted'
                    ORDER BY id DESC
                    LIMIT 1
                    """,
                    (self.current_inquiry_id, supplier_id),
                )
                sq = cur.fetchone()
                if sq:
                    supplier_quote_id = sq[0]
                    cur.execute(
                        """
                        UPDATE supplier_quotes
                        SET valid_until=%s, quote_date=CURRENT_DATE
                        WHERE id=%s
                        """,
                        (values["valid_until"], supplier_quote_id),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO supplier_quotes
                        (inquiry_order_id, supplier_id, quote_date, valid_until, status)
                        VALUES (%s,%s,CURRENT_DATE,%s,'submitted')
                        RETURNING id
                        """,
                        (self.current_inquiry_id, supplier_id, values["valid_until"]),
                    )
                    supplier_quote_id = cur.fetchone()[0]

                if selected.get("quote_item_id"):
                    cur.execute(
                        """
                        UPDATE supplier_quote_items
                        SET supplier_quote_id=%s,
                            quote_unit_price=%s,
                            lead_time_days=%s,
                            tax_rate=%s,
                            freight=%s,
                            purchase_link=%s
                        WHERE id=%s
                        """,
                        (
                            supplier_quote_id,
                            values["quote_unit_price"],
                            values["lead_time_days"],
                            values["tax_rate"],
                            values["freight"],
                            values["purchase_link"],
                            selected["quote_item_id"],
                        ),
                    )
                else:
                    cur.execute(
                        """
                        INSERT INTO supplier_quote_items
                        (supplier_quote_id, inquiry_item_id, material_id, quote_unit_price, lead_time_days, tax_rate, freight, purchase_link)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            supplier_quote_id,
                            self.current_item_id,
                            self.current_item_material_id,
                            values["quote_unit_price"],
                            values["lead_time_days"],
                            values["tax_rate"],
                            values["freight"],
                            values["purchase_link"],
                        ),
                    )
                cur.execute(
                    """
                    UPDATE inquiry_order_items
                    SET status='quoted', updated_at=NOW()
                    WHERE id=%s AND status='pending'
                    """,
                    (self.current_item_id,),
                )
                cur.execute(
                    """
                    UPDATE inquiry_orders
                    SET status='quoted', updated_at=NOW()
                    WHERE id=%s AND status IN ('draft', 'inquiring')
                    """,
                    (self.current_inquiry_id,),
                )
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"保存报价失败: {exc}")
            return

        self.load_quotes()
        self.load_items()
        self.load_inquiries()

    def auto_pick_lowest(self):
        if not self.current_item_id or not self.current_inquiry_id or not self.current_item_is_quoteable:
            QMessageBox.warning(self, "提示", "请选择可询价的子物料节点")
            return

        rows = self.db.fetch_all(
            """
            SELECT sqi.id, sq.supplier_id, sqi.quote_unit_price, COALESCE(sqi.lead_time_days, 999999)
            FROM supplier_quote_items sqi
            JOIN supplier_quotes sq ON sqi.supplier_quote_id = sq.id
            WHERE sq.inquiry_order_id=%s
              AND sqi.inquiry_item_id=%s
            ORDER BY sqi.quote_unit_price ASC, COALESCE(sqi.lead_time_days, 999999) ASC, sqi.id ASC
            """,
            (self.current_inquiry_id, self.current_item_id),
        )
        if not rows:
            QMessageBox.warning(self, "提示", "当前物料还没有有效报价")
            return

        try:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    "UPDATE supplier_quote_items SET is_selected=FALSE, rank_no=NULL WHERE inquiry_item_id=%s",
                    (self.current_item_id,),
                )
                for idx, (quote_item_id, _, _, _) in enumerate(rows, start=1):
                    cur.execute(
                        "UPDATE supplier_quote_items SET rank_no=%s WHERE id=%s",
                        (idx, quote_item_id),
                    )
                best_quote_item_id, best_supplier_id, best_price, _ = rows[0]
                cur.execute(
                    "UPDATE supplier_quote_items SET is_selected=TRUE WHERE id=%s",
                    (best_quote_item_id,),
                )
                cur.execute(
                    """
                    UPDATE inquiry_order_items
                    SET selected_quote_item_id=%s,
                        selected_supplier_id=%s,
                        selected_unit_price=%s,
                        status='selected',
                        updated_at=NOW()
                    WHERE id=%s
                    """,
                    (best_quote_item_id, best_supplier_id, best_price, self.current_item_id),
                )

                summary = self.db.fetch_all(
                    """
                    SELECT COUNT(*),
                           SUM(CASE WHEN status IN ('selected', 'inventory') THEN 1 ELSE 0 END)
                    FROM inquiry_order_items
                    WHERE inquiry_order_id=%s
                    """,
                    (self.current_inquiry_id,),
                )
                total_count = int(summary[0][0]) if summary else 0
                selected_count = int(summary[0][1] or 0) if summary else 0
                if total_count > 0 and selected_count == total_count:
                    cur.execute(
                        "UPDATE inquiry_orders SET status='selected', updated_at=NOW() WHERE id=%s",
                        (self.current_inquiry_id,),
                    )
                else:
                    cur.execute(
                        "UPDATE inquiry_orders SET status='quoted', updated_at=NOW() WHERE id=%s",
                        (self.current_inquiry_id,),
                    )
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"自动选最低价失败: {exc}")
            return

        QMessageBox.information(self, "提示", "已自动选出最低价，采购可直接使用该中标价")
        self.load_quotes()
        self.load_items()
        self.load_inquiries()

    def refresh_data(self):
        self.load_inquiries()
