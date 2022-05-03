import sys
import time
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QPixmap
from PyQt5.QtWidgets import QSplashScreen, QProgressBar, QStyleFactory, QMessageBox
from qgis.core import QgsApplication
# from qgis.core import 
from gui.mainwindow import MainWindow
import multiprocessing
from gui import license
from utils.setting import Settings

class MulStart:

    def __init__(self, **kargs) -> None:
        super(MulStart, self).__init__()
        self.kargs = kargs
    def run(self):

        QgsApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
        QgsApplication.setAttribute(Qt.AA_UseHighDpiPixmaps)
        QgsApplication.setOrganizationName("西安理工大学-ImgSciGroup")
        QgsApplication.setApplicationName("Easy Change Detection")
        QgsApplication.setApplicationVersion("v0.0.1")
        QgsApplication.setFont(QFont("Segoe UI", 10))
        QgsApplication.setStyle(QStyleFactory.create("Fusion"))

        
        # pyrcc5 res.qrc -o rc.py
        import rc  

        app = QgsApplication([], True)
        QgsApplication.initQgis()
        while not Settings.General().license:
            QMessageBox.warning(None, "Warning", "Please select a license file.")
            if(license.License().exec_() == license.License.Accepted):
                continue
            else:
                sys.exit(0)
        # Create and display the splash screen
        splash_pix = QPixmap(':/icons/splash.png')

        splash = QSplashScreen(splash_pix, Qt.WindowStaysOnTopHint)
        progressBar = QProgressBar(splash)
        progressBar.setMaximum(10)
        progressBar.setTextVisible(False)
        progressBar.setGeometry(46, splash_pix.height() - 60, splash_pix.width()-92, 10)

        splash.show()
        for i in range(1, 11):
            progressBar.setValue(i)
            t = time.time()
            while time.time() < t + 0.05:
                app.processEvents()

        ex = MainWindow(**self.kargs)
        # ex.canvas.load_image(r'data\100001678.jpg')
        # ex.canvas.load_result_from_txt(r'data\100001678.txt')
        # ex.showMaximized()
        ex.show()
        splash.finish(ex)
        sys.exit(app.exec_())
        