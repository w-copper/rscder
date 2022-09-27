from threading import Thread
from plugins.misc.utils import Register
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QGroupBox, QWidget, QComboBox, QVBoxLayout


class MISCPlugin(BasicPlugin):

    @staticmethod
    def info():
        return {
            'name': 'MISC Plugin',
            'description': '基本开发工具',
            'author': 'Wangtong',
            'version': '1.0.0',
        }
    
    def set_action(self):
        pass


class AlgFrontend(object):

    @staticmethod
    def get_name():
        return None

    @staticmethod
    def get_icon():
        return None

    @staticmethod
    def get_widget(parent=None):
        return QWidget(parent)
    
    @staticmethod
    def get_params(widget=None):
        return dict()

    @staticmethod
    def run_alg(*args, **kargs):
        pass


class AlgSelectWidget(QGroupBox):

    def __init__(self, parent= None, registery:Register = None) -> None:
        super().__init__(parent)
        self.reg = registery
        if registery is None:
            return
        self.setTitle(registery.name)
        self.selectbox = QComboBox(self)
        self.selectbox.addItem('--', None)
        for key in self.reg.keys():
            alg:AlgFrontend = self.reg[key]
            if alg.get_name() is None:
                name = key
            else:
                name = alg.get_name()
            self.selectbox.addItem(name, key)
        
        self.vbox = QVBoxLayout(self)
        self.vbox.addWidget(self.selectbox)
        
        self.params_widget = QWidget()
        self.vbox.addWidget(self.params_widget)

        self.selectbox.currentIndexChanged.connect(self.on_changed)

    def on_changed(self, index):
        if index == 0:
            self.alg = None
            self.params_widget.setParent(None)
            self.vbox.removeWidget(self.params_widget)
            self.params_widget = QWidget(self)
            self.vbox.addWidget(self.params_widget)
            return

        self.alg:AlgFrontend = self.reg[self.selectbox.itemData(index)]
        self.params_widget.setParent(None)
        self.vbox.removeWidget(self.params_widget)
        self.params_widget = self.alg.get_widget(self)
        self.vbox.addWidget(self.params_widget)

        

    def get_alg_and_params(self):
        if self.selectbox.currentIndex() == 0:
            return None, None
        
        return self.alg, self.alg.get_params(self.params_widget)