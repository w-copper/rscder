import logging
import os
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QAction, QActionGroup, QLabel, QFileDialog
from gui.about import AboutDialog
from gui.project import Create
from utils.project import Project

class ActionManager(QtCore.QObject):

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

    def set_menus(self, menubar):
        self.menubar = menubar
        self.file_menu = menubar.addMenu('&文件')
        # self.view_menu = menubar.addMenu('&视图')
        self.basic_menu = menubar.addMenu('&基本工具')
        self.preop_menu = menubar.addMenu('&预处理')
        self.change_detection_menu = menubar.addMenu('&变化检测')
        self.special_chagne_detec_menu = menubar.addMenu('&专题变化检测')
        self.postop_menu = menubar.addMenu('&后处理')
        self.eval_menu = menubar.addMenu('&评估')
        self.help_menu = menubar.addMenu('&帮助')
    
    def set_toolbar(self, toolbar):
        self.toolbar = toolbar
        self.toolbar.setIconSize(QtCore.QSize(24, 24))
    
    def set_status_bar(self, status_bar):
        self.status_bar = status_bar
    
    def set_actions(self):
        '''
        File menu
        '''
        project_create = self.add_action(QAction('&工程创建', self.w_parent), 'File')
        project_open = self.add_action(QAction('&打开工程', self.w_parent), 'File')
        project_save = self.add_action(QAction('&保存工程', self.w_parent), 'File')
        data_load = self.add_action(QAction('&数据加载', self.w_parent), 'File')
        view_setting = self.add_action(QAction('&界面定制', self.w_parent), 'File')
        exit_app = self.add_action(QAction('&退出', self.w_parent), 'File')
        project_create.triggered.connect(self.project_create)
        project_open.triggered.connect(self.project_open)
        project_save.triggered.connect(self.project_save)
        data_load.triggered.connect(self.data_load)
        view_setting.triggered.connect(self.view_setting)
        exit_app.triggered.connect(self.w_parent.close)

        self.allways_enable.append(project_create, project_open, exit_app, view_setting)
        self.init_enable.append(project_save, data_load)
        
        self.file_menu.addAction(project_create)
        self.file_menu.addAction(project_open)
        self.file_menu.addAction(project_save)
        self.file_menu.addAction(data_load)
        self.file_menu.addAction(view_setting)
        self.file_menu.addAction(exit_app)

        if self.toolbar is not None:
            self.toolbar.addAction(project_create)
            self.toolbar.addAction(project_open)
            self.toolbar.addAction(project_save)

        '''
        Basic menu
        '''
        grid_line = self.add_action(QAction('&网格线', self.w_parent), 'Basic')
        grid_line.setCheckable(True)
        grid_line.setChecked(True)
        
        zomm_in = self.add_action(QAction('&放大', self.w_parent), 'Basic')
        zomm_out = self.add_action(QAction('&缩小', self.w_parent), 'Basic')
        pan = self.add_action(QAction('&漫游', self.w_parent), 'Basic')
        locate = self.add_action(QAction('&定位', self.w_parent), 'Basic')

        

        self.basic_menu.addAction(grid_line)
        self.basic_menu.addAction(zomm_in)
        self.basic_menu.addAction(zomm_out)
        self.basic_menu.addAction(pan)
        self.basic_menu.addAction(locate)

        '''
        Preop menu
        '''
        morphology_filter = self.add_action(QAction('&形态学滤波', self.w_parent), 'filter')
        lee_filter = self.add_action(QAction('&Lee滤波', self.w_parent), 'filter')
        auto_filter = self.add_action(QAction('&自适应滤波-自主', self.w_parent), 'filter')
        auto_filter_no_params = self.add_action(QAction('自动滤波（无参自适应滤波）-自主', self.w_parent), 'filter')
        double_filter = self.add_action(QAction('&双边滤波', self.w_parent), 'filter')
        align_action = self.add_action(QAction('&配准', self.w_parent), 'align')
        filter_action_group = self.get_action_group('filter')

        filter_menu = self.preop_menu.addMenu('&滤波')
        for action in filter_action_group.actions():
            filter_menu.addAction(action)
        
        # self.preop_menu.addActionGroup(filter_action_group)
        self.preop_menu.addAction(align_action)

        if self.toolbar is not None:
            self.toolbar.addAction(morphology_filter)
            self.toolbar.addAction(lee_filter)
            self.toolbar.addAction(auto_filter)
            self.toolbar.addAction(auto_filter_no_params)
            self.toolbar.addAction(double_filter)

        '''
        Change detection menu
        '''
        diff_method = self.add_action(QAction('&差分法', self.w_parent), 'unsuper_change_detection')
        log_diff = self.add_action(QAction('&对数差分法', self.w_parent), 'unsuper_change_detection')
        lsts_ = self.add_action(QAction('&LSTS法', self.w_parent), 'unsuper_change_detection')
        lhba = self.add_action(QAction('&LHBA法', self.w_parent), 'unsuper_change_detection')
        aht = self.add_action(QAction('&AHT法', self.w_parent), 'unsuper_change_detection')
        kpvd = self.add_action(QAction('&KPVD法', self.w_parent), 'unsuper_change_detection')
        mohd = self.add_action(QAction('&MOHD法', self.w_parent), 'unsuper_change_detection')
        sh = self.add_action(QAction('&SH法', self.w_parent), 'unsuper_change_detection')
        cva = self.add_action(QAction('&CVA法', self.w_parent), 'unsuper_change_detection')
        mls = self.add_action(QAction('&MLS法', self.w_parent), 'unsuper_change_detection')
        pca_kmean = self.add_action(QAction('&PCA-KMean法', self.w_parent), 'unsuper_change_detection')
        semi_fcm = self.add_action(QAction('&Semi-FCM法', self.w_parent), 'unsuper_change_detection')
        mls_svm = self.add_action(QAction('&MLS-SVM法', self.w_parent), 'unsuper_change_detection')
        cva_fcm = self.add_action(QAction('&CVA-FCM法', self.w_parent), 'unsuper_change_detection')
        cva_emgmm = self.add_action(QAction('&CVA-EMGMM法', self.w_parent), 'unsuper_change_detection')
        gwdm = self.add_action(QAction('&GWDM法', self.w_parent), 'unsuper_change_detection')

        mrf = self.add_action(QAction('&MRF法', self.w_parent), 'super_change_detection')
        mad = self.add_action(QAction('&MAD法', self.w_parent), 'super_change_detection')
        irmad = self.add_action(QAction('&IRMAD法', self.w_parent), 'super_change_detection')

        dcva = self.add_action(QAction('&DCVA法', self.w_parent), 'ai_change_detection')
        dp_fcn = self.add_action(QAction('&DP-FCN法', self.w_parent), 'ai_change_detection')
        rcnn = self.add_action(QAction('&RCNN法', self.w_parent), 'ai_change_detection')

        if self.toolbar is not None:
            self.toolbar.addAction(diff_method)
            self.toolbar.addAction(log_diff)
            self.toolbar.addAction(lsts_)
            self.toolbar.addAction(lhba)
            

        unsuper_change_detection = self.get_action_group('unsuper_change_detection')
        super_change_detection = self.get_action_group('super_change_detection')
        ai_change_detection = self.get_action_group('ai_change_detection')
        unsuper_menu = self.change_detection_menu.addMenu('&非监督')
        for action in unsuper_change_detection.actions():
            unsuper_menu.addAction(action)
        super_menu = self.change_detection_menu.addMenu('&监督')
        for action in super_change_detection.actions():
            super_menu.addAction(action)
        ai_menu = self.change_detection_menu.addMenu('&AI')
        for action in ai_change_detection.actions():
            ai_menu.addAction(action)

        # self.change_detection_menu.addActionGroup(super_change_detection)
        # self.change_detection_menu.addActionGroup(ai_change_detection)

        '''
        Special change detection menu
        '''

        water_change = self.add_action(QAction('&水体变化', self.w_parent), 'special_change_detection')
        vegetation_change = self.add_action(QAction('&植被变化', self.w_parent), 'special_change_detection')
        build_change = self.add_action(QAction('&房屋变化', self.w_parent), 'special_change_detection')

        self.special_chagne_detec_menu.addAction(water_change)
        self.special_chagne_detec_menu.addAction(vegetation_change)
        self.special_chagne_detec_menu.addAction(build_change)

        '''
        Postop menu
        '''
        slide_window = self.add_action(QAction('&滑动窗口法', self.w_parent), 'noise_reduction')
        density = self.add_action(QAction('&密度法', self.w_parent), 'noise_reduction')

        raster_export = self.add_action(QAction('&二值栅格数据导出', self.w_parent), 'export')
        txt_pos_export = self.add_action(QAction('&兼容ArcMap的坐标Txt文件', self.w_parent), 'export')
        render_export = self.add_action(QAction('&渲染图像导出', self.w_parent), 'export')

        noise_reduction = self.get_action_group('noise_reduction')
        export = self.get_action_group('export')

        noise_reduction_menu = self.postop_menu.addMenu('&噪声抑制')
        for action in noise_reduction.actions():
            noise_reduction_menu.addAction(action)
        export_menu = self.postop_menu.addMenu('&导出')
        for action in export.actions():
            export_menu.addAction(action)
        
        # self.postop_menu.addActionGroup(noise_reduction)
        # self.postop_menu.addActionGroup(export)

        '''
        Evaluation menu
        '''

        evaluation = self.add_action(QAction('&评估', self.w_parent), 'evaluation')
        self.eval_menu.addAction(evaluation)

        '''
        Help menu
        '''
        about = self.add_action(QAction('&关于', self.w_parent), 'about')
        about.triggered.connect(lambda : AboutDialog(self.w_parent).show())
        self.help_menu.addAction(about)

        self.message_box.info('Menu init finished')
        self.message_box.info(self.actions.keys())
        for group in self.action_groups.keys():
            self.message_box.info('%s:' % (group))
            for action in self.action_groups[group].actions():
                action.setEnabled(False)
                self.message_box.info('\t%s' % (action.text()))

        '''
        Enabled actions
        '''
        about.setEnabled(True)
        project_create.setEnabled(True)
        project_open.setEnabled(True)

        Project().project_init.connect(self.project_init)

        if self.status_bar is not None:
            corr_widget = QLabel(self.status_bar)
            # corr_widget.setLineWidth(200)
            corr_widget.setFixedWidth(200)
            self.status_bar.addWidget(corr_widget)
            scale_widget = QLabel(self.status_bar)
            scale_widget.setFixedWidth(200)
            self.status_bar.addWidget(scale_widget)
            self.double_map.corr_changed.connect(corr_widget.setText)
            self.double_map.scale_changed.connect(scale_widget.setText)

    def project_create(self):
        project = Project()
        if project.is_init:
            project.save()
        
        projec_create = Create(self.w_parent)
        if(projec_create.exec_()):
            project.setup(os.path.join(projec_create.file, projec_create.name + '.prj'))
            project.is_init = True
            project.cell_size = projec_create.cell_size
    
    def project_init(self, state):
        self.message_box.info('Project init')
        for group in self.action_groups.keys():
            # self.message_box.info('%s:' % (group))
            for action in self.action_groups[group].actions():
                action.setEnabled(state)
                # self.message_box.info('\t%s' % (action.text()))
        
        self.message_box.info('Project init finished')

    def project_open(self):
        if Project().is_init:
            Project().save()
            
        project_file = QFileDialog.getOpenFileName(self.w_parent, '打开工程', '.', '*.prj')
        if project_file[0] != '':
            Project().clear()
            Project().setup(project_file[0])

    def project_save(self):
        if Project().is_init:
            Project().save()

    def data_load(self):
        if Project().is_init:
            Project().save()

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
            self.action_group_actions[group] = action
        return action

    def get_action(self, action_name, group_name=None):
        if action_name in self.actions:
            return self.actions[action_name]
        else:
            if group_name is None:
                return None
            else:
                if group_name not in self.action_group_actions:
                    return None
                else:
                    group =  self.action_group_actions[group_name]
                    for action in group.actions():
                        if action.text() == action_name:
                            return action
        return None

    def get_action_group(self, group_name):
        return self.action_groups[group_name]

    def get_action_group_action(self, group_name):
        return self.action_group_actions[group_name]

    def get_action_group_actions(self, group_name):
        return self.action_group_actions[group_name].actions()

    def get_actions(self):
        return self.actions