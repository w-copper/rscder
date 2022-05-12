from rscder.gui.keygen import LicenseGen
from PyQt5.QtWidgets import QApplication
import sys

if __name__ == "__main__":
    app =QApplication(sys.argv)
    license = LicenseGen()
    license.show()
    sys.exit(app.exec_())