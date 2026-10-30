#!/usr/bin/env bash
# Builds Caldera-<version>-x86_64.AppImage. Run on Linux with Python 3.10+. Output lands in ./dist/.
set -euo pipefail
cd "$(dirname "$(readlink -f "$0")")/.."
VERSION=$(python3 -c "import caldera; print(caldera.__version__)")
python3 -m venv .buildenv
. .buildenv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt pyinstaller
pyinstaller --noconfirm --clean --name Caldera --windowed --paths . \
    --add-data "caldera/assets:caldera/assets" main.py

APPDIR=build/Caldera.AppDir
rm -rf "$APPDIR"; mkdir -p "$APPDIR/usr/bin"
cp -r dist/Caldera/* "$APPDIR/usr/bin/"

# The AppImage needs a PNG icon, so render the SVG to one with Qt.
QT_QPA_PLATFORM=offscreen python3 - <<'PY'
from PySide6.QtGui import QGuiApplication, QImage, QPainter, QColor
from PySide6.QtSvg import QSvgRenderer
app = QGuiApplication([])
img = QImage(256, 256, QImage.Format.Format_ARGB32)
img.fill(QColor(0, 0, 0, 0))
p = QPainter(img)
QSvgRenderer('caldera/assets/caldera.svg').render(p)
p.end()
assert img.save('build/Caldera.AppDir/caldera.png')
PY
cp "$APPDIR/caldera.png" "$APPDIR/.DirIcon"

cat > "$APPDIR/caldera.desktop" <<'DESK'
[Desktop Entry]
Type=Application
Name=Caldera
Comment=Offline engineering calculation workbench
Exec=Caldera
Icon=caldera
Terminal=false
Categories=Science;Engineering;
DESK

cat > "$APPDIR/AppRun" <<'RUN'
#!/bin/sh
HERE="$(dirname "$(readlink -f "$0")")"
exec "$HERE/usr/bin/Caldera" "$@"
RUN
chmod +x "$APPDIR/AppRun"

[ -x build/appimagetool ] || { mkdir -p build; curl -L -o build/appimagetool \
  https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage; chmod +x build/appimagetool; }
ARCH=x86_64 build/appimagetool --appimage-extract-and-run "$APPDIR" "dist/Caldera-$VERSION-x86_64.AppImage"
echo "Built dist/Caldera-$VERSION-x86_64.AppImage"
