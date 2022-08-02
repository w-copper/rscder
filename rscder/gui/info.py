from distutils.log import info
from PyQt5.QtWidgets import  QHBoxLayout,QDialog,QLabel,QVBoxLayout
from PyQt5.QtGui import QColor, QDragEnterEvent, QDropEvent,QPixmap
from PyQt5.QtCore import QSize,Qt
import yaml



class InfoBox(QDialog):
    def __init__(self,infodic:dict,parent=None):
        super(InfoBox,self).__init__(parent=parent)
        v=QVBoxLayout()
        if 'prewmap'  in infodic.keys():
            
            pmap=infodic.pop('prewmap')
            label=QLabel(yaml.dump(infodic,allow_unicode=True,sort_keys=False))
            label.setWordWrap(True)#过长自动换行，主要是wkt过长
            v.addWidget(label)
            
            maplabel=QLabel()
            maplabel.setPixmap(QPixmap.fromImage(pmap))
            v.addWidget(maplabel,0,Qt.AlignHCenter)
        else:
            label=QLabel(yaml.dump(infodic,allow_unicode=True,sort_keys=False))
            label.setWordWrap(True)#过长自动换行，主要是wkt过长
            v.addWidget(label)
        self.setLayout(v)
        self.show()
    