# 工序模板管理主窗口
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
                             QTableWidgetItem, QPushButton, QLabel, QLineEdit, QComboBox,
                             QMessageBox, QHeaderView, QCheckBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont
from DBConnection import DBConnection
from ProcessTemplateDialog import ProcessTemplateDialog

class ProcessTemplateManagement(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("工序模板管理")
        #self.setMinimumSize(1200, 700)
        
        self.init_ui()
        self.load_templates()

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
        
        # 查询条件1：工序编码
        query_layout.addWidget(QLabel("工序编码:"))
        self.query_code = QLineEdit()
        self.query_code.setMaximumWidth(120)
        query_layout.addWidget(self.query_code)

        # 查询条件2：工序名称
        query_layout.addWidget(QLabel("工序名称:"))
        self.query_name = QLineEdit()
        self.query_name.setMaximumWidth(120)
        query_layout.addWidget(self.query_name)

        # 查询条件3：工序关系
        query_layout.addWidget(QLabel("工序关系:"))
        self.query_relation = QComboBox()
        self.query_relation.addItems(["", "ES", "EE"])
        self.query_relation.setMaximumWidth(100)
        query_layout.addWidget(self.query_relation)

        # 查询按钮
        self.query_btn = QPushButton("查询")
        self.query_btn.clicked.connect(self.load_templates)
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
        
        self.add_btn = QPushButton("新增工序模板")
        self.add_btn.clicked.connect(self.add_template)
        btn_layout.addWidget(self.add_btn)
        
        self.edit_btn = QPushButton("编辑工序模板")
        self.edit_btn.clicked.connect(self.edit_selected_template)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)
        
        self.delete_btn = QPushButton("删除工序模板")
        self.delete_btn.clicked.connect(self.delete_selected_templates)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)
        
        btn_layout.addStretch()
        
        top_layout.addWidget(btn_container)
        
        main_layout.addWidget(top_container)
        
        # 工序模板列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(9)
        self.table.setHorizontalHeaderLabels([
            "选择", "工序编码", "工序名称", "工序关系", "前间隔时长", 
            "后间隔时长", "缓冲时长", "主资源数", "使用物料数"
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

    def reset_query(self):
        """重置查询条件"""
        self.query_code.clear()
        self.query_name.clear()
        self.query_relation.setCurrentIndex(0)

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

    def load_templates(self):
        """加载工序模板数据"""
        # 获取查询条件
        code = self.query_code.text().strip()
        name = self.query_name.text().strip()
        relation = self.query_relation.currentText()

        # 构建查询条件
        where_clause = []
        params = []

        if code:
            where_clause.append("code LIKE %s")
            params.append(f"%{code}%")
        if name:
            where_clause.append("name LIKE %s")
            params.append(f"%{name}%")
        if relation:
            where_clause.append("relation = %s")
            params.append(relation)

        # 构建SQL查询
        query = """
        SELECT t.*, 
               (SELECT COUNT(*) FROM pc_template_resources tr WHERE tr.template_id = t.id) as resource_count,
               (SELECT COUNT(*) FROM pc_template_materials tm WHERE tm.template_id = t.id) as material_count
        FROM pc_process_template t
        """
        if where_clause:
            query += " WHERE " + " AND ".join(where_clause)
        query += " ORDER BY created_at DESC"

        # 执行查询
        db = DBConnection()
        templates = db.execute_query(query, params)
        db.close()

        # 填充表格
        self.table.setRowCount(0)
        if templates:
            for row, template in enumerate(templates):
                self.table.insertRow(row)
                
                # 添加复选框
                check_item = QTableWidgetItem()
                check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                check_item.setCheckState(Qt.Unchecked)
                self.table.setItem(row, 0, check_item)
                
                # 工序编码
                self.table.setItem(row, 1, QTableWidgetItem(template['code']))
                
                # 工序名称
                self.table.setItem(row, 2, QTableWidgetItem(template['name']))
                
                # 工序关系
                self.table.setItem(row, 3, QTableWidgetItem(template['relation']))
                
                # 前间隔时长
                pre_interval = f"{template['pre_interval_value']} {template['pre_interval_unit']}"
                self.table.setItem(row, 4, QTableWidgetItem(pre_interval))
                
                # 后间隔时长
                post_interval = f"{template['post_interval_value']} {template['post_interval_unit']}"
                self.table.setItem(row, 5, QTableWidgetItem(post_interval))
                
                # 缓冲时长
                buffer_time = f"{template['buffer_time_value']} {template['buffer_time_unit']}"
                self.table.setItem(row, 6, QTableWidgetItem(buffer_time))
                
                # 主资源数
                self.table.setItem(row, 7, QTableWidgetItem(str(template['resource_count'] or 0)))
                
                # 使用物料数
                self.table.setItem(row, 8, QTableWidgetItem(str(template['material_count'] or 0)))

        self.table.resizeColumnsToContents()
        self.update_button_states()

    def add_template(self):
        """新增工序模板"""
        dialog = ProcessTemplateDialog(self)
        if dialog.exec_():
            self.load_templates()

    def edit_selected_template(self):
        """编辑选中的工序模板"""
        selected_rows = self.get_selected_rows()
        if len(selected_rows) != 1:
            QMessageBox.warning(self, "提示", "请选择一行进行编辑")
            return
            
        row = selected_rows[0]
        # 获取模板ID（实际应用中可能需要从数据库获取）
        code = self.table.item(row, 1).text()
        
        # 查询获取模板ID
        db = DBConnection()
        query = "SELECT id FROM pc_process_template WHERE code = %s"
        result = db.execute_query(query, (code,))
        db.close()
        
        if result and len(result) > 0:
            template_id = result[0]['id']
            dialog = ProcessTemplateDialog(self, template_id)
            if dialog.exec_():
                self.load_templates()
        else:
            QMessageBox.warning(self, "错误", "未找到选中的工序模板")

    def delete_selected_templates(self):
        """删除选中的工序模板"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            QMessageBox.warning(self, "提示", "请先选择要删除的工序模板")
            return
            
        # 收集要删除的模板信息
        template_info = []
        template_ids = []
        
        # 先获取模板ID
        codes = [self.table.item(row, 1).text() for row in selected_rows]
        
        db = DBConnection()
        query = "SELECT id, code, name FROM pc_process_template WHERE code IN ({})".format(
            ', '.join(['%s'] * len(codes))
        )
        result = db.execute_query(query, codes)
        db.close()
        
        if result:
            for item in result:
                template_ids.append(item['id'])
                template_info.append(f"{item['code']} - {item['name']}")
        
        if not template_ids:
            QMessageBox.warning(self, "错误", "未找到选中的工序模板")
            return
        
        confirm = QMessageBox.question(
            self, "确认删除", 
            f"确定要删除以下{len(template_info)}个工序模板吗？\n{chr(10).join(template_info)}",
            QMessageBox.Yes | QMessageBox.No, QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            db = DBConnection()
            try:
                db.begin_transaction()
                
                # 删除模板关联数据
                db.execute_update(
                    "DELETE FROM pc_template_resources WHERE template_id IN ({})".format(
                        ', '.join(['%s'] * len(template_ids))
                    ), tuple(template_ids)
                )
                
                db.execute_update(
                    "DELETE FROM pc_template_materials WHERE template_id IN ({})".format(
                        ', '.join(['%s'] * len(template_ids))
                    ), tuple(template_ids)
                )
                
                # 删除模板本身
                db.execute_update(
                    "DELETE FROM pc_process_template WHERE id IN ({})".format(
                        ', '.join(['%s'] * len(template_ids))
                    ), tuple(template_ids)
                )
                
                db.commit()
                QMessageBox.information(self, "成功", "删除成功")
                self.load_templates()
            except Exception as e:
                db.rollback()
                QMessageBox.warning(self, "失败", f"删除失败：{str(e)}")
            finally:
                db.close()