from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QStackedWidget
)
from PySide6.QtCore import Qt
from modules.quotation.quotation_page import QuotationPage
from modules.project.project_page import ProjectPage
from modules.order.order_page import OrderPage
from modules.inquiry.inquiry_page import InquiryPage
from modules.purchase.purchase_page import PurchasePage
from modules.production.production_page import ProductionPage
from modules.warehouse.warehouse_page import WarehousePage
from modules.finance.finance_page import FinancePage
from modules.material.material_page import MaterialPage
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

        self.stack = QStackedWidget()
        self.page_quotation = QuotationPage()
        self.page_project = ProjectPage()
        self.page_order = OrderPage()
        self.page_inquiry = InquiryPage()
        self.page_purchase = PurchasePage()
        self.page_production = ProductionPage()
        self.page_warehouse = WarehousePage()
        self.page_finance = FinancePage()
        self.page_material = MaterialPage()
        self.page_user = UserManagePage()
        self.page_role = RoleManagePage()

        self.stack.addWidget(self.page_quotation)
        self.stack.addWidget(self.page_project)
        self.stack.addWidget(self.page_order)
        self.stack.addWidget(self.page_inquiry)
        self.stack.addWidget(self.page_purchase)
        self.stack.addWidget(self.page_production)
        self.stack.addWidget(self.page_warehouse)
        self.stack.addWidget(self.page_finance)
        self.stack.addWidget(self.page_material)
        self.stack.addWidget(self.page_user)
        self.stack.addWidget(self.page_role)

        self.btn_quotation.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        self.btn_project.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        self.btn_order.clicked.connect(lambda: self.stack.setCurrentIndex(2))
        self.btn_inquiry.clicked.connect(lambda: self.stack.setCurrentIndex(3))
        self.btn_purchase.clicked.connect(lambda: self.stack.setCurrentIndex(4))
        self.btn_production.clicked.connect(lambda: self.stack.setCurrentIndex(5))
        self.btn_warehouse.clicked.connect(lambda: self.stack.setCurrentIndex(6))
        self.btn_finance.clicked.connect(lambda: self.stack.setCurrentIndex(7))
        self.btn_material.clicked.connect(lambda: self.stack.setCurrentIndex(8))
        self.btn_user.clicked.connect(lambda: self.stack.setCurrentIndex(9))
        self.btn_role.clicked.connect(lambda: self.stack.setCurrentIndex(10))
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
