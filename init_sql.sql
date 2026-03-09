-- 物料以及BOM
CREATE TABLE materials (
    id SERIAL PRIMARY KEY,
    material_code VARCHAR(50) UNIQUE NOT NULL,
    material_name VARCHAR(200) NOT NULL,
    category_id INT,
    unit VARCHAR(20),
    material_type VARCHAR(20),
    specification TEXT,
    standard_cost NUMERIC(18,4),
    safety_stock NUMERIC(18,4),
    is_produced BOOLEAN DEFAULT FALSE,
    inspection_required BOOLEAN DEFAULT FALSE,
    status VARCHAR(20) DEFAULT '启用',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE material_components (
    id SERIAL PRIMARY KEY,
    parent_material_id INT REFERENCES materials(id) ON DELETE CASCADE,
    component_material_id INT REFERENCES materials(id),
    quantity NUMERIC(18,4) NOT NULL
);

CREATE TABLE material_drawings (
    id SERIAL PRIMARY KEY,
    material_id INT REFERENCES materials(id) ON DELETE CASCADE,
    file_name VARCHAR(255),
    file_path TEXT,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 用户以及权限管理
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    real_name VARCHAR(100),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE roles (
    id SERIAL PRIMARY KEY,
    role_name VARCHAR(50) UNIQUE NOT NULL
);

CREATE TABLE permissions (
    id SERIAL PRIMARY KEY,
    permission_name VARCHAR(100) UNIQUE NOT NULL
);

CREATE TABLE user_roles (
    user_id INT REFERENCES users(id),
    role_id INT REFERENCES roles(id),
    PRIMARY KEY(user_id, role_id)
);

CREATE TABLE role_permissions (
    role_id INT REFERENCES roles(id) ON DELETE CASCADE,
    permission_id INT REFERENCES permissions(id) ON DELETE CASCADE,
    PRIMARY KEY(role_id, permission_id)
);

-- 项目以及订单管理
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    project_code VARCHAR(50) UNIQUE NOT NULL,
    project_name VARCHAR(200) NOT NULL,
    customer_name VARCHAR(200),
    status VARCHAR(20) DEFAULT '新建',
    start_date DATE,
    end_date DATE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE orders (
    id SERIAL PRIMARY KEY,
    project_id INT REFERENCES projects(id) ON DELETE CASCADE,
    order_code VARCHAR(50) UNIQUE NOT NULL,
    order_name VARCHAR(200),
    amount NUMERIC(18,2),
    status VARCHAR(20) DEFAULT '新建',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE order_details (
    id SERIAL PRIMARY KEY,
    order_id INT REFERENCES orders(id) ON DELETE CASCADE,
    material_id INT REFERENCES materials(id),
    quantity NUMERIC(18,4) NOT NULL,
    unit_price NUMERIC(18,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =========================
-- 询价管理（RFQ）表结构设计
-- =========================

-- 1) 询价单主表：一个订单可对应一张询价单
CREATE TABLE inquiry_orders (
    id SERIAL PRIMARY KEY,
    inquiry_code VARCHAR(50) UNIQUE NOT NULL,              -- 询价单号
    source_order_id INT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    status VARCHAR(20) NOT NULL DEFAULT 'draft',           -- draft / inquiring / quoted / selected / closed / cancelled
    inquiry_deadline DATE,                                 -- 报价截止日期
    currency VARCHAR(10) DEFAULT 'CNY',
    remark TEXT,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('draft', 'inquiring', 'quoted', 'selected', 'closed', 'cancelled'))
);

CREATE INDEX idx_inquiry_orders_source_order ON inquiry_orders(source_order_id);
CREATE INDEX idx_inquiry_orders_status ON inquiry_orders(status);


-- 2) 询价明细：按订单明细拆分到“每个物料”
CREATE TABLE inquiry_order_items (
    id SERIAL PRIMARY KEY,
    inquiry_order_id INT NOT NULL REFERENCES inquiry_orders(id) ON DELETE CASCADE,
    source_order_detail_id INT NOT NULL REFERENCES order_details(id) ON DELETE RESTRICT,
    material_id INT NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    required_qty NUMERIC(18,4) NOT NULL CHECK (required_qty > 0),
    target_unit_price NUMERIC(18,4),                       -- 可选：目标价
    required_delivery_date DATE,                           -- 可选：期望交期
    status VARCHAR(20) NOT NULL DEFAULT 'pending',         -- pending / quoted / selected / closed
    selected_quote_item_id INT,                            -- 最终中标报价行（后补外键）
    selected_supplier_id INT REFERENCES suppliers(id),
    selected_unit_price NUMERIC(18,4),                     -- 冗余保存中标价，便于采购直接取值
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('pending', 'quoted', 'selected', 'inventory', 'closed'))
);

CREATE INDEX idx_inquiry_items_inquiry ON inquiry_order_items(inquiry_order_id);
CREATE INDEX idx_inquiry_items_material ON inquiry_order_items(material_id);
CREATE INDEX idx_inquiry_items_order_detail ON inquiry_order_items(source_order_detail_id);


-- 3) 询价邀请供应商清单：每个询价明细可邀请多个供应商
CREATE TABLE inquiry_item_suppliers (
    id SERIAL PRIMARY KEY,
    inquiry_item_id INT NOT NULL REFERENCES inquiry_order_items(id) ON DELETE CASCADE,
    supplier_id INT NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    invite_status VARCHAR(20) NOT NULL DEFAULT 'invited',  -- invited / responded / rejected / expired
    invited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,
    remark TEXT,
    UNIQUE (inquiry_item_id, supplier_id),
    CHECK (invite_status IN ('invited', 'responded', 'rejected', 'expired'))
);

