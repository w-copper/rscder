import shutil
from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
import os

from rscder.utils.license import LicenseHelper

class License(QtWidgets.QDialog):

    def __init__(self, parent = None, flags = QtCore.Qt.WindowFlags() ) -> None:
        super().__init__(parent, flags)
        self.setWindowTitle("License")
        self.setWindowIcon(QIcon(':/icons/logo.png'))
        self.setWindowFlags(QtCore.Qt.WindowCloseButtonHint)
        self.setFixedSize(600, 400)

        self.text = QtWidgets.QLineEdit()
        self.text.setReadOnly(False)
        self.label = QtWidgets.QLabel()
        self.label.setText("License File Path: ")

        self.setModal(True)

        self.btn_open = QtWidgets.QPushButton("Open")
        self.btn_open.clicked.connect(self.open_file)

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.label, 0, alignment=QtCore.Qt.AlignTop)
        hlayout.addWidget(self.text, 0, alignment=QtCore.Qt.AlignTop)
        hlayout.addWidget(self.btn_open, 0, alignment=QtCore.Qt.AlignTop)

        self.btn_ok = QtWidgets.QPushButton("OK")
        self.btn_ok.clicked.connect(self.ok_clicked)
        
        hlayout2 = QtWidgets.QHBoxLayout()
        hlayout2.addWidget(self.btn_ok, alignment = QtCore.Qt.AlignRight, stretch= 0)

        vlayout = QtWidgets.QVBoxLayout()
        
        infobox = QtWidgets.QTextEdit(self)
        infobox.setSizeAdjustPolicy(QtWidgets.QAbstractScrollArea.AdjustToContents)
        infobox.setPlainText("""
        This program is NOT free software: you can NOT redistribute it and/or modify
        it under the terms of the GNU General Public License as published by
        the Free Software Foundation, either version 3 of the License, or
        (at your option) any later version.
        
        Copy the MAC address to the clipboard and send it to the developer.
        MAC address: {}""".format(LicenseHelper().get_mac_address()))

        vlayout.addLayout(hlayout)
        vlayout.addWidget(infobox)
        vlayout.addLayout(hlayout2)

        self.setLayout(vlayout)
    
    def open_file(self) -> None:
        file_path = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", "", "License Files (*.*)")
        if file_path[0]:
            self.text.setText(file_path[0])
            # self.label.setText("License File Path: " + file_path[0])

    def ok_clicked(self) -> None:
        if self.text.text() == "":
            QtWidgets.QMessageBox.warning(self, "Warning", "Please select a license file.")
        else:
            pth = self.text.text()
            if not os.path.exists(pth):
                QtWidgets.QMessageBox.warning(self, "Warning", "The selected file does not exist.")
            else:
                if not os.path.exists('lic'):
                    os.mkdir('lic')
                shutil.copy(pth, os.path.join("lic", "license.lic"))
                self.accept()
                self.close()