from datetime import datetime

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QLabel, QTableWidget, QTableWidgetItem,
    QSplitter, QMessageBox, QDialog, QTreeWidget, QTreeWidgetItem,
    QFormLayout, QComboBox, QDateEdit, QMenu
)
from PySide6.QtCore import Qt, QDate
from database import Database
from ui.refresh_toast import show_refresh_success


class OrderPickerDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.setWindowTitle("选择订单")
        self.resize(760, 420)
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        layout = QVBoxLayout()

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

        btn_layout = QHBoxLayout()
        self.btn_ok = QPushButton("确定")
        self.btn_cancel = QPushButton("取消")
        self.btn_ok.clicked.connect(self.accept_selection)
        self.btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(self.btn_ok)
        btn_layout.addWidget(self.btn_cancel)
        layout.addLayout(btn_layout)

        self.setLayout(layout)

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
            QMessageBox.warning(self, "提示", "请选择一个订单")
            return
        self.accept()


class LogisticsEditDialog(QDialog):
    def __init__(self, db: Database, current_item, parent=None):
        super().__init__(parent)
        self.db = db
        self.current_item = current_item
        self.setWindowTitle("编辑物流信息")
        self.resize(420, 260)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        form = QFormLayout()

        self.supplier_combo = QComboBox()
        self.supplier_combo.addItem("无", None)
        suppliers = self.db.fetch_all(
            "SELECT id, supplier_code, supplier_name FROM suppliers ORDER BY id DESC"
        )
        for sid, code, name in suppliers:
            self.supplier_combo.addItem(f"{code} - {name}", sid)

        self.logistics_company_input = QLineEdit(self.current_item.get("logistics_company", ""))
        self.tracking_no_input = QLineEdit(self.current_item.get("tracking_no", ""))

        self.logistics_status_combo = QComboBox()
        self.logistics_status_combo.addItems(["pending", "shipping", "arrived"])

        self.planned_date_input = QDateEdit()
        self.planned_date_input.setCalendarPopup(True)
        self.planned_date_input.setDisplayFormat("yyyy-MM-dd")
        self.planned_date_input.setSpecialValueText("")
        self.planned_date_input.setDate(QDate(2000, 1, 1))
        self.planned_date_input.setMinimumDate(QDate(2000, 1, 1))

        supplier_id = self.current_item.get("supplier_id")
        if supplier_id is not None:
            idx = self.supplier_combo.findData(supplier_id)
            if idx >= 0:
                self.supplier_combo.setCurrentIndex(idx)

        status = self.current_item.get("logistics_status") or "pending"
        status_idx = self.logistics_status_combo.findText(status)
        self.logistics_status_combo.setCurrentIndex(status_idx if status_idx >= 0 else 0)

        planned_date = self.current_item.get("planned_delivery_date")
        if planned_date:
            qd = QDate.fromString(str(planned_date), "yyyy-MM-dd")
            if qd.isValid():
                self.planned_date_input.setDate(qd)

        form.addRow("供应商", self.supplier_combo)
        form.addRow("物流公司", self.logistics_company_input)
        form.addRow("运单号", self.tracking_no_input)
        form.addRow("物流状态", self.logistics_status_combo)
        form.addRow("计划到货", self.planned_date_input)

        btn_layout = QHBoxLayout()
        btn_ok = QPushButton("保存")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self.accept)
        btn_cancel.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(btn_ok)
        btn_layout.addWidget(btn_cancel)

        layout.addLayout(form)
        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def values(self):
        raw_date = self.planned_date_input.date().toString("yyyy-MM-dd")
        planned_date = None if raw_date == "2000-01-01" else raw_date
        return {
            "supplier_id": self.supplier_combo.currentData(),
            "logistics_company": self.logistics_company_input.text().strip(),
            "tracking_no": self.tracking_no_input.text().strip(),
            "logistics_status": self.logistics_status_combo.currentText(),
            "planned_delivery_date": planned_date,
        }


