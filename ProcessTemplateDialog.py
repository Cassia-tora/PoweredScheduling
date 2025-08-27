# 新增/编辑工序模板对话框
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QFormLayout, QLineEdit,
                             QComboBox, QTableWidget, QTableWidgetItem, QPushButton,
                             QLabel, QGroupBox, QCheckBox, QDoubleSpinBox, QSpinBox,
                             QDateEdit, QMessageBox, QHeaderView, QWidget, QGridLayout,
                             QRadioButton, QTabWidget, QSplitter,QApplication)
from PyQt5.QtCore import Qt, QDate
from PyQt5.QtGui import QColor, QFont
from DBConnection import DBConnection

class ProcessTemplateDialog(QDialog):
    def __init__(self, parent=None, template_id=None):
        super().__init__(parent)
        self.template_id = template_id  # 如果是编辑，传入模板ID
        self.setWindowTitle("新增工序模板" if not template_id else "编辑工序模板")
        
        # 增大对话框尺寸，使用相对屏幕的比例
        screen_geometry = QApplication.desktop().availableGeometry()
        dialog_width = int(screen_geometry.width() * 0.6)  # 占屏幕宽度的60%
        dialog_height = int(screen_geometry.height() * 0.7)  # 占屏幕高度的70%
        self.resize(dialog_width, dialog_height)

        # 居中显示
        self.move((screen_geometry.width() - dialog_width) // 2,
                 (screen_geometry.height() - dialog_height) // 2)
        
        self.init_ui()
        if template_id:
            self.load_template_data()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout()
        
        # 上部：基本信息区域
        top_group = QGroupBox("基本信息")
        top_layout = QFormLayout()
        
        # 工序编码
        self.code_edit = QLineEdit()
        top_layout.addRow("工序编码 <span style='color:red'>*</span>:", self.code_edit)
        
        # 工序名称
        self.name_edit = QLineEdit()
        top_layout.addRow("工序名称 <span style='color:red'>*</span>:", self.name_edit)
        
        # 前间隔时长
        self.pre_interval_edit = QDoubleSpinBox()
        self.pre_interval_edit.setMinimum(0)
        self.pre_interval_edit.setDecimals(1)
        self.pre_interval_unit = QComboBox()
        self.pre_interval_unit.addItems(["分", "时", "天"])
        pre_interval_layout = QHBoxLayout()
        pre_interval_layout.addWidget(self.pre_interval_edit)
        pre_interval_layout.addWidget(self.pre_interval_unit)
        top_layout.addRow("前间隔时长:", pre_interval_layout)
        
        # 后间隔时长
        self.post_interval_edit = QDoubleSpinBox()
        self.post_interval_edit.setMinimum(0)
        self.post_interval_edit.setDecimals(1)
        self.post_interval_unit = QComboBox()
        self.post_interval_unit.addItems(["分", "时", "天"])
        post_interval_layout = QHBoxLayout()
        post_interval_layout.addWidget(self.post_interval_edit)
        post_interval_layout.addWidget(self.post_interval_unit)
        top_layout.addRow("后间隔时长:", post_interval_layout)
        
        # 工序关系
        self.relation_combo = QComboBox()
        self.relation_combo.addItems(["ES", "EE"])
        self.relation_combo.currentTextChanged.connect(self.on_relation_changed)
        top_layout.addRow("工序关系:", self.relation_combo)
        
        # 缓冲时长
        self.buffer_time_edit = QDoubleSpinBox()
        self.buffer_time_edit.setMinimum(0)
        self.buffer_time_edit.setDecimals(1)
        self.buffer_time_unit = QComboBox()
        self.buffer_time_unit.addItems(["分", "时", "天"])
        buffer_layout = QHBoxLayout()
        buffer_layout.addWidget(self.buffer_time_edit)
        buffer_layout.addWidget(self.buffer_time_unit)
        top_layout.addRow("缓冲时长:", buffer_layout)
        
        top_group.setLayout(top_layout)
        main_layout.addWidget(top_group)
        
        # 下部：品字型布局
        bottom_layout = QHBoxLayout()
        
        # 左下：选项区域
        left_bottom_widget = QWidget()
        left_bottom_layout = QVBoxLayout(left_bottom_widget)
        left_bottom_widget.setMaximumWidth(200)
        
        # 主资源按钮
        self.resource_btn = QPushButton("主资源")
        self.resource_btn.setCheckable(True)
        self.resource_btn.setChecked(True)
        self.resource_btn.clicked.connect(lambda: self.switch_content("resource"))
        left_bottom_layout.addWidget(self.resource_btn)
        
        # 使用物料按钮
        self.material_btn = QPushButton("使用物料")
        self.material_btn.setCheckable(True)
        self.material_btn.clicked.connect(lambda: self.switch_content("material"))
        left_bottom_layout.addWidget(self.material_btn)
        
        # 自动拆分按钮
        self.split_btn = QPushButton("自动拆分")
        self.split_btn.setCheckable(True)
        self.split_btn.clicked.connect(lambda: self.switch_content("split"))
        left_bottom_layout.addWidget(self.split_btn)
        
        # 换型配置按钮
        self.changeover_btn = QPushButton("换型配置")
        self.changeover_btn.setCheckable(True)
        self.changeover_btn.clicked.connect(lambda: self.switch_content("changeover"))
        left_bottom_layout.addWidget(self.changeover_btn)
        
        left_bottom_layout.addStretch()
        bottom_layout.addWidget(left_bottom_widget)
        
        # 右下：内容展示区域
        self.right_bottom_widget = QWidget()
        self.right_bottom_layout = QVBoxLayout(self.right_bottom_widget)
        
        # 主资源内容
        self.resource_widget = self.create_resource_widget()
        
        # 使用物料内容
        self.material_widget = self.create_material_widget()
        
        # 自动拆分内容
        self.split_widget = self.create_split_widget()
        
        # 换型配置内容
        self.changeover_widget = self.create_changeover_widget()
        
        # 默认显示主资源
        self.show_current_widget(self.resource_widget)
        
        bottom_layout.addWidget(self.right_bottom_widget, 1)
        
        main_layout.addLayout(bottom_layout, 1)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        self.submit_btn = QPushButton("提交")
        self.cancel_btn = QPushButton("取消")
        self.submit_btn.clicked.connect(self.submit)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.submit_btn)
        btn_layout.addWidget(self.cancel_btn)
        
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)
        
        # 加载初始数据
        self.load_resources()
        self.load_materials()

    def create_resource_widget(self):
        """创建主资源内容区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.add_resource_btn = QPushButton("新增主资源")
        self.add_resource_btn.clicked.connect(self.add_resource)
        btn_layout.addWidget(self.add_resource_btn)
        layout.addLayout(btn_layout)
        
        # 主资源表格
        self.resource_table = QTableWidget()
        self.resource_table.setColumnCount(7)
        self.resource_table.setHorizontalHeaderLabels(["序号", "编码", "名称", "资源组", "容量", "产能", "操作"])
        self.resource_table.horizontalHeader().setStretchLastSection(True)
        layout.addWidget(self.resource_table)
        
        return widget

    def create_material_widget(self):
        """创建使用物料内容区域"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        self.add_material_btn = QPushButton("新增使用物料")
        self.add_material_btn.clicked.connect(self.add_material)
        btn_layout.addWidget(self.add_material_btn)
        layout.addLayout(btn_layout)
        
        # 使用物料表格
        self.material_table = QTableWidget()
        self.material_table.setColumnCount(6)
        self.material_table.setHorizontalHeaderLabels(["序号", "编码", "名称", "数量", "是否使用", "操作"])
        self.material_table.horizontalHeader().setStretchLastSection(True)
        self.material_table.cellChanged.connect(self.on_material_cell_changed)
        layout.addWidget(self.material_table)
        
        return widget

    def create_split_widget(self):
        """创建自动拆分内容区域"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # 是否允许自动拆分
        self.allow_split_check = QCheckBox()
        layout.addRow("是否允许自动拆分:", self.allow_split_check)
        
        # 最小拆分批量
        self.min_batch_edit = QDoubleSpinBox()
        self.min_batch_edit.setMinimum(0)
        self.min_batch_edit.setDecimals(0)
        layout.addRow("最小拆分批量:", self.min_batch_edit)
        
        # 最大拆分批量
        self.max_batch_edit = QDoubleSpinBox()
        self.max_batch_edit.setMinimum(0)
        self.max_batch_edit.setDecimals(0)
        layout.addRow("最大拆分批量:", self.max_batch_edit)
        
        # 触发拆分数量阈值
        self.split_threshold_edit = QDoubleSpinBox()
        self.split_threshold_edit.setMinimum(0)
        self.split_threshold_edit.setDecimals(0)
        layout.addRow("触发拆分数量阈值:", self.split_threshold_edit)
        
        # 拆分策略
        self.split_strategy_combo = QComboBox()
        self.split_strategy_combo.addItems(["", "平均拆分", "基准数拆分", "产能比例拆分"])
        self.split_strategy_combo.currentTextChanged.connect(self.on_split_strategy_changed)
        layout.addRow("拆分策略:", self.split_strategy_combo)
        
        # 基准数（默认隐藏）
        self.base_number_widget = QWidget()
        self.base_number_layout = QHBoxLayout(self.base_number_widget)
        self.base_number_edit = QDoubleSpinBox()
        self.base_number_edit.setMinimum(1)
        self.base_number_edit.setDecimals(0)
        self.base_number_layout.addWidget(self.base_number_edit)
        self.base_number_widget.hide()
        layout.addRow("基准数:", self.base_number_widget)
        
        return widget

    def create_changeover_widget(self):
        """创建换型配置内容区域"""
        widget = QWidget()
        layout = QFormLayout(widget)
        
        # 切换产品时长
        self.changeover_time_edit = QDoubleSpinBox()
        self.changeover_time_edit.setMinimum(0)
        self.changeover_time_edit.setDecimals(1)
        self.changeover_time_unit = QComboBox()
        self.changeover_time_unit.addItems(["分", "时", "天"])
        changeover_layout = QHBoxLayout()
        changeover_layout.addWidget(self.changeover_time_edit)
        changeover_layout.addWidget(self.changeover_time_unit)
        layout.addRow("切换产品时长:", changeover_layout)
        
        return widget

    def switch_content(self, content_type):
        """切换右下内容区域显示"""
        # 重置所有按钮状态
        self.resource_btn.setChecked(False)
        self.material_btn.setChecked(False)
        self.split_btn.setChecked(False)
        self.changeover_btn.setChecked(False)
        
        # 显示对应的内容
        if content_type == "resource":
            self.resource_btn.setChecked(True)
            self.show_current_widget(self.resource_widget)
        elif content_type == "material":
            self.material_btn.setChecked(True)
            self.show_current_widget(self.material_widget)
        elif content_type == "split":
            self.split_btn.setChecked(True)
            self.show_current_widget(self.split_widget)
        elif content_type == "changeover":
            self.changeover_btn.setChecked(True)
            self.show_current_widget(self.changeover_widget)

    def show_current_widget(self, widget):
        """显示当前选中的部件"""
        # 清除现有布局
        while self.right_bottom_layout.count():
            item = self.right_bottom_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
        
        # 添加新部件
        self.right_bottom_layout.addWidget(widget)
        widget.show()

    def on_relation_changed(self, relation):
        """工序关系变更处理"""
        # EE关系时才需要缓冲时长
        self.buffer_time_edit.setEnabled(relation == "EE")
        self.buffer_time_unit.setEnabled(relation == "EE")

    def on_split_strategy_changed(self, strategy):
        """拆分策略变更处理"""
        # 只有基准数拆分时才需要基准数
        self.base_number_widget.setVisible(strategy == "基准数拆分")

    def load_resources(self):
        """加载所有可用资源"""
        db = DBConnection()
        query = "SELECT * FROM pc_resource"
        self.all_resources = db.execute_query(query)
        db.close()

    def load_materials(self):
        """加载所有可用物料"""
        db = DBConnection()
        query = "SELECT * FROM pc_material"
        self.all_materials = db.execute_query(query)
        db.close()

    def add_resource(self):
        """添加主资源"""
        # 创建资源选择对话框（简化实现，实际应使用更完善的选择组件）
        from ResourceSelectionDialog import ResourceSelectionDialog  # 假设存在此对话框
        dialog = ResourceSelectionDialog(self, self.all_resources)
        if dialog.exec_():
            selected_resources = dialog.get_selected_resources()
            for resource in selected_resources:
                self.add_resource_to_table(resource)

    def add_resource_to_table(self, resource):
        """将资源添加到表格"""
        row = self.resource_table.rowCount()
        self.resource_table.insertRow(row)
        
        # 序号
        self.resource_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        
        # 编码
        self.resource_table.setItem(row, 1, QTableWidgetItem(resource['code']))
        
        # 名称
        self.resource_table.setItem(row, 2, QTableWidgetItem(resource['name']))
        
        # 资源组
        self.resource_table.setItem(row, 3, QTableWidgetItem(resource['resource_group']))
        
        # 容量
        self.resource_table.setItem(row, 4, QTableWidgetItem(f"{resource['capacity']} {resource['capacity_unit']}"))
        
        # 产能
        if resource['productivity_type'] == 'per_unit_time':
            productivity_text = f"{resource['productivity_value']}个/{resource['productivity_time_unit']}"
        else:
            productivity_text = f"{resource['productivity_value']}{resource['productivity_time_unit']}/每个"
        self.resource_table.setItem(row, 5, QTableWidgetItem(productivity_text))
        
        # 操作按钮
        op_widget = QWidget()
        op_layout = QHBoxLayout(op_widget)
        op_layout.setContentsMargins(2, 2, 2, 2)
        
        edit_btn = QPushButton("编辑")
        edit_btn.setMinimumSize(50, 25)
        edit_btn.clicked.connect(lambda: self.edit_resource(row, resource['code']))
        
        delete_btn = QPushButton("删除")
        delete_btn.setMinimumSize(50, 25)
        delete_btn.clicked.connect(lambda: self.resource_table.removeRow(row))
        
        op_layout.addWidget(edit_btn)
        op_layout.addWidget(delete_btn)
        self.resource_table.setCellWidget(row, 6, op_widget)

    def edit_resource(self, row, resource_code):
        """编辑资源"""
        from ResourceDialog import ResourceDialog
        dialog = ResourceDialog(self, resource_code)
        if dialog.exec_():
            # 重新加载资源数据
            self.load_resources()
            # 更新表格中对应行
            for res in self.all_resources:
                if res['code'] == resource_code:
                    self.resource_table.item(row, 2).setText(res['name'])
                    self.resource_table.item(row, 3).setText(res['resource_group'])
                    self.resource_table.item(row, 4).setText(f"{res['capacity']} {res['capacity_unit']}")
                    
                    if res['productivity_type'] == 'per_unit_time':
                        productivity_text = f"{res['productivity_value']}个/{res['productivity_time_unit']}"
                    else:
                        productivity_text = f"{res['productivity_value']}{res['productivity_time_unit']}/每个"
                    self.resource_table.item(row, 5).setText(productivity_text)
                    break

    def add_material(self):
        """添加使用物料"""
        # 创建物料选择对话框（简化实现）
        from MaterialSelectionDialog import MaterialSelectionDialog  # 假设存在此对话框
        dialog = MaterialSelectionDialog(self, self.all_materials)
        if dialog.exec_():
            selected_materials = dialog.get_selected_materials()
            for material in selected_materials:
                self.add_material_to_table(material)

    def add_material_to_table(self, material):
        """将物料添加到表格"""
        row = self.material_table.rowCount()
        self.material_table.insertRow(row)
        
        # 序号
        self.material_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
        
        # 编码
        code_item = QTableWidgetItem(material['code'])
        code_item.setData(Qt.UserRole, material)  # 存储完整物料信息
        self.material_table.setItem(row, 1, code_item)
        
        # 名称
        self.material_table.setItem(row, 2, QTableWidgetItem(material['name']))
        
        # 数量（可编辑）
        quantity_item = QTableWidgetItem("1")
        quantity_item.setTextAlignment(Qt.AlignRight)
        quantity_item.setFlags(quantity_item.flags() | Qt.ItemIsEditable)
        self.material_table.setItem(row, 3, quantity_item)
        
        # 是否使用
        use_item = QTableWidgetItem()
        use_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
        use_item.setCheckState(Qt.Checked)
        self.material_table.setItem(row, 4, use_item)
        
        # 操作按钮
        op_widget = QWidget()
        op_layout = QHBoxLayout(op_widget)
        op_layout.setContentsMargins(2, 2, 2, 2)
        
        delete_btn = QPushButton("删除")
        delete_btn.setMinimumSize(50, 25)
        delete_btn.clicked.connect(lambda: self.material_table.removeRow(row))
        
        op_layout.addWidget(delete_btn)
        self.material_table.setCellWidget(row, 5, op_widget)

    def on_material_cell_changed(self, row, column):
        """物料表格单元格变更处理"""
        if column == 3:  # 数量列变更
            item = self.material_table.item(row, 3)
            try:
                value = float(item.text())
                if value <= 0:
                    raise ValueError()
                # 保存到数据库（实际实现中应考虑批量保存）
                material = self.material_table.item(row, 1).data(Qt.UserRole)
                self.update_material_quantity(material['code'], value)
            except ValueError:
                QMessageBox.warning(self, "输入错误", "数量必须为大于0的数字")
                item.setText("1")

    def update_material_quantity(self, material_code, quantity):
        """更新物料数量到数据库"""
        # 实际实现中应根据模板ID和物料编码更新关联表
        pass

    def load_template_data(self):
        """加载要编辑的工序模板数据"""
        db = DBConnection()
        query = "SELECT * FROM pc_process_template WHERE id = %s"
        result = db.execute_query(query, (self.template_id,))
        db.close()

        if result and len(result) > 0:
            template = result[0]
            self.code_edit.setText(template['code'])
            self.name_edit.setText(template['name'])
            
            # 前间隔时长
            self.pre_interval_edit.setValue(template['pre_interval_value'])
            self.pre_interval_unit.setCurrentText(template['pre_interval_unit'])
            
            # 后间隔时长
            self.post_interval_edit.setValue(template['post_interval_value'])
            self.post_interval_unit.setCurrentText(template['post_interval_unit'])
            
            # 工序关系
            self.relation_combo.setCurrentText(template['relation'])
            
            # 缓冲时长
            self.buffer_time_edit.setValue(template['buffer_time_value'])
            self.buffer_time_unit.setCurrentText(template['buffer_time_unit'])
            
            # 自动拆分设置
            self.allow_split_check.setChecked(template['allow_split'])
            self.min_batch_edit.setValue(template['min_batch'] or 0)
            self.max_batch_edit.setValue(template['max_batch'] or 0)
            self.split_threshold_edit.setValue(template['split_threshold'] or 0)
            self.split_strategy_combo.setCurrentText(template['split_strategy'] or "")
            self.base_number_edit.setValue(template['base_number'] or 1)
            
            # 换型配置
            self.changeover_time_edit.setValue(template['changeover_time_value'] or 0)
            self.changeover_time_unit.setCurrentText(template['changeover_time_unit'] or "分")
            
            # 加载主资源
            self.load_template_resources()
            
            # 加载使用物料
            self.load_template_materials()

    def load_template_resources(self):
        """加载模板关联的主资源"""
        db = DBConnection()
        query = "SELECT r.* FROM pc_template_resources tr JOIN pc_resource r ON tr.resource_code = r.code WHERE tr.template_id = %s"
        resources = db.execute_query(query, (self.template_id,))
        db.close()
        
        if resources is None:
            resources = []

        for resource in resources:
            self.add_resource_to_table(resource)

    def load_template_materials(self):
        """加载模板关联的使用物料"""
        db = DBConnection()
        query = "SELECT m.*, tm.quantity, tm.is_used FROM pc_template_materials tm JOIN pc_material m ON tm.material_code = m.code WHERE tm.template_id = %s"
        materials = db.execute_query(query, (self.template_id,))
        db.close()
        
        if materials is None:
            materials=[]

        for material in materials:
            row = self.material_table.rowCount()
            self.material_table.insertRow(row)
            
            # 序号
            self.material_table.setItem(row, 0, QTableWidgetItem(str(row + 1)))
            
            # 编码
            code_item = QTableWidgetItem(material['code'])
            code_item.setData(Qt.UserRole, material)
            self.material_table.setItem(row, 1, code_item)
            
            # 名称
            self.material_table.setItem(row, 2, QTableWidgetItem(material['name']))
            
            # 数量
            quantity_item = QTableWidgetItem(str(material['quantity']))
            quantity_item.setTextAlignment(Qt.AlignRight)
            quantity_item.setFlags(quantity_item.flags() | Qt.ItemIsEditable)
            self.material_table.setItem(row, 3, quantity_item)
            
            # 是否使用
            use_item = QTableWidgetItem()
            use_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            use_item.setCheckState(Qt.Checked if material['is_used'] else Qt.Unchecked)
            self.material_table.setItem(row, 4, use_item)
            
            # 操作按钮
            op_widget = QWidget()
            op_layout = QHBoxLayout(op_widget)
            op_layout.setContentsMargins(2, 2, 2, 2)
            
            delete_btn = QPushButton("删除")
            delete_btn.setMinimumSize(50, 25)
            delete_btn.clicked.connect(lambda: self.material_table.removeRow(row))
            
            op_layout.addWidget(delete_btn)
            self.material_table.setCellWidget(row, 5, op_widget)

    def submit(self):
        """验证并提交数据"""
        code = self.code_edit.text().strip()
        name = self.name_edit.text().strip()
        
        # 验证必填字段
        if not code or not name:
            QMessageBox.warning(self, "输入错误", "工序编码和名称不能为空")
            return
            
        # 验证至少选择了一个主资源
        if self.resource_table.rowCount() == 0:
            QMessageBox.warning(self, "输入错误", "请至少选择一个主资源")
            return
        
        # 收集数据
        data = {
            'code': code,
            'name': name,
            'pre_interval_value': self.pre_interval_edit.value(),
            'pre_interval_unit': self.pre_interval_unit.currentText(),
            'post_interval_value': self.post_interval_edit.value(),
            'post_interval_unit': self.post_interval_unit.currentText(),
            'relation': self.relation_combo.currentText(),
            'buffer_time_value': self.buffer_time_edit.value(),
            'buffer_time_unit': self.buffer_time_unit.currentText(),
            'allow_split': self.allow_split_check.isChecked(),
            'min_batch': self.min_batch_edit.value() if self.min_batch_edit.value() > 0 else None,
            'max_batch': self.max_batch_edit.value() if self.max_batch_edit.value() > 0 else None,
            'split_threshold': self.split_threshold_edit.value() if self.split_threshold_edit.value() > 0 else None,
            'split_strategy': self.split_strategy_combo.currentText() or None,
            'base_number': self.base_number_edit.value() if self.split_strategy_combo.currentText() == "基准数拆分" else None,
            'changeover_time_value': self.changeover_time_edit.value(),
            'changeover_time_unit': self.changeover_time_unit.currentText()
        }
        
        # 收集主资源数据
        resources = []
        for row in range(self.resource_table.rowCount()):
            code = self.resource_table.item(row, 1).text()
            resources.append(code)
            
        # 收集物料数据
        materials = []
        for row in range(self.material_table.rowCount()):
            code = self.material_table.item(row, 1).text()
            quantity = float(self.material_table.item(row, 3).text())
            is_used = self.material_table.item(row, 4).checkState() == Qt.Checked
            materials.append({
                'code': code,
                'quantity': quantity,
                'is_used': is_used
            })
        
        # 保存数据
        db = DBConnection()
        try:
            db.begin_transaction()
            
            if self.template_id:
                # 编辑模式
                query = """
                UPDATE pc_process_template SET code = %s, name = %s, pre_interval_value = %s,
                pre_interval_unit = %s, post_interval_value = %s, post_interval_unit = %s,
                relation = %s, buffer_time_value = %s, buffer_time_unit = %s,
                allow_split = %s, min_batch = %s, max_batch = %s, split_threshold = %s,
                split_strategy = %s, base_number = %s, changeover_time_value = %s,
                changeover_time_unit = %s WHERE id = %s
                """
                params = (
                    data['code'], data['name'], data['pre_interval_value'],
                    data['pre_interval_unit'], data['post_interval_value'], data['post_interval_unit'],
                    data['relation'], data['buffer_time_value'], data['buffer_time_unit'],
                    data['allow_split'], data['min_batch'], data['max_batch'], data['split_threshold'],
                    data['split_strategy'], data['base_number'], data['changeover_time_value'],
                    data['changeover_time_unit'], self.template_id
                )
                db.execute_update(query, params)
                
                # 删除原有资源关联
                db.execute_update("DELETE FROM pc_template_resources WHERE template_id = %s", (self.template_id,))
                # 删除原有物料关联
                db.execute_update("DELETE FROM pc_template_materials WHERE template_id = %s", (self.template_id,))
            else:
                # 新增模式，先检查编码是否已存在
                check_query = "SELECT code FROM pc_process_template WHERE code = %s"
                exists = db.execute_query(check_query, (code,))
                if exists and len(exists) > 0:
                    db.rollback()
                    db.close()
                    QMessageBox.warning(self, "错误", f"编码 {code} 已存在")
                    return

                # 插入新记录
                query = """
                INSERT INTO pc_process_template 
                (code, name, pre_interval_value, pre_interval_unit, post_interval_value, 
                 post_interval_unit, relation, buffer_time_value, buffer_time_unit,
                 allow_split, min_batch, max_batch, split_threshold, split_strategy, 
                 base_number, changeover_time_value, changeover_time_unit)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                params = (
                    data['code'], data['name'], data['pre_interval_value'],
                    data['pre_interval_unit'], data['post_interval_value'], data['post_interval_unit'],
                    data['relation'], data['buffer_time_value'], data['buffer_time_unit'],
                    data['allow_split'], data['min_batch'], data['max_batch'], data['split_threshold'],
                    data['split_strategy'], data['base_number'], data['changeover_time_value'],
                    data['changeover_time_unit']
                )
                self.template_id = db.execute_update(query, params)
            
            # 插入资源关联
            for res_code in resources:
                db.execute_update(
                    "INSERT INTO pc_template_resources (template_id, resource_code) VALUES (%s, %s)",
                    (self.template_id, res_code)
                )
            
            # 插入物料关联
            for mat in materials:
                db.execute_update(
                    "INSERT INTO pc_template_materials (template_id, material_code, quantity, is_used) VALUES (%s, %s, %s, %s)",
                    (self.template_id, mat['code'], mat['quantity'], mat['is_used'])
                )
            
            db.commit()
            QMessageBox.information(self, "成功", "操作成功")
            self.accept()
        except Exception as e:
            db.rollback()
            QMessageBox.warning(self, "失败", f"操作失败：{str(e)}")
        finally:
            db.close()