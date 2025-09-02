from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QLineEdit, QLabel, QPushButton, QSplitter, QGroupBox, QFormLayout,
                             QTabWidget, QWidget, QDoubleSpinBox, QComboBox, QCheckBox, QMessageBox,
                             QGraphicsView, QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem,
                             QGraphicsTextItem, QScrollArea,QApplication)
from PyQt5.QtCore import Qt, QPointF, QLineF, QSize,QMimeData,QPoint
from PyQt5.QtGui import QPen, QBrush, QColor, QFont, QPainter, QDrag, QPixmap
from DBConnection import DBConnection
from ProcessTemplateDialog import ProcessTemplateDialog
import uuid

class NodeItem(QGraphicsRectItem):
    """工艺路线节点图形项"""
    def __init__(self, node_id, template_id, name, code, x=0, y=0):
        super().__init__(0, 0, 150, 60)
        self.node_id = node_id or str(uuid.uuid4())  # 临时ID，保存时替换
        self.template_id = template_id
        self.name = name
        self.code = code
        self.setPos(x, y)
        self.setBrush(QBrush(QColor(220, 230, 242)))
        self.setPen(QPen(QColor(65, 105, 225), 2))
        self.setFlag(QGraphicsRectItem.ItemIsMovable)
        self.setFlag(QGraphicsRectItem.ItemIsSelectable)
        
        # 节点文本 - 使用setParentItem方法代替addChildItem
        self.text_item = QGraphicsTextItem(f"{name}\n({code or ''})")
        self.text_item.setPos(10, 10)
        self.text_item.setFont(QFont("SimHei", 10))
        self.text_item.setParentItem(self)  # 设置当前矩形项为文本项的父项

