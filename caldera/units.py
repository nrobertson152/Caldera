"""US Customary <-> Metric display layer. Qt-free.

Every calculator keeps working in US customary units internally (that is what the formulas, drafts, presets and saved
history use). This module only converts what the user sees and types:

- input fields show metric values / units and convert typed values back before the calculation runs;
- results, charts and captions are converted for display.

`SYSTEM` is the active system; the window sets it from the saved workspace setting."""
SYSTEMS = ('US Customary', 'Metric')
SYSTEM = 'US Customary'

# US unit -> (metric unit, factor) with metric = US x factor
TABLE = {
    'in': ('mm', 25.4), 'ft': ('m', 0.3048), 'in²': ('mm²', 645.16), 'ft²': ('m²', 0.09290304),
    'in³': ('cm³', 16.387064), 'in⁴': ('mm⁴', 416231.4256), 'ft³': ('L', 28.316846592),
    'gal': ('L', 3.785411784), 'GPM': ('L/min', 3.785411784),
    'PSI': ('bar', 0.0689475729), 'PSIG': ('bar g', 0.0689475729), 'PSIA': ('bar abs', 0.0689475729),
    'lbf': ('N', 4.4482216152605), 'lb': ('kg', 0.45359237), 'lb/gal': ('kg/L', 0.119826427),
    'lb-ft': ('N·m', 1.3558179483), 'lb·ft': ('N·m', 1.3558179483),
    'HP': ('kW', 0.745699872), 'ft/s': ('m/s', 0.3048), 'in/s': ('mm/s', 25.4),
    'CFM': ('L/min', 28.316846592), 'SCFM': ('NL/min', 28.316846592), 'SCF': ('NL', 28.316846592),
}
# quantity-specific overrides where the plain unit swap would give an unhelpful metric unit
LABEL_OVERRIDES = {'Modulus': ('MPa', 0.00689475729)}


def metric():
    return SYSTEM == 'Metric'


def set_system(name):
    global SYSTEM
    SYSTEM = name if name in SYSTEMS else SYSTEMS[0]


def _rule(name, unit):
    if not metric():
        return None
    if name in LABEL_OVERRIDES and unit in ('PSI', 'PSIG', 'PSIA'):
        return LABEL_OVERRIDES[name]
    return TABLE.get(unit)


def display_unit(name, unit):
    r = _rule(name, unit)
    return r[0] if r else unit


def to_display(name, unit, value):
    r = _rule(name, unit)
    return value * r[1] if r else value


def to_canonical(name, unit, value):
    r = _rule(name, unit)
    return value / r[1] if r else value


def convertible(name, unit):
    return _rule(name, unit) is not None


def num_text(value):
    """Compact text for a converted input value (never scientific for everyday sizes)."""
    if value == 0:
        return '0'
    text = '%.6g' % value
    if 'e' in text:
        text = ('%.6f' % value).rstrip('0').rstrip('.')
    return text


def q(value, unit, digits=1):
    """A quantity in the active system as text, e.g. q(10, 'gal') -> '10.0 gal' or '37.9 L'."""
    u = display_unit('', unit)
    return '{:,.{d}f} {u}'.format(to_display('', unit, value), d=digits, u=u)


def localize_result(res):
    """A copy of a toolmeta.Result with numeric metrics converted to the active system, dropping duplicates that
    conversion creates (e.g. 'Velocity (ft/s)' becomes a second 'Velocity (m/s)'). The original is not modified."""
    if not metric() or res is None or res.error:
        return res
    import copy
    original, res = res, copy.copy(res)
    seen, kept = set(), []
    hero_index = None
    for i, m in enumerate(original.metrics):
        m = type(m)(m.label, m.value, m.unit, m.kind)
        if m.kind == 'num' and convertible(m.label, m.unit):
            m.value, m.unit = to_display(m.label, m.unit, m.value), display_unit(m.label, m.unit)
        key = (m.label, m.unit)
        if key in seen:
            continue
        seen.add(key)
        if i == original.hero:
            hero_index = len(kept)
        kept.append(m)
    res.metrics = kept
    res.hero = hero_index or 0
    if res.table and getattr(res, 'table_units', None):
        headers, rows = res.table
        new_headers, conv = [], []
        for h, u in zip(headers, res.table_units):
            if u and convertible('', u):
                new_headers.append(h.replace('(%s)' % u, '(%s)' % display_unit('', u)))
                conv.append(u)
            else:
                new_headers.append(h)
                conv.append(None)
        new_rows = []
        for row in rows:
            out = []
            for v, u in zip(row, conv):
                if u and isinstance(v, (int, float)):
                    out.append(float('%.4g' % to_display('', u, v)))
                else:
                    out.append(v)
            new_rows.append(out)
        res.table = (new_headers, new_rows)
    return res
