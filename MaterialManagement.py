from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLineEdit,
                            QComboBox, QLabel, QGroupBox, QMessageBox)
from PyQt5.QtCore import Qt
from MaterialDialog import MaterialDialog
from DBConnection import DBConnection


# 物料管理主窗口
class MaterialManagement(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("物料管理")
        #self.setMinimumSize(1200, 700)  # 适当增大窗口最小尺寸
        
        self.init_ui()
        self.load_materials()

    def init_ui(self):
        # 主Widget和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)  # 主布局内边距
        main_layout.setSpacing(10)  # 主布局控件间距
        
        # 顶部区域容器
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)  # 去除容器内边距
        top_layout.setSpacing(10)  # 容器内控件间距
        
        # 1. 查询区域（无名称）
        query_container = QWidget()
        query_layout = QHBoxLayout(query_container)
        query_layout.setContentsMargins(0, 0, 0, 0)
        query_layout.setSpacing(15)  # 查询条件间距
        
        # 查询条件1：编号
        query_layout.addWidget(QLabel("编号:"))
        self.query_code = QLineEdit()
        self.query_code.setMaximumWidth(120)
        query_layout.addWidget(self.query_code)

        # 查询条件2：名称
        query_layout.addWidget(QLabel("名称:"))
        self.query_name = QLineEdit()
        self.query_name.setMaximumWidth(120)
        query_layout.addWidget(self.query_name)

        # 查询条件3：类型
        query_layout.addWidget(QLabel("类型:"))
        self.query_type = QComboBox()
        self.query_type.addItems(["", "成品", "半成品", "原材料"])
        self.query_type.setMaximumWidth(100)
        query_layout.addWidget(self.query_type)

        # 查询条件4：来源
        query_layout.addWidget(QLabel("来源:"))
        self.query_source = QComboBox()
        self.query_source.addItems(["", "采购", "制造"])
        self.query_source.setMaximumWidth(100)
        query_layout.addWidget(self.query_source)

        # 查询条件5：是否参与齐套计算
        query_layout.addWidget(QLabel("齐套计算:"))
        self.query_include_set = QComboBox()
        self.query_include_set.addItems(["", "是", "否"])
        self.query_include_set.setMaximumWidth(80)
        query_layout.addWidget(self.query_include_set)

        # 查询条件6：库存状态
        query_layout.addWidget(QLabel("库存状态:"))
        self.query_stock_status = QComboBox()
        self.query_stock_status.addItems(["", "正常", "低于安全库存"])
        self.query_stock_status.setMaximumWidth(100)
        query_layout.addWidget(self.query_stock_status)

        # 查询按钮
        self.query_btn = QPushButton("查询")
        self.query_btn.clicked.connect(self.load_materials)
        query_layout.addWidget(self.query_btn)
        
        # 重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_query)
        query_layout.addWidget(self.reset_btn)
        
        # 添加伸缩项，将按钮推到右侧
        query_layout.addStretch()
        
        top_layout.addWidget(query_container)  # 添加查询区域到顶部容器
        
        # 2. 操作按钮区域（无名称）
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)  # 按钮间距
        
        self.add_btn = QPushButton("新增物料")
        self.add_btn.clicked.connect(self.add_material)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑物料")
        self.edit_btn.clicked.connect(self.edit_selected_material)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除物料")
        self.delete_btn.clicked.connect(self.delete_selected_material)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()  # 推到左侧
        
        top_layout.addWidget(btn_container)  # 添加按钮区域到顶部容器
        
        # 将顶部容器添加到主布局
        main_layout.addWidget(top_container)
        
        # 物料列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(12)
        self.table.setHorizontalHeaderLabels([
            "选择", "编码", "名称", "类型", "来源", "库存", "安全库存",
            "计量单位", "提前期", "缓冲期", "参与齐套计算", "拓展字段"
        ])
        # 设置表格属性
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.itemChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.table)  # 表格添加到主布局
        main_layout.setStretch(1, 1)  # 让表格占满剩余空间

    def reset_query(self):
        """重置查询条件"""
        self.query_code.clear()
        self.query_name.clear()
        self.query_type.setCurrentIndex(0)
        self.query_source.setCurrentIndex(0)
        self.query_include_set.setCurrentIndex(0)
        self.query_stock_status.setCurrentIndex(0)

    def on_cell_clicked(self, row, column):
        if column != 0:
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

    def on_item_changed(self, item):
        if item.column() == 0:
            row = item.row()
            if item.checkState() == Qt.Checked:
                self.table.selectRow(row)
            else:
                self.table.selectionModel().clearSelection()
            self.update_button_states()

    def update_button_states(self):
        selected_rows = self.get_selected_rows()
        self.delete_btn.setEnabled(len(selected_rows) > 0)
        self.edit_btn.setEnabled(len(selected_rows) == 1)

    def get_selected_rows(self):
        selected_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                selected_rows.append(row)
        return selected_rows

    def load_materials(self):
        # 获取查询条件
        code = self.query_code.text().strip()
        name = self.query_name.text().strip()
        type_ = self.query_type.currentText()
        source = self.query_source.currentText()
        include_set = self.query_include_set.currentText()
        stock_status = self.query_stock_status.currentText()

        # 构建查询条件
        where_clause = []
        params = []

        if code:
            where_clause.append("code LIKE %s")
            params.append(f"%{code}%")
        if name:
            where_clause.append("name LIKE %s")
            params.append(f"%{name}%")
        if type_:
            where_clause.append("type = %s")
            params.append(type_)
        if source:
            where_clause.append("source = %s")
            params.append(source)
        if include_set:
            where_clause.append("include_in_set = %s")
            params.append(include_set == "是")
        if stock_status == "低于安全库存":
            where_clause.append("stock < safety_stock")
        elif stock_status == "正常":
            where_clause.append("stock >= safety_stock")

        # 构建SQL查询
        query = "SELECT * FROM pc_material"
        if where_clause:
            query += " WHERE " + " AND ".join(where_clause)

        # 执行查询
        db = DBConnection()
        materials = db.execute_query(query, params)
        db.close()

        # 填充表格
        self.table.setRowCount(0)
        if materials:
            for row, material in enumerate(materials):
                self.table.insertRow(row)
                
                # 添加复选框
                check_item = QTableWidgetItem()
                check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                check_item.setCheckState(Qt.Unchecked)
                self.table.setItem(row, 0, check_item)
                
                # 填充其他数据
                self.table.setItem(row, 1, QTableWidgetItem(material['code']))
                self.table.setItem(row, 2, QTableWidgetItem(material['name']))
                self.table.setItem(row, 3, QTableWidgetItem(material['type']))
                self.table.setItem(row, 4, QTableWidgetItem(material['source']))
                self.table.setItem(row, 5, QTableWidgetItem(str(material['stock'])))
                self.table.setItem(row, 6, QTableWidgetItem(str(material['safety_stock'])))
                self.table.setItem(row, 7, QTableWidgetItem(material['unit']))
                self.table.setItem(row, 8, QTableWidgetItem(str(material['lead_time'])))
                self.table.setItem(row, 9, QTableWidgetItem(str(material['buffer_time'])))
                self.table.setItem(row, 10, QTableWidgetItem("是" if material['include_in_set'] else "否"))
                self.table.setItem(row, 11, QTableWidgetItem(material['extra_fields'] or ""))

        self.table.resizeColumnsToContents()
        self.update_button_states()

    def add_material(self):
        dialog = MaterialDialog(self)
        if dialog.exec_():
            self.load_materials()

    def edit_selected_material(self):
        selected_rows = self.get_selected_rows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "提示", "请选择一行进行编辑")
            return
            
        row = selected_rows[0]
        code = self.table.item(row, 1).text()
        dialog = MaterialDialog(self, code)
        if dialog.exec_():
            self.load_materials()

    def delete_selected_material(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的物料")
            return
            
        material_info = []
        for row in selected_rows:
            code = self.table.item(row, 1).text()
            name = self.table.item(row, 2).text()
            material_info.append(f"{code} - {name}")
        
        confirm = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除以下{len(selected_rows)}个物料吗？\n{chr(10).join(material_info)}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            db = DBConnection()
            success = True
            
            for row in selected_rows:
                code = self.table.item(row, 1).text()
                query = "DELETE FROM pc_material WHERE code = %s"
                if not db.execute_update(query, (code,)):
                    success = False
                    break
                    
            db.close()

            if success:
                QMessageBox.information(self, "成功", f"已成功删除{len(selected_rows)}个物料")
                self.load_materials()
            else:
                QMessageBox.warning(self, "失败", "删除过程中发生错误，请重试")
