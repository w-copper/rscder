nuitka run.py --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --show-progress --include-package=qgis --plugin-enable=pylint-warnings --output-dir=package --windows-disable-console --windows-icon-from-ico=logo.ico --no-pyi-file 


REM Win7 with console
REM nuitka gui.py --mingw64 --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --recurse-all --show-progress --include-package=qgis --output-dir=package --windows-icon=icons/logo.ico

REM Win7
@REM nuitka gui.py --mingw64 --standalone --plugin-enable=qt-plugins --plugin-enable=numpy --recurse-all --show-progress --include-package=qgis --output-dir=package --windows-disable-console --windows-icon=icons/logo.ico