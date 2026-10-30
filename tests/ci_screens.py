"""CI helper: render key pages offscreen and print them as chunked base64 JPEG annotations, so a reviewer without
artifact access can see the UI.  QT_QPA_PLATFORM=offscreen python3 tests/ci_screens.py"""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
import base64
import os
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['CALDERA_DATA'] = tempfile.mkdtemp(prefix='caldera-shots-')
from PySide6.QtCore import QBuffer, QByteArray, QIODevice, Qt
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import caldera.app as A
from caldera.ui import theme

app = QApplication(sys.argv)
theme.load_fonts(A.ASSETS)
win = A.Window()
win.resize(1440, 1000)
win.show()
win.add_history('Hydraulic Cylinder Cycle Time', ['4', '2', '24', '10', '10'], 'Full cycle time (s): 46.0')
win.add_history('Hydraulic Cylinder Cycle Time', ['5', '2.5', '24', '10', '10'], 'Full cycle time (s): 71.9', 'bigger')
win.add_history('Hydraulic Cylinder Cycle Time', ['4', '2', '30', '12', '10'], 'Full cycle time (s): 50.3')


def scroll_page(y):
    from PySide6.QtWidgets import QScrollArea
    for sa in win.findChildren(QScrollArea):
        if sa.isVisible():
            sa.verticalScrollBar().setValue(y)


def shot(name, prep=None, scroll=0):
    if prep:
        prep()
    QTest.qWait(700)
    page = win.page
    if page.graphicsEffect() is not None:
        page.setGraphicsEffect(None)
    target = page.widget() if hasattr(page, 'widget') and page.widget() is not None else page
    QTest.qWait(50)
    img = target.grab().toImage()
    if scroll:
        img = img.copy(0, scroll, img.width(), min(img.height() - scroll, 1500))
    else:
        img = img.copy(0, 0, img.width(), min(img.height(), 1500))
    img = img.scaledToWidth(680, Qt.TransformationMode.SmoothTransformation)
    data = QByteArray()
    buf = QBuffer(data)
    buf.open(QIODevice.OpenModeFlag.WriteOnly)
    img.save(buf, 'JPEG', 38)
    text = base64.b64encode(bytes(data)).decode()
    return name, text


def nav(name):
    return lambda: win.navigate(name, force=True)


def metric_res():
    win.set_units('Metric')
    QTest.qWait(50)
    win.navigate('Reservoir / Drip Pan', force=True)


def cylinder():
    win.navigate('Hydraulic Cylinder Cycle Time', force=True)
    QTest.qWait(150)
    from caldera.ui.page_cylinder import CylinderCyclePage
    p = [w for w in win.findChildren(CylinderCyclePage) if w.isVisible()][-1]
    p.anim.t = p.anim.t_ext * 0.6
    p.anim.update()


def seals():
    win.navigate('Seal Compatibility', force=True)
    from caldera.ui.widgets import Segmented
    seg = [w for w in win.findChildren(Segmented) if w.isVisible()][-1]
    seg.current = 'All fluids'
    seg.changed.emit('All fluids')


def compare():
    win.navigate('Compare Calculations', force=True)
    from caldera.ui.widgets import Combo
    QTest.qWait(100)
    combos = [c for c in win.findChildren(Combo) if c.isVisible()]
    combos[2].setCurrentIndex(1)


which = sys.argv[1:] or ['res', 'res_m', 'conduit', 'line', 'cyl', 'seals', 'ref', 'cmp']
plans = {
    'res': ('reservoir', nav('Reservoir / Drip Pan'), 0),
    'res_m': ('reservoir_metric', metric_res, 520),
    'conduit': ('conduit', nav('Conduit Fill'), 0),
    'line': ('line_velocity', nav('Line Velocity'), 300),
    'cyl': ('cylinder', cylinder, 0),
    'seals': ('seals_matrix', seals, 0),
    'ref': ('reference', nav('Reference Tables'), 0),
    'cmp': ('compare', compare, 0),
    'pump': ('pump_chart', nav('Hydraulic Pump & Motor'), 500),
}
shots = []
import traceback
for key in which:
    title, prep, scroll = plans[key]
    if key != 'res_m' and A.units.metric():
        win.set_units('US Customary')
        QTest.qWait(50)
    try:
        shots.append(shot(title, prep, scroll))
    except Exception:
        print('::error title=shot-failed::' + traceback.format_exc().replace('\n', '%0A'))
kinds = ['notice'] * 10 + ['warning'] * 10
k = 0
CH = 3900
for title, text in shots:
    parts = [text[i:i + CH] for i in range(0, len(text), CH)]
    for i, part in enumerate(parts):
        if k >= len(kinds):
            break
        print('::%s title=shot|%s|%d|%d::%s' % (kinds[k], title, i, len(parts), part))
        k += 1
print('emitted %d chunks for %d shots' % (k, len(shots)), file=sys.stderr)
