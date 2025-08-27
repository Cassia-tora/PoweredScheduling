# 物料选择对话框
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QHeaderView,
                             QLineEdit, QFormLayout)
from PyQt5.QtCore import Qt

class MaterialSelectionDialog(QDialog):
    def __init__(self, parent=None, materials=None):
        super().__init__(parent)
        self.materials = materials or []
        self.filtered_materials = materials or []
        self.selected_materials = []
        self.setWindowTitle("选择使用物料")
        self.setMinimumSize(600, 400)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()
        
        # 过滤区域
        filter_layout = QFormLayout()
        self.code_filter = QLineEdit()
        self.code_filter.textChanged.connect(self.filter_materials)
        self.name_filter = QLineEdit()
        self.name_filter.textChanged.connect(self.filter_materials)
        
        filter_layout.addRow("编码过滤:", self.code_filter)
        filter_layout.addRow("名称过滤:", self.name_filter)
        layout.addLayout(filter_layout)
        
        # 说明标签
        label = QLabel("请选择使用物料（可多选）：")
        layout.addWidget(label)
        
        # 物料表格
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["选择", "编码", "名称", "类型"])
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
        self.load_materials()

    def filter_materials(self):
        """过滤物料"""
        code = self.code_filter.text().lower()
        name = self.name_filter.text().lower()
        
        self.filtered_materials = []
        for mat in self.materials:
            if (code in mat['code'].lower() or not code) and \
               (name in mat['name'].lower() or not name):
                self.filtered_materials.append(mat)
        
        self.load_materials()

    def load_materials(self):
        """加载物料数据"""
        self.table.setRowCount(0)
        for row, material in enumerate(self.filtered_materials):
            self.table.insertRow(row)
            
            # 选择框
            check_item = QTableWidgetItem()
            check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
            check_item.setCheckState(Qt.Unchecked)
            self.table.setItem(row, 0, check_item)
            
            # 编码
            self.table.setItem(row, 1, QTableWidgetItem(material['code']))
            
            # 名称
            self.table.setItem(row, 2, QTableWidgetItem(material['name']))
            
            # 类型
            self.table.setItem(row, 3, QTableWidgetItem(material['type']))
        
        self.table.resizeColumnsToContents()

    def get_selected_materials(self):
        """获取选中的物料"""
        selected = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                code = self.table.item(row, 1).text()
                # 查找完整物料信息
                for mat in self.filtered_materials:
                    if mat['code'] == code:
                        selected.append(mat)
                        break
        return selected