class PurchasePage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.current_purchase_id = None
        self.init_ui()
        self.load_purchase_orders()

    def init_ui(self):
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索采购单号/来源订单")
        self.btn_search = QPushButton("查询")
        self.btn_order_purchase = QPushButton("订单采购")
        self.btn_refresh = QPushButton("刷新")
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.btn_search)
        top_layout.addWidget(self.btn_order_purchase)
        top_layout.addWidget(self.btn_refresh)
        main_layout.addLayout(top_layout)

        self.splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel("采购单"))
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(6)
        self.order_table.setHorizontalHeaderLabels(
            ["ID", "采购单号", "来源订单", "状态", "预计到货", "物流状态"]
        )
        self.order_table.setColumnHidden(0, True)
        self.order_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.order_table.setSelectionMode(QTableWidget.SingleSelection)
        self.order_table.setEditTriggers(QTableWidget.NoEditTriggers)
        left_layout.addWidget(self.order_table)
        left_widget.setLayout(left_layout)

        right_widget = QWidget()
        right_layout = QVBoxLayout()
        right_layout.addWidget(QLabel("采购单物料信息"))

        self.item_tree = QTreeWidget()
        self.item_tree.setColumnCount(8)
        self.item_tree.setHeaderLabels(
            [
                "物料编码",
                "物料名称",
                "供应商",
                "采购数量",
                "单价",
                "物流公司",
                "物流状态",
                "计划到货",
            ]
        )
        self.item_tree.setSelectionMode(QTreeWidget.ExtendedSelection)
        self.item_tree.setContextMenuPolicy(Qt.CustomContextMenu)
        right_layout.addWidget(self.item_tree)
        right_widget.setLayout(right_layout)

        self.splitter.addWidget(left_widget)
        self.splitter.addWidget(right_widget)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 2)
        main_layout.addWidget(self.splitter)

        self.setLayout(main_layout)

        self.btn_search.clicked.connect(self.load_purchase_orders)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.btn_order_purchase.clicked.connect(self.create_from_order)
        self.search_input.returnPressed.connect(self.load_purchase_orders)
        self.order_table.itemSelectionChanged.connect(self.on_order_selection_changed)
        self.item_tree.customContextMenuRequested.connect(self.show_item_context_menu)

    def _generate_purchase_code(self):
        return "PO" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    def load_purchase_orders(self):
        keyword = self.search_input.text().strip()
        like_kw = f"%{keyword}%"
        query = """
            SELECT po.id,
                   po.purchase_code,
                   o.order_code,
                   po.status,
                   po.expected_arrival_date,
                   po.logistics_status
            FROM purchase_orders po
            LEFT JOIN orders o ON po.source_order_id = o.id
            WHERE po.purchase_code ILIKE %s
               OR o.order_code ILIKE %s
            ORDER BY po.id DESC
        """
        try:
            rows = self.db.fetch_all(query, (like_kw, like_kw))
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"加载采购单失败: {exc}")
            return

        self.order_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.order_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

        if rows:
            self.order_table.selectRow(0)
        else:
            self.current_purchase_id = None
            self.item_tree.clear()

    def on_order_selection_changed(self):
        row = self.order_table.currentRow()
        if row < 0:
            self.current_purchase_id = None
            self.item_tree.clear()
            return

        purchase_id_item = self.order_table.item(row, 0)
        self.current_purchase_id = purchase_id_item.text() if purchase_id_item else None
        self.load_purchase_items()

    def _get_order_details(self, order_id):
        return self.db.fetch_all(
            """
            SELECT od.id,
                   od.material_id,
                   od.quantity,
                   od.unit_price,
                   m.material_code,
                   m.material_name,
                   COALESCE(m.material_type, '') AS material_type
            FROM order_details od
            JOIN materials m ON od.material_id = m.id
            WHERE od.order_id=%s
            ORDER BY od.id
            """,
            (order_id,),
        )

    def _get_components(self, parent_material_id):
        return self.db.fetch_all(
            """
            SELECT mc.component_material_id,
                   mc.quantity,
                   m.standard_cost
            FROM material_components mc
            JOIN materials m ON mc.component_material_id = m.id
            WHERE mc.parent_material_id=%s
            ORDER BY mc.id
            """,
            (parent_material_id,),
        )

    def _get_selected_quote_map(self, order_id):
        try:
            rows = self.db.fetch_all(
                """
                SELECT ioi.source_order_detail_id,
                       ioi.material_id,
                       ioi.selected_supplier_id,
                       ioi.selected_unit_price,
                       ioi.selected_quote_item_id,
                       ioi.status
                FROM inquiry_orders io
                JOIN inquiry_order_items ioi ON io.id = ioi.inquiry_order_id
                WHERE io.source_order_id=%s
                ORDER BY io.id DESC
                """,
                (order_id,),
            )
        except Exception:
            # Backward compatibility for environments where inquiry tables are not migrated yet.
            return {}

        quote_map = {}
        for source_order_detail_id, material_id, supplier_id, unit_price, quote_item_id, item_status in rows:
            key = (str(source_order_detail_id), str(material_id))
            if key in quote_map:
                # Keep latest inquiry result due ORDER BY io.id DESC.
                continue
            quote_map[key] = (
                supplier_id,
                float(unit_price) if unit_price is not None else None,
                quote_item_id,
                str(item_status or ""),
            )
        return quote_map

    def create_from_order(self):
        picker = OrderPickerDialog(self.db, self)
        if not picker.exec():
            return

        order_id = picker.selected_order_id()
        if not order_id:
            return

        exists = self.db.fetch_all(
            "SELECT id, purchase_code FROM purchase_orders WHERE source_order_id=%s ORDER BY id DESC LIMIT 1",
            (order_id,),
        )
        if exists:
            QMessageBox.information(
                self,
                "提示",
                f"该订单已生成采购单: {exists[0][1]}",
            )
            self.load_purchase_orders()
            return

        details = self._get_order_details(order_id)
        if not details:
            QMessageBox.warning(self, "提示", "所选订单没有订单明细，无法生成采购单")
            return
        quote_map = self._get_selected_quote_map(order_id)

        try:
            with self.db.conn.cursor() as cur:
                purchase_code = self._generate_purchase_code()
                cur.execute(
                    """
                    INSERT INTO purchase_orders
                    (purchase_code, source_order_id, status, logistics_status, remark)
                    VALUES (%s,%s,'draft','pending','由订单自动生成')
                    RETURNING id
                    """,
                    (purchase_code, order_id),
                )
                purchase_order_id = cur.fetchone()[0]
                inventory_skip_count = 0

                for detail in details:
                    detail_id, material_id, qty, unit_price, material_code, _, material_type = detail
                    qty_val = float(qty or 0)
                    price_val = float(unit_price or 0)
                    selected_supplier_id = None
                    selected_quote_item_id = None
                    direct_quote = quote_map.get((str(detail_id), str(material_id)))
                    if direct_quote:
                        selected_supplier_id = direct_quote[0]
                        if direct_quote[1] is not None:
                            price_val = direct_quote[1]
                        selected_quote_item_id = direct_quote[2]
                        if direct_quote[3] == "inventory":
                            inventory_skip_count += 1
                            continue

                    cur.execute(
                        """
                        INSERT INTO purchase_order_items
                        (purchase_order_id, source_order_detail_id, material_id,
                         supplier_id, purchase_qty, unit_price, logistics_status, source_quote_item_id, remark)
                        VALUES (%s,%s,%s,%s,%s,%s,'pending',%s,'订单明细')
                        """,
                        (
                            purchase_order_id,
                            detail_id,
                            material_id,
                            selected_supplier_id,
                            qty_val,
                            price_val,
                            selected_quote_item_id,
                        ),
                    )

                    if material_type == "生产件":
                        components = self._get_components(material_id)
                        for component_material_id, component_qty, component_cost in components:
                            comp_qty = qty_val * float(component_qty or 0)
                            comp_price = float(component_cost or 0)
                            comp_supplier_id = None
                            comp_quote_item_id = None
                            comp_quote = quote_map.get((str(detail_id), str(component_material_id)))
                            if comp_quote:
                                comp_supplier_id = comp_quote[0]
                                if comp_quote[1] is not None:
                                    comp_price = comp_quote[1]
                                comp_quote_item_id = comp_quote[2]
                                if comp_quote[3] == "inventory":
                                    inventory_skip_count += 1
                                    continue
                            cur.execute(
                                """
                                INSERT INTO purchase_order_items
                                (purchase_order_id, source_order_detail_id, material_id,
                                 supplier_id, purchase_qty, unit_price, logistics_status, source_quote_item_id, remark)
                                VALUES (%s,%s,%s,%s,%s,%s,'pending',%s,%s)
                                """,
                                (
                                    purchase_order_id,
                                    detail_id,
                                    component_material_id,
                                    comp_supplier_id,
                                    comp_qty,
                                    comp_price,
                                    comp_quote_item_id,
                                    f"生产件展开:{material_code}",
                                ),
                            )
                if inventory_skip_count > 0:
                    cur.execute(
                        """
                        UPDATE purchase_orders
                        SET remark = COALESCE(remark, '') || %s
                        WHERE id=%s
                        """,
                        (f"；使用库存，无需采购条目 {inventory_skip_count} 条", purchase_order_id),
                    )
                self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"订单采购生成失败: {exc}")
            return

        QMessageBox.information(self, "提示", "采购单已根据订单生成")
        self.load_purchase_orders()

    def load_purchase_items(self):
        if not self.current_purchase_id:
            self.item_tree.clear()
            return

        source_order_rows = self.db.fetch_all(
            "SELECT source_order_id FROM purchase_orders WHERE id=%s",
            (self.current_purchase_id,),
        )
        source_order_id = source_order_rows[0][0] if source_order_rows else None

        root_map = {}
        if source_order_id:
            roots = self.db.fetch_all(
                """
                SELECT od.id, m.id
                FROM order_details od
                JOIN materials m ON od.material_id = m.id
                WHERE od.order_id=%s
                """,
                (source_order_id,),
            )
            root_map = {str(od_id): str(mid) for od_id, mid in roots}

        query = """
            SELECT poi.id,
                   poi.source_order_detail_id,
                   m.id,
                   m.material_code,
                   m.material_name,
                   poi.supplier_id,
                   s.supplier_name,
                   poi.purchase_qty,
                   poi.unit_price,
                   poi.logistics_company,
                   poi.tracking_no,
                   poi.logistics_status,
                   poi.planned_delivery_date
            FROM purchase_order_items poi
            JOIN materials m ON poi.material_id = m.id
            LEFT JOIN suppliers s ON poi.supplier_id = s.id
            WHERE poi.purchase_order_id = %s
            ORDER BY poi.source_order_detail_id NULLS LAST, poi.id ASC
        """
        try:
            rows = self.db.fetch_all(query, (self.current_purchase_id,))
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"加载采购明细失败: {exc}")
            return

        self.item_tree.clear()
        groups = {}
        ungrouped = []
        for row in rows:
            source_detail_id = row[1]
            if source_detail_id is None:
                ungrouped.append(row)
            else:
                key = str(source_detail_id)
                groups.setdefault(key, []).append(row)

        for source_detail_id, group_rows in groups.items():
            root_material_id = root_map.get(source_detail_id)
            root_row = None
            children = []
            for r in group_rows:
                mat_id = str(r[2])
                if root_material_id and mat_id == root_material_id and root_row is None:
                    root_row = r
                else:
                    children.append(r)

            if root_row is None:
                root_row = group_rows[0]
                children = group_rows[1:]

            root_item = self._to_tree_item(root_row, is_root=True, has_children=bool(children))
            self.item_tree.addTopLevelItem(root_item)
            for c in children:
                root_item.addChild(self._to_tree_item(c, is_root=False, has_children=False))
            root_item.setExpanded(True)

        for row in ungrouped:
            self.item_tree.addTopLevelItem(self._to_tree_item(row, is_root=True, has_children=False))

    def _to_tree_item(self, row, is_root, has_children):
        poi_id, _, _, material_code, material_name, supplier_id, supplier_name, purchase_qty, unit_price, logistics_company, tracking_no, logistics_status, planned_delivery_date = row
        if is_root and has_children:
            prefix = "🧩 生产件 "
        elif is_root:
            prefix = "📦 物料 "
        else:
            prefix = "🔹 子料 "
        item = QTreeWidgetItem([
            f"{prefix}{material_code or ''}",
            material_name or "",
            supplier_name or "",
            "" if purchase_qty is None else str(purchase_qty),
            "" if unit_price is None else str(unit_price),
            logistics_company or "",
            logistics_status or "",
            "" if planned_delivery_date is None else str(planned_delivery_date),
        ])
        item.setData(0, Qt.UserRole, poi_id)
        item.setData(1, Qt.UserRole, supplier_id)
        item.setData(2, Qt.UserRole, tracking_no)
        item.setData(3, Qt.UserRole, is_root)
        item.setData(4, Qt.UserRole, has_children)
        return item

    def _is_production_parent_item(self, tree_item):
        return bool(tree_item.data(3, Qt.UserRole)) and bool(tree_item.data(4, Qt.UserRole))

    def _selected_purchase_item_id(self):
        item = self.item_tree.currentItem()
        if not item:
            return None
        return item.data(0, Qt.UserRole)

    def show_item_context_menu(self, pos):
        clicked = self.item_tree.itemAt(pos)
        if clicked and not clicked.isSelected():
            self.item_tree.clearSelection()
            clicked.setSelected(True)
            self.item_tree.setCurrentItem(clicked)

        selected = self.item_tree.selectedItems()
        if not selected:
            return

        eligible = [i for i in selected if not self._is_production_parent_item(i)]
        menu = QMenu(self)
        action_edit = menu.addAction("编辑物流信息")
        action_arrived = menu.addAction("物流到货")

        action_edit.setEnabled(len(selected) == 1 and len(eligible) == 1)
        action_arrived.setEnabled(len(eligible) > 0)

        chosen = menu.exec(self.item_tree.viewport().mapToGlobal(pos))
        if chosen == action_edit:
            self.edit_logistics(eligible[0].data(0, Qt.UserRole))
        elif chosen == action_arrived:
            self.mark_arrived(eligible)

    def edit_logistics(self, poi_id=None):
        if poi_id is None:
            poi_id = self._selected_purchase_item_id()
        if not poi_id:
            QMessageBox.warning(self, "提示", "请先选择采购明细")
            return

        rows = self.db.fetch_all(
            """
            SELECT supplier_id, logistics_company, tracking_no, logistics_status, planned_delivery_date
            FROM purchase_order_items
            WHERE id=%s
            """,
            (poi_id,),
        )
        if not rows:
            QMessageBox.warning(self, "提示", "采购明细不存在")
            return
        row = rows[0]
        dialog = LogisticsEditDialog(
            self.db,
            {
                "supplier_id": row[0],
                "logistics_company": row[1] or "",
                "tracking_no": row[2] or "",
                "logistics_status": row[3] or "pending",
                "planned_delivery_date": row[4],
            },
            self,
        )
        if not dialog.exec():
            return

        values = dialog.values()
        try:
            self.db.execute(
                """
                UPDATE purchase_order_items
                SET supplier_id=%s,
                    logistics_company=%s,
                    tracking_no=%s,
                    logistics_status=%s,
                    planned_delivery_date=%s
                WHERE id=%s
                """,
                (
                    values["supplier_id"],
                    values["logistics_company"],
                    values["tracking_no"],
                    values["logistics_status"],
                    values["planned_delivery_date"],
                    poi_id,
                ),
            )
            self._sync_purchase_order_logistics_status()
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"更新物流信息失败: {exc}")
            return

        self.load_purchase_items()
        self.load_purchase_orders()

    def _sync_purchase_order_logistics_status(self):
        if not self.current_purchase_id:
            return
        rows = self.db.fetch_all(
            "SELECT logistics_status FROM purchase_order_items WHERE purchase_order_id=%s",
            (self.current_purchase_id,),
        )
        statuses = [str(r[0] or "pending") for r in rows]
        if statuses and all(s == "arrived" for s in statuses):
            po_status = "arrived"
        elif any(s in ("shipping", "arrived") for s in statuses):
            po_status = "shipping"
        else:
            po_status = "pending"

        self.db.execute(
            "UPDATE purchase_orders SET logistics_status=%s WHERE id=%s",
            (po_status, self.current_purchase_id),
        )

    def mark_arrived(self, selected_items=None):
        if selected_items is None:
            selected_items = self.item_tree.selectedItems()
        eligible = [i for i in selected_items if not self._is_production_parent_item(i)]
        if not eligible:
            QMessageBox.warning(self, "提示", "请先选择可到货的采购明细")
            return

        success_count = 0
        skipped_count = 0
        try:
            for it in eligible:
                poi_id = it.data(0, Qt.UserRole)
                if not poi_id:
                    skipped_count += 1
                    continue
                self.db.execute(
                    "UPDATE purchase_order_items SET logistics_status='arrived' WHERE id=%s",
                    (poi_id,),
                )
                self._auto_create_inbound_from_arrived_item(poi_id)
                success_count += 1
            self._sync_purchase_order_logistics_status()
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"物流到货处理失败: {exc}")
            return

        if success_count == 0:
            QMessageBox.warning(
                self,
                "提示",
                "未处理任何有效明细。生产件母条目不能直接到货，请选择其组成物料条目。",
            )
            return

        QMessageBox.information(
            self,
            "提示",
            f"已处理到货 {success_count} 条，跳过 {skipped_count} 条，并自动生成入库单",
        )
        self.load_purchase_items()
        self.load_purchase_orders()

    def _auto_create_inbound_from_arrived_item(self, purchase_order_item_id):
        row = self.db.fetch_all(
            """
            SELECT poi.purchase_order_id, poi.material_id, poi.purchase_qty, poi.unit_price
            FROM purchase_order_items poi
            WHERE poi.id=%s
            """,
            (purchase_order_item_id,),
        )
        if not row:
            raise ValueError("采购明细不存在")
        purchase_order_id, material_id, qty, unit_price = row[0]

        exists = self.db.fetch_all(
            "SELECT id FROM stock_document_items WHERE purchase_order_item_id=%s LIMIT 1",
            (purchase_order_item_id,),
        )
        if exists:
            return

        warehouse_id, location_id = self._ensure_default_warehouse_and_location()

        doc_rows = self.db.fetch_all(
            """
            SELECT id
            FROM stock_documents
            WHERE doc_type='purchase_in'
              AND status='draft'
              AND source_type='purchase'
              AND source_id=%s
            ORDER BY id DESC
            LIMIT 1
            """,
            (purchase_order_id,),
        )

        if doc_rows:
            stock_doc_id = doc_rows[0][0]
        else:
            doc_no = "WD" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]
            with self.db.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO stock_documents
                    (doc_no, doc_type, warehouse_id, status, biz_date, source_type, source_id, remark)
                    VALUES (%s,'purchase_in',%s,'draft',CURRENT_DATE,'purchase',%s,'采购到货自动生成')
                    RETURNING id
                    """,
                    (doc_no, warehouse_id, purchase_order_id),
                )
                stock_doc_id = cur.fetchone()[0]
            self.db.conn.commit()

        self.db.execute(
            """
            INSERT INTO stock_document_items
            (stock_document_id, material_id, location_id, qty, unit_price, purchase_order_item_id, remark)
            VALUES (%s,%s,%s,%s,%s,%s,'采购到货自动生成')
            """,
            (stock_doc_id, material_id, location_id, qty, unit_price, purchase_order_item_id),
        )

    def _ensure_default_warehouse_and_location(self):
        try:
            wh_rows = self.db.fetch_all(
                "SELECT id FROM warehouses WHERE status='active' ORDER BY id LIMIT 1"
            )
        except Exception as exc:
            raise ValueError(f"仓库基础表不可用，请先执行仓库建表SQL。详细错误: {exc}")

        created = False
        if wh_rows:
            warehouse_id = wh_rows[0][0]
        else:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO warehouses
                    (warehouse_code, warehouse_name, warehouse_type, status)
                    VALUES ('WH001', '主仓库', 'main', 'active')
                    RETURNING id
                    """
                )
                warehouse_id = cur.fetchone()[0]
            created = True

        loc_rows = self.db.fetch_all(
            """
            SELECT id
            FROM warehouse_locations
            WHERE warehouse_id=%s AND status='active'
            ORDER BY id
            LIMIT 1
            """,
            (warehouse_id,),
        )

        if loc_rows:
            location_id = loc_rows[0][0]
        else:
            with self.db.conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO warehouse_locations
                    (warehouse_id, location_code, location_name, status)
                    VALUES (%s, 'LOC001', '默认库位', 'active')
                    RETURNING id
                    """,
                    (warehouse_id,),
                )
                location_id = cur.fetchone()[0]
            created = True

        if created:
            self.db.conn.commit()

        return warehouse_id, location_id

    def refresh_data(self):
        self.load_purchase_orders()
        show_refresh_success(self)
