from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
                             QLineEdit, QLabel, QPushButton, QSplitter, QMessageBox, QGraphicsView,
                             QGraphicsScene, QGraphicsRectItem, QGraphicsLineItem, QGraphicsTextItem,
                             QFrame, QGroupBox, QFormLayout)
from PyQt5.QtCore import Qt, QPointF, QLineF
from PyQt5.QtGui import QPen, QBrush, QColor, QFont,QPainter
from DBConnection import DBConnection
from ProcessRouteDesignDialog import ProcessRouteDesignDialog

class ProcessRouteManagement(QWidget):
    def __init__(self):
        super().__init__()
        self.current_material_id = None
        self.init_ui()
        self.load_materials()

    def init_ui(self):
        # 主布局
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # 左侧物料列表区域
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_widget.setMinimumWidth(250)
        left_widget.setMaximumWidth(300)

        # 搜索区域
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索物料:"))
        self.material_search = QLineEdit()
        self.material_search.textChanged.connect(self.filter_materials)
        search_layout.addWidget(self.material_search)
        left_layout.addLayout(search_layout)

        # 物料表格
        self.material_table = QTableWidget()
        self.material_table.setColumnCount(2)
        self.material_table.setHorizontalHeaderLabels(["编码", "名称"])
        self.material_table.horizontalHeader().setStretchLastSection(True)
        self.material_table.setEditTriggers(QTableWidget.NoEditTriggers)
        self.material_table.setSelectionBehavior(QTableWidget.SelectRows)
        self.material_table.cellClicked.connect(self.on_material_selected)
        left_layout.addWidget(self.material_table)

        # 左侧区域不再放设计按钮
        left_layout.addStretch()  # 用伸缩项填充剩余空间

        # 右侧工艺路线展示区域
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # 右侧顶部：标题和操作按钮（新增）
        top_right_layout = QHBoxLayout()  # 水平布局放标题和按钮
        
        self.route_title = QLabel("请选择左侧物料查看工艺路线")
        self.route_title.setAlignment(Qt.AlignCenter)
        self.route_title.setFont(QFont("SimHei", 12))
        top_right_layout.addWidget(self.route_title, 1)  # 标题占主要空间

        # 设计工艺路线按钮（迁移到右侧顶部）
        self.design_btn = QPushButton("设计工艺路线")
        self.design_btn.clicked.connect(self.open_design_dialog)
        top_right_layout.addWidget(self.design_btn)  # 按钮居右
        
        right_layout.addLayout(top_right_layout)  # 添加顶部布局

        # 工艺路线画布
        self.scene = QGraphicsScene(self)
        self.view = QGraphicsView(self.scene)
        self.view.setRenderHint(QPainter.Antialiasing)
        self.view.setSceneRect(0, 0, 800, 600)
        right_layout.addWidget(self.view)  # 画布占剩余空间

        # 添加到主布局
        main_layout.addWidget(left_widget)
        main_layout.addWidget(right_widget, 1)

    def load_materials(self):
        """加载物料列表"""
        db = DBConnection()
        query = "SELECT code, name FROM pc_material ORDER BY code"
        materials = db.execute_query(query)
        db.close()

        self.material_table.setRowCount(0)
        if materials:
            for row, material in enumerate(materials):
                self.material_table.insertRow(row)
                self.material_table.setItem(row, 0, QTableWidgetItem(material['code']))
                self.material_table.setItem(row, 1, QTableWidgetItem(material['name']))
        self.material_table.resizeColumnsToContents()

    def filter_materials(self):
        """根据搜索内容过滤物料"""
        search_text = self.material_search.text().lower().strip()
        for row in range(self.material_table.rowCount()):
            code = self.material_table.item(row, 0).text().lower()
            name = self.material_table.item(row, 1).text().lower()
            visible = search_text in code or search_text in name
            self.material_table.setRowHidden(row, not visible)

    def on_material_selected(self, row, column):
        """选择物料后加载对应的工艺路线"""
        self.current_material_id = self.material_table.item(row, 0).text()
        material_name = self.material_table.item(row, 1).text()
        self.route_title.setText(f"{self.current_material_id} - {material_name} 的工艺路线")
        self.load_process_route()

    def load_process_route(self):
        """加载选中物料的工艺路线"""
        self.scene.clear()
        if not self.current_material_id:
            return

        # 查询工艺路线节点
        db = DBConnection()
        query = """
        SELECT n.id, n.template_id, n.name, n.x_pos, n.y_pos, t.code 
        FROM pc_route_node n
        LEFT JOIN pc_process_template t ON n.template_id = t.id
        WHERE n.material_code = %s
        ORDER BY n.sort_order
        """
        nodes = db.execute_query(query, (self.current_material_id,))

        # 查询节点连接关系
        link_query = """
        SELECT from_node_id, to_node_id 
        FROM pc_route_link 
        WHERE material_code = %s
        """
        links = db.execute_query(link_query, (self.current_material_id,))
        db.close()

        # 存储节点ID与图形项的映射
        node_items = {}
        
        # 绘制节点
        if nodes:
            for node in nodes:
                rect = QGraphicsRectItem(0, 0, 150, 60)
                rect.setPos(node['x_pos'] or 50, node['y_pos'] or 50)
                rect.setBrush(QBrush(QColor(220, 230, 242)))
                rect.setPen(QPen(QColor(65, 105, 225), 2))
                
                # 节点文本
                text = QGraphicsTextItem(f"{node['name']}\n({node['code'] or ''})")
                text.setPos(10, 10)
                text.setFont(QFont("SimHei", 10))
                rect.addChildItem(text)
                
                # 存储节点ID与图形项
                node_items[node['id']] = rect
                self.scene.addItem(rect)

        # 绘制连接线
        if links:
            pen = QPen(QColor(100, 100, 100), 2, Qt.SolidLine)
            for link in links:
                from_node = node_items.get(link['from_node_id'])
                to_node = node_items.get(link['to_node_id'])
                if from_node and to_node:
                    # 计算连接点（从节点右侧中点到目标节点左侧中点）
                    from_pos = from_node.mapToScene(from_node.rect().right(), from_node.rect().center().y())
                    to_pos = to_node.mapToScene(to_node.rect().left(), to_node.rect().center().y())
                    
                    line = QGraphicsLineItem(QLineF(from_pos, to_pos))
                    line.setPen(pen)
                    self.scene.addItem(line)

    def open_design_dialog(self):
        """打开工艺路线设计对话框"""
        if not self.current_material_id:
            QMessageBox.warning(self, "提示", "请先选择一个物料")
            return
            
        material_name = ""
        for row in range(self.material_table.rowCount()):
            if self.material_table.item(row, 0).text() == self.current_material_id:
                material_name = self.material_table.item(row, 1).text()
                break

        dialog = ProcessRouteDesignDialog(self, self.current_material_id, material_name)
        if dialog.exec_():
            self.load_process_route()