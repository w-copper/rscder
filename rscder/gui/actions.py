import logging
import os
from pathlib import Path
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt, QSize, QSettings, pyqtSignal
from PyQt5.QtWidgets import QAction, QActionGroup, QLabel, QFileDialog, QMenuBar, QToolBar, QVBoxLayout, QComboBox
from rscder.gui import project
from rscder.gui.project import Create
from rscder.utils.icons import IconInstance
from rscder.utils.project import Project
from rscder.utils.misc import singleton
from rscder.gui.plugins import PluginDialog
from rscder.utils.setting import Settings
from rscder.gui.load import loader
def get_action_manager() -> 'ActionManager':
    return ActionManager()

@singleton
class ActionManager(QtCore.QObject):

    instance = None

    def __init__(self,
            double_map,
            layer_tree,
            follow_box,
            result_box,
            message_box,
            parent=None):
        super().__init__(parent)
        self.w_parent = parent
        self.actions = {}
        self.action_groups = {}
        self.action_group_actions = {}

        self.toolbars = {}

        self.double_map = double_map
        self.layer_tree = layer_tree
        self.follow_box = follow_box
        self.result_box = result_box
        self.message_box = message_box

        self.allways_enable = []
        self.init_enable = []
        self.dataload_enable = []

        self.toolbar = None
        self.menubar = None
        self.status_bar = None

    def set_menus(self, menubar:QMenuBar):
        self.menubar = menubar
        self.file_menu = menubar.addMenu( '&文件')
        self.basic_menu = menubar.addMenu( '&基础工具')
        self.filter_menu = self.basic_menu.addMenu(IconInstance().FILTER, '&滤波处理')
        self.change_detection_menu = menubar.addMenu('&通用变化检测')
        # self.unsupervised_menu = self.change_detection_menu.addMenu(IconInstance().UNSUPERVISED, '&无监督变化检测')
        self.supervised_menu = self.change_detection_menu.addMenu(IconInstance().SUPERVISED,'&监督变化检测')
        self.ai_menu = self.change_detection_menu.addMenu(IconInstance().AI_DETECT,'&AI变化检测')
        self.special_chagne_detec_menu = menubar.addMenu( '&专题变化检测')
        self.water_menu = self.special_chagne_detec_menu.addMenu(IconInstance().WATER_CHANGE,'&水体变化检测')
        self.veg_menu = self.special_chagne_detec_menu.addMenu(IconInstance().VEGETATION,'&植被变化检测')
        self.road_menu = self.special_chagne_detec_menu.addMenu(IconInstance().ROAD_CHANGE,'&道路变化检测')
        self.landslide_menu = self.special_chagne_detec_menu.addMenu(IconInstance().LANDSIDE,'&滑坡变化检测')

        self.seg_chagne_detec_menu = menubar.addMenu('&分类后变化检测')
        self.postop_menu = menubar.addMenu( '&检测后处理')

        self.noise_menu = self.postop_menu.addMenu(IconInstance().NOISE,'&噪声处理')
        self.position_menu = self.postop_menu.addMenu(IconInstance().LOCATION,'&变化位置估计')
        self.evaluation_menu = self.postop_menu.addMenu(IconInstance().EVALUATION,'&定量评价')
        self.export_menu = self.postop_menu.addMenu(IconInstance().DOCUMENT,'&结果导出')

        self.view_menu = menubar.addMenu('&视图')
        self.plugin_menu = menubar.addMenu('&插件')
        self.help_menu = menubar.addMenu( '&帮助')

        # vbox = QVBoxLayout()
        # follow_combox = QComboBox(self.follow_box)
        # vbox.addWidget(follow_combox)
        # self.follow_box.setLayout(vbox)
        

    def set_toolbar(self, toolbar):
        self.toolbar:QToolBar = toolbar
        self.toolbar.setIconSize(QtCore.QSize(24, 24))
        
    def add_toolbar(self, name=None):
        
        toolbar = self.w_parent.addToolBar(name)
        toolbar.setMovable(True)
        toolbar.setFloatable(False)
        toolbar.setIconSize(QSize(32, 32))
        toolbar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        toolbar.setContextMenuPolicy(Qt.PreventContextMenu)
        toolbar.setLayoutDirection(Qt.LeftToRight)
        
        return toolbar

    def set_status_bar(self, status_bar):
        self.status_bar = status_bar
    
    def set_actions(self):
        '''
        File menu
        '''
        project_create = self.add_action(QAction(IconInstance().CREATE, '&工程创建', self.w_parent), 'File')
        project_open = self.add_action(QAction(IconInstance().OPEN, '&打开工程', self.w_parent), 'File')
        project_save = self.add_action(QAction(IconInstance().SAVE,'&保存工程', self.w_parent), 'File')
        data_load = self.add_action(QAction(IconInstance().DATA_LOAD,'&数据加载', self.w_parent), 'File')
        view_setting = self.add_action(QAction(IconInstance().VIEW_SETTING,'&界面定制', self.w_parent), 'File')
        exit_app = self.add_action(QAction(IconInstance().EXCIT,'&退出', self.w_parent), 'File')
        project_create.triggered.connect(self.project_create)
        project_open.triggered.connect(self.project_open)
        project_save.triggered.connect(self.project_save)
        data_load.triggered.connect(self.data_load)
        
        view_setting.triggered.connect(self.view_setting)
        exit_app.triggered.connect(self.w_parent.close)

        self.allways_enable.extend([project_create, project_open, exit_app, view_setting])
        self.init_enable.extend([project_save, data_load])
        
        self.file_menu.addAction(project_create)
        self.file_menu.addAction(project_open)
        self.file_menu.addAction(project_save)
        self.file_menu.addAction(data_load)
        # self.file_menu.addAction(view_setting)
        self.file_menu.addAction(exit_app)
        self.view_menu.addAction(view_setting)
        if self.toolbar is not None:
            self.toolbar.addAction(project_create)
            self.toolbar.addAction(project_open)
            self.toolbar.addAction(project_save)

        '''
        Basic menu
        '''
        # grid_line = self.add_action(QAction(IconInstance().GRID_ON,'&网格线', self.w_parent), 'Basic Line')
        # grid_line.setCheckable(True)
        # grid_line.setChecked(True)
        
        zomm_in = self.add_action(QAction(IconInstance().ZOOM_OUT,'&放大', self.w_parent), 'Basic')
        zomm_out = self.add_action(QAction(IconInstance().ZOOM_IN,'&缩小', self.w_parent), 'Basic')
        pan = self.add_action(QAction(IconInstance().PAN,'&漫游', self.w_parent), 'Basic')
        locate = self.add_action(QAction(IconInstance().ZOOM_TO,'&定位', self.w_parent), 'Basic')

        pan.setCheckable(True)
        pan.setChecked(True)
        zomm_out.setCheckable(True)
        zomm_out.setChecked(False)
        zomm_in.setCheckable(True)
        zomm_in.setChecked(False)
        
        toolbar = self.add_toolbar('Map')
        toolbar.addActions([pan, zomm_out, zomm_in, locate])

        self.double_map.connect_map_tool(pan, zomm_in, zomm_out)
        # self.double_map.connect_grid_show(grid_line)
    
        # self.view_menu.addAction(grid_line)
        self.view_menu.addSeparator()
        self.view_menu.addAction(pan)
        self.view_menu.addAction(zomm_in)
        self.view_menu.addAction(zomm_out)
        self.view_menu.addAction(locate)

        '''
        Plugin menu
        '''
        plugin_list = self.add_action(QAction(IconInstance().PLUGINS,'&插件列表', self.w_parent), 'Plugin')
        plugin_list.triggered.connect(self.plugin_list)

        # toolbar = self.add_toolbar('Plugin')
        # toolbar.addAction(plugin_list)

        self.plugin_menu.addAction(plugin_list)

        self.message_box.info('菜单初始化完成')
        self.message_box.info(self.actions.keys())

        '''
        Enabled actions
        '''
        # about.setEnabled(True)
        project_create.setEnabled(True)
        project_open.setEnabled(True)

        Project().project_init.connect(self.project_init)

        if self.status_bar is not None:
            corr_widget = QLabel(self.status_bar)
            # corr_widget.setLineWidth(200)
            corr_widget.setFixedWidth(250)
            self.status_bar.addWidget(corr_widget)
            scale_widget = QLabel(self.status_bar)
            scale_widget.setFixedWidth(250)
            self.status_bar.addWidget(scale_widget)
            self.double_map.corr_changed.connect(corr_widget.setText)
            self.double_map.scale_changed.connect(scale_widget.setText)

            lic_end_date = QLabel(self.status_bar)
            lic_end_date.setFixedWidth(200)
            lic_end_date.setText('有效期至：%s' % (Settings.General().end_date))
            self.status_bar.addPermanentWidget(lic_end_date)

    def plugin_list(self):
        dialog = PluginDialog(self.w_parent)
        dialog.show()

    def project_create(self):
        project = Project()

        projec_create = Create(self.w_parent)
        if(projec_create.exec_()):
            if project.is_init:
                project.save()
                project.clear()
            project.setup(projec_create.file, projec_create.name)
            project.cell_size = projec_create.cell_size
            project.max_memory = projec_create.max_memory
            project.save()
            self.message_box.info('工程创建成功')
    
    def project_init(self, state):
        # self.message_box.info('工程初始化完成')
        for group in self.action_groups.keys():
            # self.message_box.info('%s:' % (group))
            for action in self.action_groups[group].actions():
                action.setEnabled(state)
                # self.message_box.info('\t%s' % (action.text()))
        
        self.message_box.info('工程初始化完成')

    def project_open(self):
        if Project().is_init:
            Project().save()
            
        project_file = QFileDialog.getOpenFileName(self.w_parent, '打开工程', Settings.General().last_path, '*.prj')
        if project_file[0] != '':
            Project().clear()
            parent = str(Path(project_file[0]).parent)
            Settings.General().last_path = parent
            Project().setup(project_file[0])

    def project_save(self):
        if Project().is_init:
            Project().save()

    def data_load(self):
        if Project().is_init:
            Project().save()
        file_loader=loader(self.w_parent)
        file_loader.setModal(True)
        if(file_loader.exec_()):
            Project().add_layer(file_loader.path1,file_loader.path2,file_loader.style1,file_loader.style2)
            self.message_box.info('Data loaded')

    def view_setting(self):
        pass


    def add_action(self, action, group=None):
        if group is None:
            self.actions[action.text()] = action
        else:
            if group not in self.action_groups:
                self.action_groups[group] = QActionGroup(self.w_parent)
                self.action_groups[group].setExclusive(True)
            self.action_groups[group].addAction(action)

        return action

    def get_action(self, action_name, group_name=None):
        if action_name in self.actions:
            return self.actions[action_name]
        else:
            if group_name is None:
                return None
            else:
                if group_name not in self.action_groups:
                    return None
                else:
                    group =  self.action_groups[group_name]
                    for action in group.actions():
                        if action.text() == action_name:
                            return action
        return None

    def get_action_group(self, group_name):
        return self.action_groups[group_name]

    def get_actions(self):
        return self.actions