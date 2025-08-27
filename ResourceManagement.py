from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                            QPushButton, QTableWidget, QTableWidgetItem, QLineEdit,
                            QComboBox, QLabel, QMessageBox)
from PyQt5.QtCore import Qt
from ResourceDialog import ResourceDialog
from DBConnection import DBConnection


# 资源管理主窗口
class ResourceManagement(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("资源管理")
        #self.setMinimumSize(1200, 700)
        
        self.init_ui()
        self.load_resources()

    def init_ui(self):
        # 主Widget和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)
        
        # 顶部区域容器
        top_container = QWidget()
        top_layout = QVBoxLayout(top_container)
        top_layout.setContentsMargins(0, 0, 0, 0)
        top_layout.setSpacing(10)
        
        # 1. 查询区域
        query_container = QWidget()
        query_layout = QHBoxLayout(query_container)
        query_layout.setContentsMargins(0, 0, 0, 0)
        query_layout.setSpacing(15)
        
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

        # 查询条件3：资源组
        query_layout.addWidget(QLabel("资源组:"))
        self.query_group = QComboBox()
        self.query_group.addItem("")
        # 动态加载资源组选项
        self.load_resource_groups()
        self.query_group.setMaximumWidth(120)
        query_layout.addWidget(self.query_group)

        # 查询条件4：状态
        query_layout.addWidget(QLabel("状态:"))
        self.query_status = QComboBox()
        self.query_status.addItems(["", "正常", "报废", "维修"])
        self.query_status.setMaximumWidth(100)
        query_layout.addWidget(self.query_status)

        # 查询按钮
        self.query_btn = QPushButton("查询")
        self.query_btn.clicked.connect(self.load_resources)
        query_layout.addWidget(self.query_btn)
        
        # 重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_query)
        query_layout.addWidget(self.reset_btn)
        
        query_layout.addStretch()
        
        top_layout.addWidget(query_container)
        
        # 2. 操作按钮区域
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(10)
        
        self.add_btn = QPushButton("新增主资源")
        self.add_btn.clicked.connect(self.add_resource)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑资源")
        self.edit_btn.clicked.connect(self.edit_selected_resource)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除资源")
        self.delete_btn.clicked.connect(self.delete_selected_resource)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        top_layout.addWidget(btn_container)
        
        main_layout.addWidget(top_container)
        
        # 资源列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "选择", "编码", "名称", "资源组", "容量", "状态", 
            "产能", "创建时间", "更新时间"
        ])
        # 设置表格属性
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.itemChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.table)
        main_layout.setStretch(1, 1)

    def load_resource_groups(self):
        """加载所有资源组作为查询选项"""
        db = DBConnection()
        query = "SELECT DISTINCT resource_group FROM pc_resource ORDER BY resource_group"
        result = db.execute_query(query)
        db.close()
        
        if result:
            for item in result:
                self.query_group.addItem(item['resource_group'])

    def reset_query(self):
        """重置查询条件"""
        self.query_code.clear()
        self.query_name.clear()
        self.query_group.setCurrentIndex(0)
        self.query_status.setCurrentIndex(0)

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

    def load_resources(self):
        # 获取查询条件
        code = self.query_code.text().strip()
        name = self.query_name.text().strip()
        group = self.query_group.currentText()
        status = self.query_status.currentText()

        # 构建查询条件
        where_clause = []
        params = []

        if code:
            where_clause.append("code LIKE %s")
            params.append(f"%{code}%")
        if name:
            where_clause.append("name LIKE %s")
            params.append(f"%{name}%")
        if group:
            where_clause.append("resource_group = %s")
            params.append(group)
        if status:
            where_clause.append("status = %s")
            params.append(status)

        # 构建SQL查询
        query = "SELECT * FROM pc_resource"
        if where_clause:
            query += " WHERE " + " AND ".join(where_clause)
        query += " ORDER BY updated_at DESC"

        # 执行查询
        db = DBConnection()
        resources = db.execute_query(query, params)
        db.close()

        # 填充表格
        self.table.setRowCount(0)
        if resources:
            for row, resource in enumerate(resources):
                self.table.insertRow(row)
                
                # 添加复选框
                check_item = QTableWidgetItem()
                check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                check_item.setCheckState(Qt.Unchecked)
                self.table.setItem(row, 0, check_item)
                
                # 产能显示处理
                if resource['productivity_type'] == 'per_unit_time':
                    productivity_text = f"{resource['productivity_value']}{resource['productivity_time_unit']}/个"                    
                else:
                    productivity_text = f"{resource['productivity_value']}个/{resource['productivity_time_unit']}"
                
                # 填充其他数据
                self.table.setItem(row, 1, QTableWidgetItem(resource['code']))
                self.table.setItem(row, 2, QTableWidgetItem(resource['name']))
                self.table.setItem(row, 3, QTableWidgetItem(resource['resource_group']))
                self.table.setItem(row, 4, QTableWidgetItem(f"{resource['capacity']} {resource['capacity_unit']}"))
                self.table.setItem(row, 5, QTableWidgetItem(resource['status']))
                self.table.setItem(row, 6, QTableWidgetItem(productivity_text))
                self.table.setItem(row, 7, QTableWidgetItem(str(resource['created_at'])))
                self.table.setItem(row, 8, QTableWidgetItem(str(resource['updated_at'])))

        self.table.resizeColumnsToContents()
        self.update_button_states()

    def add_resource(self):
        dialog = ResourceDialog(self)
        if dialog.exec_():
            self.load_resources()
            # 刷新资源组下拉列表
            self.query_group.clear()
            self.query_group.addItem("")
            self.load_resource_groups()

    def edit_selected_resource(self):
        selected_rows = self.get_selected_rows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "提示", "请选择一行进行编辑")
            return
            
        row = selected_rows[0]
        code = self.table.item(row, 1).text()
        dialog = ResourceDialog(self, code)
        if dialog.exec_():
            self.load_resources()

    def delete_selected_resource(self):
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的资源")
            return
            
        resource_info = []
        for row in selected_rows:
            code = self.table.item(row, 1).text()
            name = self.table.item(row, 2).text()
            resource_info.append(f"{code} - {name}")
        
        confirm = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除以下{len(selected_rows)}个资源吗？\n{chr(10).join(resource_info)}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            db = DBConnection()
            success = True
            
            for row in selected_rows:
                code = self.table.item(row, 1).text()
                query = "DELETE FROM pc_resource WHERE code = %s"
                if not db.execute_update(query, (code,)):
                    success = False
                    break
                    
            db.close()

            if success:
                QMessageBox.information(self, "成功", f"已成功删除{len(selected_rows)}个资源")
                self.load_resources()
                # 刷新资源组下拉列表
                self.query_group.clear()
                self.query_group.addItem("")
                self.load_resource_groups()
            else:
                QMessageBox.warning(self, "失败", "删除过程中发生错误，请重试")