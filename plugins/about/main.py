from rscder.gui.actions import ActionManager
from rscder.plugins.basic import BasicPlugin

from PyQt5.QtWidgets import QDialog, QAction, QApplication, QLabel, QTextEdit, QVBoxLayout
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon

from rscder.utils.icons import IconInstance

class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super(AboutDialog, self).__init__(parent)
        self.setWindowTitle("About")
        self.setFixedSize(800, 400)
        
        self.label = QLabel("<h1>"+ QApplication.applicationName()  + "</h1>")
        self.label.setAlignment(Qt.AlignCenter)
        self.label.setStyleSheet("font-size: 20px;")

        self.label2 = QLabel("<h2>Version: " + QApplication.applicationVersion() + "</h2>")
        self.label2.setAlignment(Qt.AlignCenter)
        self.label2.setStyleSheet("font-size: 15px;")

        self.label3 = QLabel("<h2>" + QApplication.organizationName() + "</h2>")
        self.label3.setAlignment(Qt.AlignCenter)
        self.label3.setStyleSheet("font-size: 15px;")

        self.label4 = QLabel("<h3>Copyright (c) 2020</h3>")
        self.label4.setAlignment(Qt.AlignCenter)
        self.label4.setStyleSheet("font-size: 10px;")

        self.text = QTextEdit()
        self.text.setReadOnly(True)
        self.text.setText('''
        This program is free software: you can redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.
         ''')

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.label2)
        self.layout.addWidget(self.label3)
        self.layout.addWidget(self.label4)
        self.layout.addWidget(self.text)
        self.setLayout(self.layout)


class AboutPlugin(BasicPlugin):

    @staticmethod
    def info():
        return {
            'name': '关于',
            'author': 'RSCDER',
            'version': '1.0.0',
            'description': '关于'
        }

    def set_action(self):
        
        action = QAction(IconInstance().HELP, '&关于', ActionManager().help_menu)
        action.triggered.connect(self.on_about)
        ActionManager().help_menu.addAction(action)
    
    def on_about(self):
        # print('on_about')
        dialog = AboutDialog(self.ctx['mainwindow'])
        dialog.show()