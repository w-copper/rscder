from rscder.plugins.basic import BasicPlugin
from PyQt5.QtWidgets import QAction, QDialog, QHBoxLayout, QVBoxLayout, QPushButton
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt

class EvalutationDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWindowTitle('精度评估')
        self.setWindowIcon(QIcon(":/icons/logo.png"))

        self.setFixedWidth(500)

        self.ok_button = QPushButton('OK', self)
        self.ok_button.setIcon(QIcon(":/icons/ok.svg"))
        self.ok_button.clicked.connect(self.on_ok)

        self.cancel_button = QPushButton('Cancel', self)
        self.cancel_button.setIcon(QIcon(":/icons/cancel.svg"))
        self.cancel_button.clicked.connect(self.on_cancel)

        self.button_layout = QHBoxLayout()
        self.button_layout.addWidget(self.ok_button)
        self.button_layout.addWidget(self.cancel_button)

        self.main_layout = QVBoxLayout()
        self.main_layout.addLayout(self.button_layout)
        self.setLayout(self.main_layout)

    def on_ok(self):
        self.accept()

    def on_cancel(self):
        self.reject()