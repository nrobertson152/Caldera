"""Non-GUI smoke tests; run with python3 tests.py."""
from caldera import calculations as c, legacy_calculations as l
from caldera.extended import EXTRA, calculate
assert abs(c.convert(1,'in → mm')-25.4)<1e-10
assert c.motor(125,460,93,.88,'3-phase')['Estimated current (A)']>0
assert l.cylinder_cycle(4,2,24,10,10)['cycle_sec']>0
for name,fields in EXTRA.items():
 values=[float(v) for _,v in fields]
 result=calculate(name,values)
 assert result and isinstance(result,dict),name
print('All calculation smoke tests passed')

# ---- workspace persistence, metadata adapter and exports (no Qt required) -------------------------------------
import json, os, tempfile
from pathlib import Path
from caldera import exports, workspace
from caldera.registry import TOOLS
from caldera.toolmeta import CATEGORIES, META, evaluate, parse_number

# every calculator evaluates cleanly with its defaults and has navigation metadata
allc = [n for names in CATEGORIES.values() for n in names]
for name, (specs, fn) in TOOLS.items():
    r = evaluate(name, fn, specs, [d if not isinstance(d, list) else d[0] for _, d in specs])
    assert not r.error and (r.metrics or r.raw_text), (name, r.error)
    assert name in allc and name in META, name
assert parse_number('30/2') == 15 and parse_number('1,234.5') == 1234.5 and parse_number('1,5') == 1.5
for bad in ('', 'abc', '__import__("os")', '9**9**9'):
    try:
        parse_number(bad); raise SystemExit('accepted ' + bad)
    except ValueError:
        pass

# workspace: defaults, sanitising, atomic save, corrupt-file protection
d = workspace.sanitize({'projects': ['A', 'A', ''], 'active_project': 'nope', 'history': [1, {'tool': 'x'}], 'precision': 99,
                        'favorites': 'bad', 'presets': []})
assert d['projects'] == ['General', 'A'] and d['active_project'] == 'General' and d['history'] == [{'tool': 'x'}]
assert d['precision'] == 10 and d['favorites'] == [] and d['presets'] == {}
with tempfile.TemporaryDirectory() as tmp:
    store = Path(tmp) / 'sub' / 'workspace.json'
    data, notice = workspace.load(store)
    assert notice is None and data['projects'] == ['General']
    data['history'].append({'tool': 'Unit Converter', 'result': 'Converted value: 25.4', 'project': 'General'})
    workspace.save(store, data)
    assert workspace.load(store)[0]['history'][0]['tool'] == 'Unit Converter' and not store.with_suffix('.tmp').exists()
    store.write_text('{ this is not json')
    data, notice = workspace.load(store)
    assert notice and list(store.parent.glob('workspace.corrupt-*.json')) and not store.exists()

    # exports: CSV/XLSX/PDF write valid files; PDF handles characters Helvetica cannot draw
    rows = [{'date': '2026-01-01T10:00:00', 'project': 'General', 'tool': 'Cylinder Buckling', 'inputs': ['1', '30'],
             'result': 'Area moment of inertia (in⁴): 0.049\nAllowable load ≈ 2,000 lbf → OK − margin', 'pinned': True}]
    exports.write_history_csv(Path(tmp) / 'h.csv', rows)
    assert 'Cylinder Buckling' in (Path(tmp) / 'h.csv').read_text(encoding='utf-8')
    exports.write_history_xlsx(Path(tmp) / 'h.xlsx', rows)
    from openpyxl import load_workbook
    assert load_workbook(Path(tmp) / 'h.xlsx').active['C2'].value == 'Cylinder Buckling'
    exports.build_pdf(Path(tmp) / 'p.pdf', 'Project: General', exports.project_blocks('General', 'notes <b>&', rows))
    assert (Path(tmp) / 'p.pdf').read_bytes()[:5] == b'%PDF-'
    exports.write_table_csv(Path(tmp) / 't.csv', ['A', 'B'], [['1', '2']])
    assert (Path(tmp) / 't.csv').read_text().splitlines() == ['A,B', '1,2']
assert 'CALDERA TEST REPORT' in exports.report_text({'title': 'T'})
print('Workspace, metadata and export tests passed')


# ---------------------------------------------------------------- beta 1.0.0 additions
def _beta1_tests():
    import json
    from caldera import model3d, tank, toolmeta, workspace
    from caldera.registry import TOOLS

    # reservoir / drip pan
    base = [36, 24, 24, '11 ga', 'Carbon steel', 80, 'Yes', 72, 48, '14 ga', 'Carbon steel', 'Yes', '14 ga', 8]
    r = tank.reservoir_drip(base)
    assert abs(r['Tank internal volume (gal)'] - 87.401) < 0.01, r
    assert abs(r['Oil capacity at fill level (gal)'] - 69.921) < 0.01
    off = list(base); off[11] = 'No'
    assert 'Drip rail weight (lb)' not in tank.reservoir_drip(off)
    ss = list(base); ss[10] = 'Stainless steel'
    assert tank.reservoir_drip(ss)['Drip pan weight (lb)'] > r['Drip pan weight (lb)']
    for bad in ([0] + base[1:], base[:5] + [150] + base[6:]):
        try:
            tank.reservoir_drip(bad); raise AssertionError('should fail')
        except ValueError:
            pass
    v = tank.params(base)
    for view in model3d.VIEWS:
        for ref in model3d.REFERENCES:
            parts, cap = model3d.build_scene(view, v, ref)
            assert model3d.project(parts, 0.6, 0.5)

    # linear detection
    assert toolmeta.is_linear([0, 1, 2, 3], [0, 2, 4, 6])
    assert not toolmeta.is_linear([0, 1, 2, 3], [0, 1, 4, 9])
    assert 'Reservoir / Drip Pan' in TOOLS

    # project files
    data = workspace.sanitize({'projects': ['General', 'A'], 'project_notes': {'A': 'hi'},
                               'history': [{'project': 'A', 'tool': 'T', 'date': '2026-01-01', 'result': 'x'}]})
    text = json.dumps(workspace.project_payload(data, 'A', '1.0.0'))
    proj = workspace.parse_project(text)
    assert workspace.import_project(data, proj, 'merge') == ('A', 0, 1)
    name, added, _ = workspace.import_project(data, proj, 'new')
    assert name == 'A (imported)' and added == 1 and name in data['projects']
    fresh = workspace.sanitize({})
    assert workspace.import_project(fresh, proj)[1] == 1 and fresh['project_notes']['A'] == 'hi'
    for junk in ('nope', '[]', '{"format":"x"}', json.dumps(workspace.backup_payload(data))):
        try:
            workspace.parse_project(junk); raise AssertionError('should fail')
        except ValueError:
            pass

    # backups
    back = json.dumps(workspace.backup_payload(data, '1.0.0'))
    assert workspace.parse_backup(back)['projects'] == data['projects']
    assert workspace.parse_backup(json.dumps(data))['projects'] == data['projects']      # legacy raw json
    try:
        workspace.parse_backup(text); raise AssertionError('should fail')
    except ValueError:
        pass
    assert workspace.ensure_ext('/x/y', '.caldera') == '/x/y.caldera'
    assert workspace.ensure_ext('/x/y.CALDERA', '.caldera') == '/x/y.CALDERA'


_beta1_tests()
print('Beta 1.0.0 tests passed')