class DragEnabledTableWidget(QTableWidget):
    """支持拖拽的表格组件"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setDragEnabled(True)
        self.setSelectionMode(QTableWidget.SingleSelection)
        self.setSelectionBehavior(QTableWidget.SelectRows)

    def startDrag(self, supported_actions):
        # 获取选中的行
        selected_rows = self.selectionModel().selectedRows()
        if not selected_rows:
            return

        row = selected_rows[0].row()
        template_id = self.item(row, 0).data(Qt.UserRole)  # 存储在UserRole中的ID
        code = self.item(row, 0).text()
        name = self.item(row, 1).text()

        # 准备拖拽的数据
        mime_data = QMimeData()
        mime_data.setText(f"{template_id}|{code}|{name}")

        # 创建拖拽对象
        drag = QDrag(self)
        drag.setMimeData(mime_data)
        
        # 创建拖拽时的提示图像
        pixmap = QPixmap(200, 60)
        pixmap.fill(QColor(220, 230, 242))
        painter = QPainter(pixmap)
        painter.setPen(QPen(QColor(65, 105, 225), 2))
        painter.drawRect(0, 0, 198, 58)
        painter.drawText(10, 20, f"{name}")
        painter.drawText(10, 40, f"({code})")
        painter.end()
        drag.setPixmap(pixmap)
        drag.setHotSpot(QPoint(10, 10))

        # 执行拖拽
        drag.exec_(Qt.CopyAction)

class CanvasView(QGraphicsView):
    """支持接收拖拽的画布视图"""
    def __init__(self, scene, parent=None, dialog=None):
        super().__init__(scene, parent)
        self.dialog = dialog  # 引用主对话框
        self.setAcceptDrops(True)
        self.setRenderHint(QPainter.Antialiasing)
        self.setSceneRect(0, 0, 1000, 800)

    def dragEnterEvent(self, event):
        # 检查拖拽数据格式
        if event.mimeData().hasText():
            text = event.mimeData().text()
            if "|" in text and len(text.split("|")) == 3:
                event.acceptProposedAction()

    def dragMoveEvent(self, event):
        if event.mimeData().hasText():
            event.acceptProposedAction()

    def dropEvent(self, event):
        if event.mimeData().hasText():
            # 解析拖拽的数据
            text = event.mimeData().text()
            template_id, code, name = text.split("|")
            
            # 计算在场景中的落点位置
            scene_pos = self.mapToScene(event.pos())
            
            # 创建新节点
            new_node = NodeItem(
                None,  # 临时ID
                template_id,
                name,
                code,
                scene_pos.x() - 75,  # 居中显示
                scene_pos.y() - 30
            )
            
            # 添加到场景和节点列表
            self.scene().addItem(new_node)
            self.dialog.nodes[new_node.node_id] = new_node
            
            event.acceptProposedAction()

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        selected_items = self.scene().selectedItems()
        if selected_items:
            node_item = selected_items[0]
            if isinstance(node_item, NodeItem):
                self.dialog.show_node_detail(node_item)

class LinkItem(QGraphicsLineItem):
    """节点连接线图形项"""
    def __init__(self, from_node, to_node):
        super().__init__()
        self.from_node = from_node
        self.to_node = to_node
        self.setPen(QPen(QColor(100, 100, 100), 2, Qt.SolidLine))
        self.update_position()

    def update_position(self):
        """更新连接线位置"""
        from_pos = self.from_node.mapToScene(
            self.from_node.rect().right(), 
            self.from_node.rect().center().y()
        )
        to_pos = self.to_node.mapToScene(
            self.to_node.rect().left(), 
            self.to_node.rect().center().y()
        )
        self.setLine(QLineF(from_pos, to_pos))

class ProcessRouteDesignDialog(QDialog):
    def __init__(self, parent=None, material_code=None, material_name=None):
        super().__init__(parent)
        self.material_code = material_code
        self.material_name = material_name
        self.current_node = None  # 当前选中的节点
        self.nodes = {}  # 节点ID到图形项的映射
        self.links = []  # 连接线列表
        self.init_ui()
        self.load_route_data()
        self.load_process_templates()

    def init_ui(self):
        self.setWindowTitle(f"设计工艺路线 - {self.material_code} {self.material_name}")
        screen_geometry = QApplication.desktop().availableGeometry()
        self.resize(int(screen_geometry.width() * 0.8), int(screen_geometry.height() * 0.8))
        self.move((screen_geometry.width() - self.width()) // 2,
                 (screen_geometry.height() - self.height()) // 2)

        # 主布局
        main_layout = QVBoxLayout(self)

        # 上部：工艺路线信息
        top_group = QGroupBox("工艺路线信息")
        top_layout = QFormLayout()
        
        self.route_name = QLineEdit()
        top_layout.addRow("路线名称:", self.route_name)
        
        self.route_desc = QLineEdit()
        top_layout.addRow("路线描述:", self.route_desc)
        
        top_group.setLayout(top_layout)
        main_layout.addWidget(top_group)

        # 中部：工序模板列表和画布区域
        mid_splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：工序模板列表
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        
        # 搜索和新增
        template_tool_layout = QHBoxLayout()
        self.template_search = QLineEdit()
        self.template_search.setPlaceholderText("搜索工序模板...")
        self.template_search.textChanged.connect(self.filter_templates)
        template_tool_layout.addWidget(self.template_search)
        
        self.add_template_btn = QPushButton("+")
        self.add_template_btn.setToolTip("新增工序模板")
        self.add_template_btn.setFixedSize(30, 30)
        self.add_template_btn.clicked.connect(self.add_process_template)
        template_tool_layout.addWidget(self.add_template_btn)
        
        left_layout.addLayout(template_tool_layout)
        
        # 工序模板表格（使用支持拖拽的表格）
        self.template_table = DragEnabledTableWidget()
        self.template_table.setColumnCount(2)
        self.template_table.setHorizontalHeaderLabels(["编码", "名称"])
        self.template_table.horizontalHeader().setStretchLastSection(True)
        self.template_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.template_table.setSelectionBehavior(QTableWidget.SelectRows)
        left_layout.addWidget(self.template_table)
        
        mid_splitter.addWidget(left_widget)
        mid_splitter.setSizes([300, 800])

        # 右侧：画布和节点详情
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 节点详情区域分隔线
        detail_splitter = QSplitter(Qt.Vertical)
        
        
        # 画布区域（使用支持接收拖拽的视图）
        self.scene = QGraphicsScene(self)
        self.view = CanvasView(self.scene, self, self)  # 传入对话框引用
        detail_splitter.addWidget(self.view)
        detail_splitter.setSizes([300, 300])  
        
        
        
        # 节点详情 - 包裹在滚动区域中
        self.node_detail_scroll = QScrollArea()
        self.node_detail_scroll.setWidgetResizable(True)  # 自动调整大小
        self.node_detail_widget = QWidget()
        self.node_detail_layout = QHBoxLayout(self.node_detail_widget)
        
        # 左侧基本信息
        self.basic_info_group = QGroupBox("基本信息")
        self.basic_info_layout = QFormLayout()
        self.basic_info_group.setLayout(self.basic_info_layout)

        # 右侧标签页垂直分隔线
        Tab_splitter = QSplitter(Qt.Horizontal)
        Tab_splitter.addWidget(self.basic_info_group)
        Tab_splitter.setSizes([150, 650])

        # 基本信息控件
        self.node_code_edit = QLineEdit()
        self.node_name_edit = QLineEdit()
        self.pre_interval_edit = QDoubleSpinBox()
        self.pre_interval_unit_combo = QComboBox()
        self.pre_interval_unit_combo.addItems(["分", "时", "天"])
        self.post_interval_edit = QDoubleSpinBox()
        self.post_interval_unit_combo = QComboBox()
        self.post_interval_unit_combo.addItems(["分", "时", "天"])
        self.relation_combo = QComboBox()
        self.relation_combo.addItems(["ES", "EE"])

        self.buffer_time_edit = QDoubleSpinBox()
        self.buffer_time_unit_combo = QComboBox()
        self.buffer_time_unit_combo.addItems(["分", "时", "天"])

        self.allow_split_check = QCheckBox("允许自动拆分")
        self.changeover_edit = QDoubleSpinBox()
        self.changeover_unit_combo = QComboBox()
        self.changeover_unit_combo.addItems(["分", "时", "天"])

        # 前间隔时长和单位在同一行
        pre_interval_row = QHBoxLayout()
        pre_interval_row.addWidget(self.pre_interval_edit)
        pre_interval_row.addWidget(self.pre_interval_unit_combo)

        # 后间隔时长和单位在同一行
        post_interval_row = QHBoxLayout()
        post_interval_row.addWidget(self.post_interval_edit)
        post_interval_row.addWidget(self.post_interval_unit_combo)
        
        # 缓冲时长和单位在同一行
        buffer_time_row = QHBoxLayout()
        buffer_time_row.addWidget(self.buffer_time_edit)
        buffer_time_row.addWidget(self.buffer_time_unit_combo)

        self.basic_info_layout.addRow("工序编码", self.node_code_edit)
        self.basic_info_layout.addRow("工序名称", self.node_name_edit)
        self.basic_info_layout.addRow("前间隔时长", pre_interval_row)
        self.basic_info_layout.addRow("后间隔时长", post_interval_row)
        self.basic_info_layout.addRow("工序关系", self.relation_combo)
        self.basic_info_layout.addRow("缓冲时长", buffer_time_row)

        # 右侧标签页
        self.tab_widget = QTabWidget()
        self.resource_tab = QWidget()
        self.material_tab = QWidget()
        self.split_tab = QWidget()
        self.changeover_tab = QWidget()
        
        self.tab_widget.addTab(self.resource_tab, "主资源")
        self.tab_widget.addTab(self.material_tab, "使用物料")
        self.tab_widget.addTab(self.split_tab, "自动拆分")
        self.tab_widget.addTab(self.changeover_tab, "换型配置")
        
        # 主资源标签页
        resource_layout = QVBoxLayout()

        resource_btn_layout = QHBoxLayout()
        self.add_resource_btn = QPushButton("添加资源")
        self.add_resource_btn.clicked.connect(self.add_resource)
        resource_btn_layout.addWidget(self.add_resource_btn)
        resource_layout.addLayout(resource_btn_layout)

        self.resource_table = QTableWidget()
        self.resource_table.setColumnCount(7)
        self.resource_table.setHorizontalHeaderLabels(["序号", "编码", "名称", "资源组", "容量", "产能", "操作"])
        self.resource_table.horizontalHeader().setStretchLastSection(True)
        resource_layout.addWidget(self.resource_table)      
        
        
        self.resource_tab.setLayout(resource_layout)

        # 使用物料标签页
        material_layout = QVBoxLayout()

        material_btn_layout = QHBoxLayout()
        self.add_material_btn = QPushButton("添加物料")
        self.add_material_btn.clicked.connect(self.add_material_row)
        material_btn_layout.addWidget(self.add_material_btn)
        material_layout.addLayout(material_btn_layout)

        self.material_table = QTableWidget()
        self.material_table.setColumnCount(6)
        self.material_table.setHorizontalHeaderLabels(["序号", "编码", "名称", "数量", "是否使用", "操作"])
        self.material_table.horizontalHeader().setStretchLastSection(True)
        material_layout.addWidget(self.material_table)
        
        self.material_tab.setLayout(material_layout)
        
        # 自动拆分标签页控件
        split_layout = QFormLayout()
        self.allow_split_check = QCheckBox("允许自动拆分")
        self.min_split_qty_edit = QDoubleSpinBox()
        self.min_split_qty_edit.setMinimum(0)
        self.max_split_qty_edit = QDoubleSpinBox()
        self.max_split_qty_edit.setMinimum(0)
        self.split_trigger_qty_edit = QDoubleSpinBox()
        self.split_trigger_qty_edit.setMinimum(0)
        self.split_strategy_combo = QComboBox()
        self.split_strategy_combo.addItems(["平均拆分", "优先大批量", "优先小批量"])
        self.split_base_qty_edit = QDoubleSpinBox()
        self.split_base_qty_edit.setMinimum(0)

        split_layout.addRow(self.allow_split_check)
        split_layout.addRow("最小拆分量", self.min_split_qty_edit)
        split_layout.addRow("最大拆分量", self.max_split_qty_edit)
        split_layout.addRow("触发拆分数量阀值", self.split_trigger_qty_edit)
        split_layout.addRow("拆分策略", self.split_strategy_combo)
        split_layout.addRow("基准数", self.split_base_qty_edit)
        self.split_tab.setLayout(split_layout)

        # 换型配置标签页控件
        changeover_layout = QFormLayout()
        self.changeover_time_edit = QDoubleSpinBox()
        self.changeover_time_edit.setMinimum(0)
        self.changeover_time_unit_combo = QComboBox()
        self.changeover_time_unit_combo.addItems(["分", "时", "天"])
        changeover_layout.addRow("切换产品时长", self.changeover_time_edit)
        changeover_layout.addRow("时长单位", self.changeover_time_unit_combo)
        self.changeover_tab.setLayout(changeover_layout)

        # 右侧标签页和基本信息水平分隔线
        Tab_splitter.addWidget(self.tab_widget)

        self.node_detail_layout.addWidget(Tab_splitter)
        
        # 将详情部件放入滚动区域
        self.node_detail_scroll.setWidget(self.node_detail_widget)

        detail_splitter.addWidget(self.node_detail_scroll)  # 使用滚动区域替代原部件
        
        right_layout.addWidget(detail_splitter)
        
        mid_splitter.addWidget(right_widget)
        main_layout.addWidget(mid_splitter, 1)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self.save_route)
        self.cancel_btn = QPushButton("取消")
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.cancel_btn)
        main_layout.addLayout(btn_layout)

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
        """将选中的资源添加到资源表格"""
            

    def add_material_row(self):
        row = self.material_table.rowCount()
        self.material_table.insertRow(row)
        self.material_table.setItem(row, 0, QTableWidgetItem(""))
        self.material_table.setItem(row, 1, QTableWidgetItem(""))
        btn = QPushButton("删除")
        btn.clicked.connect(lambda: self.material_table.removeRow(row))
        self.material_table.setCellWidget(row, 2, btn)

    def load_route_data(self):
        """加载工艺路线数据"""
        db = DBConnection()
        # 查询工艺路线基本信息
        route_query = "SELECT name, description FROM pc_process_route WHERE material_code = %s"
        route_data = db.execute_query(route_query, (self.material_code,))
        if route_data:
            self.route_name.setText(route_data[0]['name'] or "")
            self.route_desc.setText(route_data[0]['description'] or "")

        # 查询节点数据
        node_query = """
        SELECT n.*, t.code,t.name               
        FROM pc_route_node n
        LEFT JOIN pc_process_template t ON n.template_id = t.id
        WHERE n.material_code = %s
        """
        nodes = db.execute_query(node_query, (self.material_code,))
        
        # 查询连接关系
        link_query = "SELECT from_node_id, to_node_id FROM pc_route_link WHERE material_code = %s"
        links = db.execute_query(link_query, (self.material_code,))
        db.close()

        # 加载节点
        for node in nodes:
            node_item = NodeItem(
                node['id'],
                node['template_id'],
                node['name'],
                node['code'],
                node['x_pos'] or 50,
                node['y_pos'] or 50
            )
            self.nodes[node['id']] = node_item
            self.scene.addItem(node_item)

        # 读取并设置控件值
            self.allow_split_check.setChecked(bool(node.get('allow_split')))
            self.min_split_qty_edit.setValue(node.get('min_batch') or 0)
            self.max_split_qty_edit.setValue(node.get('max_batch') or 0)
            self.split_trigger_qty_edit.setValue(node.get('split_threshold') or 0)
            self.split_strategy_combo.setCurrentText(node.get('split_strategy') or "平均拆分")
            self.split_base_qty_edit.setValue(node.get('base_number') or 0)
            self.changeover_time_edit.setValue(node.get('changeover_time_value') or 0)
            unit = node.get('changeover_time_unit') or "分"
            idx = self.changeover_time_unit_combo.findText(unit)
            self.changeover_time_unit_combo.setCurrentIndex(idx if idx >= 0 else 0)            

        # 加载连接
        for link in links:
            from_node = self.nodes.get(link['from_node_id'])
            to_node = self.nodes.get(link['to_node_id'])
            if from_node and to_node:
                link_item = LinkItem(from_node, to_node)
                self.links.append(link_item)
                self.scene.addItem(link_item)

    def load_process_templates(self):
        """加载工序模板列表，将ID存储在UserRole中"""
        db = DBConnection()
        query = "SELECT id, code, name FROM pc_process_template ORDER BY code"
        templates = db.execute_query(query)
        db.close()

        self.template_table.setRowCount(0)
        if templates:
            for row, template in enumerate(templates):
                self.template_table.insertRow(row)
                
                # 编码单元格存储ID在UserRole中
                code_item = QTableWidgetItem(template['code'])
                code_item.setData(Qt.UserRole, template['id'])  # 存储ID
                self.template_table.setItem(row, 0, code_item)
                
                self.template_table.setItem(row, 1, QTableWidgetItem(template['name']))
        self.template_table.resizeColumnsToContents()

    def filter_templates(self):
        """过滤工序模板"""
        search_text = self.template_search.text().lower().strip()
        for row in range(self.template_table.rowCount()):
            code = self.template_table.item(row, 0).text().lower()
            name = self.template_table.item(row, 1).text().lower()
            visible = search_text in code or search_text in name
            self.template_table.setRowHidden(row, not visible)

    def add_process_template(self):
        """新增工序模板"""
        dialog = ProcessTemplateDialog(self)
        if dialog.exec_():
            self.load_process_templates()

    def save_route(self):
        """保存工艺路线"""
        if not self.route_name.text().strip():
            QMessageBox.warning(self, "错误", "请输入工艺路线名称")
            return

        db = DBConnection()
        try:
            # 开始事务
            db.begin_transaction()

            # 保存工艺路线基本信息
            route_name = self.route_name.text().strip()
            route_desc = self.route_desc.text().strip()
            
            # 检查是否存在现有路线
            check_query = "SELECT id FROM pc_process_route WHERE material_code = %s"
            route_exists = db.execute_query(check_query, (self.material_code,))
            
            if route_exists:
                # 更新现有路线
                update_query = """
                UPDATE pc_process_route 
                SET name = %s, description = %s 
                WHERE material_code = %s
                """
                db.execute_update(update_query, (route_name, route_desc, self.material_code))
                route_id = route_exists[0]['id']
            else:
                # 新增路线
                insert_query = """
                INSERT INTO pc_process_route (material_code, name, description)
                VALUES (%s, %s, %s)
                """
                route_id = db.execute_insert(insert_query, (self.material_code, route_name, route_desc))

            # 先删除现有节点和连接
            db.execute_update("DELETE FROM pc_route_node WHERE material_code = %s", (self.material_code,))
            db.execute_update("DELETE FROM pc_route_link WHERE material_code = %s", (self.material_code,))
            db.execute_update("DELETE FROM pc_route_node_resource WHERE material_code = %s", (self.material_code,))

            # 保存节点
            node_ids = []
            for idx, (node_id, node_item) in enumerate(self.nodes.items()):
                insert_node_query = """
                INSERT INTO pc_route_node (
                    material_code, template_id, name, x_pos, y_pos, sort_order,pre_interval, pre_interval_unit,
                    post_interval, post_interval_unit, relation, buffer_time, buffer_time_unit,allow_split,
                    min_batch, max_batch, split_threshold, split_strategy, base_number,changeover_time_value, changeover_time_unit
                ) VALUES (%s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s, %s,%s, %s, %s, %s, %s, %s,%s, %s)
                """
                # 获取控件值
                pre_interval = self.pre_interval_edit.value()
                pre_interval_unit = self.pre_interval_unit_combo.currentText()
                post_interval = self.post_interval_edit.value()
                post_interval_unit = self.post_interval_unit_combo.currentText()
                relation = self.relation_combo.currentText()
                buffer_time = self.buffer_time_edit.value()
                buffer_time_unit = self.buffer_time_unit_combo.currentText()                
                allow_split = int(self.allow_split_check.isChecked())
                min_split_qty = self.min_split_qty_edit.value()
                max_split_qty = self.max_split_qty_edit.value()
                split_trigger_qty = self.split_trigger_qty_edit.value()
                split_strategy = self.split_strategy_combo.currentText()
                split_base_qty = self.split_base_qty_edit.value()
                changeover_time_value = self.changeover_time_edit.value()
                changeover_time_unit = self.changeover_time_unit_combo.currentText()

                new_node_id = db.execute_insert(
                    insert_node_query,
                    (self.material_code, node_item.template_id, node_item.name,
                     node_item.x(), node_item.y(), idx + 1,pre_interval, pre_interval_unit,
                     post_interval, post_interval_unit, relation, buffer_time, buffer_time_unit,allow_split,
                     min_split_qty, max_split_qty, split_trigger_qty, split_strategy, split_base_qty,changeover_time_value, changeover_time_unit)
                )
                node_ids.append((node_id, new_node_id))  # 记录旧ID到新ID的映射

                for row in range(self.resource_table.rowCount()):
                    resource_code = self.resource_table.item(row, 1).text().strip() if self.resource_table.item(row, 1) else ""
                    resource_name = self.resource_table.item(row, 2).text().strip() if self.resource_table.item(row, 2) else ""
                    resource_group = self.resource_table.item(row, 3).text().strip() if self.resource_table.item(row, 3) else ""
                    capacity = self.resource_table.item(row, 4).text().strip() if self.resource_table.item(row, 4) else ""
                    productivity = self.resource_table.item(row, 5).text().strip() if self.resource_table.item(row, 5) else ""
                    if resource_code:  # 编码不能为空
                        db.execute_insert(
                            "INSERT INTO pc_route_node_resource (node_id,material_code, resource_code, resource_name, resource_group, capacity, productivity) VALUES (%s, %s, %s,%s, %s, %s, %s)",
                            (node_id,self.material_code, resource_code, resource_name, resource_group, capacity, productivity)
                        )

            # 保存连接
            node_id_map = dict(node_ids)
            for link in self.links:
                from_old_id = link.from_node.node_id
                to_old_id = link.to_node.node_id
                if from_old_id in node_id_map and to_old_id in node_id_map:
                    insert_link_query = """
                    INSERT INTO pc_route_link (material_code, from_node_id, to_node_id)
                    VALUES (%s, %s, %s)
                    """
                    db.execute_insert(
                        insert_link_query,
                        (self.material_code, node_id_map[from_old_id], node_id_map[to_old_id])
                    )

            # 提交事务
            db.commit()
            QMessageBox.information(self, "成功", "工艺路线保存成功")
            self.accept()

        except Exception as e:
            db.rollback()
            QMessageBox.warning(self, "错误", f"保存失败: {str(e)}")
        finally:
            db.close()

    def show_node_detail(self, node_item):
        """显示节点详情，优先从pc_route_node读取，否则从pc_process_template读取"""
        db = DBConnection()
        # 先查pc_route_node
        query = """
        SELECT n.*, t.code, t.name
        FROM pc_route_node n
        LEFT JOIN pc_process_template t ON n.template_id = t.id
        WHERE n.id = %s
        """
        result = db.execute_query(query, (node_item.node_id,))
        if result:
            node = result[0]
            self.node_code_edit.setText(node['code'])
            self.node_name_edit.setText(node['name'])
            self.pre_interval_edit.setValue(node.get('pre_interval', 0))
            self.pre_interval_unit_combo.setCurrentText(node.get('pre_interval_unit', '分'))
            self.post_interval_edit.setValue(node.get('post_interval', 0))
            self.post_interval_unit_combo.setCurrentText(node.get('post_interval_unit', '分'))
            self.relation_combo.setCurrentText(node.get('relation', 'ES'))
            self.buffer_time_edit.setValue(node.get('buffer_time', 0))
            self.buffer_time_unit_combo.setCurrentText(node.get('buffer_time_unit', '分'))            
            self.allow_split_check.setChecked(bool(node.get('allow_split', 0)))
            self.min_split_qty_edit.setValue(node.get('min_batch', 0))
            self.max_split_qty_edit.setValue(node.get('max_batch', 0))
            self.split_trigger_qty_edit.setValue(node.get('split_threshold', 0))
            self.split_strategy_combo.setCurrentText(node.get('split_strategy', '平均拆分'))
            self.split_base_qty_edit.setValue(node.get('base_number', 0))            
            self.changeover_edit.setValue(node.get('changeover_time_value', 0))
            self.changeover_unit_combo.setCurrentText(node.get('changeover_time_unit', '分'))

        else:
            # 查模板表
            query = "SELECT * FROM pc_process_template WHERE id = %s"
            result = db.execute_query(query, (node_item.template_id,))
            if result:
                tpl = result[0]
                self.node_code_edit.setText(tpl['code'])
                self.node_name_edit.setText(tpl['name'])
                self.pre_interval_edit.setValue(tpl.get('pre_interval_value', 0))
                self.pre_interval_unit_combo.setCurrentText(tpl.get('pre_interval_unit', '分'))
                self.post_interval_edit.setValue(tpl.get('post_interval_value', 0))
                self.post_interval_unit_combo.setCurrentText(tpl.get('post_interval_unit', '分'))
                self.relation_combo.setCurrentText(tpl.get('relation', 'ES'))
                self.buffer_time_edit.setValue(tpl.get('buffer_time', 0))
                self.buffer_time_unit_combo.setCurrentText(tpl.get('buffer_time_unit', '分'))                
                self.allow_split_check.setChecked(bool(tpl.get('allow_split', 0)))
                self.min_split_qty_edit.setValue(tpl.get('min_batch') or 0)
                self.max_split_qty_edit.setValue(tpl.get('max_batch') or 0)
                self.split_trigger_qty_edit.setValue(tpl.get('split_threshold') or 0)
                self.split_strategy_combo.setCurrentText(tpl.get('split_strategy', '平均拆分'))
                self.split_base_qty_edit.setValue(tpl.get('base_number') or 0)
                self.changeover_edit.setValue(tpl.get('changeover_time_value', 0))
                self.changeover_unit_combo.setCurrentText(tpl.get('changeover_time_unit', '分'))
        
        #加裁主资源
        resource_query = """
        SELECT resource_code, resource_name, resource_group, capacity, productivity
        FROM pc_route_node_resource WHERE node_id = %s
        """
        resources = db.execute_query(resource_query, (node_item.node_id,))
        if resources:
            self.resource_table.setRowCount(0)
            for idx, r in enumerate(resources):
                self.resource_table.insertRow(idx)
                self.resource_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))  # 序号
                self.resource_table.setItem(idx, 1, QTableWidgetItem(r.get('resource_code', '')))
                self.resource_table.setItem(idx, 2, QTableWidgetItem(r.get('resource_name', '')))
                self.resource_table.setItem(idx, 3, QTableWidgetItem(r.get('resource_group', '')))
                self.resource_table.setItem(idx, 4, QTableWidgetItem(str(r.get('capacity', ''))))
                self.resource_table.setItem(idx, 5, QTableWidgetItem(str(r.get('productivity', ''))))
                # 操作按钮
                op_widget = QWidget()
                op_layout = QHBoxLayout(op_widget)
                op_layout.setContentsMargins(2, 2, 2, 2)
                #编辑
                edit_btn = QPushButton("编辑")
                edit_btn.setMinimumSize(50, 25)
                edit_btn.clicked.connect(lambda _, row=idx: self.edit_resource(row, r.get('resource_code', '')))
                op_layout.addWidget(edit_btn)
                #删除
                btn = QPushButton("删除")
                btn.setMinimumSize(50, 25)
                btn.clicked.connect(lambda _, row=idx: self.resource_table.removeRow(row))
                op_layout.addWidget(btn)
                self.resource_table.setCellWidget(idx, 6, op_widget)
        else:
            # 查模板表
            resource_query = """
            SELECT r.`code`AS resource_code,r.`name` AS resource_name,r.resource_group,r.capacity, 
            r.productivity_value As productivity 
            FROM pc_template_resources tr JOIN pc_resource r ON tr.resource_code = r.code WHERE tr.template_id = %s
            """
            resources = db.execute_query(resource_query, (node_item.template_id,))
            if resources:
                self.resource_table.setRowCount(0)
                for idx, r in enumerate(resources):
                    self.resource_table.insertRow(idx)
                    self.resource_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))  # 序号
                    self.resource_table.setItem(idx, 1, QTableWidgetItem(r.get('resource_code', '')))
                    self.resource_table.setItem(idx, 2, QTableWidgetItem(r.get('resource_name', '')))
                    self.resource_table.setItem(idx, 3, QTableWidgetItem(r.get('resource_group', '')))
                    self.resource_table.setItem(idx, 4, QTableWidgetItem(str(r.get('capacity', ''))))
                    self.resource_table.setItem(idx, 5, QTableWidgetItem(str(r.get('productivity', ''))))
                    # 操作按钮
                    op_widget = QWidget()
                    op_layout = QHBoxLayout(op_widget)
                    op_layout.setContentsMargins(2, 2, 2, 2)
                    #编辑
                    edit_btn = QPushButton("编辑")
                    edit_btn.setMinimumSize(50, 25)
                    edit_btn.clicked.connect(lambda _, row=idx: self.edit_resource(row, r.get('resource_code', '')))
                    op_layout.addWidget(edit_btn)
                    #删除
                    btn = QPushButton("删除")
                    btn.setMinimumSize(50, 25)
                    btn.clicked.connect(lambda _, row=idx: self.resource_table.removeRow(row))
                    op_layout.addWidget(btn)
                    self.resource_table.setCellWidget(idx, 6, op_widget)
        # 使用物料读取
        material_query = """
        SELECT material_code, material_name, quantity, is_used
        FROM pc_route_node_material WHERE node_id = %s
        """
        materials = db.execute_query(material_query, (node_item.node_id,))
        if materials:
            self.material_table.setRowCount(0)
            for idx, m in enumerate(materials):
                self.material_table.insertRow(idx)
                self.material_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))  # 序号
                self.material_table.setItem(idx, 1, QTableWidgetItem(m.get('material_code', '')))
                self.material_table.setItem(idx, 2, QTableWidgetItem(m.get('material_name', '')))
                self.material_table.setItem(idx, 3, QTableWidgetItem(str(m.get('quantity', ''))))
                use_checkbox = QCheckBox()
                use_checkbox.setChecked(bool(m.get('is_used', 0)))
                self.material_table.setCellWidget(idx, 4, use_checkbox)
                btn = QPushButton("删除")
                btn.clicked.connect(lambda _, row=idx: self.material_table.removeRow(row))
                self.material_table.setCellWidget(idx, 5, btn)
        else:
            # 查模板表
            material_query = """
            SELECT m.code AS material_code, m.name AS material_name, tm.quantity
            FROM pc_template_materials tm 
            JOIN pc_material m ON tm.material_code = m.code 
            WHERE tm.template_id = %s
            """
            materials = db.execute_query(material_query, (node_item.template_id,))
            if materials:
                self.material_table.setRowCount(0)
                for idx, m in enumerate(materials):
                    self.material_table.insertRow(idx)
                    self.material_table.setItem(idx, 0, QTableWidgetItem(str(idx + 1)))  # 序号
                    self.material_table.setItem(idx, 1, QTableWidgetItem(m.get('material    _code', '')))
                    self.material_table.setItem(idx, 2, QTableWidgetItem(m.get('material_name', '')))
                    self.material_table.setItem(idx, 3, QTableWidgetItem(str(m.get('quantity', ''))))
                    use_checkbox = QCheckBox()
                    use_checkbox.setChecked(bool(m.get('is_used', 0)))
                    self.material_table.setCellWidget(idx, 4, use_checkbox)
                    btn = QPushButton("删除")
                    btn.clicked.connect(lambda _, row=idx: self.material_table.removeRow(row))
                    self.material_table.setCellWidget(idx, 5, btn)

        db.close()

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