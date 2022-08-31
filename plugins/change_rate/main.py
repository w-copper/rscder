import os
from pickle import TRUE
from threading import Thread
from rscder.gui.actions import ActionManager
from rscder.gui.layercombox import ResultPointLayerCombox
from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QDialog, QLabel, QHBoxLayout, QVBoxLayout, QPushButton,QSlider,QSpinBox,QSpacerItem,QDialogButtonBox
from PyQt5.QtCore import pyqtSignal,Qt
from PyQt5.QtGui import QIcon
from rscder.utils.icons import IconInstance
from rscder.utils.project import Project, ResultPointLayer, SingleBandRasterLayer
import numpy as np
class RateSetdialog(QDialog):
    def __init__(self, parent=None):
        super(RateSetdialog,self).__init__(parent)
        self.setWindowTitle('设置变化阈值')
        self.setWindowIcon(IconInstance().LOGO)

        self.layer_select = ResultPointLayerCombox(self)
        self.slider=QSlider(Qt.Horizontal)
        self.spin=QSpinBox()

        h1=QHBoxLayout()
        h1.addWidget(QLabel('表格结果:'))
        h1.addWidget(self.layer_select)

        h2=QHBoxLayout()

        
        self.slider.valueChanged.connect(self.spin.setValue)#valueChanged当值与原来不同是发射
        self.spin.valueChanged.connect(self.slider.setValue)

        h2.addItem(QSpacerItem(10,0))
        h2.addWidget(self.slider)
        h2.addWidget(self.spin)
        h2.addItem(QSpacerItem(10,0))
        self.ok_button = QPushButton('确定', self)
        self.ok_button.setIcon(IconInstance().OK)
        self.ok_button.clicked.connect(self.on_ok)
        self.ok_button.setDefault(True)
        self.cancel_button = QPushButton('取消', self)
        self.cancel_button.setIcon(IconInstance().CANCEL)
        self.cancel_button.clicked.connect(self.on_cancel)
        self.cancel_button.setDefault(False)
        self.buttonbox=QDialogButtonBox(self)
        self.buttonbox.addButton(self.ok_button,QDialogButtonBox.NoRole)
        self.buttonbox.addButton(self.cancel_button,QDialogButtonBox.NoRole)
        self.buttonbox.setCenterButtons(True)
        vlayout=QVBoxLayout()
        vlayout.addLayout(h1)
        vlayout.addWidget(QLabel('设置阈值'))
        vlayout.addLayout(h2)
        vlayout.addWidget(self.buttonbox)
        self.setLayout(vlayout)

        self.old_data = None
        
    def on_ok(self):
        self.onclose()
        self.accept()

    def on_cancel(self):
        if self.layer_select.current_layer is not None:
            self.layer_select.current_layer.data = self.layer_select.current_layer.old_data
            self.layer_select.current_layer.update_point_layer(-1)
        self.reject()
    
    def onclose(self) -> None:
        if self.layer_select.current_layer is not None:
            self.layer_select.current_layer.save()
    
    def closeEvent(self, a0) -> None:
        if self.layer_select.current_layer is not None:
            self.layer_select.current_layer.data = self.layer_select.current_layer.old_data
            self.layer_select.current_layer.update_point_layer(-1)


class RateSetPlugin(BasicPlugin):
    current_layer=None
    @staticmethod
    def info():
        return {
            'name': 'set_change_rate',
            'description': 'set_change_rate',
            'author': 'RSCDER',
            'version': '1.0.0',
        }
    
    def set_action(self):
        self.action = QAction(IconInstance().VECTOR, '变化阈值设定', self.mainwindow)
        self.action.triggered.connect(self.show_dialog)
        ActionManager().position_menu.addAction(self.action)

    def show_dialog(self):
        dialog=RateSetdialog(self.mainwindow)
        dialog.layer_select.currentIndexChanged.connect(lambda index: self.currentLayer(dialog.layer_select.itemData(index) if index>0 else None))
        dialog.slider.valueChanged.connect(lambda input:self.setrate(input))
        dialog.setModal(False)
        dialog.show()
    def currentLayer(self,layer):
        self.current_layer=layer
        if not isinstance(layer,ResultPointLayer):
            return
        layer.old_data = layer.data.copy()


    def setrate(self,input:int):
        layer=self.current_layer
        # print(layer.__class__)
        if not isinstance(layer,ResultPointLayer):
            return
        data=layer.data.copy()
        # print(input)
        data[np.where(data[:,-2]<(input)),-1]=0
        data[np.where(data[:,-2]>(input)),-1]=1
        layer.data=data
        layer.update_point_layer(-1)
        

    
