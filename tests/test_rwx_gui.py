"""RevisionWorx in the real Caldera window (offscreen Qt), with a stand-in client so it needs no RevisionWorx:
publish a project summary, see its status on the project card, link a saved calculation to a document.

    QT_QPA_PLATFORM=offscreen python3 tests/test_rwx_gui.py"""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))
import hashlib
import os
import sys
import tempfile
import time
from pathlib import Path

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
os.environ['CALDERA_DATA'] = tempfile.mkdtemp(prefix='caldera-rwx-gui-')
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

import caldera.app as A
from caldera import revisionworx as R
from caldera.ui import chrome, pages_data, theme

app = QApplication(sys.argv)
theme.load_fonts(A.ASSETS)


class Fake:
    def __init__(self):
        self.docs, self.opened = {}, []
        self.drawing = {'id': 'dwg', 'number': 'DWG-100', 'title': 'Manifold', 'project': {'id': 'p1', 'name': 'Skid'},
                        'latest': {'label': 'C', 'state': 'released', 'state_name': 'Released'}}

    def projects(self):
        return [{'id': 'p1', 'number': 'PS-1', 'name': 'Skid'}]

    def documents(self, project=None, text=''):
        return [self.drawing, *self.docs.values()]

    def document(self, ref, project=None):
        return self.drawing if ref == 'dwg' else self.docs[ref]

    def open(self, document=None, file=None):
        self.opened.append(document)
        return {'ok': True}

    def publish(self, file, project=None, document=None, number='', title='', folder='', message=''):
        sha = hashlib.sha256(Path(file).read_bytes()).hexdigest()
        if document:
            doc = self.docs[document]
            same = doc['sha'] == sha
            if not same:
                doc['latest']['label'] = chr(ord(doc['latest']['label']) + 1)
                doc['sha'] = sha
            return {'result': 'unchanged' if same else 'revised', 'document': doc}
        doc = {'id': 'calc1', 'number': number, 'title': title, 'sha': sha, 'project': {'id': project, 'name': 'Skid'},
               'latest': {'label': 'A', 'state': 'wip', 'state_name': 'Work in Progress'}}
        self.docs['calc1'] = doc
        return {'result': 'created', 'document': doc}


def wait_for(cond, what):
    end = time.time() + 10
    while time.time() < end:
        app.processEvents()
        if cond():
            return
        time.sleep(0.02)
    raise SystemExit('timed out waiting for ' + what)


# The real dialogs build and return their defaults.
QTimer.singleShot(150, lambda: QApplication.activeModalWidget().accept())
assert chrome.rwx_publish_dialog(None, 'Skid', Fake().projects(), 'CALC-SKID') == ('p1', 'CALC-SKID', 'Calculations: Skid')
QTimer.singleShot(150, lambda: QApplication.activeModalWidget().accept())
assert chrome.rwx_pick_document(None, Fake().documents())['id'] == 'dwg'

fake = Fake()
win = A.Window(rwx=fake)
win.resize(1440, 900)
win.show()
win.data['projects'].append('Skid')
win.data['active_project'] = 'Skid'
win.add_history('Line Velocity', ['20', '1', 'Return line'], 'Velocity (ft/s): 12')
A.rwx_publish_dialog = lambda parent, name, projects, number: ('p1', number, 'Calculations: ' + name)
A.rwx_pick_document = lambda parent, docs: docs[0]
win.confirm = lambda *a, **k: True

win.navigate('Project Dashboard', force=True)
got = win.publish_project_to_rwx('Skid')
assert got['result'] == 'created' and R.project_link(win.data, 'Skid')['number'] == 'CALC-SKID'
assert win.publish_project_to_rwx('Skid')['result'] == 'unchanged'      # identical report records nothing
assert A.workspace.load(win.store_path)[0]['rwx_links']['Skid']['document'] == 'calc1'   # saved
wait_for(lambda: [p for p in win.page.findChildren(A.QWidget) if getattr(p, 'rwx_pill', None)]
         and any('rev A' in getattr(c, 'rwx_pill').text() for c in win.page.findChildren(A.QWidget)
                 if getattr(c, 'rwx_pill', None)), 'the project card status')
win.grab().save(os.path.join(os.environ['CALDERA_DATA'], 'projects.png'))

win.ask_text = lambda *a, **k: "Skid 2"   # renaming keeps the link
win.rename_project('Skid')
assert R.project_link(win.data, 'Skid 2') and not R.project_link(win.data, 'Skid')

win.navigate('Calculation History', force=True)
page = win.page
page.table.selectRow(0)
app.processEvents()
idx = page.selected if page.selected is not None else page.indices[0]
page._rwx_link(idx)
assert R.record_link(win.data['history'][idx])['number'] == 'DWG-100'
wait_for(lambda: getattr(page, 'rwx_pill', None) is not None and 'rev C · Released' in page.rwx_pill.text(),
         'the calculation document status')
win.show_in_rwx("dwg")
wait_for(lambda: fake.opened == ['dwg'], 'show in RevisionWorx')
page._rwx_unlink(idx)
assert R.record_link(win.data['history'][idx]) is None

# Without RevisionWorx nothing about it shows, and publishing explains why.
plain = A.Window(rwx=False)
plain.navigate('Calculation History', force=True)
plain.page.table.selectRow(0)
app.processEvents()
assert getattr(plain.page, 'rwx_pill', None) is None
assert plain.publish_project_to_rwx('General') is None
win.close()
plain.close()
print('RevisionWorx GUI tests passed')