CREATE INDEX idx_inquiry_item_suppliers_item ON inquiry_item_suppliers(inquiry_item_id);
CREATE INDEX idx_inquiry_item_suppliers_supplier ON inquiry_item_suppliers(supplier_id);


-- 4) 供应商报价主表：一次供应商回报价（可含多行）
CREATE TABLE supplier_quotes (
    id SERIAL PRIMARY KEY,
    inquiry_order_id INT NOT NULL REFERENCES inquiry_orders(id) ON DELETE CASCADE,
    supplier_id INT NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    quote_no VARCHAR(50),                                  -- 供应商报价单号
    quote_date DATE DEFAULT CURRENT_DATE,
    valid_until DATE,                                      -- 报价有效期
    payment_terms VARCHAR(200),
    delivery_terms VARCHAR(200),
    tax_rate NUMERIC(5,2) DEFAULT 0,
    freight NUMERIC(18,4) DEFAULT 0,
    status VARCHAR(20) NOT NULL DEFAULT 'submitted',       -- submitted / withdrawn
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (status IN ('submitted', 'withdrawn'))
);

CREATE INDEX idx_supplier_quotes_inquiry ON supplier_quotes(inquiry_order_id);
CREATE INDEX idx_supplier_quotes_supplier ON supplier_quotes(supplier_id);


-- 5) 供应商报价明细：针对某个询价物料的报价
CREATE TABLE supplier_quote_items (
    id SERIAL PRIMARY KEY,
    supplier_quote_id INT NOT NULL REFERENCES supplier_quotes(id) ON DELETE CASCADE,
    inquiry_item_id INT NOT NULL REFERENCES inquiry_order_items(id) ON DELETE CASCADE,
    material_id INT NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    quote_unit_price NUMERIC(18,4) NOT NULL CHECK (quote_unit_price >= 0),
    quote_qty NUMERIC(18,4) CHECK (quote_qty > 0),         -- 可为空：默认按询价数量
    min_order_qty NUMERIC(18,4),
    lead_time_days INT,                                    -- 交期（天）
    tax_rate NUMERIC(5,2) DEFAULT 0,
    freight NUMERIC(18,4) DEFAULT 0,
    is_selected BOOLEAN DEFAULT FALSE,                     -- 是否中标
    rank_no INT,                                           -- 价格排序名次（1=最低）
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_supplier_quote_items_quote ON supplier_quote_items(supplier_quote_id);
CREATE INDEX idx_supplier_quote_items_inquiry_item ON supplier_quote_items(inquiry_item_id);
CREATE INDEX idx_supplier_quote_items_material ON supplier_quote_items(material_id);


-- 6) 回填外键（因为前面有循环依赖）
ALTER TABLE inquiry_order_items
ADD CONSTRAINT fk_inquiry_order_items_selected_quote
FOREIGN KEY (selected_quote_item_id) REFERENCES supplier_quote_items(id) ON DELETE SET NULL;


