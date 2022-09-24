from threading import Thread
from plugins.misc.main import AlgFrontend
from rscder.gui.actions import ActionManager
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QToolBar,  QMenu, QDialog, QHBoxLayout, QVBoxLayout, QPushButton,QWidget,QLabel,QLineEdit,QPushButton,QComboBox,QDialogButtonBox

from rscder.gui.layercombox import PairLayerCombox
from rscder.utils.icons import IconInstance
from filter_collection import FILTER
from .scripts import UNSUPER_CD
from thres import THRES
from misc import table_layer, AlgSelectWidget

class UnsupervisedCDMethod(QDialog):
    def __init__(self,parent=None, alg:AlgFrontend=None):
        super(UnsupervisedCDMethod, self).__init__(parent)
        self.alg = alg
        self.setWindowTitle('无监督变化检测:{}'.format(alg.get_name()))
        self.setWindowIcon(IconInstance().LOGO)
        self.initUI()
        self.setMinimumWidth(500)

    def initUI(self):
        #图层
        self.layer_combox = PairLayerCombox(self)
        layerbox = QHBoxLayout()
        layerbox.addWidget(self.layer_combox)
        
        self.filter_select = AlgSelectWidget(self, FILTER)
        self.param_widget = self.alg.get_widget(self)
        self.unsupervised_menu = self.param_widget
        self.thres_select = AlgSelectWidget(self, THRES)

        self.ok_button = QPushButton('确定', self)
        self.ok_button.setIcon(IconInstance().OK)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)

        self.cancel_button = QPushButton('取消', self)
        self.cancel_button.setIcon(IconInstance().CANCEL)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setDefault(False)
        buttonbox=QDialogButtonBox(self)
        buttonbox.addButton(self.ok_button,QDialogButtonBox.NoRole)
        buttonbox.addButton(self.cancel_button,QDialogButtonBox.NoRole)
        buttonbox.setCenterButtons(True)

        totalvlayout=QVBoxLayout()
        totalvlayout.addLayout(layerbox)
        totalvlayout.addWidget(self.filter_select)
        if self.param_widget is not None:
            totalvlayout.addWidget(self.param_widget)
        totalvlayout.addWidget(self.thres_select)
        totalvlayout.addWidget(buttonbox)
        totalvlayout.addStretch()
        
        self.setLayout(totalvlayout)

class UnsupervisedCD(QDialog):
    def __init__(self,parent=None):
        super(UnsupervisedCD, self).__init__(parent)
        self.setWindowTitle('无监督变化检测')
        self.setWindowIcon(IconInstance().LOGO)
        self.setMinimumWidth(600)
        self.initUI()

    def initUI(self):
        #图层
        self.layer_combox = PairLayerCombox(self)
        layerbox = QHBoxLayout()
        layerbox.addWidget(self.layer_combox)
        
        self.filter_select = AlgSelectWidget(self, FILTER)
        self.unsupervised_select = AlgSelectWidget(self, UNSUPER_CD)
        self.thres_select = AlgSelectWidget(self, THRES)

        self.ok_button = QPushButton('确定', self)
        self.ok_button.setIcon(IconInstance().OK)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)

        self.cancel_button = QPushButton('取消', self)
        self.cancel_button.setIcon(IconInstance().CANCEL)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setDefault(False)
        buttonbox=QDialogButtonBox(self)
        buttonbox.addButton(self.ok_button,QDialogButtonBox.NoRole)
        buttonbox.addButton(self.cancel_button,QDialogButtonBox.NoRole)
        buttonbox.setCenterButtons(True)

        totalvlayout=QVBoxLayout()
        totalvlayout.addLayout(layerbox)
        totalvlayout.addWidget(self.filter_select)
        totalvlayout.addWidget(self.unsupervised_select)
        totalvlayout.addWidget(self.thres_select)
        totalvlayout.addWidget(buttonbox)
        totalvlayout.addStretch()
        
        self.setLayout(totalvlayout)



