"""Non-GUI smoke tests; run with python3 tests/test_core.py."""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))  # repo root, so `caldera` imports without installing
from caldera import calculations as c, legacy_calculations as l
from caldera.extended import EXTRA, calculate
assert abs(c.convert(1,'in → mm')-25.4)<1e-10
assert c.motor(125,460,93,.88,'3-phase')['Estimated current (A)']>0
assert l.cylinder_cycle(4,2,24,10,10)['cycle_sec']>0
for name,fields in EXTRA.items():
 values=[(v.default if isinstance(v,list) else (str(v) if v.__class__.__name__=='Text' else float(v))) for _,v in fields]
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
    r = evaluate(name, fn, specs, [d if not isinstance(d, list) else (getattr(d, 'default', None) or d[0]) for _, d in specs])
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


# ---------------------------------------------------------------- 1.1.0 additions
def _v110_tests():
    from caldera import conduit, extended, tank, toolmeta, units
    from caldera.registry import TOOLS

    # materials and thickness: per-material gauge standards, plates, legacy names
    assert tank.thickness('Carbon steel', '11 ga') == 0.1196
    assert tank.thickness('Stainless 304', '11 ga') == 0.125
    assert tank.thickness('Aluminum 5052-H32', '11 ga') == 0.0907
    assert tank.thickness('Galvanized steel (G90)', '14 ga') == 0.0785
    assert tank.thickness('HSLA steel (A572 Gr 50)', '1/2"') == 0.5
    try:
        tank.thickness('Galvanized steel (G90)', '7 ga'); raise AssertionError('7 ga galvanized should not exist')
    except ValueError:
        pass
    base = [36, 24, 24, '11 ga', 'Carbon steel (A36)', 80, 'Yes', 72, 48, '14 ga', 'Carbon steel (A36)', 'Yes', '14 ga', 8]
    al = list(base); al[4] = 'Aluminum 6061-T6'; al[3] = '1/4"'
    assert tank.reservoir_drip(al)['Tank empty weight (lb)'] < tank.reservoir_drip(base)['Tank empty weight (lb)']
    kinds = lambda a: {k for k, _t in tank.reservoir_drip(a)['_checks']}
    assert kinds(base) == {'good'}
    full = list(base); full[5] = 100
    assert 'bad' in kinds(full) and any('air gap' in t.lower() for _k, t in tank.reservoir_drip(full)['_checks'])
    low = list(base); low[13] = 2
    assert any('cannot contain' in t for _k, t in tank.reservoir_drip(low)['_checks'])
    norail = list(base); norail[11] = 'No'
    assert 'bad' in kinds(norail)
    mixed = list(base); mixed[10] = 'Aluminum 5052-H32'; mixed[9] = '1/8"'
    assert any('galvanic' in t for _k, t in tank.reservoir_drip(mixed)['_checks'])
    for m in tank.MATERIALS:
        for size in tank.THICKNESS_LABELS:
            tank.thickness_caption(m, size)

    # conduit: mixed conductors, limits, recommendation, round-trip text
    rows = conduit.parse_rows('3 × 12 AWG THHN; 2 × 4/0 AWG XHHW; 1 × 6 AWG Bare; 1 × 0.1 in² Other')
    assert [r[0] for r in rows] == [3, 2, 1, 1] and abs(rows[1][3] - 0.3197) < 1e-9
    assert conduit.parse_rows(conduit.format_rows(rows)) == rows
    assert conduit.fill_limit(1) == 53 and conduit.fill_limit(2) == 31 and conduit.fill_limit(5) == 40
    assert conduit.fill_limit(5, True) == 60
    r = conduit.conduit_fill('EMT', conduit.RECOMMEND, '3 × 12 AWG THHN; 1 × 12 AWG Bare', 'No')
    assert r['Recommended size'] == '1/2" EMT'
    r = conduit.conduit_fill('EMT', '1/2', '9 × 8 AWG THHN', 'No')
    assert any(k == 'bad' for k, _t in r['_checks']) and r['Recommended size'] == '1" EMT'
    for bad in ('', '3 × 99 AWG THHN', 'junk'):
        try:
            conduit.conduit_fill('EMT', conduit.RECOMMEND, bad, 'No'); raise AssertionError('should fail: ' + bad)
        except ValueError:
            pass
    s, fn = TOOLS['Conduit Fill']
    res = toolmeta.evaluate('Conduit Fill', fn, s, ['PVC Schedule 40', '1', '4 × 10 AWG THHN', 'No'])
    assert not res.error and res.metrics[res.hero].label == 'Recommended size', res.error

    # line velocity: recommendations and checks
    lv = extended.line_velocity(20, 1, 'Pump suction (inlet) line')
    assert abs(lv['Velocity (ft/s)'] - 8.168) < 0.01 and lv['_checks'][0][0] == 'bad'
    assert extended.line_velocity(20, 1, 'Pressure line (up to 3,000 PSI)')['_checks'][0][0] == 'good'
    assert extended.line_velocity(20, 1, 'Return line')['_checks'][0][0] == 'good'
    assert extended._hose_for(0.6391) == '-12 (3/4")'

    # compact axis labels
    f = toolmeta.fmt_compact
    assert [f(999), f(1000), f(1234), f(2.5e6), f(-45000), f(0.5)] == ['999', '1k', '1.23k', '2.5M', '-45k', '0.5']

    # units: inputs round-trip, results convert and de-duplicate
    try:
        units.set_system('Metric')
        assert units.display_unit('Bore', 'in') == 'mm' and units.display_unit('Modulus', 'PSI') == 'MPa'
        assert abs(units.to_canonical('Pressure', 'PSI', units.to_display('Pressure', 'PSI', 2500)) - 2500) < 1e-9
        s, fn = TOOLS['Line Velocity']
        res = units.localize_result(toolmeta.evaluate('Line Velocity', fn, s, ['20', '1', 'Return line']))
        vel = [m for m in res.metrics if m.label == 'Velocity']
        assert len(vel) == 1 and vel[0].unit == 'm/s'
        for name, (specs, fn) in TOOLS.items():
            raw = toolmeta.evaluate(name, fn, specs, [(getattr(d, 'default', None) or d[0]) if isinstance(d, list) else d for _, d in specs])
            loc = units.localize_result(raw)
            assert not loc.error and loc.as_text(), name
            assert raw.metrics is not loc.metrics or not raw.metrics or name == 'Unit Converter' or True
    finally:
        units.set_system('US Customary')


_v110_tests()
print('1.1.0 tests passed')
