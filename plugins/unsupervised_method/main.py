from functools import partial
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
from follow import FOLLOW

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
        totalvlayout.addStretch(1)
        hbox = QHBoxLayout()
        hbox.addStretch(1)
        hbox.addWidget(buttonbox)
        totalvlayout.addLayout(hbox)
        # totalvlayout.addStretch()
        
        self.setLayout(totalvlayout)

@FOLLOW.register
class UnsupervisedCDFollow(AlgFrontend):

    @staticmethod
    def get_name():
        return '无监督变化检测'

    @staticmethod
    def get_icon():
        return IconInstance().UNSUPERVISED
    
    @staticmethod
    def get_widget(parent=None):
        widget = QWidget(parent)
        layer_combox = PairLayerCombox(widget)
        layer_combox.setObjectName('layer_combox')
        
        filter_select = AlgSelectWidget(widget, FILTER)
        filter_select.setObjectName('filter_select')
        unsupervised_select = AlgSelectWidget(widget, UNSUPER_CD)
        unsupervised_select.setObjectName('unsupervised_select')
        thres_select = AlgSelectWidget(widget, THRES)
        thres_select.setObjectName('thres_select')

        totalvlayout=QVBoxLayout()
        totalvlayout.addWidget(layer_combox)
        totalvlayout.addWidget(filter_select)
        totalvlayout.addWidget(unsupervised_select)
        totalvlayout.addWidget(thres_select)
        totalvlayout.addStretch()
        
        widget.setLayout(totalvlayout)

        return widget

    @staticmethod
    def get_params(widget:QWidget=None):
        if widget is None:
            return dict()
        
        layer_combox = widget.findChild(PairLayerCombox, 'layer_combox')
        filter_select = widget.findChild(AlgSelectWidget, 'filter_select')
        unsupervised_select = widget.findChild(AlgSelectWidget, 'unsupervised_select')
        thres_select = widget.findChild(AlgSelectWidget, 'thres_select')

        layer1=layer_combox.layer1        
        pth1 = layer_combox.layer1.path
        pth2 = layer_combox.layer2.path

        falg, fparams =  filter_select.get_alg_and_params()
        cdalg, cdparams = unsupervised_select.get_alg_and_params()
        thalg, thparams = thres_select.get_alg_and_params()
        
        if cdalg is None or thalg is None:
            return dict()

        return dict(
            layer1=layer1,
            pth1 = pth1,
            pth2 = pth2,
            falg = falg,
            fparams = fparams,
            cdalg = cdalg,
            cdparams = cdparams,
            thalg = thalg,
            thparams = thparams,
        )

    @staticmethod
    def run_alg(layer1=None,
            pth1 = None,
            pth2 = None,
            falg = None,
            fparams = None,
            cdalg = None,
            cdparams = None,
            thalg = None,
            thparams = None,
            send_message = None):
        
        if cdalg is None or thalg is None:
            return

        name = layer1.name

        if falg is not None:
            pth1 = falg.run_alg(pth1, name=name, send_message= send_message, **fparams)
            pth2 = falg.run_alg(pth2, name=name, send_message= send_message, **fparams)

        
        cdpth = cdalg.run_alg(pth1, pth2, layer1.layer_parent,  send_message= send_message,**cdparams)
        thpth = thalg.run_alg(cdpth, name=name, send_message= send_message, **thparams)

        table_layer(thpth,layer1,name, send_message)




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

        for key in UNSUPER_CD.keys():
            alg:AlgFrontend = UNSUPER_CD[key]
            if alg.get_name() is None:
                name = key
            else:
                name = alg.get_name()
            
            action = QAction(name, unsupervised_menu)
            func = partial(self.run_cd, alg)
            action.triggered.connect(func)

            unsupervised_menu.addAction(action)


    def run_cd(self, alg):
        print(alg.get_name())
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
        cdparams = w.alg.get_params(w.param_widget)
        thalg, thparams = w.thres_select.get_alg_and_params()
        
        if cdalg is None or thalg is None:
            return

        if falg is not None:
            pth1 = falg.run_alg(pth1, name=name, send_message=self.send_message, **fparams)
            pth2 = falg.run_alg(pth2, name=name, send_message=self.send_message, **fparams)

        
        cdpth = cdalg.run_alg(pth1, pth2, layer1.layer_parent,  send_message=self.send_message,**cdparams)
        thpth = thalg.run_alg(cdpth, name=name, send_message=self.send_message, **thparams)

        table_layer(thpth,layer1,name,self.send_message)
        