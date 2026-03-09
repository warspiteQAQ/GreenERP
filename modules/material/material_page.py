from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton,
    QLineEdit, QTreeWidget, QTreeWidgetItem,
    QTableWidget, QTableWidgetItem, QMessageBox,
    QFileDialog, QSplitter, QDialog, QLabel, QDoubleSpinBox
)
from PySide6.QtCore import Qt
from database import Database
from .material_dialog import MaterialDialog
from ui.refresh_toast import show_refresh_success


class ComponentPickerDialog(QDialog):
    def __init__(self, db: Database, parent=None):
        super().__init__(parent)
        self.db = db
        self.page_size = 10
        self.current_page = 1
        self.total_pages = 1
        self.allowed_types = ("原材料", "成品")

        self.setWindowTitle("选择组成原材料")
        self.resize(700, 450)
        self.init_ui()
        self.load_page()

    def init_ui(self):
        layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.keyword_input = QLineEdit()
        self.keyword_input.setPlaceholderText("输入编码或名称筛选")
        self.btn_search = QPushButton("筛选")
        self.btn_search.clicked.connect(self.on_search)
        top_layout.addWidget(self.keyword_input)
        top_layout.addWidget(self.btn_search)
        layout.addLayout(top_layout)

        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["ID", "编码", "名称", "单位"])
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.SingleSelection)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        layout.addWidget(self.table)

        qty_layout = QHBoxLayout()
        qty_layout.addWidget(QLabel("数量"))
        self.qty_input = QDoubleSpinBox()
        self.qty_input.setDecimals(4)
        self.qty_input.setMinimum(0.0001)
        self.qty_input.setMaximum(999999999)
        self.qty_input.setValue(1.0)
        qty_layout.addWidget(self.qty_input)
        qty_layout.addStretch()
        layout.addLayout(qty_layout)

        pager_layout = QHBoxLayout()
        self.btn_prev = QPushButton("上一页")
        self.btn_next = QPushButton("下一页")
        self.page_label = QLabel("第 1/1 页")
        self.btn_prev.clicked.connect(self.prev_page)
        self.btn_next.clicked.connect(self.next_page)
        pager_layout.addWidget(self.btn_prev)
        pager_layout.addWidget(self.btn_next)
        pager_layout.addWidget(self.page_label)
        pager_layout.addStretch()
        layout.addLayout(pager_layout)

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

    def _build_filter_params(self):
        keyword = self.keyword_input.text().strip()
        like_kw = f"%{keyword}%"
        return keyword, like_kw

    def load_page(self):
        _, like_kw = self._build_filter_params()

        count_query = """
            SELECT COUNT(*)
            FROM materials
            WHERE material_type IN (%s, %s)
              AND (material_code ILIKE %s OR material_name ILIKE %s)
        """
        count_rows = self.db.fetch_all(
            count_query,
            (self.allowed_types[0], self.allowed_types[1], like_kw, like_kw)
        )
        total = int(count_rows[0][0]) if count_rows else 0
        self.total_pages = max(1, (total + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, self.total_pages)

        offset = (self.current_page - 1) * self.page_size
        data_query = """
            SELECT id, material_code, material_name, unit
            FROM materials
            WHERE material_type IN (%s, %s)
              AND (material_code ILIKE %s OR material_name ILIKE %s)
            ORDER BY id DESC
            LIMIT %s OFFSET %s
        """
        data = self.db.fetch_all(
            data_query,
            (
                self.allowed_types[0],
                self.allowed_types[1],
                like_kw,
                like_kw,
                self.page_size,
                offset,
            )
        )

        self.table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

        self.page_label.setText(f"第 {self.current_page}/{self.total_pages} 页")
        self.btn_prev.setEnabled(self.current_page > 1)
        self.btn_next.setEnabled(self.current_page < self.total_pages)

    def on_search(self):
        self.current_page = 1
        self.load_page()

    def prev_page(self):
        if self.current_page <= 1:
            return
        self.current_page -= 1
        self.load_page()

    def next_page(self):
        if self.current_page >= self.total_pages:
            return
        self.current_page += 1
        self.load_page()

    def accept_selection(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择一条原材料")
            return
        self.accept()

    def selected_material_id(self):
        row = self.table.currentRow()
        if row < 0:
            return None
        item = self.table.item(row, 0)
        return item.text() if item else None

    def selected_quantity(self):
        return self.qty_input.value()


class MaterialPage(QWidget):
    def __init__(self):
        super().__init__()
        self.db = Database()
        self.db.connect()
        self.material_id = None
        self.init_ui()
        self.load_materials()

    def init_ui(self):
        main_layout = QVBoxLayout()

        top_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("搜索物料名称或编码")
        self.btn_add = QPushButton("新增")
        self.btn_edit = QPushButton("编辑")
        self.btn_delete = QPushButton("删除")
        self.btn_refresh = QPushButton("刷新")
        top_layout.addWidget(self.search_input)
        top_layout.addWidget(self.btn_add)
        top_layout.addWidget(self.btn_edit)
        top_layout.addWidget(self.btn_delete)
        top_layout.addWidget(self.btn_refresh)

        body_layout = QHBoxLayout()

        self.tree = QTreeWidget()
        self.tree.setHeaderLabel("物料分类")
        self.tree.setFixedWidth(200)
        self.tree.addTopLevelItem(QTreeWidgetItem(["全部"]))

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "编码", "名称", "单位", "物料种类", "标准成本", "状态"]
        )
        self.table.setColumnHidden(0, True)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)

        body_layout.addWidget(self.tree)
        body_layout.addWidget(self.table)

        self.btn_add.clicked.connect(self.add_material)
        self.btn_edit.clicked.connect(self.edit_material)
        self.btn_delete.clicked.connect(self.delete_material)
        self.btn_refresh.clicked.connect(self.refresh_data)
        self.search_input.textChanged.connect(self.load_materials)
        self.table.itemSelectionChanged.connect(self.on_material_selection_changed)

        self.splitter = QSplitter(Qt.Vertical)

        self.component_table = QTableWidget()
        self.component_table.setColumnCount(3)
        self.component_table.setHorizontalHeaderLabels(["ID", "物料名称", "数量"])
        self.component_table.setColumnHidden(0, True)

        self.btn_add_component = QPushButton("添加组成物料")
        self.btn_remove_component = QPushButton("删除组成")

        component_layout = QVBoxLayout()
        component_layout.addWidget(self.component_table)
        component_layout.addWidget(self.btn_add_component)
        component_layout.addWidget(self.btn_remove_component)
        self.component_widget = QWidget()
        self.component_widget.setLayout(component_layout)

        self.drawing_table = QTableWidget()
        self.drawing_table.setColumnCount(3)
        self.drawing_table.setHorizontalHeaderLabels(["ID", "文件名", "路径"])
        self.drawing_table.setColumnHidden(0, True)

        self.btn_add_drawing = QPushButton("添加图纸")
        self.btn_remove_drawing = QPushButton("删除图纸")

        drawing_layout = QVBoxLayout()
        drawing_layout.addWidget(self.drawing_table)
        drawing_layout.addWidget(self.btn_add_drawing)
        drawing_layout.addWidget(self.btn_remove_drawing)
        drawing_widget = QWidget()
        drawing_widget.setLayout(drawing_layout)

        self.splitter.addWidget(self.component_widget)
        self.splitter.addWidget(drawing_widget)

        body_layout.addWidget(self.splitter)
        main_layout.addLayout(top_layout)
        main_layout.addLayout(body_layout)
        self.setLayout(main_layout)

        self.component_widget.setEnabled(False)
        self.btn_add_component.clicked.connect(self.add_component)
        self.btn_remove_component.clicked.connect(self.remove_component)
        self.btn_add_drawing.clicked.connect(self.add_drawing)
        self.btn_remove_drawing.clicked.connect(self.remove_drawing)

    def load_materials(self):
        keyword = self.search_input.text()
        query = """
            SELECT id, material_code, material_name,
                   unit, material_type, standard_cost, status
            FROM materials
            WHERE material_name ILIKE %s
               OR material_code ILIKE %s
            ORDER BY id DESC
        """
        data = self.db.fetch_all(query, (f"%{keyword}%", f"%{keyword}%"))

        self.table.setRowCount(len(data))
        for row_idx, row in enumerate(data):
            for col_idx, value in enumerate(row):
                self.table.setItem(row_idx, col_idx, QTableWidgetItem("" if value is None else str(value)))

        if not data:
            self.material_id = None
            self.component_widget.setEnabled(False)
            self.component_table.setRowCount(0)
            self.drawing_table.setRowCount(0)

    def refresh_data(self):
        self.load_materials()
        show_refresh_success(self)

    def add_material(self):
        dialog = MaterialDialog()
        if dialog.exec():
            self.load_materials()

    def edit_material(self):
        row = self.table.currentRow()
        if row < 0:
            QMessageBox.warning(self, "提示", "请选择一条记录")
            return

        material_id = self.table.item(row, 0).text()
        dialog = MaterialDialog(material_id)
        if dialog.exec():
            self.load_materials()

    def delete_material(self):
        row = self.table.currentRow()
        if row < 0:
            return

        material_id = self.table.item(row, 0).text()
        self.db.execute("DELETE FROM materials WHERE id=%s", (material_id,))
        self.load_materials()

    def on_material_selection_changed(self):
        row = self.table.currentRow()
        if row < 0:
            self.material_id = None
            self.component_widget.setEnabled(False)
            self.component_table.setRowCount(0)
            self.drawing_table.setRowCount(0)
            return

        self.material_id = self.table.item(row, 0).text()
        material_type_item = self.table.item(row, 4)
        material_type = material_type_item.text().strip() if material_type_item else ""
        is_semi_finished = ("生产件" in material_type)
        self.component_widget.setEnabled(is_semi_finished)
        if is_semi_finished:
            self.load_components()
        else:
            self.component_table.setRowCount(0)
        self.load_drawings()

    def load_components(self):
        if not self.material_id:
            return

        query = """
            SELECT mc.id, m.material_name, mc.quantity
            FROM material_components mc
            JOIN materials m ON mc.component_material_id = m.id
            WHERE mc.parent_material_id=%s
        """
        data = self.db.fetch_all(query, (self.material_id,))
        self.component_table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.component_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))

    def add_component(self):
        if not self.material_id:
            QMessageBox.warning(self, "提示", "请先选择物料")
            return
        if not self.component_widget.isEnabled():
            QMessageBox.warning(self, "提示", "当前物料不是生产件，不能维护组成物料")
            return

        dialog = ComponentPickerDialog(self.db, self)
        if not dialog.exec():
            return

        mat_id = dialog.selected_material_id()
        qty = dialog.selected_quantity()
        if not mat_id:
            QMessageBox.warning(self, "提示", "请选择一条原材料")
            return

        self.db.execute(
            """
            INSERT INTO material_components
            (parent_material_id, component_material_id, quantity)
            VALUES (%s,%s,%s)
            """,
            (self.material_id, mat_id, qty)
        )
        self.load_components()

    def remove_component(self):
        if not self.material_id:
            return
        if not self.component_widget.isEnabled():
            QMessageBox.warning(self, "提示", "当前物料不是生产件，不能删除组成物料")
            return

        row = self.component_table.currentRow()
        if row < 0:
            return

        comp_id = self.component_table.item(row, 0).text()
        self.db.execute("DELETE FROM material_components WHERE id=%s", (comp_id,))
        self.load_components()

    def add_drawing(self):
        if not self.material_id:
            QMessageBox.warning(self, "提示", "请先选择物料")
            return

        file_path, _ = QFileDialog.getOpenFileName(self, "选择图纸")
        if not file_path:
            return

        file_name = file_path.split("/")[-1]
        self.db.execute(
            """
            INSERT INTO material_drawings
            (material_id, file_name, file_path)
            VALUES (%s,%s,%s)
            """,
            (self.material_id, file_name, file_path)
        )
        self.load_drawings()

    def remove_drawing(self):
        if not self.material_id:
            return
        row = self.drawing_table.currentRow()
        if row < 0:
            return

        drawing_id = self.drawing_table.item(row, 0).text()
        self.db.execute("DELETE FROM material_drawings WHERE id=%s", (drawing_id,))
        self.load_drawings()

    def load_drawings(self):
        if not self.material_id:
            return

        data = self.db.fetch_all(
            """
            SELECT id, file_name, file_path
            FROM material_drawings
            WHERE material_id=%s
            """,
            (self.material_id,)
        )

        self.drawing_table.setRowCount(len(data))
        for r, row in enumerate(data):
            for c, val in enumerate(row):
                self.drawing_table.setItem(r, c, QTableWidgetItem("" if val is None else str(val)))
