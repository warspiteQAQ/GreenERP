from datetime import datetime

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QTabWidget, QTableWidgetItem,
    QLineEdit, QComboBox, QDialog, QFormLayout, QMessageBox,
    QTextEdit, QDoubleSpinBox, QDateEdit, QMenu
)

from database import Database
from .inventory_tab import InventoryTab
from .stock_tab import StockTab
from .transaction_tab import TransactionTab
from ui.refresh_toast import show_refresh_success


class WarehouseDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增仓库")
        self.resize(420, 320)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.code_input = QLineEdit()
        self.name_input = QLineEdit()
        self.type_input = QComboBox()
        self.type_input.addItems(["main", "raw", "finished", "spare"])
        self.manager_input = QLineEdit()
        self.phone_input = QLineEdit()
        self.address_input = QTextEdit()

        form.addRow("仓库编码", self.code_input)
        form.addRow("仓库名称", self.name_input)
        form.addRow("仓库类型", self.type_input)
        form.addRow("负责人", self.manager_input)
        form.addRow("联系电话", self.phone_input)
        form.addRow("地址", self.address_input)

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

    def values(self):
        return {
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
            "wtype": self.type_input.currentText(),
            "manager": self.manager_input.text().strip(),
            "phone": self.phone_input.text().strip(),
            "address": self.address_input.toPlainText().strip(),
        }


