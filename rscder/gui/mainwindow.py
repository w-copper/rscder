import pdb
from PyQt5.QtWidgets import  QWidget, QApplication, QMainWindow, QToolBox
from PyQt5.QtCore import Qt, QSize
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui
from PyQtAds import QtAds
from rscder.gui.actions import ActionManager
from rscder.gui.layertree import LayerTree
from rscder.gui.mapcanvas import DoubleCanvas
from rscder.gui.messagebox import MessageBox
from rscder.gui.result import ResultTable
from rscder.plugins.loader import PluginLoader
from rscder.utils import Settings
from rscder.utils.project import Project

class MainWindow(QMainWindow):

    def __init__(self, parent=None, **kargs):
        super().__init__(parent) 
        self.current_instance = kargs.get('current_instance', 0)
        if self.current_instance > 0:   
            self.setWindowTitle(QApplication.applicationName() + ' ' + str(self.current_instance))
        else:
            self.setWindowTitle(QApplication.applicationName())
        self.setWindowIcon(QIcon(":/icons/change_detect.png"))
        
        self.setAcceptDrops(True) 
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.set_toolbar()
        self.set_pannels()
        Project(self).connect(
                self.double_map,
                self.layer_tree, 
                self.message_box, 
                self.result_box)
        self.layer_tree.tree_changed.connect(self.double_map.layer_changed)
        self.layer_tree.result_clicked.connect(self.result_box.on_result)
        self.result_box.on_item_click.connect(self.double_map.zoom_to_result)
        self.result_box.on_item_changed.connect(Project().change_result)
        self.layer_tree.zoom_to_layer_signal.connect(self.double_map.zoom_to_layer)

        self.action_manager = ActionManager(
            self.double_map, 
            self.layer_tree, 
            self.follow_box, 
            self.result_box, 
            self.message_box, self)
        self.action_manager.set_menus(self.menuBar())
        self.action_manager.set_toolbar(self.toolbar)
        self.action_manager.set_status_bar(self.statusBar())
        self.action_manager.set_actions()

        PluginLoader(dict(
            layer_tree=self.layer_tree,
            pair_canvas=self.double_map,
            message_box=self.message_box,
            result_table=self.result_box,
            project=Project(self),
            mainwindow=self,
            toolbar=self.toolbar,
            statusbar=self.statusBar(),
            **self.action_manager.menus
        )).load_plugin()

        self.resize(*Settings.General().size)


    def set_toolbar(self):
        self.toolbar = self.addToolBar('Toolbar')
        self.toolbar.setMovable(False)
        self.toolbar.setFloatable(False)
        self.toolbar.setIconSize(QSize(32, 32))
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        self.toolbar.setLayoutDirection(Qt.LeftToRight)


    def set_pannels(self):
        
        self.dock_manager = QtAds.CDockManager(self)
        self.dock_manager.setContextMenuPolicy(Qt.CustomContextMenu)
        
        self.double_map = DoubleCanvas(self)
        central_dock_widget = QtAds.CDockWidget(self.tr("Canvas"))
        central_dock_widget.setWidget(self.double_map)
        central_dock_area = self.dock_manager.setCentralWidget(central_dock_widget)
        central_dock_area.setAllowedAreas(QtAds.DockWidgetArea.OuterDockAreas) 
        
        self.double_map.setContextMenuPolicy(Qt.CustomContextMenu)
        self.layer_tree = LayerTree(self)
        left_tool_box = QToolBox(self)
        
        self.follow_box = QWidget(self)
        self.eye_box = QWidget(self)
        left_tool_box.setContextMenuPolicy(Qt.CustomContextMenu)
        left_tool_box.addItem(self.layer_tree, self.tr("图层树"))
        left_tool_box.addItem(self.follow_box, self.tr("流程"))
        left_tool_box.addItem(self.eye_box, self.tr("鹰眼"))

        
        # self.layer_tree.setContextMenuPolicy(Qt.CustomContextMenu)

        def set_docker_fixed(docker):
            docker.setFeature(QtAds.ads.CDockWidget.DockWidgetFeature.DockWidgetClosable , False)
            docker.setFeature(QtAds.ads.CDockWidget.DockWidgetFeature.DockWidgetMovable , False)
            docker.setFeature(QtAds.ads.CDockWidget.DockWidgetFeature.DockWidgetFloatable , False)

        self.layer_tree_dock = QtAds.CDockWidget(self.tr("面板"), self)
        
        self.layer_tree_dock.setWidget(left_tool_box)
        left_area = self.dock_manager.addDockWidget(QtAds.DockWidgetArea.LeftDockWidgetArea, self.layer_tree_dock, central_dock_area)
        self.left_arre = left_area

        self.result_dock = QtAds.CDockWidget(self.tr("结果"))
        self.result_box = ResultTable(self)
        self.result_dock.setWidget(self.result_box)
        bottom_area = self.dock_manager.addDockWidget(QtAds.DockWidgetArea.BottomDockWidgetArea, self.result_dock, central_dock_area)
        self.message_dock = QtAds.CDockWidget(self.tr("消息"))
        self.message_box = MessageBox(self, MessageBox.INFO)
        self.message_dock.setWidget(self.message_box)
        self.dock_manager.addDockWidget(QtAds.DockWidgetArea.RightDockWidgetArea, self.message_dock, bottom_area)
        self.bottom_area = bottom_area

        set_docker_fixed(self.layer_tree_dock)
        set_docker_fixed(self.result_dock)
        set_docker_fixed(self.message_dock)

    def closeEvent(self, event):
        pass

    def resizeEvent(self, a0: QtGui.QResizeEvent) -> None:
        Settings.General().size = (a0.size().width(), a0.size().height())
        return super().resizeEvent(a0)