"""RevisionWorx integration without Qt; run with python3 tests/test_revisionworx.py.

Part 1 uses a stand-in client and always runs. Part 2 drives the real RevisionWorx (`python -m revisionworx`) when it
is installed; CI sets CALDERA_REQUIRE_RWX=1 so a missing RevisionWorx fails instead of skipping."""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))  # repo root, so `caldera` imports without installing
import hashlib
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from caldera import exports, workspace
from caldera import revisionworx as R


class Fake:
    """Records publishes like RevisionWorx: same bytes -> 'unchanged'."""

    def __init__(self):
        self.docs, self.calls = {}, []

    def publish(self, file, project=None, document=None, number='', title='', folder='', message=''):
        data = Path(file).read_bytes()
        self.calls.append(dict(file=Path(file).name, project=project, document=document, number=number, title=title,
                               message=message))
        if document:
            doc = self.docs[document]
            if doc['sha'] == hashlib.sha256(data).hexdigest():
                return {'result': 'unchanged', 'document': doc}
            doc['latest']['label'] = chr(ord(doc['latest']['label']) + 1)
            doc['sha'] = hashlib.sha256(data).hexdigest()
            return {'result': 'revised', 'document': doc}
        doc = {'id': 'd%d' % (len(self.docs) + 1), 'number': number, 'title': title, 'sha': hashlib.sha256(data).hexdigest(),
               'project': {'id': project, 'name': 'Proj ' + project}, 'latest': {'label': 'A', 'state': 'wip',
                                                                                 'state_name': 'Work in Progress'}}
        self.docs[doc['id']] = doc
        return {'result': 'created', 'document': doc}


def writer(data, name):
    rows = [r for r in data['history'] if r.get('project') == name]
    return lambda path: exports.build_pdf(path, 'Project: %s' % name, exports.project_blocks(name, '', rows),
                                          '%d saved' % len(rows), invariant=True)


# ---- part 1: link bookkeeping with a stand-in client
d = workspace.sanitize({'projects': ['General', 'Pump skid'], 'history': [
    {'tool': 'Line Velocity', 'project': 'Pump skid', 'date': '2026-11-04T10:00:00', 'result': 'Velocity (ft/s): 12'}]})
assert d['rwx_links'] == {}
assert workspace.sanitize({'rwx_links': 'bad'})['rwx_links'] == {}
assert R.default_number('Pump skid #2') == 'CALC-PUMP-SKID-2' and R.default_number('***') == 'CALC-PROJECT'
fake = Fake()
try:
    R.publish_project(fake, d, 'Pump skid', writer(d, 'Pump skid'))
    raise SystemExit('published without a RevisionWorx project')
except ValueError:
    pass
got = R.publish_project(fake, d, 'Pump skid', writer(d, 'Pump skid'), rwx_project='p1', app_version='9.9')
assert got['result'] == 'created' and fake.calls[-1]['number'] == 'CALC-PUMP-SKID'
assert fake.calls[-1]['title'] == 'Calculations: Pump skid' and '1 calculation in project Pump skid' in fake.calls[-1]['message']
link = R.project_link(d, 'Pump skid')
assert link == {'document': 'd1', 'number': 'CALC-PUMP-SKID', 'project': 'p1', 'project_name': 'Proj p1'}, link
assert R.publish_project(fake, d, 'Pump skid', writer(d, 'Pump skid'))['result'] == 'unchanged'   # same report
assert fake.calls[-1]['document'] == 'd1' and fake.calls[-1]['file'] == 'CALC-PUMP-SKID.pdf'
d['history'].append({'tool': 'Pump & Motor', 'project': 'Pump skid', 'result': 'Flow (GPM): 30'})
again = R.publish_project(fake, d, 'Pump skid', writer(d, 'Pump skid'))
assert again['result'] == 'revised' and again['document']['latest']['label'] == 'B'
R.rename_project(d, 'Pump skid', 'Pump skid v2')
assert R.project_link(d, 'Pump skid') is None and R.project_link(d, 'Pump skid v2')['document'] == 'd1'
assert R.unlink_project(d, 'Pump skid v2') and not R.unlink_project(d, 'Pump skid v2')
rec = d['history'][0]
R.link_record(rec, {'id': 'x1', 'number': 'DWG-100', 'title': 'Manifold'})
assert R.record_link(rec) == {'id': 'x1', 'number': 'DWG-100', 'title': 'Manifold'}
assert R.unlink_record(rec) and R.record_link(rec) is None
assert R.doc_line({'number': 'DWG-1', 'latest': {'label': 'C', 'state': 'released', 'state_name': 'Released'}}) == \
    ('DWG-1 rev C · Released', 'Good')