class UnsupervisedPlugin(BasicPlugin):


    @staticmethod
    def info():
        return {
            'name': 'UnsupervisedPlugin',
            'description': 'UnsupervisedPlugin',
            'author': 'RSCDER',
            'version': '1.0.0',
        }

    def set_action(self):
        unsupervised_menu = QMenu('&无监督变化检测', self.mainwindow)
        unsupervised_menu.setIcon(IconInstance().UNSUPERVISED)
        ActionManager().change_detection_menu.addMenu(unsupervised_menu)
        basic_diff_method_in_one = QAction(IconInstance().UNSUPERVISED, '&无监督变化检测', self.mainwindow)
        basic_diff_method_in_one.triggered.connect(self.run) 
        toolbar:QToolBar = ActionManager().add_toolbar('无监督变化检测')
        toolbar.addAction(basic_diff_method_in_one)
        # self.mainwindow.addToolbar(toolbar)
        # print(UNSUPER_CD.keys())
        for key in UNSUPER_CD.keys():
            alg:AlgFrontend = UNSUPER_CD[key]
            if alg.get_name() is None:
                name = key
            else:
                name = alg.get_name()
            
            action = QAction(name, unsupervised_menu)
            action.triggered.connect(lambda : self.run_cd(alg))

            unsupervised_menu.addAction(action)

    def run(self):
        myDialog= UnsupervisedCD(self.mainwindow)
        myDialog.show()
        if myDialog.exec_()==QDialog.Accepted:
            w=myDialog
            t=Thread(target=self.run_alg,args=(w,))
            t.start()

    def run_cd(self, alg):
        dialog = UnsupervisedCDMethod(self.mainwindow, alg)
        dialog.show()

        if dialog.exec_() == QDialog.Accepted:
            t = Thread(target=self.run_cd_alg, args=(dialog,))
            t.start()
    
    def run_cd_alg(self, w:UnsupervisedCDMethod):
        
        layer1=w.layer_combox.layer1        
        pth1 = w.layer_combox.layer1.path
        pth2 = w.layer_combox.layer2.path
        name = layer1.layer_parent.name

        falg, fparams =  w.filter_select.get_alg_and_params()
        cdalg = w.alg
        cdparams = w.alg.get_params()
        thalg, thparams = w.thres_select.get_alg_and_params()
        
        if cdalg is None or thalg is None:
            return

        if falg is not None:
            pth1 = falg.run_alg(pth1, name=name, send_message=self.send_message, **fparams)
            pth2 = falg.run_alg(pth2, name=name, send_message=self.send_message, **fparams)

        
        cdpth = cdalg.run_alg(pth1, pth2, layer1.layer_parent,  send_message=self.send_message,**cdparams)
        thpth = thalg.run_alg(cdpth, name=name, send_message=self.send_message, **thparams)

        table_layer(thpth,layer1,name,self.send_message)

    def run_alg(self,w:UnsupervisedCD):

        layer1=w.layer_combox.layer1        
        pth1 = w.layer_combox.layer1.path
        pth2 = w.layer_combox.layer2.path
        name = layer1.layer_parent.name

        falg, fparams =  w.filter_select.get_alg_and_params()
        cdalg, cdparams = w.unsupervised_select.get_alg_and_params()
        thalg, thparams = w.thres_select.get_alg_and_params()
        
        if cdalg is None or thalg is None:
            return

        if falg is not None:
            pth1 = falg.run_alg(pth1, name=name, send_message=self.send_message, **fparams)
            pth2 = falg.run_alg(pth2, name=name, send_message=self.send_message, **fparams)

        
        cdpth = cdalg.run_alg(pth1, pth2, layer1.layer_parent,  send_message=self.send_message,**cdparams)

        
        thpth = thalg.run_alg(cdpth, name=name, send_message=self.send_message, **thparams)

        table_layer(thpth,layer1,name,self.send_message)