-- 7) 与采购衔接：采购明细增加来源报价行
ALTER TABLE purchase_order_items
ADD COLUMN source_quote_item_id INT REFERENCES supplier_quote_items(id) ON DELETE SET NULL;

CREATE INDEX idx_purchase_items_source_quote ON purchase_order_items(source_quote_item_id);


-- Purchase management
-- One purchase order is generated from one order and can contain multiple material lines.

CREATE TABLE suppliers (
    id SERIAL PRIMARY KEY,
    supplier_code VARCHAR(50) UNIQUE NOT NULL,
    supplier_name VARCHAR(200) NOT NULL,
    contact_name VARCHAR(100),
    contact_phone VARCHAR(50),
    address TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE material_suppliers (
    id SERIAL PRIMARY KEY,
    material_id INT NOT NULL REFERENCES materials(id) ON DELETE CASCADE,
    supplier_id INT NOT NULL REFERENCES suppliers(id) ON DELETE RESTRICT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (material_id, supplier_id)
);

CREATE TABLE purchase_orders (
    id SERIAL PRIMARY KEY,
    purchase_code VARCHAR(50) UNIQUE NOT NULL,
    source_order_id INT NOT NULL REFERENCES orders(id) ON DELETE RESTRICT,
    status VARCHAR(20) DEFAULT 'draft',
    expected_arrival_date DATE,
    logistics_status VARCHAR(30) DEFAULT 'pending',
    remark TEXT,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE purchase_order_items (
    id SERIAL PRIMARY KEY,
    purchase_order_id INT NOT NULL REFERENCES purchase_orders(id) ON DELETE CASCADE,
    source_order_detail_id INT REFERENCES order_details(id) ON DELETE SET NULL,
    material_id INT NOT NULL REFERENCES materials(id),
    supplier_id INT REFERENCES suppliers(id),
    purchase_qty NUMERIC(18,4) NOT NULL CHECK (purchase_qty > 0),
    unit_price NUMERIC(18,4) NOT NULL DEFAULT 0,
    tax_rate NUMERIC(5,2) DEFAULT 0,
    logistics_company VARCHAR(100),
    tracking_no VARCHAR(100),
    logistics_status VARCHAR(30) DEFAULT 'pending',
    planned_delivery_date DATE,
    received_qty NUMERIC(18,4) DEFAULT 0 CHECK (received_qty >= 0),
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_purchase_orders_source_order
    ON purchase_orders(source_order_id);

CREATE INDEX idx_purchase_items_order
    ON purchase_order_items(purchase_order_id);

CREATE INDEX idx_purchase_items_material
    ON purchase_order_items(material_id);

CREATE INDEX idx_purchase_items_supplier
    ON purchase_order_items(supplier_id);

-- Production management

CREATE TABLE production_orders (
    id SERIAL PRIMARY KEY,
    production_code VARCHAR(50) UNIQUE NOT NULL,
    source_order_id INT REFERENCES orders(id) ON DELETE SET NULL,
    status VARCHAR(20) DEFAULT 'draft',
    plan_start_date DATE,
    plan_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    remark TEXT,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE production_order_items (
    id SERIAL PRIMARY KEY,
    production_order_id INT NOT NULL REFERENCES production_orders(id) ON DELETE CASCADE,
    source_order_detail_id INT REFERENCES order_details(id) ON DELETE SET NULL,
    material_id INT NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    planned_qty NUMERIC(18,4) NOT NULL CHECK (planned_qty > 0),
    completed_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (completed_qty >= 0),
    status VARCHAR(20) DEFAULT 'pending',
    plan_start_date DATE,
    plan_end_date DATE,
    actual_start_date DATE,
    actual_end_date DATE,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE production_order_components (
    id SERIAL PRIMARY KEY,
    production_order_item_id INT NOT NULL REFERENCES production_order_items(id) ON DELETE CASCADE,
    component_material_id INT NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    required_qty NUMERIC(18,4) NOT NULL CHECK (required_qty >= 0),
    issued_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (issued_qty >= 0),
    returned_qty NUMERIC(18,4) NOT NULL DEFAULT 0 CHECK (returned_qty >= 0),
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_production_orders_source_order
    ON production_orders(source_order_id);

CREATE INDEX idx_production_orders_status
    ON production_orders(status);

CREATE INDEX idx_production_items_order
    ON production_order_items(production_order_id);

CREATE INDEX idx_production_items_material
    ON production_order_items(material_id);

CREATE INDEX idx_production_components_item
    ON production_order_components(production_order_item_id);

CREATE INDEX idx_production_components_material
    ON production_order_components(component_material_id);

-- Warehouse management

CREATE TABLE warehouses (
    id SERIAL PRIMARY KEY,
    warehouse_code VARCHAR(50) UNIQUE NOT NULL,
    warehouse_name VARCHAR(200) NOT NULL,
    warehouse_type VARCHAR(30) DEFAULT 'main',
    manager_name VARCHAR(100),
    phone VARCHAR(50),
    address TEXT,
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE warehouse_locations (
    id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE CASCADE,
    location_code VARCHAR(50) NOT NULL,
    location_name VARCHAR(100),
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (warehouse_id, location_code)
);

CREATE TABLE inventory_balances (
    id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
    location_id INT REFERENCES warehouse_locations(id) ON DELETE SET NULL,
    material_id INT NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    qty NUMERIC(18,4) NOT NULL DEFAULT 0,
    locked_qty NUMERIC(18,4) NOT NULL DEFAULT 0,
    avg_cost NUMERIC(18,4) NOT NULL DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (warehouse_id, location_id, material_id)
);

CREATE TABLE stock_documents (
    id SERIAL PRIMARY KEY,
    doc_no VARCHAR(50) UNIQUE NOT NULL,
    doc_type VARCHAR(30) NOT NULL,
    warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
    status VARCHAR(20) DEFAULT 'draft',
    biz_date DATE DEFAULT CURRENT_DATE,
    source_type VARCHAR(30),
    source_id INT,
    remark TEXT,
    created_by INT REFERENCES users(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CHECK (doc_type IN ('purchase_in', 'sale_out', 'production_in', 'production_out', 'adjustment', 'transfer_in', 'transfer_out'))
);

CREATE TABLE stock_document_items (
    id SERIAL PRIMARY KEY,
    stock_document_id INT NOT NULL REFERENCES stock_documents(id) ON DELETE CASCADE,
    material_id INT NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    location_id INT REFERENCES warehouse_locations(id) ON DELETE SET NULL,
    qty NUMERIC(18,4) NOT NULL CHECK (qty > 0),
    unit_price NUMERIC(18,4) DEFAULT 0,
    purchase_order_item_id INT REFERENCES purchase_order_items(id) ON DELETE SET NULL,
    order_detail_id INT REFERENCES order_details(id) ON DELETE SET NULL,
    remark TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_transactions (
    id SERIAL PRIMARY KEY,
    warehouse_id INT NOT NULL REFERENCES warehouses(id) ON DELETE RESTRICT,
    location_id INT REFERENCES warehouse_locations(id) ON DELETE SET NULL,
    material_id INT NOT NULL REFERENCES materials(id) ON DELETE RESTRICT,
    direction VARCHAR(10) NOT NULL CHECK (direction IN ('in', 'out')),
    qty NUMERIC(18,4) NOT NULL CHECK (qty > 0),
    before_qty NUMERIC(18,4) NOT NULL DEFAULT 0,
    after_qty NUMERIC(18,4) NOT NULL DEFAULT 0,
    unit_price NUMERIC(18,4) DEFAULT 0,
    stock_document_id INT REFERENCES stock_documents(id) ON DELETE SET NULL,
    stock_document_item_id INT REFERENCES stock_document_items(id) ON DELETE SET NULL,
    occurred_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_by INT REFERENCES users(id)
);

CREATE INDEX idx_locations_warehouse
    ON warehouse_locations(warehouse_id);

CREATE INDEX idx_inventory_material
    ON inventory_balances(material_id);

CREATE INDEX idx_inventory_warehouse
    ON inventory_balances(warehouse_id);

CREATE INDEX idx_stock_docs_warehouse
    ON stock_documents(warehouse_id);

CREATE INDEX idx_stock_docs_type_status
    ON stock_documents(doc_type, status);

CREATE INDEX idx_stock_items_doc
    ON stock_document_items(stock_document_id);

CREATE INDEX idx_stock_items_material
    ON stock_document_items(material_id);

CREATE INDEX idx_inventory_tx_material_time
    ON inventory_transactions(material_id, occurred_at DESC);