assert R.doc_line({'number': 'DWG-1', 'latest': {'label': 'A', 'state': 'wip', 'state_name': 'Work in Progress'},
                   'checkout': {'user': 'x'}})[0] == 'DWG-1 rev A · Work in Progress · checked out'
with tempfile.TemporaryDirectory() as tmp:
    a, b = Path(tmp) / 'a.pdf', Path(tmp) / 'b.pdf'
    writer(d, 'Pump skid v2')(a)
    writer(d, 'Pump skid v2')(b)
    assert a.read_bytes() == b.read_bytes(), 'invariant PDFs must be byte-identical'
print('RevisionWorx link tests passed (stand-in client)')

# ---- part 2: the real RevisionWorx
try:
    import revisionworx.integration  # noqa: F401
except ImportError:
    if os.environ.get('CALDERA_REQUIRE_RWX'):
        raise SystemExit('RevisionWorx with `link` is required here (CALDERA_REQUIRE_RWX=1) but is not installed')
    print('SKIPPED real RevisionWorx tests: RevisionWorx is not installed')
    raise SystemExit(0)

with tempfile.TemporaryDirectory() as tmp:
    tmp = Path(tmp)
    for var in ('XDG_CONFIG_HOME', 'XDG_STATE_HOME', 'XDG_CACHE_HOME', 'APPDATA', 'LOCALAPPDATA'):
        os.environ[var] = str(tmp / 'profile' / var)
    ws = tmp / 'ws'
    os.environ['REVISIONWORX_WORKSPACE'] = str(ws)

    def rwx_cli(*args):
        out = subprocess.run([sys.executable, '-m', 'revisionworx', *args], capture_output=True, text=True, timeout=120)
        assert out.returncode == 0, out.stdout + out.stderr
        return out.stdout
    rwx_cli('init', str(ws), '--name', 'Caldera test')
    (ws / 'Projects').mkdir()
    rwx_cli('root', 'add', 'Projects', str(ws / 'Projects'))
    rwx_cli('project', 'new', '--name', 'Pump skid', '--number', 'PS-1')
    client = R.RevisionWorx()
    client.command = [sys.executable, '-m', 'revisionworx']
    assert client.available()
    pid = [p for p in client.projects() if p.get('number') == 'PS-1'][0]['id']
    d = workspace.sanitize({'projects': ['General', 'Pump skid'], 'history': [
        {'tool': 'Line Velocity', 'project': 'Pump skid', 'date': '2026-11-04T10:00:00', 'result': 'Velocity: 12'}]})
    first = R.publish_project(client, d, 'Pump skid', writer(d, 'Pump skid'), rwx_project=pid, app_version='test')
    assert first['result'] == 'created' and first['document']['number'] == 'CALC-PUMP-SKID'
    assert first['document']['latest']['label'] == 'A'
    assert R.publish_project(client, d, 'Pump skid', writer(d, 'Pump skid'))['result'] == 'unchanged'
    d['history'].append({'tool': 'Pump & Motor', 'project': 'Pump skid', 'result': 'Flow: 30'})
    second = R.publish_project(client, d, 'Pump skid', writer(d, 'Pump skid'))
    assert second['result'] == 'revised' and second['document']['latest']['label'] == 'B', second
    doc = client.document(R.project_link(d, 'Pump skid')['document'])
    assert len(doc['history']) == 2 and '2 calculations in project Pump skid' in json.dumps(doc['history'][-1])
    text, kind = R.doc_line(doc)
    assert text.startswith('CALC-PUMP-SKID rev B'), text
    # a calculation linked to the report document shows the same live status
    R.link_record(d['history'][0], doc)
    assert R.doc_line(client.document(R.record_link(d['history'][0])['id']))[0] == text
print('RevisionWorx link tests passed (real RevisionWorx)')
