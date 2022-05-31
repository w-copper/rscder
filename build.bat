nuitka ECD.py --standalone --plugin-enable=pyqt5  --include-qt-plugins=sensible,styles --plugin-enable=numpy --nofollow-import-to=cv2 --nofollow-import-to=scipy --nofollow-import-to=yaml --nofollow-import-to=matplotlib --nofollow-import-to=PIL --nofollow-import-to=skimage --nofollow-import-to=numpy --nofollow-import-to=osgeo --nofollow-import-to=cryptography --nofollow-import-to=brotli --nofollow-import-to=cffi  --show-progress --include-package=qgis --include-package=distutils --output-dir=package --windows-icon-from-ico=logo.ico --windows-disable-console

@REM nuitka ECD.py --standalone --plugin-enable=pyqt5  --include-qt-plugins=sensible,styles --plugin-enable=numpy --plugin-enable=anti-bloat --show-progress --include-package=qgis --output-dir=package --windows-icon-from-ico=logo.ico
@REM nuitka keygen.py --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --show-progress --plugin-enable=pylint-warnings --output-dir=package --windows-disable-console --windows-icon-from-ico=logo.ico --no-pyi-file 


REM Win7 with console
REM nuitka gui.py --mingw64 --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --recurse-all --show-progress --include-package=qgis --output-dir=package --windows-icon=icons/logo.ico

REM Win7
@REM nuitka gui.py --mingw64 --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --recurse-all --show-progress --include-package=qgis --output-dir=package --windows-disable-console --windows-icon=icons/logo.ico