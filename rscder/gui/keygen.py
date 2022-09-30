from PyQt5.QtWidgets import QDialog, QLineEdit, QDateTimeEdit, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QTextEdit, QFileDialog, QMessageBox
from PyQt5 import QtCore
from PyQt5.QtGui import QIcon
from rscder.utils.icons import IconInstance

from rscder.utils.license import LicenseHelper
import re
class LicenseGen(QDialog): 

    def __init__(self, parent = None, flags = QtCore.Qt.WindowFlags() ) -> None:
        super().__init__(parent, flags)

        self.setWindowTitle("证书生成器")
        self.setWindowIcon(IconInstance(parent).LOGO)

        mac_address_label = QLabel("MAC地址:")
        self.mac_address_text = QLineEdit()

        hbox1 = QHBoxLayout()
        hbox1.addWidget(mac_address_label)
        hbox1.addWidget(self.mac_address_text)
        
        end_date_label = QLabel("结束日期:")
        self.end_date_text = QDateTimeEdit()

        hbox2 = QHBoxLayout()
        hbox2.addWidget(end_date_label)
        hbox2.addWidget(self.end_date_text)

        
        self.license_file_path_text = QLineEdit()
        self.license_file_path_text.setReadOnly(True)

        btn_open = QPushButton("选择保存路径")
        btn_open.clicked.connect(self.open_file)

        hbox3 = QHBoxLayout()
        hbox3.addWidget(btn_open)
        hbox3.addWidget(self.license_file_path_text)
        # hbox3.addWidget(btn_open)


        self.btn_generate = QPushButton("生成")
        self.btn_generate.clicked.connect(self.generate_license)

        self.btn_cancel = QPushButton("取消")
        self.btn_cancel.clicked.connect(self.reject)

        hbox4 = QHBoxLayout()
        hbox4.addWidget(self.btn_generate, alignment = QtCore.Qt.AlignCenter, stretch= 0)
        hbox4.addWidget(self.btn_cancel, alignment = QtCore.Qt.AlignCenter, stretch= 0)

        vbox = QVBoxLayout()
        vbox.addLayout(hbox1)
        vbox.addLayout(hbox2)
        vbox.addLayout(hbox3)
        vbox.addLayout(hbox4)

        self.setLayout(vbox)

    def open_file(self) -> None:
        file_path, _ = QFileDialog.getSaveFileName(self, "保存证书路径", "", "License Files (*.lic)")
        if file_path:
            self.license_file_path_text.setText(file_path)
    
    def isValidMac(self,mac):
        if re.match(r"^\s*([0-9a-fA-F]{2,2}:){5,5}[0-9a-fA-F]{2,2}\s*$", mac):
            return True
        return False


    def generate_license(self) -> None:
        if self.mac_address_text.text() and self.license_file_path_text.text() and \
            self.end_date_text.dateTime().isValid():
            if not self.isValidMac(self.mac_address_text.text()):
                QMessageBox.warning(self, "Warning", "非法MAC地址")
            
            end_date = self.end_date_text.dateTime().toPyDateTime().strftime("%Y-%m-%d %H:%M:%S")

            lic = LicenseHelper().generate_license(end_date, self.mac_address_text.text())
            with open(self.license_file_path_text.text(), 'w') as f:
                f.write(lic[::-1])
            
            QMessageBox.information(self, "Information", "证书生成成功")