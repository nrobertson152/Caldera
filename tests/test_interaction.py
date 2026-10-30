"""Real-Qt interaction test: drags the Reservoir / Drip Pan 3D viewer and hovers / re-targets every sensitivity chart.

    QT_QPA_PLATFORM=offscreen python3 tests/test_interaction.py

These are the two interactions that crashed 1.0.0. Mouse events are delivered through QTest so Qt creates and frees
each event itself, exactly like a real mouse does. A hard crash (segfault) fails the run with a native stack trace."""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))  # repo root, so `caldera` imports without installing
import faulthandler
import gc
import os
import sys
import tempfile

faulthandler.enable()
os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['CALDERA_DATA'] = tempfile.mkdtemp(prefix='caldera-interaction-test-')
from PySide6.QtCore import QEvent, QPoint, QPointF, Qt
from PySide6.QtGui import QMouseEvent, QWheelEvent
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication

import caldera.app as A
from caldera.registry import TOOL_PAGES
from caldera.ui import theme
from caldera.ui.viewer3d import Viewer3D
from caldera.ui.widgets import SweepChart

app = QApplication(sys.argv)
theme.load_fonts(A.ASSETS)
win = A.Window()
win.resize(1440, 900)
win.show()
errors = []
A.traceback.print_exc = lambda *a, **k: errors.append('page raised (see traceback above)')
_hook = sys.excepthook


def _record(*exc):
    errors.append('exception in an event handler (see traceback above)')
    _hook(*exc)


sys.excepthook = _record
LEFT, NOMOD = Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier


def pump():
    app.processEvents()
    gc.collect()


def send_move(w, pos, buttons):
    """A move event built in Python and dropped straight away (mimics a short-lived native event)."""
    ev = QMouseEvent(QEvent.Type.MouseMove, QPointF(pos), QPointF(w.mapToGlobal(pos)), Qt.MouseButton.NoButton,
                     buttons, NOMOD)
    QApplication.sendEvent(w, ev)
    del ev
    gc.collect()


def drag(w, path):
    QTest.mousePress(w, LEFT, NOMOD, path[0])
    pump()
    for pt in path[1:]:
        QTest.mouseMove(w, pt)
        send_move(w, pt + QPoint(1, 1), LEFT)
        pump()
    QTest.mouseRelease(w, LEFT, NOMOD, path[-1])
    pump()


def sweep_path(w, steps=40):
    h = w.height() // 2
    return [QPoint(int(8 + (w.width() - 16) * k / steps), h + (k % 7) * 4 - 12) for k in range(steps + 1)]


# ---------------------------------------------------------------- 3D viewer: rotate, zoom, reset
win.navigate('Reservoir / Drip Pan', force=True)
pump()
viewers = win.findChildren(Viewer3D)
assert viewers, 'Reservoir page has no 3D viewer'
for v in viewers:
    if not v.isVisible():
        continue
    yaw0 = v.yaw
    for _round in range(3):
        drag(v, sweep_path(v))
        drag(v, list(reversed(sweep_path(v))))
        c = v.rect().center()
        drag(v, [c + QPoint(0, dy) for dy in range(-120, 121, 8)])          # pitch up/down past the clamps
    assert v.yaw != yaw0, 'dragging did not rotate the view'
    for delta in (120, 120, -240, -1200, 2400):
        ev = QWheelEvent(QPointF(v.rect().center()), QPointF(v.mapToGlobal(v.rect().center())), QPoint(0, 0),
                         QPoint(0, delta), Qt.MouseButton.NoButton, NOMOD, Qt.ScrollPhase.NoScrollPhase, False)
        QApplication.sendEvent(v, ev)
        pump()
    QTest.mouseDClick(v, LEFT, NOMOD, v.rect().center())
    pump()
    v.grab()
print('3D viewer: rotate / zoom / reset OK')

# ---------------------------------------------------------------- sensitivity charts on every calculator
charts_seen = 0
for name in TOOL_PAGES:
    win.navigate(name, force=True)
    pump()
    page = win.findChildren(SweepChart)
    for chart in page:
        if not chart.isVisible():
            continue
        owner = chart
        while owner is not None and not hasattr(owner, 'in_combo'):
            owner = owner.parentWidget()
        for i in range(owner.in_combo.count() if owner else 1):
            if owner:
                owner.in_combo.setCurrentIndex(i)
                pump()
            for j in range(owner.out_combo.count() if owner else 1):
                if owner:
                    owner.out_combo.setCurrentIndex(j)
                    pump()
                for pt in sweep_path(chart, 30):
                    QTest.mouseMove(chart, pt)
                    send_move(chart, pt, Qt.MouseButton.NoButton)
                    pump()
                drag(chart, sweep_path(chart, 10))
                QApplication.sendEvent(chart, QEvent(QEvent.Type.Leave))
                pump()
                chart.grab()
                charts_seen += 1
        # recalculating while hovered must not leave a stale hover index behind
        if owner:
            QTest.mouseMove(chart, chart.rect().center())
            pump()
            owner.recalc()
            pump()
            chart.grab()
