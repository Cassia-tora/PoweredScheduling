from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                            QComboBox, QCheckBox, QHBoxLayout, QPushButton, QMessageBox,QApplication)


# 新增/编辑物料对话框
class MaterialDialog(QDialog):
    def __init__(self, parent=None, material_id=None):
        super().__init__(parent)
        self.material_id = material_id  # 如果是编辑，传入物料ID
        self.setWindowTitle("新增物料" if not material_id else "编辑物料")
        self.setMinimumWidth(400)
        

        
        self.init_ui()
        if material_id:
            self.load_material_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # 表单布局
        form_layout = QFormLayout()

        # 物料编码
        self.code_edit = QLineEdit()
        form_layout.addRow("编码:", self.code_edit)

        # 物料名称
        self.name_edit = QLineEdit()
        form_layout.addRow("名称:", self.name_edit)

        # 类型（成品、半成品、原材料）
        self.type_combo = QComboBox()
        self.type_combo.addItems(["成品", "半成品", "原材料"])
        form_layout.addRow("类型:", self.type_combo)

        # 来源（采购或制造）
        self.source_combo = QComboBox()
        self.source_combo.addItems(["采购", "制造"])
        form_layout.addRow("来源:", self.source_combo)

        # 库存
        self.stock_edit = QLineEdit()
        self.stock_edit.setPlaceholderText("请输入数字")
        form_layout.addRow("库存:", self.stock_edit)

        # 安全库存
        self.safety_stock_edit = QLineEdit()
        self.safety_stock_edit.setPlaceholderText("请输入数字")
        form_layout.addRow("安全库存:", self.safety_stock_edit)

        # 计量单位
        self.unit_edit = QLineEdit()
        form_layout.addRow("计量单位:", self.unit_edit)

        # 提前期
        self.lead_time_edit = QLineEdit()
        self.lead_time_edit.setPlaceholderText("请输入数字")
        form_layout.addRow("提前期:", self.lead_time_edit)

        # 缓冲期
        self.buffer_time_edit = QLineEdit()
        self.buffer_time_edit.setPlaceholderText("请输入数字")
        form_layout.addRow("缓冲期:", self.buffer_time_edit)

        # 参与齐套计算
        self.include_in_set_check = QCheckBox()
        form_layout.addRow("参与齐套计算:", self.include_in_set_check)

        # 拓展字段
        self.extra_fields_edit = QLineEdit()
        form_layout.addRow("拓展字段:", self.extra_fields_edit)

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

    def load_material_data(self):
        """加载要编辑的物料数据"""
        from DBConnection import DBConnection
        db = DBConnection()
        query = "SELECT * FROM pc_material WHERE code = %s"
        result = db.execute_query(query, (self.material_id,))
        db.close()

        if result and len(result) > 0:
            material = result[0]
            self.code_edit.setText(material['code'])
            self.code_edit.setEnabled(False)  # 编码不可编辑
            self.name_edit.setText(material['name'])
            self.type_combo.setCurrentText(material['type'])
            self.source_combo.setCurrentText(material['source'])
            self.stock_edit.setText(str(material['stock']))
            self.safety_stock_edit.setText(str(material['safety_stock']))
            self.unit_edit.setText(material['unit'])
            self.lead_time_edit.setText(str(material['lead_time']))
            self.buffer_time_edit.setText(str(material['buffer_time']))
            self.include_in_set_check.setChecked(material['include_in_set'])
            self.extra_fields_edit.setText(material['extra_fields'] or "")

    def submit(self):
        """验证并提交数据"""
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        type_ = self.type_combo.currentText()
        source = self.source_combo.currentText()
        
        # 验证必填字段
        if not code or not name:
            QMessageBox.warning(self, "输入错误", "编码和名称不能为空")
            return

        # 处理数字字段
        try:
            stock = float(self.stock_edit.text().strip() or 0)
            safety_stock = float(self.safety_stock_edit.text().strip() or 0)
            lead_time = int(self.lead_time_edit.text().strip() or 0)
            buffer_time = int(self.buffer_time_edit.text().strip() or 0)
        except ValueError:
            QMessageBox.warning(self, "输入错误", "库存、安全库存、提前期、缓冲期必须为数字")
            return

        unit = self.unit_edit.text().strip()
        include_in_set = self.include_in_set_check.isChecked()
        extra_fields = self.extra_fields_edit.text().strip()

        # 保存数据
        from DBConnection import DBConnection
        db = DBConnection()
        if self.material_id:
            # 编辑模式
            query = """
            UPDATE pc_material SET name = %s, type = %s, source = %s, stock = %s,
            safety_stock = %s, unit = %s, lead_time = %s, buffer_time = %s,
            include_in_set = %s, extra_fields = %s WHERE code = %s
            """
            params = (name, type_, source, stock, safety_stock, unit, lead_time,
                     buffer_time, include_in_set, extra_fields, self.material_id)
        else:
            # 新增模式，先检查编码是否已存在
            check_query = "SELECT code FROM pc_material WHERE code = %s"
            exists = db.execute_query(check_query, (code,))
            if exists and len(exists) > 0:
                QMessageBox.warning(self, "错误", f"编码 {code} 已存在")
                db.close()
                return

            # 插入新记录
            query = """
            INSERT INTO pc_material (code, name, type, source, stock, safety_stock,
            unit, lead_time, buffer_time, include_in_set, extra_fields)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (code, name, type_, source, stock, safety_stock, unit,
                     lead_time, buffer_time, include_in_set, extra_fields)

        success = db.execute_update(query, params)
        db.close()

        if success:
            QMessageBox.information(self, "成功", "操作成功")
            self.accept()
        else:
            QMessageBox.warning(self, "失败", "操作失败，请重试")
