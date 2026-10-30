"""Builds dist/Caldera-<version>-windows-x64.exe (one self-contained file). Run on Windows with Python 3.10+:

    py -3.12 -m pip install -r requirements.txt pyinstaller pillow
    py -3.12 packaging/build_windows.py
"""
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
os.chdir(ROOT)
sys.path.insert(0, str(ROOT))
import caldera  # noqa: E402

VERSION = caldera.__version__
build = ROOT / 'build'
build.mkdir(exist_ok=True)

# Render the SVG logo to a 256 px PNG; PyInstaller (with Pillow) turns it into the .exe icon.
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtGui import QColor, QGuiApplication, QImage, QPainter  # noqa: E402
from PySide6.QtSvg import QSvgRenderer  # noqa: E402

app = QGuiApplication([])
img = QImage(256, 256, QImage.Format.Format_ARGB32)
img.fill(QColor(0, 0, 0, 0))
p = QPainter(img)
QSvgRenderer(str(ROOT / 'caldera' / 'assets' / 'caldera.svg')).render(p)
p.end()
icon = build / 'caldera.png'
assert img.save(str(icon)), 'could not write icon'
del p, app

name = 'Caldera-%s-windows-x64' % VERSION
subprocess.check_call([sys.executable, '-m', 'PyInstaller', '--noconfirm', '--clean', '--onefile', '--windowed',
                       '--name', name, '--icon', str(icon), '--paths', str(ROOT),
                       '--add-data', 'caldera/assets%scaldera/assets' % os.pathsep,
                       str(ROOT / 'packaging' / 'launcher.py')])
out = ROOT / 'dist' / (name + '.exe')
assert out.exists(), out
print('Built %s (%.1f MB)' % (out, out.stat().st_size / 1e6))