class LocationDialog(QDialog):
    def __init__(self, warehouses, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增库位")
        self.resize(420, 220)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.wh_combo = QComboBox()
        for wid, code, name in warehouses:
            self.wh_combo.addItem(f"{code} - {name}", wid)
        self.code_input = QLineEdit()
        self.name_input = QLineEdit()

        form.addRow("所属仓库", self.wh_combo)
        form.addRow("库位编码", self.code_input)
        form.addRow("库位名称", self.name_input)

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

    def values(self):
        return {
            "warehouse_id": self.wh_combo.currentData(),
            "code": self.code_input.text().strip(),
            "name": self.name_input.text().strip(),
        }


class StockDocDialog(QDialog):
    def __init__(self, warehouses, doc_no, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增出入库单")
        self.resize(440, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.doc_no_input = QLineEdit(doc_no)
        self.doc_type_combo = QComboBox()
        self.doc_type_combo.addItems([
            "purchase_in", "sale_out", "production_in",
            "production_out", "transfer_in", "transfer_out"
        ])

        self.wh_combo = QComboBox()
        for wid, code, name in warehouses:
            self.wh_combo.addItem(f"{code} - {name}", wid)

        self.biz_date = QDateEdit()
        self.biz_date.setDate(QDate.currentDate())
        self.biz_date.setDisplayFormat("yyyy-MM-dd")
        self.biz_date.setCalendarPopup(True)

        self.source_type = QComboBox()
        self.source_type.addItems(["manual", "purchase", "order", "production", "transfer"])
        self.source_id = QLineEdit()
        self.remark = QLineEdit()

        form.addRow("单据编号", self.doc_no_input)
        form.addRow("单据类型", self.doc_type_combo)
        form.addRow("仓库", self.wh_combo)
        form.addRow("业务日期", self.biz_date)
        form.addRow("来源类型", self.source_type)
        form.addRow("来源ID", self.source_id)
        form.addRow("备注", self.remark)

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

    def values(self):
        sid = self.source_id.text().strip()
        return {
            "doc_no": self.doc_no_input.text().strip(),
            "doc_type": self.doc_type_combo.currentText(),
            "warehouse_id": self.wh_combo.currentData(),
            "biz_date": self.biz_date.date().toString("yyyy-MM-dd"),
            "source_type": self.source_type.currentText(),
            "source_id": int(sid) if sid.isdigit() else None,
            "remark": self.remark.text().strip(),
        }


class StockItemDialog(QDialog):
    def __init__(self, materials, locations, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新增单据明细")
        self.resize(460, 300)

        layout = QVBoxLayout(self)
        form = QFormLayout()

        self.material_combo = QComboBox()
        for mid, code, name in materials:
            self.material_combo.addItem(f"{code} - {name}", mid)

        self.location_combo = QComboBox()
        self.location_combo.addItem("无库位", None)
        for lid, code, name in locations:
            self.location_combo.addItem(f"{code} - {name or code}", lid)

        self.qty_input = QDoubleSpinBox()
        self.qty_input.setDecimals(4)
        self.qty_input.setMinimum(0.0001)
        self.qty_input.setMaximum(999999999)
        self.qty_input.setValue(1)

        self.price_input = QDoubleSpinBox()
        self.price_input.setDecimals(4)
        self.price_input.setMinimum(0)
        self.price_input.setMaximum(999999999)

        self.purchase_item = QLineEdit()
        self.order_detail = QLineEdit()
        self.remark = QLineEdit()

        form.addRow("物料", self.material_combo)
        form.addRow("库位", self.location_combo)
        form.addRow("数量", self.qty_input)
        form.addRow("单价", self.price_input)
        form.addRow("采购明细ID", self.purchase_item)
        form.addRow("订单明细ID", self.order_detail)
        form.addRow("备注", self.remark)

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

    def values(self):
        p = self.purchase_item.text().strip()
        o = self.order_detail.text().strip()
        return {
            "material_id": self.material_combo.currentData(),
            "location_id": self.location_combo.currentData(),
            "qty": self.qty_input.value(),
            "unit_price": self.price_input.value(),
            "purchase_order_item_id": int(p) if p.isdigit() else None,
            "order_detail_id": int(o) if o.isdigit() else None,
            "remark": self.remark.text().strip(),
        }

class WarehousePage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.current_doc_id = None
        self.current_doc_status = None
        self.current_doc_type = None

        self.ensure_base_data()
        self.init_ui()
        self.refresh_data()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()

        self.inventory_tab = InventoryTab()
        self.stock_tab = StockTab()
        self.transaction_tab = TransactionTab()

        # Backward-compatible aliases for existing business methods.
        self.inv_kw = self.inventory_tab.inv_kw
        self.inv_wh = self.inventory_tab.inv_wh
        self.btn_add_wh = self.inventory_tab.btn_add_wh
        self.btn_add_loc = self.inventory_tab.btn_add_loc
        self.btn_refresh_inv = self.inventory_tab.btn_refresh_inv
        self.inv_table = self.inventory_tab.inv_table

        self.doc_kw = self.stock_tab.doc_kw
        self.doc_type = self.stock_tab.doc_type
        self.btn_add_doc = self.stock_tab.btn_add_doc
        self.btn_add_item = self.stock_tab.btn_add_item
        self.btn_del_item = self.stock_tab.btn_del_item
        self.btn_post = self.stock_tab.btn_post
        self.btn_refresh_doc = self.stock_tab.btn_refresh_doc
        self.doc_table = self.stock_tab.doc_table
        self.item_table = self.stock_tab.item_table

        self.tx_kw = self.transaction_tab.tx_kw
        self.tx_wh = self.transaction_tab.tx_wh
        self.btn_refresh_tx = self.transaction_tab.btn_refresh_tx
        self.tx_table = self.transaction_tab.tx_table

        self.tabs.addTab(self.inventory_tab.widget, "库存总览")
        self.tabs.addTab(self.stock_tab.widget, "出入库")
        self.tabs.addTab(self.transaction_tab.widget, "库存流水")
        main_layout.addWidget(self.tabs)

        self.btn_add_wh.clicked.connect(self.add_warehouse)
        self.btn_add_loc.clicked.connect(self.add_location)
        self.btn_refresh_inv.clicked.connect(self.refresh_inventory_data)
        self.inv_kw.returnPressed.connect(self.load_inventory)
        self.inv_wh.currentIndexChanged.connect(self.load_inventory)

        self.btn_add_doc.clicked.connect(self.add_stock_doc)
        self.btn_add_item.clicked.connect(self.add_stock_item)
        self.btn_del_item.clicked.connect(self.delete_stock_item)
        self.btn_post.clicked.connect(self.post_stock_doc)
        self.btn_refresh_doc.clicked.connect(self.refresh_stock_doc_data)
        self.doc_kw.returnPressed.connect(self.load_stock_docs)
        self.doc_type.currentIndexChanged.connect(self.load_stock_docs)
        self.doc_table.itemSelectionChanged.connect(self.on_doc_selection_changed)
        self.doc_table.customContextMenuRequested.connect(self.show_doc_context_menu)

        self.btn_refresh_tx.clicked.connect(self.refresh_transaction_data)
        self.tx_kw.returnPressed.connect(self.load_transactions)
        self.tx_wh.currentIndexChanged.connect(self.load_transactions)

    def ensure_base_data(self):
        if self.db.fetch_all("SELECT id FROM warehouses LIMIT 1"):
            return
        with self.db.conn.cursor() as cur:
            cur.execute("INSERT INTO warehouses (warehouse_code, warehouse_name, warehouse_type, status) VALUES ('WH001','主仓库','main','active') RETURNING id")
            wh_id = cur.fetchone()[0]
            cur.execute("INSERT INTO warehouse_locations (warehouse_id, location_code, location_name, status) VALUES (%s,'LOC001','默认库位','active')", (wh_id,))
        self.db.conn.commit()

    def refresh_data(self):
        self.load_warehouse_filters()
        self.load_inventory()
        self.load_stock_docs()
        self.load_transactions()
        show_refresh_success(self)

    def refresh_inventory_data(self):
        self.load_inventory()
        show_refresh_success(self)

    def refresh_stock_doc_data(self):
        self.load_stock_docs()
        show_refresh_success(self)

    def refresh_transaction_data(self):
        self.load_transactions()
        show_refresh_success(self)

    def load_warehouse_filters(self):
        rows = self.db.fetch_all("SELECT id, warehouse_code, warehouse_name FROM warehouses ORDER BY id")
        self.inv_wh.blockSignals(True)
        self.tx_wh.blockSignals(True)
        self.inv_wh.clear()
        self.tx_wh.clear()
        self.inv_wh.addItem("全部仓库", None)
        self.tx_wh.addItem("全部仓库", None)
        for wid, code, name in rows:
            label = f"{code} - {name}"
            self.inv_wh.addItem(label, wid)
            self.tx_wh.addItem(label, wid)
        self.inv_wh.blockSignals(False)
        self.tx_wh.blockSignals(False)

    def add_warehouse(self):
        dialog = WarehouseDialog(self)
        if not dialog.exec():
            return
        v = dialog.values()
        if not v["code"] or not v["name"]:
            QMessageBox.warning(self, "提示", "仓库编码和名称不能为空")
            return
        try:
            self.db.execute("INSERT INTO warehouses (warehouse_code, warehouse_name, warehouse_type, manager_name, phone, address, status) VALUES (%s,%s,%s,%s,%s,%s,'active')", (v["code"], v["name"], v["wtype"], v["manager"], v["phone"], v["address"]))
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"新增仓库失败: {exc}")
            return
        self.refresh_data()

    def add_location(self):
        warehouses = self.db.fetch_all("SELECT id, warehouse_code, warehouse_name FROM warehouses ORDER BY id")
        if not warehouses:
            QMessageBox.warning(self, "提示", "请先新增仓库")
            return
        dialog = LocationDialog(warehouses, self)
        if not dialog.exec():
            return
        v = dialog.values()
        if not v["code"]:
            QMessageBox.warning(self, "提示", "库位编码不能为空")
            return
        try:
            self.db.execute("INSERT INTO warehouse_locations (warehouse_id, location_code, location_name, status) VALUES (%s,%s,%s,'active')", (v["warehouse_id"], v["code"], v["name"]))
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"新增库位失败: {exc}")
            return
        self.load_inventory()

    def load_inventory(self):
        kw = self.inv_kw.text().strip()
        like_kw = f"%{kw}%"
        wh_id = self.inv_wh.currentData()

        where_sql = "WHERE (m.material_code ILIKE %s OR m.material_name ILIKE %s)"
        params = [like_kw, like_kw]
        if wh_id:
            where_sql += " AND ib.warehouse_id=%s"
            params.append(wh_id)

        rows = self.db.fetch_all(
            f"""
            SELECT w.warehouse_name, COALESCE(l.location_code, '-'),
                   m.material_code, m.material_name,
                   ib.qty, ib.locked_qty, ib.avg_cost, ib.updated_at
            FROM inventory_balances ib
            JOIN warehouses w ON ib.warehouse_id = w.id
            LEFT JOIN warehouse_locations l ON ib.location_id = l.id
            JOIN materials m ON ib.material_id = m.id
            {where_sql}
            ORDER BY ib.updated_at DESC, ib.id DESC
            """,
            tuple(params),
        )
        self.inv_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.inv_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

    def _gen_doc_no(self):
        return "WD" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    def add_stock_doc(self):
        warehouses = self.db.fetch_all("SELECT id, warehouse_code, warehouse_name FROM warehouses ORDER BY id")
        if not warehouses:
            QMessageBox.warning(self, "提示", "没有可用仓库，请先新增仓库")
            return
        dialog = StockDocDialog(warehouses, self._gen_doc_no(), self)
        if not dialog.exec():
            return
        v = dialog.values()
        if not v["doc_no"]:
            QMessageBox.warning(self, "提示", "单据编号不能为空")
            return
        try:
            self.db.execute("INSERT INTO stock_documents (doc_no, doc_type, warehouse_id, status, biz_date, source_type, source_id, remark) VALUES (%s,%s,%s,'draft',%s,%s,%s,%s)", (v["doc_no"], v["doc_type"], v["warehouse_id"], v["biz_date"], v["source_type"], v["source_id"], v["remark"]))
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"新增单据失败: {exc}")
            return
        self.load_stock_docs()

    def load_stock_docs(self):
        kw = self.doc_kw.text().strip()
        like_kw = f"%{kw}%"
        doc_type = self.doc_type.currentData()
        where = ["sd.doc_no ILIKE %s"]
        params = [like_kw]
        if doc_type:
            where.append("sd.doc_type=%s")
            params.append(doc_type)

        rows = self.db.fetch_all(
            f"""
            SELECT sd.id, sd.doc_no, sd.doc_type, w.warehouse_name,
                   sd.status, sd.biz_date,
                   COALESCE(sd.source_type,'') || ':' || COALESCE(sd.source_id::text,''),
                   sd.created_at
            FROM stock_documents sd
            JOIN warehouses w ON sd.warehouse_id = w.id
            WHERE {' AND '.join(where)}
            ORDER BY sd.id DESC
            """,
            tuple(params),
        )

        self.doc_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.doc_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

        if rows:
            self.doc_table.selectRow(0)
        else:
            self.current_doc_id = None
            self.current_doc_status = None
            self.current_doc_type = None
            self.item_table.setRowCount(0)

    def on_doc_selection_changed(self):
        row = self.doc_table.currentRow()
        if row < 0:
            self.current_doc_id = None
            self.current_doc_status = None
            self.current_doc_type = None
            self.item_table.setRowCount(0)
            return
        self.current_doc_id = self.doc_table.item(row, 0).text()
        self.current_doc_type = self.doc_table.item(row, 2).text()
        self.current_doc_status = self.doc_table.item(row, 4).text()
        self.load_stock_items()

    def show_doc_context_menu(self, pos):
        row = self.doc_table.rowAt(pos.y())
        if row < 0:
            return
        self.doc_table.selectRow(row)

        menu = QMenu(self)
        action_complete_in = menu.addAction("完成入库")
        action_complete_out = menu.addAction("完成出库")

        current_type = self.doc_table.item(row, 2).text() if self.doc_table.item(row, 2) else ""
        current_status = self.doc_table.item(row, 4).text() if self.doc_table.item(row, 4) else ""
        inbound_types = {"purchase_in", "production_in", "transfer_in"}
        outbound_types = {"sale_out", "production_out", "transfer_out"}
        action_complete_in.setEnabled(current_type in inbound_types and current_status == "draft")
        action_complete_out.setEnabled(current_type in outbound_types and current_status == "draft")

        chosen = menu.exec(self.doc_table.viewport().mapToGlobal(pos))
        if chosen == action_complete_in:
            self.complete_inbound_doc()
        elif chosen == action_complete_out:
            self.complete_outbound_doc()

    def _selected_doc_warehouse_id(self):
        rows = self.db.fetch_all("SELECT warehouse_id FROM stock_documents WHERE id=%s", (self.current_doc_id,))
        return rows[0][0] if rows else None

    def add_stock_item(self):
        if not self.current_doc_id:
            QMessageBox.warning(self, "提示", "请先选择单据")
            return
        if self.current_doc_status != "draft":
            QMessageBox.warning(self, "提示", "仅草稿单据允许新增明细")
            return

        materials = self.db.fetch_all("SELECT id, material_code, material_name FROM materials ORDER BY id DESC")
        if not materials:
            QMessageBox.warning(self, "提示", "没有可用物料，请先维护物料")
            return

        warehouse_id = self._selected_doc_warehouse_id()
        locations = self.db.fetch_all("SELECT id, location_code, location_name FROM warehouse_locations WHERE warehouse_id=%s ORDER BY id", (warehouse_id,))

        dialog = StockItemDialog(materials, locations, self)
        if not dialog.exec():
            return
        v = dialog.values()

        try:
            self.db.execute("INSERT INTO stock_document_items (stock_document_id, material_id, location_id, qty, unit_price, purchase_order_item_id, order_detail_id, remark) VALUES (%s,%s,%s,%s,%s,%s,%s,%s)", (self.current_doc_id, v["material_id"], v["location_id"], v["qty"], v["unit_price"], v["purchase_order_item_id"], v["order_detail_id"], v["remark"]))
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"新增明细失败: {exc}")
            return
        self.load_stock_items()

    def load_stock_items(self):
        rows = self.db.fetch_all(
            """
            SELECT sdi.id, m.material_code, m.material_name,
                   COALESCE(wl.location_code, '-'),
                   sdi.qty, sdi.unit_price,
                   sdi.purchase_order_item_id, sdi.order_detail_id, sdi.remark
            FROM stock_document_items sdi
            JOIN materials m ON sdi.material_id = m.id
            LEFT JOIN warehouse_locations wl ON sdi.location_id = wl.id
            WHERE sdi.stock_document_id=%s
            ORDER BY sdi.id DESC
            """,
            (self.current_doc_id,),
        )
        self.item_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.item_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

    def delete_stock_item(self):
        if not self.current_doc_id or self.current_doc_status != "draft":
            return
        row = self.item_table.currentRow()
        if row < 0:
            return
        item_id = self.item_table.item(row, 0).text()
        self.db.execute("DELETE FROM stock_document_items WHERE id=%s", (item_id,))
        self.load_stock_items()

    def post_stock_doc(self):
        if not self.current_doc_id:
            QMessageBox.warning(self, "提示", "请先选择单据")
            return
        if self.current_doc_status != "draft":
            QMessageBox.warning(self, "提示", "该单据不是草稿，不能重复过账")
            return

        header = self.db.fetch_all("SELECT warehouse_id, doc_type FROM stock_documents WHERE id=%s", (self.current_doc_id,))
        if not header:
            QMessageBox.warning(self, "提示", "单据不存在")
            return
        warehouse_id, doc_type = header[0]

        direction_map = {
            "purchase_in": "in",
            "production_in": "in",
            "transfer_in": "in",
            "sale_out": "out",
            "production_out": "out",
            "transfer_out": "out",
        }
        direction = direction_map.get(doc_type)
        if not direction:
            QMessageBox.warning(self, "提示", f"单据类型不支持过账: {doc_type}")
            return

        items = self.db.fetch_all("SELECT id, material_id, location_id, qty, unit_price FROM stock_document_items WHERE stock_document_id=%s ORDER BY id", (self.current_doc_id,))
        if not items:
            QMessageBox.warning(self, "提示", "单据无明细，无法过账")
            return

        try:
            with self.db.conn.cursor() as cur:
                for item_id, material_id, location_id, qty, unit_price in items:
                    cur.execute(
                        """
                        SELECT id, qty, avg_cost
                        FROM inventory_balances
                        WHERE warehouse_id=%s
                          AND material_id=%s
                          AND ((location_id IS NULL AND %s IS NULL) OR location_id=%s)
                        FOR UPDATE
                        """,
                        (warehouse_id, material_id, location_id, location_id),
                    )
                    bal = cur.fetchone()

                    qty_val = float(qty or 0)
                    price_val = float(unit_price or 0)

                    if bal:
                        balance_id, before_qty, before_avg = bal
                        before_qty = float(before_qty or 0)
                        before_avg = float(before_avg or 0)
                    else:
                        balance_id = None
                        before_qty = 0.0
                        before_avg = 0.0

                    if direction == "in":
                        after_qty = before_qty + qty_val
                        avg_cost = (((before_qty * before_avg) + (qty_val * price_val)) / after_qty) if after_qty > 0 else before_avg
                    else:
                        if before_qty < qty_val:
                            raise ValueError(f"库存不足: material_id={material_id}, 现有={before_qty}, 出库={qty_val}")
                        after_qty = before_qty - qty_val
                        avg_cost = before_avg

                    if balance_id:
                        cur.execute("UPDATE inventory_balances SET qty=%s, avg_cost=%s, updated_at=NOW() WHERE id=%s", (after_qty, avg_cost, balance_id))
                    else:
                        cur.execute("INSERT INTO inventory_balances (warehouse_id, location_id, material_id, qty, locked_qty, avg_cost, updated_at) VALUES (%s,%s,%s,%s,0,%s,NOW())", (warehouse_id, location_id, material_id, after_qty, avg_cost))

                    cur.execute(
                        """
                        INSERT INTO inventory_transactions
                        (warehouse_id, location_id, material_id, direction, qty, before_qty, after_qty,
                         unit_price, stock_document_id, stock_document_item_id)
                        VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                        """,
                        (warehouse_id, location_id, material_id, direction, qty_val, before_qty, after_qty, price_val, self.current_doc_id, item_id),
                    )

                cur.execute("UPDATE stock_documents SET status='posted' WHERE id=%s", (self.current_doc_id,))
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"过账失败: {exc}")
            return

        QMessageBox.information(self, "提示", "单据过账成功")
        self.load_stock_docs()
        self.load_inventory()
        self.load_transactions()

    def complete_inbound_doc(self):
        if not self.current_doc_id:
            QMessageBox.warning(self, "提示", "请先选择单据")
            return
        if self.current_doc_status != "draft":
            QMessageBox.warning(self, "提示", "该单据不是草稿，不能重复入库")
            return

        inbound_types = {"purchase_in", "production_in", "transfer_in"}
        if self.current_doc_type not in inbound_types:
            QMessageBox.warning(self, "提示", "仅入库类型单据支持“完成入库”")
            return

        header = self.db.fetch_all(
            "SELECT warehouse_id FROM stock_documents WHERE id=%s",
            (self.current_doc_id,),
        )
        if not header:
            QMessageBox.warning(self, "提示", "单据不存在")
            return
        warehouse_id = header[0][0]

        items = self.db.fetch_all(
            "SELECT id, material_id, location_id, qty, unit_price FROM stock_document_items WHERE stock_document_id=%s ORDER BY id",
            (self.current_doc_id,),
        )
        if not items:
            QMessageBox.warning(self, "提示", "单据无明细，无法入库")
            return

        try:
            with self.db.conn.cursor() as cur:
                for item_id, material_id, location_id, qty, unit_price in items:
                    cur.execute(
                        """
                        SELECT id, qty, avg_cost
                        FROM inventory_balances
                        WHERE warehouse_id=%s
                          AND material_id=%s
                          AND ((location_id IS NULL AND %s IS NULL) OR location_id=%s)
                        FOR UPDATE
                        """,
                        (warehouse_id, material_id, location_id, location_id),
                    )
                    bal = cur.fetchone()

                    qty_val = float(qty or 0)
                    price_val = float(unit_price or 0)

                    if bal:
                        balance_id, before_qty, before_avg = bal
                        before_qty = float(before_qty or 0)
                        before_avg = float(before_avg or 0)
                    else:
                        balance_id = None
                        before_qty = 0.0
                        before_avg = 0.0

                    after_qty = before_qty + qty_val
                    avg_cost = (((before_qty * before_avg) + (qty_val * price_val)) / after_qty) if after_qty > 0 else before_avg

                    if balance_id:
                        cur.execute(
                            "UPDATE inventory_balances SET qty=%s, avg_cost=%s, updated_at=NOW() WHERE id=%s",
                            (after_qty, avg_cost, balance_id),
                        )
                    else:
                        cur.execute(
                            "INSERT INTO inventory_balances (warehouse_id, location_id, material_id, qty, locked_qty, avg_cost, updated_at) VALUES (%s,%s,%s,%s,0,%s,NOW())",
                            (warehouse_id, location_id, material_id, after_qty, avg_cost),
                        )

                    cur.execute(
                        """
                        INSERT INTO inventory_transactions
                        (warehouse_id, location_id, material_id, direction, qty, before_qty, after_qty,
                         unit_price, stock_document_id, stock_document_item_id)
                        VALUES (%s,%s,%s,'in',%s,%s,%s,%s,%s,%s)
                        """,
                        (warehouse_id, location_id, material_id, qty_val, before_qty, after_qty, price_val, self.current_doc_id, item_id),
                    )

                cur.execute("UPDATE stock_documents SET status='posted' WHERE id=%s", (self.current_doc_id,))
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"完成入库失败: {exc}")
            return

        QMessageBox.information(self, "提示", "入库完成，库存已更新")
        self.load_stock_docs()
        self.load_inventory()
        self.load_transactions()

    def complete_outbound_doc(self):
        if not self.current_doc_id:
            QMessageBox.warning(self, "提示", "请先选择单据")
            return
        if self.current_doc_status != "draft":
            QMessageBox.warning(self, "提示", "该单据不是草稿，不能重复出库")
            return

        outbound_types = {"sale_out", "production_out", "transfer_out"}
        if self.current_doc_type not in outbound_types:
            QMessageBox.warning(self, "提示", "仅出库类型单据支持“完成出库”")
            return

        header = self.db.fetch_all(
            "SELECT warehouse_id FROM stock_documents WHERE id=%s",
            (self.current_doc_id,),
        )
        if not header:
            QMessageBox.warning(self, "提示", "单据不存在")
            return
        warehouse_id = header[0][0]

        items = self.db.fetch_all(
            "SELECT id, material_id, location_id, qty, unit_price FROM stock_document_items WHERE stock_document_id=%s ORDER BY id",
            (self.current_doc_id,),
        )
        if not items:
            QMessageBox.warning(self, "提示", "单据无明细，无法出库")
            return

        try:
            with self.db.conn.cursor() as cur:
                for item_id, material_id, location_id, qty, unit_price in items:
                    cur.execute(
                        """
                        SELECT id, qty, avg_cost
                        FROM inventory_balances
                        WHERE warehouse_id=%s
                          AND material_id=%s
                          AND ((location_id IS NULL AND %s IS NULL) OR location_id=%s)
                        FOR UPDATE
                        """,
                        (warehouse_id, material_id, location_id, location_id),
                    )
                    bal = cur.fetchone()
                    if not bal:
                        raise ValueError(f"库存不存在: material_id={material_id}")

                    balance_id, before_qty, before_avg = bal
                    before_qty = float(before_qty or 0)
                    before_avg = float(before_avg or 0)
                    qty_val = float(qty or 0)
                    price_val = float(unit_price or 0)

                    if before_qty < qty_val:
                        raise ValueError(
                            f"库存不足: material_id={material_id}, 现有={before_qty}, 出库={qty_val}"
                        )
                    after_qty = before_qty - qty_val

                    cur.execute(
                        "UPDATE inventory_balances SET qty=%s, updated_at=NOW() WHERE id=%s",
                        (after_qty, balance_id),
                    )

                    cur.execute(
                        """
                        INSERT INTO inventory_transactions
                        (warehouse_id, location_id, material_id, direction, qty, before_qty, after_qty,
                         unit_price, stock_document_id, stock_document_item_id)
                        VALUES (%s,%s,%s,'out',%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            warehouse_id,
                            location_id,
                            material_id,
                            qty_val,
                            before_qty,
                            after_qty,
                            price_val,
                            self.current_doc_id,
                            item_id,
                        ),
                    )

                cur.execute(
                    "UPDATE stock_documents SET status='posted' WHERE id=%s",
                    (self.current_doc_id,),
                )
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"完成出库失败: {exc}")
            return

        QMessageBox.information(self, "提示", "出库完成，库存已扣减")
        self.load_stock_docs()
        self.load_inventory()
        self.load_transactions()

    def load_transactions(self):
        kw = self.tx_kw.text().strip()
        like_kw = f"%{kw}%"
        wh_id = self.tx_wh.currentData()

        where_sql = "WHERE (m.material_code ILIKE %s OR m.material_name ILIKE %s)"
        params = [like_kw, like_kw]
        if wh_id:
            where_sql += " AND it.warehouse_id=%s"
            params.append(wh_id)

        rows = self.db.fetch_all(
            f"""
            SELECT it.occurred_at, it.direction,
                   w.warehouse_name, COALESCE(l.location_code, '-'),
                   m.material_code, m.material_name,
                   it.qty, it.before_qty, it.after_qty,
                   sd.doc_no
            FROM inventory_transactions it
            JOIN warehouses w ON it.warehouse_id = w.id
            LEFT JOIN warehouse_locations l ON it.location_id = l.id
            JOIN materials m ON it.material_id = m.id
            LEFT JOIN stock_documents sd ON it.stock_document_id = sd.id
            {where_sql}
            ORDER BY it.occurred_at DESC, it.id DESC
            LIMIT 500
            """,
            tuple(params),
        )

        self.tx_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.tx_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
