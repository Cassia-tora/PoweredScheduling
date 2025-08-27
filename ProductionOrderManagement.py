from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
                            QComboBox, QPushButton, QTableWidget, QTableWidgetItem, 
                            QHeaderView, QMessageBox, QCheckBox, QDialog, QRadioButton,QStyledItemDelegate)
from PyQt5.QtCore import Qt, QSize, QRect
from PyQt5.QtGui import QColor, QPainter
from DBConnection import DBConnection
from ProductionOrderDialog import ProductionOrderDialog

# 自定义颜色块委托（固定宽度）
class ColorBlockDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # 获取颜色值
        color_str = index.data(Qt.UserRole)  # 从UserRole获取颜色值
        if not color_str:
            super().paint(painter, option, index)
            return
            
        # 绘制固定宽度的颜色块（100px）
        painter.save()
        
        # 计算颜色块位置（居中显示）
        block_rect = QRect(
            option.rect.center().x() - 50,  # 左侧位置（固定宽度100px的一半）
            option.rect.top() + 2,          # 顶部位置（留2px边距）
            100,                            # 固定宽度
            option.rect.height() - 4        # 高度（留4px上下边距）
        )
        
        # 绘制颜色块背景
        painter.fillRect(block_rect, QColor(color_str))
        
        # 绘制边框
        painter.setPen(QColor(0, 0, 0, 50))  # 半透明边框
        painter.drawRect(block_rect)
        
        painter.restore()

    def sizeHint(self, option, index):
        # 提示单元格尺寸（宽度100px）
        return QSize(100, 24)

