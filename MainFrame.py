# 新增主框架文件: AI-PoweredScheduling/MainFrame.py
import sys
from PyQt5.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                            QTreeWidget, QTreeWidgetItem, QStackedWidget, 
                            QLabel, QFrame)
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon, QFont

# 导入现有模块
from MaterialManagement import MaterialManagement
from ResourceManagement import ResourceManagement
from ProductionOrderManagement import ProductionOrderManagement
from ProcessTemplateManagement import ProcessTemplateManagement
from ProcessRouteManagement import ProcessRouteManagement

class MainFrame(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        """初始化主界面"""
        self.setWindowTitle("AI智能排程系统")
        #self.setGeometry(100, 100, 1200, 800)
        
        self.setMinimumSize(1200, 800)  # 只设置最小尺寸，不限制最大尺寸
        self.showMaximized()  # 最大化窗口，占据整个屏幕
        
        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QHBoxLayout(main_widget)
        
        # 创建左侧菜单
        self.create_left_menu()
        main_layout.addWidget(self.left_menu, 1)
        
        # 创建右侧内容区域分隔线
        line = QFrame()
        line.setFrameShape(QFrame.VLine)
        line.setFrameShadow(QFrame.Sunken)
        main_layout.addWidget(line)
        
        # 创建右侧内容区域
        self.create_right_content()
        main_layout.addWidget(self.right_content, 5)
        
        # 初始化菜单与内容关联
        self.bind_menu_actions()
        
    def create_left_menu(self):
        """创建左侧菜单树"""
        self.left_menu = QTreeWidget()
        self.left_menu.setHeaderHidden(True)  # 隐藏表头
        self.left_menu.setMinimumWidth(200)
        self.left_menu.setMaximumWidth(250)
        self.left_menu.setStyleSheet("""
            QTreeWidget {
                background-color: #f5f5f5;
                border: none;
                padding-top: 10px;
            }
            QTreeWidget::item {
                height: 30px;
                border-radius: 4px;
                margin: 2px 5px;
            }
            QTreeWidget::item:selected {
                background-color: #cce5ff;
                color: #004085;
            }
        """)
        
        # 一级菜单：基础数据
        base_data = QTreeWidgetItem(["基础数据"])
        base_data.setFlags(base_data.flags() | Qt.ItemIsTristate | Qt.ItemIsUserCheckable)
        # 二级菜单
        self.material_item = QTreeWidgetItem(["物料管理"])
        self.resource_item = QTreeWidgetItem(["资源管理"])  # 新增资源管理菜单
        self.process_template_item = QTreeWidgetItem(["工序模板"])
        self.ProcessRoute_item = QTreeWidgetItem(["工序路线"])        
        self.customer_item = QTreeWidgetItem(["客户管理"])
        self.supplier_item = QTreeWidgetItem(["供应商管理"])
        base_data.addChild(self.material_item)
        base_data.addChild(self.resource_item)  # 添加到基础数据下
        base_data.addChild(self.process_template_item)
        base_data.addChild(self.ProcessRoute_item)
        base_data.addChild(self.customer_item)
        base_data.addChild(self.supplier_item)
        
        # 一级菜单：生产管理
        production_data = QTreeWidgetItem(["生产管理"])
        self.production_order_item = QTreeWidgetItem(["生产订单"])        
        self.scheduling_item = QTreeWidgetItem(["排程管理"])        
        production_data.addChild(self.production_order_item)   
        production_data.addChild(self.scheduling_item)   
        
        # 一级菜单：系统设置
        system_data = QTreeWidgetItem(["系统设置"])
        self.user_item = QTreeWidgetItem(["用户管理"])
        self.role_item = QTreeWidgetItem(["角色权限"])
        self.log_item = QTreeWidgetItem(["操作日志"])
        system_data.addChild(self.user_item)
        system_data.addChild(self.role_item)
        system_data.addChild(self.log_item)
        
        # 添加到菜单树
        self.left_menu.addTopLevelItem(base_data)
        self.left_menu.addTopLevelItem(production_data)
        self.left_menu.addTopLevelItem(system_data)
        
        # 展开所有菜单
        self.left_menu.expandAll()
        
    def create_right_content(self):
        """创建右侧内容区域"""
        self.right_content = QStackedWidget()
        
        # 初始页面
        self.init_page = QWidget()
        init_layout = QVBoxLayout(self.init_page)
        init_label = QLabel("欢迎使用AI智能排程系统，请从左侧选择功能菜单")
        init_label.setAlignment(Qt.AlignCenter)
        init_label.setFont(QFont("SimHei", 14))
        init_layout.addWidget(init_label)
        self.right_content.addWidget(self.init_page)
        
        # 物料管理页面（现有模块）
        self.material_page = MaterialManagement()
        self.right_content.addWidget(self.material_page)
        # 资源管理页面（新增）
        self.resource_page = ResourceManagement()
        self.right_content.addWidget(self.resource_page)
        # 生产订单页面
        self.production_order_page = ProductionOrderManagement()
        self.right_content.addWidget(self.production_order_page)
        # 工序模板页面
        self.process_template_page = ProcessTemplateManagement()
        self.right_content.addWidget(self.process_template_page)
        # 工序路线页面
        self.Process_Route_page = ProcessRouteManagement()
        self.right_content.addWidget(self.Process_Route_page)
        
        # 其他占位页面
        self.customer_page = self.create_placeholder_page("客户管理模块开发中...")
        self.supplier_page = self.create_placeholder_page("供应商管理模块开发中...")        
        self.scheduling_page = self.create_placeholder_page("排程管理模块开发中...")        
        self.user_page = self.create_placeholder_page("用户管理模块开发中...")
        self.role_page = self.create_placeholder_page("角色权限模块开发中...")
        self.log_page = self.create_placeholder_page("操作日志模块开发中...")
        
        # 添加到堆叠窗口
        self.right_content.addWidget(self.customer_page)
        self.right_content.addWidget(self.supplier_page)
        
        self.right_content.addWidget(self.scheduling_page)        
        self.right_content.addWidget(self.user_page)
        self.right_content.addWidget(self.role_page)
        self.right_content.addWidget(self.log_page)
        
    def create_placeholder_page(self, text):
        """创建占位页面"""
        page = QWidget()
        layout = QVBoxLayout(page)
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setFont(QFont("SimHei", 12))
        layout.addWidget(label)
        return page
        
    def bind_menu_actions(self):
        """绑定菜单点击事件"""
        self.left_menu.itemClicked.connect(self.on_menu_clicked)
        
    def on_menu_clicked(self, item, column):
        """菜单点击事件处理"""
        # 根据点击的菜单项切换到对应的页面
        if item == self.material_item:
            self.right_content.setCurrentWidget(self.material_page)
        elif item == self.customer_item:
            self.right_content.setCurrentWidget(self.customer_page)
        elif item == self.supplier_item:
            self.right_content.setCurrentWidget(self.supplier_page)        
        elif item == self.scheduling_item:
            self.right_content.setCurrentWidget(self.scheduling_page)        
        elif item == self.user_item:
            self.right_content.setCurrentWidget(self.user_page)
        elif item == self.role_item:
            self.right_content.setCurrentWidget(self.role_page)
        elif item == self.log_item:
            self.right_content.setCurrentWidget(self.log_page)
        elif item == self.resource_item:  # 新增资源管理页面切换
            self.right_content.setCurrentWidget(self.resource_page)
        elif item == self.production_order_item: # 新增生产订单页面切换
            self.right_content.setCurrentWidget(self.production_order_page)
        elif item == self.process_template_item: # 新增工序模板页面切换
            self.right_content.setCurrentWidget(self.process_template_page)
        elif item == self.ProcessRoute_item: # 新增工序路线页面切换
            self.right_content.setCurrentWidget(self.Process_Route_page)