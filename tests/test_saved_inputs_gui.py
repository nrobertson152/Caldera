"""Saved inputs from before a calculator gained an input still open in the real window (offscreen Qt):
an older draft, an older preset and an older history record of Cylinder Buckling (which gained 'Yield strength').

    QT_QPA_PLATFORM=offscreen python3 tests/test_saved_inputs_gui.py"""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
import os
import sys
import tempfile

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['CALDERA_DATA'] = tempfile.mkdtemp(prefix='caldera-saved-inputs-')
from PySide6.QtWidgets import QApplication, QLabel

import caldera.app as A
from caldera.ui import theme

app = QApplication(sys.argv)
theme.load_fonts(A.ASSETS)
OLD = ['1.5', '40', '29000000', '0.7', '3', '1000']          # six inputs, saved before 'Yield strength' existed

win = A.Window(rwx=False)
win.resize(1440, 900)
win.show()

# an older draft re-opens with its values; the new input shows its default
win.open_with_inputs('Cylinder Buckling', OLD)
app.processEvents()
page = win.page
assert page.values()[:6] == OLD, page.values()
assert page.values()[6] == '50000', page.values()

# an older preset loads too
win.data['presets']['Cylinder Buckling'] = {'Old rod': OLD[:5] + ['2500']}
page.reset_inputs()
page.load_preset('Old rod')
app.processEvents()
assert page.values()[:6] == OLD[:5] + ['2500'] and page.values()[6] == '50000', page.values()

# a history record from before still shows its inputs
win.data['history'].append({'date': '2026-10-01T09:00:00', 'tool': 'Cylinder Buckling', 'project': 'General',
                            'inputs': OLD, 'result': 'Allowable load (lbf): 1234'})
win.navigate('Calculation History', force=True)
app.processEvents()
hist = win.page
hist.table.selectRow(0)
app.processEvents()
shown = [w.text() for w in hist.detail.findChildren(QLabel)]
assert 'Unsupported length' in shown and 'Diameter' in shown, shown

# a short rod now reports the Johnson check in the page's status
win.open_with_inputs('Cylinder Buckling', ['1', '10', '30000000', '1', '2', '2000', '50000'])
app.processEvents()
page = win.page
page.recalc()
app.processEvents()
texts = ' '.join(w.text() for w in page.findChildren(QLabel))
assert 'Johnson' in texts, texts[:500]

win.close()
print('Saved-input GUI tests passed')
