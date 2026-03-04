from datetime import datetime

from PySide6.QtCore import Qt, QDate
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QPushButton,
    QLineEdit,
    QLabel,
    QTableWidget,
    QTableWidgetItem,
    QSplitter,
    QMessageBox,
    QDialog,
    QFormLayout,
    QComboBox,
    QDoubleSpinBox,
    QDateEdit,
    QMenu,
    QAbstractItemView,
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
        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索订单号/订单名称")
        self.btn_search = QPushButton("查询")
        self.btn_search.clicked.connect(self.load_orders)
        self.search_input.returnPressed.connect(self.load_orders)
        top.addWidget(self.search_input)
        top.addWidget(self.btn_search)
        layout.addLayout(top)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "订单号", "订单名称", "状态", "创建时间"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.table)

        bottom = QHBoxLayout()
        btn_ok = QPushButton("确定")
        btn_cancel = QPushButton("取消")
        btn_ok.clicked.connect(self.accept_selection)
        btn_cancel.clicked.connect(self.reject)
        bottom.addStretch()
        bottom.addWidget(btn_ok)
        bottom.addWidget(btn_cancel)
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


class ProductionPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.current_production_id = None
        self.init_ui()
        self.load_production_orders()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索生产单号/来源订单")
        self.status_filter = QComboBox()
        self.status_filter.addItem("全部状态", None)
        for s in ["draft", "planned", "in_progress", "completed", "cancelled"]:
            self.status_filter.addItem(s, s)
        self.btn_search = QPushButton("查询")
        self.btn_order_to_production = QPushButton("订单转生产")
        self.btn_refresh = QPushButton("刷新")
        top.addWidget(self.search_input)
        top.addWidget(self.status_filter)
        top.addWidget(self.btn_search)
        top.addWidget(self.btn_order_to_production)
        top.addWidget(self.btn_refresh)
        main_layout.addLayout(top)

        splitter = QSplitter(Qt.Horizontal)

        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.addWidget(QLabel("生产单"))
        self.order_table = QTableWidget()
        self.order_table.setColumnCount(7)
        self.order_table.setHorizontalHeaderLabels(
            ["ID", "生产单号", "来源订单", "状态", "计划开始", "计划结束", "创建时间"]
        )
        self.order_table.setColumnHidden(0, True)
        self.order_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.order_table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.order_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        left_layout.addWidget(self.order_table)

        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.addWidget(QLabel("生产明细"))
        self.detail_table = QTableWidget()
        self.detail_table.setColumnCount(8)
        self.detail_table.setHorizontalHeaderLabels(
            ["ID", "物料编码", "物料名称", "计划数量", "完工数量", "状态", "计划开始", "计划结束"]
        )
        self.detail_table.setColumnHidden(0, True)
        self.detail_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.detail_table.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.detail_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.detail_table.setContextMenuPolicy(Qt.CustomContextMenu)
        right_layout.addWidget(self.detail_table)

        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        main_layout.addWidget(splitter)

        self.btn_search.clicked.connect(self.load_production_orders)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.btn_order_to_production.clicked.connect(self.create_from_order)
        self.search_input.returnPressed.connect(self.load_production_orders)
        self.status_filter.currentIndexChanged.connect(self.load_production_orders)
        self.order_table.itemSelectionChanged.connect(self.on_production_order_changed)
        self.detail_table.customContextMenuRequested.connect(self.show_detail_context_menu)

    def _gen_production_code(self):
        return "MO" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    def _gen_stock_doc_no(self):
        return "WD" + datetime.now().strftime("%Y%m%d%H%M%S%f")[:-3]

    def load_production_orders(self):
        kw = self.search_input.text().strip()
        like_kw = f"%{kw}%"
        status = self.status_filter.currentData()

        where = ["(po.production_code ILIKE %s OR COALESCE(o.order_code,'') ILIKE %s)"]
        params = [like_kw, like_kw]
        if status:
            where.append("po.status=%s")
            params.append(status)

        rows = self.db.fetch_all(
            f"""
            SELECT po.id, po.production_code, o.order_code, po.status,
                   po.plan_start_date, po.plan_end_date, po.created_at
            FROM production_orders po
            LEFT JOIN orders o ON po.source_order_id = o.id
            WHERE {' AND '.join(where)}
            ORDER BY po.id DESC
            """,
            tuple(params),
        )

        self.order_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.order_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

        if rows:
            self.order_table.selectRow(0)
        else:
            self.current_production_id = None
            self.detail_table.setRowCount(0)

    def on_production_order_changed(self):
        row = self.order_table.currentRow()
        if row < 0:
            self.current_production_id = None
            self.detail_table.setRowCount(0)
            return
        self.current_production_id = self.order_table.item(row, 0).text()
        self.load_details()

    def load_details(self):
        if not self.current_production_id:
            self.detail_table.setRowCount(0)
            return

        rows = self.db.fetch_all(
            """
            SELECT poi.id, m.material_code, m.material_name,
                   poi.planned_qty, poi.completed_qty, poi.status,
                   poi.plan_start_date, poi.plan_end_date
            FROM production_order_items poi
            JOIN materials m ON poi.material_id = m.id
            WHERE poi.production_order_id=%s
            ORDER BY poi.id DESC
            """,
            (self.current_production_id,),
        )
        self.detail_table.setRowCount(len(rows))
        for r, row in enumerate(rows):
            for c, val in enumerate(row):
                self.detail_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

    def create_from_order(self):
        picker = OrderPickerDialog(self.db, self)
        if not picker.exec():
            return
        order_id = picker.selected_order_id()
        if not order_id:
            return

        exists = self.db.fetch_all(
            "SELECT id, production_code FROM production_orders WHERE source_order_id=%s ORDER BY id DESC LIMIT 1",
            (order_id,),
        )
        if exists:
            QMessageBox.information(self, "提示", f"该订单已生成生产单: {exists[0][1]}")
            self.load_production_orders()
            return

        details = self.db.fetch_all(
            """
            SELECT od.id, od.material_id, od.quantity, m.material_code
            FROM order_details od
            JOIN materials m ON od.material_id = m.id
            WHERE od.order_id=%s AND m.material_type='生产件'
            ORDER BY od.id
            """,
            (order_id,),
        )
        if not details:
            QMessageBox.warning(self, "提示", "订单中没有生产件明细，无法生成生产单")
            return

        try:
            with self.db.conn.cursor() as cur:
                code = self._gen_production_code()
                cur.execute(
                    """
                    INSERT INTO production_orders
                    (production_code, source_order_id, status, plan_start_date, plan_end_date, remark)
                    VALUES (%s,%s,'planned',CURRENT_DATE,CURRENT_DATE,'由订单自动生成')
                    RETURNING id
                    """,
                    (code, order_id),
                )
                production_id = cur.fetchone()[0]

                for detail_id, material_id, qty, material_code in details:
                    qty_val = float(qty or 0)
                    cur.execute(
                        """
                        INSERT INTO production_order_items
                        (production_order_id, source_order_detail_id, material_id, planned_qty,
                         completed_qty, status, plan_start_date, plan_end_date, remark)
                        VALUES (%s,%s,%s,%s,0,'pending',CURRENT_DATE,CURRENT_DATE,'订单生产明细')
                        RETURNING id
                        """,
                        (production_id, detail_id, material_id, qty_val),
                    )
                    item_id = cur.fetchone()[0]

                    components = self.db.fetch_all(
                        """
                        SELECT component_material_id, quantity
                        FROM material_components
                        WHERE parent_material_id=%s
                        """,
                        (material_id,),
                    )
                    for comp_mid, comp_qty in components:
                        req_qty = qty_val * float(comp_qty or 0)
                        cur.execute(
                            """
                            INSERT INTO production_order_components
                            (production_order_item_id, component_material_id, required_qty, remark)
                            VALUES (%s,%s,%s,%s)
                            """,
                            (item_id, comp_mid, req_qty, f"BOM展开:{material_code}"),
                        )
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"订单转生产失败: {exc}")
            return

        QMessageBox.information(self, "提示", "生产单已根据订单生成")
        self.load_production_orders()

    def show_detail_context_menu(self, pos):
        row = self.detail_table.rowAt(pos.y())
        if row >= 0 and not self.detail_table.item(row, 0).isSelected():
            self.detail_table.selectRow(row)

        selected_rows = sorted({idx.row() for idx in self.detail_table.selectionModel().selectedRows()})
        if not selected_rows:
            return

        menu = QMenu(self)
        action_issue = menu.addAction("生产领料")
        action_start = menu.addAction("开始生产")
        action_finish = menu.addAction("生产完成")
        action_start.setEnabled(len(selected_rows) == 1)
        chosen = menu.exec(self.detail_table.viewport().mapToGlobal(pos))
        if chosen == action_issue:
            self.generate_production_issue(selected_rows)
        elif chosen == action_start:
            self.start_production(selected_rows[0])
        elif chosen == action_finish:
            self.finish_production(selected_rows)

    def start_production(self, row_index):
        if not self.current_production_id:
            QMessageBox.warning(self, "提示", "请先选择生产单")
            return

        id_item = self.detail_table.item(row_index, 0)
        if not id_item or not id_item.text():
            QMessageBox.warning(self, "提示", "未找到有效生产明细")
            return
        production_item_id = int(id_item.text())

        docs = self.db.fetch_all(
            """
            SELECT DISTINCT sd.id, sd.doc_no, sd.status
            FROM stock_document_items sdi
            JOIN stock_documents sd ON sdi.stock_document_id = sd.id
            WHERE sd.doc_type='production_out'
              AND sd.source_type='production'
              AND sd.source_id=%s
              AND sdi.remark ILIKE %s
            ORDER BY sd.id DESC
            """,
            (self.current_production_id, f"%生产明细ID={production_item_id}%"),
        )

        if not docs:
            QMessageBox.warning(self, "提示", "该明细尚未生成生产出库单，请先执行“生产领料”")
            return

        not_posted = [d for d in docs if str(d[2]) != "posted"]
        if not_posted:
            doc_nos = ", ".join([str(d[1]) for d in not_posted])
            QMessageBox.warning(
                self,
                "提示",
                f"该明细对应出库单未完成：{doc_nos}。请先确认完成领料（完成出库）后再开始生产。",
            )
            return

        try:
            self.db.execute(
                "UPDATE production_order_items SET status='in_progress', actual_start_date=CURRENT_DATE WHERE id=%s",
                (production_item_id,),
            )
            self.db.execute(
                "UPDATE production_orders SET status='in_progress' WHERE id=%s",
                (self.current_production_id,),
            )
        except Exception as exc:
            QMessageBox.warning(self, "提示", f"开始生产失败: {exc}")
            return

        QMessageBox.information(self, "提示", "已开始生产，状态更新为生产中")
        self.load_details()
        self.load_production_orders()

    def _ensure_active_warehouse_and_location(self):
        wh_rows = self.db.fetch_all(
            "SELECT id FROM warehouses WHERE status='active' ORDER BY id LIMIT 1"
        )
        if not wh_rows:
            raise ValueError("未找到启用仓库，请先在仓库管理中维护仓库")
        warehouse_id = wh_rows[0][0]

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
        location_id = loc_rows[0][0] if loc_rows else None
        return warehouse_id, location_id

    def generate_production_issue(self, selected_rows):
        if not self.current_production_id:
            QMessageBox.warning(self, "提示", "请先选择生产单")
            return

        detail_ids = []
        for r in selected_rows:
            item = self.detail_table.item(r, 0)
            if item and item.text():
                detail_ids.append(int(item.text()))
        if not detail_ids:
            QMessageBox.warning(self, "提示", "未选中有效生产明细")
            return

        try:
            warehouse_id, location_id = self._ensure_active_warehouse_and_location()
        except Exception as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return

        placeholders = ",".join(["%s"] * len(detail_ids))
        components = self.db.fetch_all(
            f"""
            SELECT poc.id,
                   poi.id AS production_item_id,
                   poc.component_material_id,
                   m.standard_cost,
                   poc.required_qty,
                   poc.issued_qty
            FROM production_order_components poc
            JOIN production_order_items poi ON poc.production_order_item_id = poi.id
            JOIN materials m ON poc.component_material_id = m.id
            WHERE poi.production_order_id=%s
              AND poi.id IN ({placeholders})
            ORDER BY poi.id, poc.id
            """,
            tuple([self.current_production_id] + detail_ids),
        )

        if not components:
            QMessageBox.warning(self, "提示", "选中明细没有可领料的BOM用料")
            return

        lines = []
        for component_id, production_item_id, material_id, std_cost, required_qty, issued_qty in components:
            req = float(required_qty or 0)
            issued = float(issued_qty or 0)
            remain = req - issued
            if remain <= 0:
                continue
            lines.append(
                (
                    component_id,
                    production_item_id,
                    material_id,
                    remain,
                    float(std_cost or 0),
                )
            )

        if not lines:
            QMessageBox.information(self, "提示", "选中明细已全部领料，无需重复生成出库单")
            return

        try:
            with self.db.conn.cursor() as cur:
                doc_no = self._gen_stock_doc_no()
                cur.execute(
                    """
                    INSERT INTO stock_documents
                    (doc_no, doc_type, warehouse_id, status, biz_date, source_type, source_id, remark)
                    VALUES (%s,'production_out',%s,'draft',CURRENT_DATE,'production',%s,%s)
                    RETURNING id
                    """,
                    (
                        doc_no,
                        warehouse_id,
                        self.current_production_id,
                        f"生产领料自动生成，生产明细:{','.join([str(i) for i in detail_ids])}",
                    ),
                )
                stock_doc_id = cur.fetchone()[0]

                for component_id, production_item_id, material_id, remain_qty, unit_price in lines:
                    cur.execute(
                        """
                        INSERT INTO stock_document_items
                        (stock_document_id, material_id, location_id, qty, unit_price, remark)
                        VALUES (%s,%s,%s,%s,%s,%s)
                        """,
                        (
                            stock_doc_id,
                            material_id,
                            location_id,
                            remain_qty,
                            unit_price,
                            f"生产领料:生产明细ID={production_item_id}",
                        ),
                    )
                    cur.execute(
                        """
                        UPDATE production_order_components
                        SET issued_qty = issued_qty + %s
                        WHERE id=%s
                        """,
                        (remain_qty, component_id),
                    )

            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"生成生产出库单失败: {exc}")
            return

        QMessageBox.information(
            self,
            "提示",
            f"已为 {len(detail_ids)} 条生产明细统一生成生产出库单，明细行数 {len(lines)}",
        )
        self.load_details()

    def finish_production(self, selected_rows):
        if not self.current_production_id:
            QMessageBox.warning(self, "提示", "请先选择生产单")
            return

        detail_ids = []
        for r in selected_rows:
            item = self.detail_table.item(r, 0)
            if item and item.text():
                detail_ids.append(int(item.text()))
        if not detail_ids:
            QMessageBox.warning(self, "提示", "未选中有效生产明细")
            return

        try:
            warehouse_id, location_id = self._ensure_active_warehouse_and_location()
        except Exception as exc:
            QMessageBox.warning(self, "提示", str(exc))
            return

        placeholders = ",".join(["%s"] * len(detail_ids))
        rows = self.db.fetch_all(
            f"""
            SELECT id, material_id, planned_qty, completed_qty, status
            FROM production_order_items
            WHERE production_order_id=%s
              AND id IN ({placeholders})
            ORDER BY id
            """,
            tuple([self.current_production_id] + detail_ids),
        )
        if not rows:
            QMessageBox.warning(self, "提示", "未找到对应生产明细")
            return

        lines = []
        already_inbound = 0
        for detail_id, material_id, planned_qty, completed_qty, _ in rows:
            exists = self.db.fetch_all(
                """
                SELECT sdi.id
                FROM stock_document_items sdi
                JOIN stock_documents sd ON sdi.stock_document_id = sd.id
                WHERE sd.doc_type='production_in'
                  AND sd.source_type='production'
                  AND sd.source_id=%s
                  AND sdi.remark ILIKE %s
                LIMIT 1
                """,
                (self.current_production_id, f"%生产明细ID={detail_id}%"),
            )
            if exists:
                already_inbound += 1
                continue

            qty = float(completed_qty or 0)
            if qty <= 0:
                qty = float(planned_qty or 0)
            if qty <= 0:
                continue
            lines.append((detail_id, material_id, qty))

        try:
            with self.db.conn.cursor() as cur:
                for detail_id, _, qty in lines:
                    cur.execute(
                        """
                        UPDATE production_order_items
                        SET status='completed',
                            completed_qty = CASE WHEN completed_qty IS NULL OR completed_qty <= 0 THEN %s ELSE completed_qty END,
                            actual_end_date = CURRENT_DATE
                        WHERE id=%s
                        """,
                        (qty, detail_id),
                    )

                if lines:
                    doc_no = self._gen_stock_doc_no()
                    cur.execute(
                        """
                        INSERT INTO stock_documents
                        (doc_no, doc_type, warehouse_id, status, biz_date, source_type, source_id, remark)
                        VALUES (%s,'production_in',%s,'draft',CURRENT_DATE,'production',%s,%s)
                        RETURNING id
                        """,
                        (
                            doc_no,
                            warehouse_id,
                            self.current_production_id,
                            f"生产完成自动生成，生产明细:{','.join([str(v[0]) for v in lines])}",
                        ),
                    )
                    stock_doc_id = cur.fetchone()[0]

                    for detail_id, material_id, qty in lines:
                        cur.execute(
                            """
                            INSERT INTO stock_document_items
                            (stock_document_id, material_id, location_id, qty, unit_price, remark)
                            VALUES (%s,%s,%s,%s,0,%s)
                            """,
                            (
                                stock_doc_id,
                                material_id,
                                location_id,
                                qty,
                                f"生产完工入库:生产明细ID={detail_id}",
                            ),
                        )

                # 选中但已入库的明细，仍允许状态置为完成
                for detail_id, _, planned_qty, completed_qty, _ in rows:
                    if any(detail_id == l[0] for l in lines):
                        continue
                    cur.execute(
                        """
                        UPDATE production_order_items
                        SET status='completed',
                            completed_qty = CASE WHEN completed_qty IS NULL OR completed_qty <= 0 THEN %s ELSE completed_qty END,
                            actual_end_date = CURRENT_DATE
                        WHERE id=%s
                        """,
                        (float(completed_qty or planned_qty or 0), detail_id),
                    )

                summary = self.db.fetch_all(
                    """
                    SELECT COUNT(*),
                           SUM(CASE WHEN status='completed' THEN 1 ELSE 0 END)
                    FROM production_order_items
                    WHERE production_order_id=%s
                    """,
                    (self.current_production_id,),
                )
                total_count = int(summary[0][0]) if summary else 0
                completed_count = int(summary[0][1] or 0) if summary else 0
                if total_count > 0 and completed_count == total_count:
                    cur.execute(
                        """
                        UPDATE production_orders
                        SET status='completed', actual_end_date=CURRENT_DATE
                        WHERE id=%s
                        """,
                        (self.current_production_id,),
                    )
            self.db.conn.commit()
        except Exception as exc:
            self.db.conn.rollback()
            QMessageBox.warning(self, "提示", f"生产完成处理失败: {exc}")
            return

        QMessageBox.information(
            self,
            "提示",
            f"已完成 {len(rows)} 条明细；新生成入库行 {len(lines)}，已存在入库 {already_inbound} 条。",
        )
        self.load_details()
        self.load_production_orders()

    def refresh_data(self):
        self.load_production_orders()
