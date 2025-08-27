# 资源选择对话框
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView)
from PyQt5.QtCore import Qt

class ResourceSelectionDialog(QDialog):
    def __init__(self, parent=None, resources=None):
        super().__init__(parent)
        self.resources = resources or []
        self.selected_resources = []
        self.setWindowTitle("选择主资源")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 说明标签
        label = QLabel("请选择主资源（可多选）：")
        layout.addWidget(label)
        
        # 资源表格
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["选择", "编码", "名称", "资源组", "产能"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        layout.addWidget(self.table)
        
        # 按钮布局
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
        self.load_resources()

    def load_resources(self):
        """加载资源数据"""
        self.table.setRowCount(0)
        for row, resource in enumerate(self.resources):
            self.table.insertRow(row)
            
            # 选择框
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, check_item)
            
            # 编码
            self.table.setItem(row, 1, QTableWidgetItem(resource['code']))
            
            # 名称
            self.table.setItem(row, 2, QTableWidgetItem(resource['name']))
            
            # 资源组
            self.table.setItem(row, 3, QTableWidgetItem(resource['resource_group']))
            
            # 产能
            if resource['productivity_type'] == 'per_unit_time':
                productivity_text = f"{resource['productivity_value']}{resource['productivity_time_unit']}/个"
            else:
                productivity_text = f"{resource['productivity_value']}个/{resource['productivity_time_unit']}"
            self.table.setItem(row, 4, QTableWidgetItem(productivity_text))
        
        self.table.resizeColumnsToContents()

    def get_selected_resources(self):
        """获取选中的资源"""
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                code = self.table.item(row, 1).text()
                # 查找完整资源信息
                for res in self.resources:
                    if res['code'] == code:
                        selected.append(res)
                        break
        return selected