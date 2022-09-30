from functools import partial
from threading import Thread
from rscder.plugins.basic import BasicPlugin
from rscder.utils.icons import IconInstance
from rscder.gui.actions import ActionManager
from PyQt5 import QtWidgets, QtGui
from follow import FOLLOW
from misc import AlgFrontend

class FollowDialog(QtWidgets.QDialog):

    def __init__(self, parent=None, alg:AlgFrontend=None) -> None:
        super().__init__(parent)
        if alg is None:
            return
        self.setMinimumWidth(700)
        # self.setMinimumHeight(500)
        vbox = QtWidgets.QVBoxLayout()

        self.widget = alg.get_widget(self)
        vbox.addWidget(self.widget)
        
        self.ok_button = QtWidgets.QPushButton('确定', self)
        self.ok_button.setIcon(IconInstance().OK)
        self.ok_button.clicked.connect(self.accept)
        self.ok_button.setDefault(True)

        self.cancel_button = QtWidgets.QPushButton('取消', self)
        self.cancel_button.setIcon(IconInstance().CANCEL)
        self.cancel_button.clicked.connect(self.reject)
        self.cancel_button.setDefault(False)
        buttonbox= QtWidgets.QDialogButtonBox()
        buttonbox.addButton(self.ok_button,QtWidgets.QDialogButtonBox.NoRole)
        buttonbox.addButton(self.cancel_button,QtWidgets.QDialogButtonBox.NoRole)
        buttonbox.setCenterButtons(True)

        vbox.addWidget(buttonbox)
        vbox.addStretch()

        self.setLayout(vbox)
    
class FollowPlugin(BasicPlugin):

    @staticmethod
    def get_info():
        return {
            'name': 'Follow',
            'version': '1.0.0'
        }


    def set_action(self):
        follow_box:QtWidgets.QWidget = ActionManager().follow_box
        toolbar = ActionManager().add_toolbar('Follow')
        vbox = QtWidgets.QVBoxLayout(follow_box)

        combox = QtWidgets.QComboBox(follow_box)

        # print(FOLLOW.keys())
        for key in FOLLOW.keys():
            alg:AlgFrontend = FOLLOW[key]
            if alg.get_name() is None:
                name = key
            else:
                name = alg.get_name()
            combox.addItem(name, key)

            action = QtWidgets.QAction(alg.get_icon(), name, self.mainwindow)
            func = partial(self.run_dialog, alg)
            action.triggered.connect(func)
            toolbar.addAction(action)
        

        combox.currentIndexChanged.connect(self.on_change)

        vbox.addWidget(combox)

        self.current_widget = None

        
        self.combox = combox
        self.layout = vbox

        self.ok_button = QtWidgets.QPushButton('运行')
        self.ok_button.setIcon(IconInstance().OK)
        self.ok_button.clicked.connect(self.run)
        self.ok_button.setDefault(True)

        self.cancel_button = QtWidgets.QPushButton('重置')
        self.cancel_button.setIcon(IconInstance().CANCEL)
        self.cancel_button.clicked.connect(self.reset)
        self.cancel_button.setDefault(False)
        buttonbox= QtWidgets.QDialogButtonBox()
        buttonbox.addButton(self.ok_button,QtWidgets.QDialogButtonBox.NoRole)
        buttonbox.addButton(self.cancel_button,QtWidgets.QDialogButtonBox.NoRole)
        buttonbox.setCenterButtons(True)

        self.btn_box = buttonbox 
        follow_box.setLayout(vbox)
        # vbox.addStretch()
        self.on_change(0)

    def on_change(self, index):
        
        print(self.combox.currentData())
        if self.current_widget is not None:
            self.current_widget.setParent(None)
            self.btn_box.setParent(None)
            self.layout.removeWidget(self.current_widget)
            self.layout.removeWidget(self.btn_box)
            self.current_widget = None

        alg:AlgFrontend = FOLLOW[self.combox.currentData()]

        if alg.get_widget() is None:
            return
        
        self.current_widget = alg.get_widget(ActionManager().follow_box)
        self.layout.addWidget(self.current_widget)
        self.layout.addWidget(self.btn_box)
    
    
    def run(self):
        alg:AlgFrontend = FOLLOW[self.combox.currentData()]

        if alg is None:
            return

        params = alg.get_params(self.current_widget)

        t = Thread(target=self.run_alg, args=(params,))
        t.start()

    def run_dialog(self, alg:AlgFrontend):

        dialog = FollowDialog(self.mainwindow, alg)
        dialog.show()

        if dialog.exec_() == QtWidgets.QDialog.Accepted:

            params = alg.get_params(dialog.widget)

            t = Thread(target=self.run_alg, args = (alg, params,))
            t.start()


    def run_alg(self, alg:AlgFrontend, p):

        alg.run_alg(**p, send_message=self.send_message)

    def reset(self):

        if self.current_widget is None:
            return
        self.current_widget.setParent(None)
        self.btn_box.setParent(None)
        self.layout.removeWidget(self.current_widget)
        self.layout.removeWidget(self.btn_box)

        self.current_widget = FOLLOW[self.combox.currentData()].get_widget(ActionManager().follow_box)

        self.layout.addWidget(self.current_widget)
        self.layout.addLayout(self.btn_box)

    