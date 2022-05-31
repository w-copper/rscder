import os

os.environ['PROJ_LIB'] = os.path.join(os.path.dirname(__file__), 'share/proj')
os.environ['GDAL_DATA'] = os.path.join(os.path.dirname(__file__), 'share')
os.environ['ECD_BASEDIR'] = os.path.dirname(__file__)
BASE_DIR = os.path.dirname(__file__)

from rscder.gui.keygen import LicenseGen
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app =QApplication(sys.argv)
    license = LicenseGen()
    license.show()
    sys.exit(app.exec_())