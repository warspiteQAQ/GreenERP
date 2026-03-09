from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget, QStyle, QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QIcon
from pathlib import Path
from modules.quotation.quotation_page import QuotationPage
from modules.project.project_page import ProjectPage
from modules.order.order_page import OrderPage
from modules.inquiry.inquiry_page import InquiryPage
from modules.purchase.purchase_page import PurchasePage
from modules.production.production_page import ProductionPage
from modules.warehouse.warehouse_page import WarehousePage
from modules.finance.finance_page import FinancePage
from modules.material.material_page import MaterialPage
from modules.material.supplier_manage_page import SupplierManagePage
from modules.user.user_manage_page import UserManagePage
from modules.role.role_manage_page import RoleManagePage


class MainWindow(QMainWindow):
    def __init__(self, username):
        super().__init__()
        self.setWindowTitle("GLDG 企业ERP系统")
        self.resize(1400, 800)

        self.username = username

        central = QWidget()
        main_layout = QHBoxLayout()

        self.sidebar_layout = QVBoxLayout()
        self.sidebar_layout.setSpacing(10)
        self.sidebar_layout.setContentsMargins(10, 10, 10, 10)

        self.btn_quotation = QPushButton("报价管理")
        self.btn_project = QPushButton("项目管理")
        self.btn_order = QPushButton("订单管理")
        self.btn_inquiry = QPushButton("询价管理")
        self.btn_purchase = QPushButton("采购管理")
        self.btn_production = QPushButton("生产管理")
        self.btn_warehouse = QPushButton("仓库管理")
        self.btn_finance = QPushButton("财务管理")
        self.btn_material = QPushButton("物料管理")
        self.btn_supplier = QPushButton("供应商管理")
        self.btn_user = QPushButton("用户管理")
        self.btn_role = QPushButton("角色管理")

        self.top_buttons = [
            self.btn_quotation,
            self.btn_project,
            self.btn_order,
            self.btn_inquiry,
            self.btn_purchase,
            self.btn_production,
            self.btn_warehouse,
            self.btn_finance,
        ]
        self.bottom_buttons = [
            self.btn_material,
            self.btn_supplier,
            self.btn_user,
            self.btn_role,
        ]

        for btn in self.top_buttons + self.bottom_buttons:
            btn.setFixedHeight(45)
            btn.setCursor(Qt.PointingHandCursor)

        for btn in self.top_buttons:
            self.sidebar_layout.addWidget(btn)

        self.sidebar_layout.addStretch()

        for btn in self.bottom_buttons:
            self.sidebar_layout.addWidget(btn)

        sidebar_widget = QWidget()
        sidebar_widget.setLayout(self.sidebar_layout)
        sidebar_widget.setFixedWidth(220)
        sidebar_widget.setObjectName("sidebar")
        self.sidebar_widget = sidebar_widget

        self.toggle_btn = QPushButton("<")
        self.toggle_btn.setObjectName("sidebarToggle")
        self.toggle_btn.setFixedSize(20, 20)
        self.toggle_btn.setCursor(Qt.PointingHandCursor)

        sidebar_container = QWidget()
        sidebar_container_layout = QHBoxLayout()
        sidebar_container_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_container_layout.setSpacing(0)
        sidebar_container_layout.addWidget(sidebar_widget)

        toggle_layout = QVBoxLayout()
        toggle_layout.setContentsMargins(0, 0, 0, 0)
        toggle_layout.addWidget(self.toggle_btn, alignment=Qt.AlignLeft | Qt.AlignTop)

        toggle_widget = QWidget()
        toggle_widget.setLayout(toggle_layout)
        sidebar_container_layout.addWidget(toggle_widget)
        sidebar_container.setLayout(sidebar_container_layout)
        self.sidebar_expanded_width = 220
        self.sidebar_collapsed_width = 48
        self.sidebar_collapsed = False

        self.nav_buttons = self.top_buttons + self.bottom_buttons
        self._apply_nav_icons()

        self.stack = QStackedWidget()
        self._page_factories = [
            QuotationPage,
            ProjectPage,
            OrderPage,
            InquiryPage,
            PurchasePage,
            ProductionPage,
            WarehousePage,
            FinancePage,
            MaterialPage,
            SupplierManagePage,
            UserManagePage,
            RoleManagePage,
        ]
        self._pages = [None] * len(self._page_factories)

        for _ in self._page_factories:
            self.stack.addWidget(QWidget())

        self.btn_quotation.clicked.connect(lambda: self.open_page(0))
        self.btn_project.clicked.connect(lambda: self.open_page(1))
        self.btn_order.clicked.connect(lambda: self.open_page(2))
        self.btn_inquiry.clicked.connect(lambda: self.open_page(3))
        self.btn_purchase.clicked.connect(lambda: self.open_page(4))
        self.btn_production.clicked.connect(lambda: self.open_page(5))
        self.btn_warehouse.clicked.connect(lambda: self.open_page(6))
        self.btn_finance.clicked.connect(lambda: self.open_page(7))
        self.btn_material.clicked.connect(lambda: self.open_page(8))
        self.btn_supplier.clicked.connect(lambda: self.open_page(9))
        self.btn_user.clicked.connect(lambda: self.open_page(10))
        self.btn_role.clicked.connect(lambda: self.open_page(11))
        self.toggle_btn.clicked.connect(self.toggle_sidebar)

        top_bar = QLabel(f"当前登录用户: {self.username}")
        top_bar.setFixedHeight(40)
        top_bar.setAlignment(Qt.AlignRight)
        top_bar.setStyleSheet("padding-right:20px;")

        right_layout = QVBoxLayout()
        right_layout.addWidget(top_bar)
        right_layout.addWidget(self.stack)

        right_widget = QWidget()
        right_widget.setLayout(right_layout)

        main_layout.addWidget(sidebar_container)
        main_layout.addWidget(right_widget)

        central.setLayout(main_layout)
        self.setCentralWidget(central)
        self.open_page(0)

    def open_page(self, index):
        if index < 0 or index >= len(self._page_factories):
            return

        if self._pages[index] is None:
            try:
                page = self._page_factories[index]()
            except Exception as exc:
                QMessageBox.warning(self, "提示", f"模块加载失败: {exc}")
                return

            placeholder = self.stack.widget(index)
            self.stack.removeWidget(placeholder)
            placeholder.deleteLater()
            self.stack.insertWidget(index, page)
            self._pages[index] = page

        self.stack.setCurrentIndex(index)

    def _apply_nav_icons(self):
        icon_map = {
            self.btn_quotation: ("quotation.svg", QStyle.SP_FileDialogDetailedView),
            self.btn_project: ("project.svg", QStyle.SP_DirOpenIcon),
            self.btn_order: ("order.svg", QStyle.SP_FileIcon),
            self.btn_inquiry: ("inquiry.svg", QStyle.SP_FileDialogContentsView),
            self.btn_purchase: ("purchase.svg", QStyle.SP_DriveHDIcon),
            self.btn_production: ("production.svg", QStyle.SP_ComputerIcon),
            self.btn_warehouse: ("warehouse.svg", QStyle.SP_DirIcon),
            self.btn_finance: ("finance.svg", QStyle.SP_DialogSaveButton),
            self.btn_material: ("material.svg", QStyle.SP_FileDialogListView),
            self.btn_supplier: ("supplier.svg", QStyle.SP_DirHomeIcon),
            self.btn_user: ("user.svg", QStyle.SP_ComputerIcon),
            self.btn_role: ("role.svg", QStyle.SP_DialogApplyButton),
        }

        icon_dir = Path(__file__).resolve().parent / "icons" / "modules"
        for btn, (icon_file, fallback_icon) in icon_map.items():
            icon_path = icon_dir / icon_file
            if icon_path.exists():
                btn.setIcon(QIcon(str(icon_path)))
            else:
                btn.setIcon(self.style().standardIcon(fallback_icon))
            btn.setIconSize(QSize(18, 18))
            btn.setStyleSheet("text-align:left; padding-left:10px;")

    def toggle_sidebar(self):
        self.sidebar_collapsed = not self.sidebar_collapsed
        for btn in self.nav_buttons:
            btn.setVisible(not self.sidebar_collapsed)

        if self.sidebar_collapsed:
            self.sidebar_widget.setFixedWidth(self.sidebar_collapsed_width)
            self.toggle_btn.setText(">")
        else:
            self.sidebar_widget.setFixedWidth(self.sidebar_expanded_width)
            self.toggle_btn.setText("<")
