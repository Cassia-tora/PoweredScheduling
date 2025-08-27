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
        
        # 画布区域（使用支持接收拖拽的视图）
        self.scene = QGraphicsScene(self)
        self.view = CanvasView(self.scene, self, self)  # 传入对话框引用
        right_layout.addWidget(self.view)
        
        # 节点详情区域
        detail_splitter = QSplitter(Qt.Vertical)
        detail_splitter.setSizes([300, 200])
        
        # 节点详情
        self.node_detail_widget = QWidget()
        self.node_detail_layout = QHBoxLayout(self.node_detail_widget)
        
        # 左侧基本信息
        self.basic_info_group = QGroupBox("基本信息")
        self.basic_info_layout = QFormLayout()
        self.basic_info_group.setLayout(self.basic_info_layout)
        
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
        
        self.node_detail_layout.addWidget(self.basic_info_group)
        self.node_detail_layout.addWidget(self.tab_widget)
        
        detail_splitter.addWidget(self.node_detail_widget)
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
        SELECT n.id, n.template_id, n.name, n.x_pos, n.y_pos, t.code,
               n.pre_interval, n.pre_interval_unit, n.post_interval, n.post_interval_unit,
               n.relation, n.buffer_time, n.buffer_time_unit
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

            # 保存节点
            node_ids = []
            for idx, (node_id, node_item) in enumerate(self.nodes.items()):
                insert_node_query = """
                INSERT INTO pc_route_node (
                    material_code, template_id, name, x_pos, y_pos, sort_order
                ) VALUES (%s, %s, %s, %s, %s, %s)
                """
                new_node_id = db.execute_insert(
                    insert_node_query,
                    (self.material_code, node_item.template_id, node_item.name,
                     node_item.x(), node_item.y(), idx + 1)
                )
                node_ids.append((node_id, new_node_id))  # 记录旧ID到新ID的映射

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