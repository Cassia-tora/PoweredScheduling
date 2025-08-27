from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QFormLayout, QLineEdit,
                            QComboBox, QHBoxLayout, QPushButton, QMessageBox,
                            QRadioButton, QGroupBox)


# 新增/编辑资源对话框
class ResourceDialog(QDialog):
    def __init__(self, parent=None, resource_code=None):
        super().__init__(parent)
        self.resource_code = resource_code  # 如果是编辑，传入资源编码
        self.setWindowTitle("新增主资源" if not resource_code else "编辑主资源")
        self.setMinimumWidth(450)
        self.init_ui()
        if resource_code:
            self.load_resource_data()

    def init_ui(self):
        layout = QVBoxLayout()

        # 表单布局
        form_layout = QFormLayout()

        # 资源编码
        self.code_edit = QLineEdit()
        form_layout.addRow("编码:", self.code_edit)

        # 资源名称
        self.name_edit = QLineEdit()
        form_layout.addRow("名称:", self.name_edit)

        # 资源组
        self.group_combo = QComboBox()
        self.group_combo.addItems(["加工厂",  "其他"])
        self.group_combo.setEditable(True)  # 允许自定义输入
        form_layout.addRow("资源组:", self.group_combo)

        # 容量
        capacity_layout = QHBoxLayout()
        self.capacity_edit = QLineEdit()
        self.capacity_unit_edit = QLineEdit()
        self.capacity_unit_edit.setPlaceholderText("如：个、台")
        capacity_layout.addWidget(self.capacity_edit)
        capacity_layout.addWidget(self.capacity_unit_edit)
        form_layout.addRow("容量:", capacity_layout)

        # 状态
        self.status_combo = QComboBox()
        self.status_combo.addItems(["正常", "报废", "维修"])
        form_layout.addRow("状态:", self.status_combo)

        # 产能设置
        productivity_group = QGroupBox("产能设置")
        productivity_layout = QVBoxLayout()
        
        # 产能类型选择
        self.per_unit_time_radio = QRadioButton("按单位时间：每个需要多少时间）")
        self.time_per_unit_radio = QRadioButton("按单位产品：单位时间生产多少个")
        self.batch_production_radio = QRadioButton("按批次生产：生产一批需要多少时间")
        self.per_unit_time_radio.setChecked(True)  # 默认选择第一种
        
        # 绑定单选按钮状态变化事件
        self.per_unit_time_radio.toggled.connect(self.update_productivity_controls)
        self.time_per_unit_radio.toggled.connect(self.update_productivity_controls)
        self.batch_production_radio.toggled.connect(self.update_productivity_controls)
        
        productivity_layout.addWidget(self.per_unit_time_radio)
        productivity_layout.addWidget(self.time_per_unit_radio)
        productivity_layout.addWidget(self.batch_production_radio)
        
        # 产能值和单位控件
        self.value_layout = QHBoxLayout()  # 改为实例变量
        self.productivity_value = QLineEdit()  # 数量输入框

        self.per_unit_combo = QComboBox()      # "个"选择框
        self.per_unit_combo.addItem("个")

        self.time_unit_combo = QComboBox()     # 时间单位选择框
        self.time_unit_combo.addItems(["分", "小时", "天"])
        


        # 添加所有控件到布局（初始状态）
        self.value_layout.addWidget(self.productivity_value)
        self.value_layout.addWidget(self.time_unit_combo)    
        self.value_layout.addWidget(self.per_unit_combo)            
        self.value_layout.addStretch()  # 伸缩项放在最后
        
        productivity_layout.addLayout(self.value_layout)
        productivity_group.setLayout(productivity_layout)
        
        form_layout.addRow(productivity_group)

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
        # 初始化控件显示状态
        self.update_productivity_controls()

    def update_productivity_controls(self):
        # 先清除现有布局中的控件（保留伸缩项）
        while self.value_layout.count() > 1:  # 假设最后一个是伸缩项
            item = self.value_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.setParent(None)
        
        if self.per_unit_time_radio.isChecked():
            # 按单位时间：数量 + 每个 + 时间单位
            self.per_unit_combo.setVisible(True)
            self.per_unit_combo.setMinimumWidth(50)
            self.time_unit_combo.setMinimumWidth(60)
            # 添加控件到布局
            self.value_layout.addWidget(self.productivity_value)
            self.value_layout.addWidget(self.time_unit_combo)
            self.value_layout.addWidget(self.per_unit_combo)            
            
        elif self.time_per_unit_radio.isChecked():
            # 按单位产品：数量 + 时间单位 + 每个（交换位置）
            self.per_unit_combo.setVisible(True)
            self.per_unit_combo.setMinimumWidth(50)
            self.time_unit_combo.setMinimumWidth(60)
            # 添加控件到布局（交换顺序）
            self.value_layout.addWidget(self.productivity_value)
            self.value_layout.addWidget(self.per_unit_combo)
            self.value_layout.addWidget(self.time_unit_combo)            
            
        elif self.batch_production_radio.isChecked():
            # 按批次生产：数量 + 时间单位
            self.per_unit_combo.setVisible(False)
            self.time_unit_combo.setMinimumWidth(60)
            # 添加控件到布局
            self.value_layout.addWidget(self.productivity_value)
            self.value_layout.addWidget(self.time_unit_combo)

    def load_resource_data(self):
        """加载要编辑的资源数据"""
        from DBConnection import DBConnection
        db = DBConnection()
        query = "SELECT * FROM pc_resource WHERE code = %s"
        result = db.execute_query(query, (self.resource_code,))
        db.close()

        if result and len(result) > 0:
            resource = result[0]
            self.code_edit.setText(resource['code'])
            self.code_edit.setEnabled(False)  # 编码不可编辑
            self.name_edit.setText(resource['name'])
            self.group_combo.setCurrentText(resource['resource_group'])
            self.capacity_edit.setText(str(resource['capacity']))
            self.capacity_unit_edit.setText(resource['capacity_unit'])
            self.status_combo.setCurrentText(resource['status'])
            
            # 产能数据
            self.productivity_value.setText(str(resource['productivity_value']))
            self.time_unit_combo.setCurrentText(resource['productivity_time_unit'])
            
            # 产能类型
            if resource['productivity_type'] == 'per_unit_time':
                self.per_unit_time_radio.setChecked(True)
            elif resource['productivity_type'] == 'time_per_unit':
                self.time_per_unit_radio.setChecked(True)
            else:  # batch_production
                self.batch_production_radio.setChecked(True)

    def submit(self):
        """验证并提交数据"""
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        resource_group = self.group_combo.currentText().strip()
        
        # 验证必填字段
        if not code or not name or not resource_group:
            QMessageBox.warning(self, "输入错误", "编码、名称和资源组不能为空")
            return

        # 处理数字字段
        try:
            capacity = float(self.capacity_edit.text().strip() or 0)
            productivity_value = float(self.productivity_value.text().strip())
            if productivity_value <= 0:
                raise ValueError("产能值必须大于0")
        except ValueError as e:
            QMessageBox.warning(self, "输入错误", f"容量和产能值必须为有效数字：{str(e)}")
            return

        capacity_unit = self.capacity_unit_edit.text().strip()
        status = self.status_combo.currentText()
        time_unit = self.time_unit_combo.currentText()
        
        # 产能类型
        if self.per_unit_time_radio.isChecked():
            productivity_type = 'per_unit_time'
        elif self.time_per_unit_radio.isChecked():
            productivity_type = 'time_per_unit'
        else:
            productivity_type = 'batch_production'

        # 保存数据
        from DBConnection import DBConnection
        db = DBConnection()
        if self.resource_code:
            # 编辑模式
            query = """
            UPDATE pc_resource SET name = %s, resource_group = %s, capacity = %s,
            capacity_unit = %s, status = %s, productivity_value = %s,
            productivity_time_unit = %s, productivity_type = %s WHERE code = %s
            """
            params = (name, resource_group, capacity, capacity_unit, status,
                     productivity_value, time_unit, productivity_type, self.resource_code)
        else:
            # 新增模式，先检查编码是否已存在
            check_query = "SELECT code FROM pc_resource WHERE code = %s"
            exists = db.execute_query(check_query, (code,))
            if exists and len(exists) > 0:
                QMessageBox.warning(self, "错误", f"编码 {code} 已存在")
                db.close()
                return

            # 插入新记录
            query = """
            INSERT INTO pc_resource (code, name, resource_group, capacity, capacity_unit,
            status, productivity_value, productivity_time_unit, productivity_type)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            params = (code, name, resource_group, capacity, capacity_unit, status,
                     productivity_value, time_unit, productivity_type)

        success = db.execute_update(query, params)
        db.close()

        if success:
            QMessageBox.information(self, "成功", "操作成功")
            self.accept()
        else:
            QMessageBox.warning(self, "失败", "操作失败，请重试")