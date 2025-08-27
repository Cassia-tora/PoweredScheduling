from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit, QComboBox, 
                            QDateEdit, QPushButton, QHBoxLayout, QMessageBox, QColorDialog)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor
from DBConnection import DBConnection

class ProductionOrderDialog(QDialog):
    def __init__(self, parent=None, order_no=None):
        super().__init__(parent)
        self.order_no = order_no  # 如果是编辑，传入订单号
        self.setWindowTitle("新增生产订单" if not order_no else "编辑生产订单")
        self.setMinimumWidth(500)
        self.init_ui()
        if order_no:
            self.load_order_data()
        self.load_products()  # 加载产品数据

    def init_ui(self):
        layout = QVBoxLayout()

        # 表单布局
        form_layout = QFormLayout()

        # 订单号
        self.order_no_edit = QLineEdit()
        self.order_no_edit.setReadOnly(bool(self.order_no))  # 编辑时不可修改
        form_layout.addRow("订单号 <span style='color:red'>*</span>:", self.order_no_edit)

        # 产品编码
        self.product_combo = QComboBox()
        self.product_combo.setEditable(True)
        self.product_combo.setMinimumWidth(250)
        form_layout.addRow("产品编码 <span style='color:red'>*</span>:", self.product_combo)

        # 数量
        self.quantity_edit = QLineEdit()
        form_layout.addRow("数量 <span style='color:red'>*</span>:", self.quantity_edit)

        # 订单状态
        self.status_combo = QComboBox()
        self.status_combo.addItems(["待处理", "已取消", "已完成"])
        form_layout.addRow("订单状态:", self.status_combo)

        # 需求交付日期
        self.due_date_edit = QDateEdit(QDate.currentDate())
        self.due_date_edit.setCalendarPopup(True)
        form_layout.addRow("需求交付日期 <span style='color:red'>*</span>:", self.due_date_edit)

        # 优先级
        self.priority_combo = QComboBox()
        priorities = ["P1", "P2", "P3", "P4", "P5"]
        self.priority_combo.addItems(priorities)
        self.priority_combo.setCurrentIndex(0)  # 默认P1
        # 设置优先级颜色
        for i, priority in enumerate(priorities):
            color = self.get_priority_color(priority)
            self.priority_combo.setItemData(i, color, Qt.BackgroundRole)
        form_layout.addRow("优先级:", self.priority_combo)

        # 订单类型
        self.type_combo = QComboBox()
        self.type_combo.addItems(["需求制造订单", "空闲产能填补订单"])
        form_layout.addRow("订单类型 <span style='color:red'>*</span>:", self.type_combo)

        # 显示颜色
        self.color_edit = QLineEdit()
        self.color_btn = QPushButton("选择颜色")
        self.color_btn.clicked.connect(self.choose_color)
        color_layout = QHBoxLayout()
        color_layout.addWidget(self.color_edit)
        color_layout.addWidget(self.color_btn)
        form_layout.addRow("显示颜色:", color_layout)

        layout.addLayout(form_layout)

        # 按钮布局
        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("提交")
        self.cancel_btn = QPushButton("取消")
        self.submit_btn.clicked.connect(self.submit)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)

        self.setLayout(layout)

    def get_priority_color(self, priority):
        """根据优先级获取对应的颜色"""
        colors = {
            "P1": "#808080",  # 灰色
            "P2": "#A0A0A0",
            "P3": "#C0C0C0",
            "P4": "#FFA0A0",
            "P5": "#FF0000"   # 红色
        }
        return QColor(colors.get(priority, "#000000"))

    def choose_color(self):
        """选择显示颜色"""
        color = QColorDialog.getColor()
        if color.isValid():
            self.color_edit.setText(color.name())

    def load_products(self):
        """加载物料管理中的产品数据"""
        db = DBConnection()
        query = "SELECT code, name FROM pc_material"
        products = db.execute_query(query)
        db.close()

        if products:
            for product in products:
                self.product_combo.addItem(f"{product['code']} - {product['name']}", product['code'])

    def load_order_data(self):
        """加载要编辑的订单数据"""
        db = DBConnection()
        query = "SELECT * FROM pc_production_order WHERE order_no = %s"
        result = db.execute_query(query, (self.order_no,))
        db.close()

        if result and len(result) > 0:
            order = result[0]
            self.order_no_edit.setText(order['order_no'])
            # 设置产品
            product_text = f"{order['product_code']} - {order['product_name']}"
            index = self.product_combo.findText(product_text)
            if index >= 0:
                self.product_combo.setCurrentIndex(index)
            self.quantity_edit.setText(str(order['quantity']))
            self.status_combo.setCurrentText(order['status'])
            
            due_date = order['due_date']  # datetime.date对象
            # 先将date对象转换为字符串（如"2023-10-01"）
            due_date_str = due_date.strftime("%Y-%m-%d")
            # 再用字符串创建QDate对象
            self.due_date_edit.setDate(QDate.fromString(due_date_str, "yyyy-MM-dd"))

            self.priority_combo.setCurrentText(order['priority'])
            self.type_combo.setCurrentText(order['type'])
            self.color_edit.setText(order['display_color'])

    def submit(self):
        """验证并提交数据"""
        order_no = self.order_no_edit.text().strip()
        product_text = self.product_combo.currentText().strip()
        quantity_text = self.quantity_edit.text().strip()
        due_date = self.due_date_edit.date().toString("yyyy-MM-dd")
        order_type = self.type_combo.currentText()

        # 验证必填字段
        if not order_no:
            QMessageBox.warning(self, "输入错误", "订单号不能为空")
            return
            
        if not product_text:
            QMessageBox.warning(self, "输入错误", "产品编码不能为空")
            return
            
        if not quantity_text:
            QMessageBox.warning(self, "输入错误", "数量不能为空")
            return
            
        if not due_date:
            QMessageBox.warning(self, "输入错误", "需求交付日期不能为空")
            return
            
        if not order_type:
            QMessageBox.warning(self, "输入错误", "订单类型不能为空")
            return

        # 提取产品编码和名称
        if " - " in product_text:
            product_code, product_name = product_text.split(" - ", 1)
        else:
            product_code = product_text
            product_name = ""

        # 验证数量
        try:
            quantity = float(quantity_text)
            if quantity <= 0:
                raise ValueError("数量必须大于0")
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", f"数量必须为有效数字：{str(e)}")
            return

        # 其他字段
        status = self.status_combo.currentText()
        priority = self.priority_combo.currentText()
        display_color = self.color_edit.text().strip() or "#000000"

        # 保存数据
        db = DBConnection()
        if self.order_no:
            # 编辑模式
            query = """
            UPDATE pc_production_order SET product_code = %s, product_name = %s, quantity = %s,
            status = %s, due_date = %s, priority = %s, type = %s, display_color = %s
            WHERE order_no = %s
            """
            params = (product_code, product_name, quantity, status, due_date, priority, 
                     order_type, display_color, self.order_no)
        else:
            # 新增模式，先检查订单号是否已存在
            check_query = "SELECT order_no FROM pc_production_order WHERE order_no = %s"
            exists = db.execute_query(check_query, (order_no,))
            if exists and len(exists) > 0:
                QMessageBox.warning(self, "错误", f"订单号 {order_no} 已存在")
                db.close()
                return

            # 插入新记录
            query = """
            INSERT INTO pc_production_order 
            (order_no, product_code, product_name, quantity, status, due_date, priority, 
             type, display_color)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (order_no, product_code, product_name, quantity, status, due_date, 
                     priority, order_type, display_color)

        success = db.execute_update(query, params)
        db.close()

        if success:
            QMessageBox.information(self, "成功", "操作成功")
            self.accept()
        else:
            QMessageBox.warning(self, "失败", "操作失败，请重试")