class ProductionOrderManagement(QWidget):
    def __init__(self):
        super().__init__()
        
        self.init_ui()
        self.load_orders()

    def init_ui(self):
        # 主布局
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 顶部查询区域
        query_layout = QHBoxLayout()
        query_layout.setSpacing(15)

        # 订单号查询
        query_layout.addWidget(QLabel("订单号:"))
        self.query_order_no = QLineEdit()
        self.query_order_no.setMaximumWidth(120)
        query_layout.addWidget(self.query_order_no)

        # 排产状态查询
        query_layout.addWidget(QLabel("排产状态:"))
        self.query_scheduling_status = QComboBox()
        self.query_scheduling_status.addItems(["", "未排产", "已排产"])
        self.query_scheduling_status.setMaximumWidth(100)
        query_layout.addWidget(self.query_scheduling_status)

        # 订单状态查询
        query_layout.addWidget(QLabel("订单状态:"))
        self.query_status = QComboBox()
        self.query_status.addItems(["", "待处理", "已取消", "已完成"])
        self.query_status.setMaximumWidth(100)
        query_layout.addWidget(self.query_status)

        # 优先级查询
        query_layout.addWidget(QLabel("优先级:"))
        self.query_priority = QComboBox()
        self.query_priority.addItems(["", "P1", "P2", "P3", "P4", "P5"])
        self.query_priority.setMaximumWidth(80)
        query_layout.addWidget(self.query_priority)

        # 查询按钮
        self.query_btn = QPushButton("查询")
        self.query_btn.clicked.connect(self.load_orders)
        query_layout.addWidget(self.query_btn)

        # 重置按钮
        self.reset_btn = QPushButton("重置")
        self.reset_btn.clicked.connect(self.reset_query)
        query_layout.addWidget(self.reset_btn)

        query_layout.addStretch()
        main_layout.addLayout(query_layout)

        # 操作按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.add_btn = QPushButton("新增订单")
        self.add_btn.clicked.connect(self.add_order)
        btn_layout.addWidget(self.add_btn)

        self.edit_btn = QPushButton("编辑订单")
        self.edit_btn.clicked.connect(self.edit_selected_order)
        self.edit_btn.setEnabled(False)
        btn_layout.addWidget(self.edit_btn)

        self.delete_btn = QPushButton("删除订单")
        self.delete_btn.clicked.connect(self.delete_selected_orders)
        self.delete_btn.setEnabled(False)
        btn_layout.addWidget(self.delete_btn)

        # 修改按钮文本和点击事件
        self.batch_scheduling_btn = QPushButton("批量设置排产")
        self.batch_scheduling_btn.clicked.connect(self.show_batch_scheduling_dialog)
        self.batch_scheduling_btn.setEnabled(False)
        btn_layout.addWidget(self.batch_scheduling_btn)

        btn_layout.addStretch()
        main_layout.addLayout(btn_layout)

        # 订单列表表格
        self.table = QTableWidget()
        self.table.setColumnCount(11)
        self.table.setHorizontalHeaderLabels([
            "选择", "订单号", "产品编码", "产品名称", "数量", "订单状态", 
            "排产状态", "参与排产", "需求交付日期", "优先级", "显示颜色"
        ])

        # 为颜色列设置自定义委托（第10列）
        self.color_delegate = ColorBlockDelegate()
        self.table.setItemDelegateForColumn(10, self.color_delegate)
        
        # 设置列的最小宽度（大于等于色块宽度）
        self.table.setColumnWidth(10, 120)  # 列宽可以大于色块宽度，但色块保持100px

        # 设置表格属性
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.table.setSelectionBehavior(QTableWidget.SelectRows)
        self.table.setSelectionMode(QTableWidget.ExtendedSelection)
        self.table.cellClicked.connect(self.on_cell_clicked)
        self.table.itemChanged.connect(self.on_item_changed)
        main_layout.addWidget(self.table)
        main_layout.setStretch(2, 1)  # 让表格占满剩余空间

    def reset_query(self):
        """重置查询条件"""
        self.query_order_no.clear()
        self.query_scheduling_status.setCurrentIndex(0)
        self.query_status.setCurrentIndex(0)
        self.query_priority.setCurrentIndex(0)

    def on_cell_clicked(self, row, column):
        """单元格点击事件"""
        if column != 0 and column != 7:  # 不是选择列和参与排产列
            item = self.table.item(row, 0)
            if item:
                item.setCheckState(Qt.Unchecked if item.checkState() == Qt.Checked else Qt.Checked)

    def on_item_changed(self, item):
        """项目变化事件"""
        if item.column() == 0:
            # 选择列变化，更新按钮状态
            self.update_button_states()   

    def show_batch_scheduling_dialog(self):
        """显示批量设置排产弹窗"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return

        # 创建弹窗
        dialog = BatchSchedulingDialog(self)
        if dialog.exec_():
            # 获取用户选择的参与排产状态
            participate = dialog.get_selected_option()
            self.batch_update_participate_scheduling(participate)

    def batch_update_participate_scheduling(self, participate):
        """批量更新参与排产状态"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return

        # 执行批量更新
        db = DBConnection()
        success = True
        for row in selected_rows:
            order_no = self.table.item(row, 1).text()
            query = "UPDATE pc_production_order SET participate_scheduling = %s WHERE order_no = %s"
            if not db.execute_update(query, (participate, order_no)):
                success = False
                break
        db.close()

        if success:
            QMessageBox.information(self, "成功", f"已成功批量设置参与排产为{'是' if participate else '否'}")
            self.load_orders()
        else:
            QMessageBox.warning(self, "失败", "批量设置失败，请重试")    
                
    def update_participate_scheduling(self, order_no, participate):
        """更新参与排产状态"""
        db = DBConnection()
        query = "UPDATE pc_production_order SET participate_scheduling = %s WHERE order_no = %s"
        success = db.execute_update(query, (participate, order_no))
        db.close()
        if not success:
            QMessageBox.warning(self, "失败", "更新参与排产状态失败")
            # 恢复状态
            self.load_orders()

    def update_button_states(self):
        """更新按钮状态"""
        selected_rows = self.get_selected_rows()
        self.delete_btn.setEnabled(len(selected_rows) > 0)
        self.edit_btn.setEnabled(len(selected_rows) == 1)
        self.batch_scheduling_btn.setEnabled(len(selected_rows) > 0)

    def get_selected_rows(self):
        """获取选中的行"""
        selected_rows = []
        for row in range(self.table.rowCount()):
            item = self.table.item(row, 0)
            if item and item.checkState() == Qt.Checked:
                selected_rows.append(row)
        return selected_rows

    
    def load_orders(self):
        """加载生产订单数据"""
        # 获取查询条件
        order_no = self.query_order_no.text().strip()
        scheduling_status = self.query_scheduling_status.currentText()
        status = self.query_status.currentText()
        priority = self.query_priority.currentText()

        # 构建查询条件
        where_clause = []
        params = []

        if order_no:
            where_clause.append("order_no LIKE %s")
            params.append(f"%{order_no}%")
        if scheduling_status:
            where_clause.append("scheduling_status = %s")
            params.append(scheduling_status)
        if status:
            where_clause.append("status = %s")
            params.append(status)
        if priority:
            where_clause.append("priority = %s")
            params.append(priority)

        # 构建SQL查询
        query = "SELECT * FROM pc_production_order"
        if where_clause:
            query += " WHERE " + " AND ".join(where_clause)
        query += " ORDER BY due_date"

        # 执行查询
        db = DBConnection()
        orders = db.execute_query(query, params)
        db.close()

        # 填充表格
        self.table.setRowCount(0)
        if orders:
            for row, order in enumerate(orders):
                self.table.insertRow(row)
                
                # 添加复选框（选择列）
                check_item = QTableWidgetItem()
                check_item.setFlags(Qt.ItemIsUserCheckable | Qt.ItemIsEnabled)
                check_item.setCheckState(Qt.Unchecked)
                self.table.setItem(row, 0, check_item)
                
                # 订单号
                self.table.setItem(row, 1, QTableWidgetItem(order['order_no']))
                
                # 产品编码
                self.table.setItem(row, 2, QTableWidgetItem(order['product_code']))
                
                # 产品名称
                self.table.setItem(row, 3, QTableWidgetItem(order['product_name']))
                
                # 数量
                self.table.setItem(row, 4, QTableWidgetItem(str(order['quantity'])))
                
                # 订单状态
                self.table.setItem(row, 5, QTableWidgetItem(order['status']))
                
                # 排产状态（设置颜色）
                scheduling_item = QTableWidgetItem(order['scheduling_status'])
                color = QColor(255, 0, 0) if order['scheduling_status'] == '未排产' else QColor(0, 0, 255)
                scheduling_item.setForeground(color)
                self.table.setItem(row, 6, scheduling_item)
                
                # 参与排产（复选框）
                participate_item = QTableWidgetItem()
                participate_item.setFlags(Qt.ItemIsUserCheckable)
                participate_item.setCheckState(Qt.Checked if order['participate_scheduling'] else Qt.Unchecked)
                
                self.table.setItem(row, 7, participate_item)
                
                # 需求交付日期
                date_str = order['due_date'].strftime("%Y-%m-%d") 
                self.table.setItem(row, 8, QTableWidgetItem(date_str))
                
                # 优先级（设置背景色）
                priority_item = QTableWidgetItem(order['priority'])
                priority_color = self.get_priority_color(order['priority'])
                priority_item.setBackground(priority_color)
                self.table.setItem(row, 9, priority_item)
                
                # 显示颜色（显示颜色块）
                color_item = QTableWidgetItem()
                # 将颜色值存储在UserRole中，供委托使用
                color_item.setData(Qt.UserRole, order['display_color'])
                # 设置单元格不可编辑
                color_item.setFlags(Qt.ItemIsEnabled)
                self.table.setItem(row, 10, color_item)

        self.table.resizeColumnsToContents()
        self.update_button_states()

    def get_priority_color(self, priority):
        """根据优先级获取对应的颜色"""
        colors = {
            "P1": "#808080",  # 灰色
            "P2": "#A0A0A0",
            "P3": "#C0C0C0",
            "P4": "#FFA0A0",
            "P5": "#FF0000"   # 红色
        }
        return QColor(colors.get(priority, "#FFFFFF"))

    def add_order(self):
        """新增订单"""
        dialog = ProductionOrderDialog(self)
        if dialog.exec_():
            self.load_orders()

    def edit_selected_order(self):
        """编辑选中的订单"""
        selected_rows = self.get_selected_rows()
        if len(selected_rows) == 1:
            row = selected_rows[0]
            order_no = self.table.item(row, 1).text()
            dialog = ProductionOrderDialog(self, order_no)
            if dialog.exec_():
                self.load_orders()

    def delete_selected_orders(self):
        """删除选中的订单"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return
            
        # 确认删除
        reply = QMessageBox.question(self, "确认", 
                                    f"确定要删除选中的 {len(selected_rows)} 个订单吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
            
        # 执行删除
        db = DBConnection()
        success = True
        for row in selected_rows:
            order_no = self.table.item(row, 1).text()
            query = "DELETE FROM pc_production_order WHERE order_no = %s"
            if not db.execute_update(query, (order_no,)):
                success = False
                break
        db.close()
        
        if success:
            QMessageBox.information(self, "成功", "删除成功")
            self.load_orders()
        else:
            QMessageBox.warning(self, "失败", "删除失败，请重试")

    def batch_set_scheduling(self):
        """批量设置排产状态"""
        selected_rows = self.get_selected_rows()
        if not selected_rows:
            return
            
        # 获取当前选中订单的排产状态
        current_status = None
        for row in selected_rows:
            status = self.table.item(row, 6).text()
            if current_status is None:
                current_status = status
            elif current_status != status:
                current_status = "混合"
                break
        
        # 确定要设置的目标状态
        target_status = "已排产" if current_status == "未排产" else "未排产"
        
        # 确认操作
        reply = QMessageBox.question(self, "确认", 
                                    f"确定要将选中的 {len(selected_rows)} 个订单设置为{target_status}吗？",
                                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if reply != QMessageBox.Yes:
            return
            
        # 执行更新
        db = DBConnection()
        success = True
        for row in selected_rows:
            order_no = self.table.item(row, 1).text()
            query = "UPDATE pc_production_order SET scheduling_status = %s WHERE order_no = %s"
            if not db.execute_update(query, (target_status, order_no)):
                success = False
                break
        db.close()
        
        if success:
            QMessageBox.information(self, "成功", f"已成功设置为{target_status}")
            self.load_orders()
        else:
            QMessageBox.warning(self, "失败", "操作失败，请重试")

# 批量设置排产弹窗类
class BatchSchedulingDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("批量设置参与排产")
        self.setMinimumWidth(300)
        self.selected_option = True  # 默认选择"是"
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # 说明文本
        label = QLabel("请选择是否参与排产：")
        layout.addWidget(label)

        # 单选按钮组
        self.yes_radio = QRadioButton("是")
        self.yes_radio.setChecked(True)
        self.yes_radio.toggled.connect(lambda: self.set_option(True))

        self.no_radio = QRadioButton("否")
        self.no_radio.toggled.connect(lambda: self.set_option(False))

        layout.addWidget(self.yes_radio)
        layout.addWidget(self.no_radio)

        # 按钮区域
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.ok_btn.clicked.connect(self.accept)

        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)

        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)

        layout.addLayout(btn_layout)
        self.setLayout(layout)

    def set_option(self, value):
        """设置选中的选项"""
        self.selected_option = value

    def get_selected_option(self):
        """返回用户选择的选项"""
        return self.selected_option
