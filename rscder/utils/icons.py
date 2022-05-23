from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject
from .misc import singleton

@singleton
class IconInstance(QObject):

    def __init__(self, parent) -> None:
        super().__init__(parent)

        self.GRID_ON = QIcon(':/icons/grid.png')    
        self.TABLE = QIcon(':/icons/table.png')
        self.DELETE = QIcon(':/icons/delete.png')