print('Sensitivity charts: %d chart views hovered OK' % charts_seen)
assert charts_seen, 'no sensitivity chart was found on any page'

# ---------------------------------------------------------------- 1.1.0: cylinder animation
from caldera.ui.page_cylinder import CylinderCyclePage
from caldera.ui.page_conduit import ConductorList
from caldera.ui.widgets import Combo, Segmented
from caldera import units
from caldera.toolmeta import SYSTEM_PAGES


def live(cls):
    found = [w for w in win.findChildren(cls) if w.isVisible()]
    assert found, 'no visible %s' % cls.__name__
    return found[-1]


win.navigate('Hydraulic Cylinder Cycle Time', force=True)
pump()
cyl = live(CylinderCyclePage)
assert cyl.anim.valid, cyl.anim.message
QTest.mouseClick(cyl.play_btn, LEFT)
QTest.qWait(400)
assert cyl._playing and cyl.anim.t > 0, 'animation did not advance'
for name in ('5×', '¼×', '1×'):
    cyl._speed_changed(name)
    QTest.qWait(120)
cyl.anim.grab()
QTest.mouseClick(cyl.play_btn, LEFT)
assert not cyl._playing
cyl.restart()
QTest.qWait(150)
cyl.inputs[1].setText('99')            # rod bigger than bore -> error path must not crash the animation
QTest.qWait(400)
assert not cyl.anim.valid
cyl.inputs[1].setText('2')
QTest.qWait(400)
assert cyl.anim.valid
print('Cylinder animation OK')

# ---------------------------------------------------------------- 1.1.0: conduit fill with mixed conductors
win.navigate('Conduit Fill', force=True)
pump()
lst = live(ConductorList)
before = len(lst.rows)
lst._add_clicked()
lst._add_clicked()
pump()
assert len(lst.rows) == before + 2
lst.rows[-1].ins.set_value('XHHW / XHHW-2')
lst.rows[-1].size.set_value('4/0')
lst.rows[-1].qty.setText('3')
lst.rows[-2].ins.set_value('Other (enter area)')
lst.rows[-2].area.setText('0.2')
QTest.qWait(400)
cpage = lst.parentWidget()
while cpage is not None and not hasattr(cpage, 'canon'):
    cpage = cpage.parentWidget()
assert cpage.canon and not cpage.canon.error, cpage.canon.error if cpage.canon else 'no result'
assert '4/0' in cpage.values()[2] and 'Other' in cpage.values()[2], cpage.values()[2]
lst._remove(lst.rows[0])
QTest.qWait(300)
assert not cpage.canon.error
cpage.note_edit.setPlainText('Panel P-3 feeder')
cpage.save_result()
assert win.data['history'][-1].get('note') == 'Panel P-3 feeder'
print('Conduit fill editor + notes OK')

# ---------------------------------------------------------------- 1.1.0: reservoir materials / thickness relabel
win.navigate('Reservoir / Drip Pan', force=True)
pump()
rpage = live(Viewer3D)
while rpage is not None and not hasattr(rpage, 'canon'):
    rpage = rpage.parentWidget()
rpage.inputs[4].set_value('Aluminum 5052-H32')
pump()
assert 'mm' in rpage.inputs[3].currentText() or 'in' in rpage.inputs[3].currentText(), rpage.inputs[3].currentText()
rpage.inputs[3].set_value('1/4"')
rpage.inputs[5].setText('100')
QTest.qWait(400)
assert any(ok == 'bad' for ok, _t in rpage.canon.status), rpage.canon.status
rpage.inputs[5].setText('80')
QTest.qWait(400)
print('Reservoir materials + checks OK')

# ---------------------------------------------------------------- 1.1.0: seals, reference, compare views
win.navigate('Seal Compatibility', force=True)
pump()
seg = live(Segmented)
for view in list(seg.options):
    seg.current = view
    seg.changed.emit(view)
    pump()
win.navigate('Reference Tables', force=True)
pump()
seg = live(Segmented)
for view in list(seg.options):
    seg.current = view
    seg.changed.emit(view)
    pump()
win.navigate('Compare Calculations', force=True)
pump()
combos = [c for c in win.findChildren(Combo) if c.isVisible()]
assert len(combos) >= 3, len(combos)
combos[2].setCurrentIndex(1)
pump()
print('Seals / reference / 3-way compare OK')

# ---------------------------------------------------------------- 1.1.0: every page in metric units
win.set_units('Metric')
pump()
assert units.metric()
for name in [*SYSTEM_PAGES, *TOOL_PAGES]:
    win.navigate(name, force=True)
    pump()
    win.grab()
win.navigate('Hydraulic Pump & Motor', force=True)
pump()
win.set_units('US Customary')
pump()
print('Metric pass over every page OK')
if errors:
    print('\n'.join(errors))
sys.exit(1 if errors else 0)
