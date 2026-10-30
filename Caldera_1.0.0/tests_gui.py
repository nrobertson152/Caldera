"""Real-Qt smoke test: opens the window headlessly, visits every page and saves a PNG of each to ./screenshots.

    QT_QPA_PLATFORM=offscreen python3 tests_gui.py [theme]      (needs PySide6; theme defaults to the saved one)

Uses a throw-away data directory, so your real workspace is never touched."""
import os
import sys
import tempfile
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['CALDERA_DATA'] = tempfile.mkdtemp(prefix='caldera-gui-test-')
from PySide6.QtWidgets import QApplication

import caldera.app as A
from caldera.registry import TOOL_PAGES
from caldera.toolmeta import SYSTEM_PAGES
from caldera.ui import theme

app = QApplication(sys.argv)
theme.load_fonts(A.ASSETS)
win = A.Window()
if len(sys.argv) > 1 and sys.argv[1] in theme.THEMES:
    win.set_theme(sys.argv[1])
    app.processEvents()
win.resize(1440, 900)
win.show()
out = Path('screenshots') / theme.current()['name']
out.mkdir(parents=True, exist_ok=True)
errors = []
A.traceback.print_exc = lambda *a, **k: errors.append('page raised (see traceback above)')
win.add_history('Hydraulic Power & Efficiency', ['2500', '30', '0.9'], 'Hydraulic power (HP): 43.759\nInput power (HP): 48.621')
for name in [*SYSTEM_PAGES, *TOOL_PAGES]:
    win.navigate(name, force=True)
    app.processEvents()
    win.grab().save(str(out / (name.replace(' ', '_').replace('/', '-').replace('&', 'and') + '.png')))
win.open_palette()
app.processEvents()
win._palette.grab().save(str(out / 'command_palette.png'))
win._palette.close()
print('Visited %d pages; screenshots in %s' % (len(SYSTEM_PAGES) + len(TOOL_PAGES), out))
sys.exit(1 if errors else 0)
