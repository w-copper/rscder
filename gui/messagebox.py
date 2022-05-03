from PyQt5.QtWidgets import QTextEdit
from PyQt5 import QtWidgets
from PyQt5.QtGui import QTextCursor
from PyQt5.QtCore import Qt
from datetime import datetime, time
class MessageBox(QTextEdit):

    INFO=0
    WARNING=1
    DEBUG=2
    ERROR=3

    def __init__(self, parent=None, level=0):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.setStyleSheet("QTextEdit { background-color: #f0f0f0; }")
        self.msg = ''
        self.level = level

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.right_menu_show)
    
    def right_menu_show(self, position):
        rightMenu = QtWidgets.QMenu(self)
        # QAction = QtWidgets.QAction(self.menuBar1)
        action = QtWidgets.QAction('清空')
        action.triggered.connect(self.clear)
        rightMenu.addAction(action)
        
        rightMenu.exec_(self.mapToGlobal(position))

    def append(self, text):
        self.msg += '<br/>' + text
        self.setText(self.msg)
        cursor = self.textCursor()
        # QTextCursor
        cursor.movePosition(QTextCursor.End)
        self.setTextCursor(cursor)
    
    def info(self, text):
        if self.level <= self.INFO:
            timestr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.append('<span style="color:green">[INFO] %s</span> <br/>'%timestr + str(text))
            # self.append(text)
        # self.append(text)

    def warning(self, text):
        if self.level <= self.WARNING:
            timestr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.append('<span style="color:yellow">[WARNING] %s</span> <br/>'%timestr + str(text))
    
    def debug(self, text):
        if self.level <= self.DEBUG:
            timestr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.append('<span style="color:green">[DEBUG] %s</span> <br/>'%timestr + str(text))
            # self.append(text)
        # self.append(text)
    
    def error(self, text):
        if self.level <= self.ERROR:
            timestr = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.append('<span style="color:red">[ERROR] %s</span> <br/>'%timestr + str(text))
            # self.append(text)
        # self.append(text)

    def clear(self):
        self.msg = ''
        self.setText(self.msg)
    