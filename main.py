import sys
from PyQt5.QtWidgets import QApplication
from DBConnection import DBConnection
from MainFrame import MainFrame

# 初始化数据库表结构（首次运行时需要执行）
def init_database():
    db = DBConnection()
    # 创建物料表（已存在）
    create_material_table = """
    CREATE TABLE IF NOT EXISTS pc_material (
        code VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        type ENUM('成品', '半成品', '原材料') NOT NULL,
        source ENUM('采购', '制造') NOT NULL,
        stock DECIMAL(10, 2) DEFAULT 0,
        safety_stock DECIMAL(10, 2) DEFAULT 0,
        unit VARCHAR(20) DEFAULT '',
        lead_time INT DEFAULT 0,
        buffer_time INT DEFAULT 0,
        include_in_set BOOLEAN DEFAULT FALSE,
        extra_fields TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    # 创建客户表
    create_customer_table = """
    CREATE TABLE IF NOT EXISTS pc_customer (
        id INT PRIMARY KEY AUTO_INCREMENT,
        code VARCHAR(50) NOT NULL UNIQUE,
        name VARCHAR(100) NOT NULL,
        contact_person VARCHAR(50),
        phone VARCHAR(20),
        email VARCHAR(100),
        address TEXT,
        status ENUM('启用', '禁用') DEFAULT '启用',
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    # 创建供应商表
    create_supplier_table = """
    CREATE TABLE IF NOT EXISTS pc_supplier (
        id INT PRIMARY KEY AUTO_INCREMENT,
        code VARCHAR(50) NOT NULL UNIQUE,
        name VARCHAR(100) NOT NULL,
        contact_person VARCHAR(50),
        phone VARCHAR(20),
        email VARCHAR(100),
        address TEXT,
        status ENUM('启用', '禁用') DEFAULT '启用',
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    # 创建设备表
    create_equipment_table = """
    CREATE TABLE IF NOT EXISTS pc_equipment (
        id INT PRIMARY KEY AUTO_INCREMENT,
        code VARCHAR(50) NOT NULL UNIQUE,
        name VARCHAR(100) NOT NULL,
        type VARCHAR(50),
        model VARCHAR(50),
        status ENUM('运行', '维护', '停机') DEFAULT '运行',
        location VARCHAR(100),
        purchase_date DATE,
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    # 创建用户表
    create_user_table = """
    CREATE TABLE IF NOT EXISTS sys_user (
        id INT PRIMARY KEY AUTO_INCREMENT,
        username VARCHAR(50) NOT NULL UNIQUE,
        password VARCHAR(100) NOT NULL,
        realname VARCHAR(50),
        phone VARCHAR(20),
        email VARCHAR(100),
        role_id INT,
        status ENUM('启用', '禁用') DEFAULT '启用',
        last_login_time DATETIME,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    # 创建角色表
    create_role_table = """
    CREATE TABLE IF NOT EXISTS sys_role (
        id INT PRIMARY KEY AUTO_INCREMENT,
        name VARCHAR(50) NOT NULL UNIQUE,
        permissions TEXT,
        remark TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    
    # 创建操作日志表
    create_log_table = """
    CREATE TABLE IF NOT EXISTS sys_operation_log (
        id INT PRIMARY KEY AUTO_INCREMENT,
        user_id INT,
        username VARCHAR(50),
        operation VARCHAR(100),
        module VARCHAR(50),
        content TEXT,
        ip_address VARCHAR(50),
        operation_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
    
    # 创建工单表
    create_work_order_table = """
    CREATE TABLE IF NOT EXISTS pc_work_order (
        id INT PRIMARY KEY AUTO_INCREMENT,
        order_no VARCHAR(50) NOT NULL UNIQUE,
        product_code VARCHAR(50) NOT NULL,
        product_name VARCHAR(100) NOT NULL,
        quantity DECIMAL(10, 2) NOT NULL,
        completed_quantity DECIMAL(10, 2) DEFAULT 0,
        status ENUM('待排程', '排程中', '生产中', '已完成', '已取消') DEFAULT '待排程',
        start_date DATE,
        end_date DATE,
        actual_start_date DATE,
        actual_end_date DATE,
        customer_id INT,
        remark TEXT,
        created_by INT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    # 创建资源表
    create_resource_table = """
    CREATE TABLE IF NOT EXISTS pc_resource (
        code VARCHAR(50) PRIMARY KEY,
        name VARCHAR(100) NOT NULL,
        resource_group VARCHAR(50) NOT NULL,
        capacity DECIMAL(10, 2) DEFAULT 0,
        capacity_unit VARCHAR(20) DEFAULT '',
        status ENUM('正常', '报废', '维修') DEFAULT '正常',
        productivity_value DECIMAL(10, 2) NOT NULL,
        productivity_time_unit VARCHAR(10) NOT NULL,
        productivity_type ENUM('per_unit_time', 'time_per_unit', 'batch_production') NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
    )
    """
    # 创建生产订单表
    create_production_order_table = """
    CREATE TABLE IF NOT EXISTS pc_production_order (
        order_no VARCHAR(50) PRIMARY KEY,
        product_code VARCHAR(50) NOT NULL,
        product_name VARCHAR(100) NOT NULL,
        quantity DECIMAL(10, 2) NOT NULL,
        status ENUM('待处理', '已取消', '已完成') DEFAULT '待处理',
        due_date DATE NOT NULL,
        priority ENUM('P1', 'P2', 'P3', 'P4', 'P5') DEFAULT 'P3',
        type ENUM('需求制造订单', '空闲产能填补订单') DEFAULT '需求制造订单',
        display_color VARCHAR(20) DEFAULT '#000000',
        scheduling_status ENUM('未排产', '已排产') DEFAULT '未排产',
        participate_scheduling BOOLEAN DEFAULT TRUE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        FOREIGN KEY (product_code) REFERENCES pc_material(code)
    )
    """
    # 创建工序模板表
    create_process_template_table = """
    CREATE TABLE IF NOT EXISTS pc_process_template (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT ' 主键 ID',
    code VARCHAR (50) NOT NULL COMMENT ' 工序编码 ',
    name VARCHAR (100) NOT NULL COMMENT ' 工序名称 ',
    pre_interval_value DECIMAL (10,1) DEFAULT 0 COMMENT ' 前间隔时长值 ',
    pre_interval_unit VARCHAR (10) DEFAULT ' 分 ' COMMENT ' 前间隔时长单位（分 / 时 / 天）',
    post_interval_value DECIMAL (10,1) DEFAULT 0 COMMENT ' 后间隔时长值 ',
    post_interval_unit VARCHAR (10) DEFAULT ' 分 ' COMMENT ' 后间隔时长单位（分 / 时 / 天）',
    relation VARCHAR (5) NOT NULL COMMENT ' 工序关系（ES/EE）',
    buffer_time_value DECIMAL (10,1) DEFAULT 0 COMMENT ' 缓冲时长值 ',
    buffer_time_unit VARCHAR (10) DEFAULT ' 分 ' COMMENT ' 缓冲时长单位（分 / 时 / 天）',
    allow_split TINYINT (1) DEFAULT 0 COMMENT ' 是否允许自动拆分（0 - 否 1 - 是）',
    min_batch INT DEFAULT NULL COMMENT ' 最小拆分批量 ',
    max_batch INT DEFAULT NULL COMMENT ' 最大拆分批量 ',
    split_threshold INT DEFAULT NULL COMMENT ' 触发拆分数量阈值 ',
    split_strategy VARCHAR (20) DEFAULT NULL COMMENT ' 拆分策略（平均拆分 / 基准数拆分 / 产能比例拆分）',
    base_number INT DEFAULT NULL COMMENT ' 基准数（拆分策略为基准数拆分时使用）',
    changeover_time_value DECIMAL (10,1) DEFAULT 0 COMMENT ' 切换产品时长值 ',
    changeover_time_unit VARCHAR (10) DEFAULT ' 分 ' COMMENT ' 切换产品时长单位（分 / 时 / 天）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT ' 创建时间 ',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT ' 更新时间 ',
    PRIMARY KEY (id),
    UNIQUE KEY uk_code (code) COMMENT ' 工序编码唯一约束 ',
    KEY idx_name (name) COMMENT ' 工序名称索引 '
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT=' 工序模板主表 '
    """
    # 创建工序模板与资源关联表
    create_template_resources_table = """
    CREATE TABLE IF NOT EXISTS pc_template_resources (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT ' 主键 ID',
    template_id BIGINT NOT NULL COMMENT ' 工序模板 ID',
    resource_code VARCHAR (50) NOT NULL COMMENT ' 资源编码 ',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT ' 创建时间 ',
    PRIMARY KEY (id),
    UNIQUE KEY uk_template_resource (template_id, resource_code) COMMENT ' 模板与资源关联唯一约束 ',
    KEY fk_template_id (template_id) COMMENT ' 模板 ID 外键索引 ',
    KEY fk_resource_code (resource_code) COMMENT ' 资源编码外键索引 '    
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT=' 工序模板与资源关联表 '
    """
    # 创建工序模板与物料关联表
    create_template_materials_table = """
    CREATE TABLE IF NOT EXISTS pc_template_materials (
    id BIGINT NOT NULL AUTO_INCREMENT COMMENT ' 主键 ID',
    template_id BIGINT NOT NULL COMMENT ' 工序模板 ID',
    material_code VARCHAR (50) NOT NULL COMMENT ' 物料编码 ',
    quantity DECIMAL (15,2) NOT NULL DEFAULT 1 COMMENT ' 物料数量 ',
    is_used TINYINT (1) DEFAULT 1 COMMENT ' 是否使用（0 - 否 1 - 是）',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT ' 创建时间 ',
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT ' 更新时间 ',
    PRIMARY KEY (id),
    UNIQUE KEY uk_template_material (template_id, material_code) COMMENT ' 模板与物料关联唯一约束 ',
    KEY fk_ptm_template_id (template_id) COMMENT ' 模板 ID 外键索引 ',
    KEY fk_ptm_material_code (material_code) COMMENT ' 物料编码外键索引 '    
    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT=' 工序模板与物料关联表 '
    """
    # 工艺路线表
    create_process_route_table= """CREATE TABLE IF NOT EXISTS pc_process_route (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    material_code VARCHAR(50) NOT NULL,
    name VARCHAR(100) NOT NULL,
    description TEXT,
    create_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    update_time DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (material_code) REFERENCES pc_material(code)
    )"""    

    #-- 工艺路线节点表
    create_route_node_table= """CREATE TABLE IF NOT EXISTS pc_route_node (
    id BIGINT  NOT NULL AUTO_INCREMENT PRIMARY KEY,
    material_code VARCHAR(50) NOT NULL,
    template_id BIGINT,
    name VARCHAR(100) NOT NULL,
    x_pos INT DEFAULT 0,
    y_pos INT DEFAULT 0,
    sort_order INT,
    pre_interval DECIMAL(10,1),
    pre_interval_unit VARCHAR(10),
    post_interval DECIMAL(10,1),
    post_interval_unit VARCHAR(10),
    relation VARCHAR(2),
    buffer_time DECIMAL(10,1),
    buffer_time_unit VARCHAR(10),
    FOREIGN KEY (material_code) REFERENCES pc_material(code),
    FOREIGN KEY (template_id) REFERENCES pc_process_template(id)
    )"""

    #-- 工艺路线节点连接表
    create_route_link_table= """CREATE TABLE IF NOT EXISTS pc_route_link (
    id BIGINT AUTO_INCREMENT PRIMARY KEY,
    material_code VARCHAR(50) NOT NULL,
    from_node_id BIGINT NOT NULL,
    to_node_id BIGINT NOT NULL,
    FOREIGN KEY (material_code) REFERENCES pc_material(code),
    FOREIGN KEY (from_node_id) REFERENCES pc_route_node(id),
    FOREIGN KEY (to_node_id) REFERENCES pc_route_node(id)
    )"""
    # 执行创建表语句
    success = True
    try:
        db.execute_update(create_material_table)
        db.execute_update(create_customer_table)
        db.execute_update(create_supplier_table)
        db.execute_update(create_equipment_table)
        db.execute_update(create_user_table)
        db.execute_update(create_role_table)
        db.execute_update(create_log_table)
        db.execute_update(create_work_order_table)
        db.execute_update(create_resource_table)  # 添加资源表
        db.execute_update(create_production_order_table) # 添加生产订单表 
        db.execute_update(create_process_template_table) # 创建工序模板表 
        db.execute_update(create_template_resources_table) # 创建工序模板与资源关联表
        db.execute_update(create_template_materials_table) # 创建工序模板与物料关联表 
        db.execute_update(create_process_route_table) #  工艺路线表
        db.execute_update(create_route_node_table) #  工艺路线节点表
        db.execute_update(create_route_link_table) #  工艺路线节点连接表
    except Exception as e:
        print(f"初始化数据库错误: {e}")
        success = False
    finally:
        db.close()
    return success


if __name__ == "__main__":
    # 初始化数据库表
    init_database()
    
    app = QApplication(sys.argv)
    window = MainFrame()  # 使用新的主框架
    window.show()
    sys.exit(app.exec_())
