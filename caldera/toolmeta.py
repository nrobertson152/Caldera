"""Presentation metadata for every Caldera page, plus the adapter that turns each calculator's raw
return value (dict or text) into a structured, unit-aware `Result` the UI can render.

The calculation modules themselves are untouched; this file only describes and formats them."""
import ast
import math
import operator
import re

# --------------------------------------------------------------------------- input spec types
class Choice(list):
    """A calculator input that picks from fixed options. `default` is the option selected initially / on reset."""

    def __init__(self, items, default=None):
        super().__init__(items)
        self.default = default if default in items else (items[0] if items else None)


def Toggle(on=True):
    """A yes/no input, shown as a tick box. Values are the strings 'Yes' / 'No'."""
    c = Choice(['Yes', 'No'], 'Yes' if on else 'No')
    c.toggle = True
    return c


def is_toggle(default):
    return isinstance(default, Choice) and getattr(default, 'toggle', False)


# choice values renamed in later versions -> current value (so old drafts / history re-open correctly)
CHOICE_ALIASES = {'Carbon steel': 'Carbon steel (A36)', 'Stainless steel': 'Stainless 304'}


class Text(str):
    """A free-text calculator input (passed to the calculator as-is, never parsed as a number or swept)."""


def is_text(default):
    return isinstance(default, Text)


# --------------------------------------------------------------------------- navigation model
CATEGORIES = {
    'Hydraulic': ['Hydraulic Pump & Motor', 'Hydraulic Motor', 'Hydraulic Power & Efficiency', 'Hydraulic Cylinder',
                  'Hydraulic Cylinder Cycle Time', 'Hydraulic Accumulator', 'Heat Load & Cooler Sizing',
                  'Line Velocity', 'Pressure Drop Calculator', 'Orifice Flow Estimate', 'Reservoir / Drip Pan',
                  'Seal Compatibility'],
    'Pneumatic': ['Pneumatic Cylinder', 'Pneumatic Air Consumption', 'Compressed Air Horsepower'],
    'Mechanical': ['Cylinder Buckling', 'Torque, RPM & Power'],
    'Electrical': ['Motor & Electrical Power', 'Wire Gauge & Voltage Drop', 'Conduit Fill',
                   'Electrical Load Summary', 'Wire List / CSV Generator'],
    'Utilities': ['Unit Converter', 'Labor Savings', 'Reference Tables', 'Test Report Generator',
                  'Compare Calculations', 'Methodology'],
}
CATEGORY_ICONS = {'Hydraulic': 'droplet', 'Pneumatic': 'wind', 'Mechanical': 'cog', 'Electrical': 'zap',
                  'Utilities': 'ruler'}

SYSTEM_PAGES = {  # name -> (icon, short label)
    'Overview': ('home', 'Home'),
    'Calculation History': ('history', 'History'),
    'Project Dashboard': ('folder', 'Projects'),
    'Settings': ('sliders', 'Settings'),
    'About Caldera': ('info', 'About'),
}

META = {
    'Unit Converter': ('swap', 'Convert common hydraulic, pneumatic and electrical units.'),
    'Motor & Electrical Power': ('motor', 'Current draw from motor output, voltage, efficiency and power factor.'),
    'Hydraulic Pump & Motor': ('pump', 'Pump flow, hydraulic output and shaft input from displacement and speed.'),
    'Hydraulic Power & Efficiency': ('gauge', 'Hydraulic horsepower, input power and heat loss.'),
    'Cylinder Buckling': ('ruler', 'Euler column check for cylinder rods and struts.'),
    'Hydraulic Cylinder Cycle Time': ('timer', 'Extend and retract time from bore, rod, stroke and flow.'),
    'Pneumatic Air Consumption': ('wind', 'Free-air demand of a double-acting cylinder in SCFM.'),
    'Torque, RPM & Power': ('cog', 'Convert between torque, speed and power.'),
    'Reservoir / Drip Pan': ('tank', 'Size a steel, stainless or aluminum reservoir and drip pan: capacity, containment, weight, safety checks and a 3D preview.'),
    'Wire Gauge & Voltage Drop': ('cable', 'Conductor sizes that stay inside a voltage-drop budget.'),
    'Conduit Fill': ('conduit', 'Mixed conductor sizes in one raceway: fill %, code limit and the smallest conduit that fits.'),
    'Hydraulic Cylinder': ('cylinder', 'Push / pull force and stroke times.'),
    'Hydraulic Motor': ('cog', 'Output torque, flow demand and power.'),
    'Heat Load & Cooler Sizing': ('flame', 'System heat load and a cooler target.'),
    'Hydraulic Accumulator': ('tank', 'Gas volume for a required usable discharge.'),
    'Pneumatic Cylinder': ('cylinder', 'Force and stroke time for a pneumatic cylinder.'),
    'Compressed Air Horsepower': ('wind', 'Idealized isothermal compressor input power.'),
    'Line Velocity': ('flow', 'Fluid velocity, recommended ranges for suction, return and pressure lines, and hose size.'),
    'Pressure Drop Calculator': ('activity', 'Darcy–Weisbach pressure drop with flow-regime detection.'),
    'Orifice Flow Estimate': ('funnel', 'Flow through a sharp-edged orifice.'),
    'Labor Savings': ('timer', 'Hours and cost saved by a faster cycle.'),
    'Seal Compatibility': ('shield', 'Colour-coded seal material screening by fluid family.'),
    'Reference Tables': ('book', 'Conversions, constants and quick formulas.'),
    'Electrical Load Summary': ('table', 'Tabulate electrical loads and export CSV.'),
    'Wire List / CSV Generator': ('list', 'Build a wire list and export CSV.'),
    'Test Report Generator': ('clipboard', 'Compose an inspection or test report.'),
    'Compare Calculations': ('compare', 'Put two saved results side by side.'),
    'Methodology': ('sigma', 'Formulas, assumptions and scope for every calculator.'),
}

FORMULAS = {
    'Unit Converter': ['result = value × factor', '°F → °C = (°F − 32) × 5/9', '°C → °F = °C × 9/5 + 32'],
    'Motor & Electrical Power': ['P_out (kW) = HP × 0.745700', 'P_in = P_out / η',
                                 'I = P_in × 1000 / (V × PF × √3)      (√3 dropped for single phase)'],
    'Hydraulic Pump & Motor': ['Q_theoretical (GPM) = D (cc/rev) × n / 3785.41', 'Q_actual = Q_theoretical × η_vol',
                               'P_hyd (HP) = psi × Q / 1714', 'P_shaft = P_hyd / η_mech'],
    'Hydraulic Power & Efficiency': ['P_hyd (HP) = psi × GPM / 1714', 'P_input = P_hyd / η', 'P_loss = P_hyd × (1/η − 1)'],
    'Cylinder Buckling': ['I = π d⁴ / 64', 'P_cr = π² E I / (K L)²', 'P_allow = P_cr / SF'],
    'Hydraulic Cylinder Cycle Time': ['A_cap = π b² / 4        A_ann = π (b² − r²) / 4', 'V (gal) = A × stroke / 231',
                                      't (s) = V / Q × 60'],
    'Pneumatic Air Consumption': ['V_swept (ft³) = π/4 × (2b² − r²) × stroke / 1728',
                                  'V_free = V_swept × (P_gauge + P_atm) / P_atm', 'SCFM = V_free × cycles/min'],
    'Torque, RPM & Power': ['HP = T (lb·ft) × 2π × RPM / (60 × 550)', 'kW = HP × 0.745700', 'N·m = lb·ft × 1.355818'],
    'Reservoir / Drip Pan': ['t = plate size, or gauge looked up in the material’s own gauge standard',
                             'V_internal = (L − 2t)(W − 2t)(H − 2t)      (one t less in height if open top)',
                             'Oil = V_internal × fill %        Air gap = V_internal − Oil',
                             'Shell weight = (V_outer − V_internal) × ρ      ρ = 0.284 steel / 0.289 stainless / 0.097 aluminum lb/in³',
                             'Pan weight = L × W × t × ρ      Rail weight = (L·W − (L−2t_r)(W−2t_r)) × h × ρ',
                             'Pan capacity = (L−2t_r)(W−2t_r) × h / 231      Net = (pan area − tank footprint) × h / 231'],
    'Conduit Fill': ['Fill % = Σ (n × A_conductor) / A_conduit × 100',
                     'Limit: 53 % (1 conductor), 31 % (2), 40 % (3 or more), 60 % for a nipple ≤ 24 in',
                     'Recommended = smallest trade size with Σ A ≤ A_conduit × limit',
                     'A_conductor: NEC Ch. 9 Table 5 / 8      A_conduit: NEC Ch. 9 Table 4'],
    'Hydraulic Cylinder': ['F = P × A', 'A_cap = π b² / 4        A_ann = π (b² − r²) / 4', 't = A × stroke / 231 / Q × 60'],
    'Hydraulic Motor': ['T (lb·ft) = P × D / (2π) × η_mech / 12', 'Q = D × n / 3785.41 / η_vol',
                        'HP_out = P × D × n / 3785.41 / 1714 × η_mech'],
    'Heat Load & Cooler Sizing': ['P_heat (HP) = psi × GPM / 1714 × loss %', 'kW = HP × 0.7457',
                                  'Cooler target = kW × (1 + margin %)'],
    'Hydraulic Accumulator': ['V₀ = ΔV / [ (P₀/P₁)^(1/n) − (P₀/P₂)^(1/n) ]', 'Pressures absolute; P₀ < P₁ < P₂'],
    'Pneumatic Cylinder': ['F = P × A', 't = A × stroke / 1728 / CFM × 60'],
    'Compressed Air Horsepower': ['P_iso = P₁ × Q₁ × ln(P₂ / P₁)', 'P_input = P_iso / η'],
    'Line Velocity': ['v (ft/s) = 0.3208 × Q (GPM) / A (in²)        A = π d² / 4',
                      'd_min = √(4 × 0.3208 × Q / (v_max × π))',
                      'v_max: suction 4, return 15, pressure 20 (25 above 3,000 PSI) ft/s'],
    'Pressure Drop Calculator': ['Re = v D / ν', 'f = 64 / Re   (laminar, Re < 2300)',
                                 'f = 0.25 / [log₁₀(ε / 3.7D + 5.74 / Re^0.9)]²   (Swamee–Jain)',
                                 'ΔP = f × (L / D) × ρ v² / 2'],
    'Orifice Flow Estimate': ['Q (GPM) = 29.84 × C_d × d² × √(ΔP / SG)'],
    'Labor Savings': ['Hours saved = (t_old − t_new) × cycles / 60', 'Savings = hours × rate'],
}
NOTES = {
    'Wire Gauge & Voltage Drop': 'Voltage drop depends on conductor resistance, one-way distance, load current and '
                                 'return path. Ampacity requires a separate code assessment.',
    'Cylinder Buckling': 'Euler buckling applies to slender members. Check end-fixity factor and consider '
                         'side loading and manufacturer rod ratings.',
    'Unit Converter': 'Conversions use fixed physical ratios. US customary gallons are assumed.',
    'Pneumatic Air Consumption': 'Estimated from cylinder displacement, pressure ratio and cycle frequency.',
}
DEFAULT_NOTE = ('Preliminary estimate. Review input units, efficiency assumptions, manufacturer specifications '
                'and applicable design standards.')


def category_of(name):
    for cat, names in CATEGORIES.items():
        if name in names:
            return cat
    return 'Utilities'


def icon_of(name):
    if name in META:
        return META[name][0]
    return SYSTEM_PAGES.get(name, ('info', ''))[0]


def blurb_of(name):
    return META.get(name, ('', ''))[1]


# --------------------------------------------------------------------------- input parsing
_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.Pow: operator.pow, ast.USub: operator.neg, ast.UAdd: operator.pos}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)
    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return float(node.value)
    if isinstance(node, ast.Name) and node.id in ('pi', 'e'):
        return math.pi if node.id == 'pi' else math.e
    if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)
        if isinstance(node.op, ast.Pow) and abs(right) > 64:
            raise ValueError('exponent too large')
        return _OPS[type(node.op)](left, right)
    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
        return _OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError('unsupported expression')


def parse_number(text):
    """Parse a field value. Accepts plain numbers, 1,234.5 grouping, 1,5 decimal commas and simple
    arithmetic such as 30/2 or 2*pi*1.5. Raises ValueError when it is not a number."""
    s = str(text).strip().replace('_', '').replace(' ', '')
    if not s:
        raise ValueError('empty')
    try:
        return float(s)
    except ValueError:
        pass
    if re.fullmatch(r'-?\d{1,3}(,\d{3})+(\.\d+)?', s):
        return float(s.replace(',', ''))
    if re.fullmatch(r'-?\d+,\d+', s):
        return float(s.replace(',', '.'))
    try:
        return float(_safe_eval(ast.parse(s.replace('^', '**'), mode='eval')))
    except (SyntaxError, ValueError, ZeroDivisionError, OverflowError, RecursionError):
        raise ValueError('not a number')


_UNIT_RE = re.compile(r'^(.*?)\s*\(([^()]+)\)\s*$')


def split_label(label):
    """'Pressure (PSI)' -> ('Pressure', 'PSI')."""
    m = _UNIT_RE.match(label)
    return (m.group(1), m.group(2)) if m else (label, '')


# --------------------------------------------------------------------------- results
class Metric:
    __slots__ = ('label', 'value', 'unit', 'kind')

    def __init__(self, label, value, unit='', kind='num'):
        self.label, self.value, self.unit, self.kind = label, value, unit, kind


class Result:
    def __init__(self):
        self.metrics = []
        self.status = []        # [(ok: bool, text)]
        self.table = None       # (headers, rows)
        self.table_units = None  # optional US unit per table column, for metric display
        self.notes = []
        self.hero = 0
        self.sweepable = True
        self.error = None
        self.raw_text = None    # when the calculator returns prose (e.g. wire sizing)

    def numeric(self):
        return [i for i, m in enumerate(self.metrics) if m.kind == 'num']

    def as_text(self, precision=3):
        lines = []
        for m in self.metrics:
            name = '%s (%s)' % (m.label, m.unit) if m.unit else m.label
            lines.append('%s: %s' % (name, format_metric(m, precision)))
        for ok, text in self.status:
            if isinstance(ok, str):
                lines.append('%s: %s' % (CHECK_WORDS.get(ok, 'Note'), text))
            else:
                lines.append('%s: %s' % (text, 'Yes' if ok else 'No'))
        if self.table:
            headers, rows = self.table
            lines.append('')
            lines.append('  |  '.join(headers))
            lines.extend('  |  '.join(str(c) for c in row) for row in rows)
        return '\n'.join(lines)


def fmt_num(v, precision=3):
    """Compact, readable number: thousands separators, at most `precision` decimals, no trailing zeros."""
    if isinstance(v, bool):
        return 'Yes' if v else 'No'
    if not isinstance(v, (int, float)):
        return str(v)
    if math.isnan(v):
        return '—'
    if math.isinf(v):
        return '∞' if v > 0 else '−∞'
    if v == 0:
        return '0'
    a = abs(v)
    if a >= 1e15 or a < 10 ** (-precision):
        return ('%.' + str(max(precision, 1)) + 'e') % v
    text = ('{:,.' + str(precision) + 'f}').format(v)
    if '.' in text:
        text = text.rstrip('0').rstrip('.')
    return text


def fmt_compact(v):
    """Short axis label: 950, 1.2k, 45k, 3.5M, 1.2B. Small values keep up to 3 significant digits."""
    if isinstance(v, bool) or not isinstance(v, (int, float)) or math.isnan(v) or math.isinf(v):
        return fmt_num(v)
    a = abs(v)
    if a < 1e-12:
        return '0'
    for div, suffix in ((1e12, 'T'), (1e9, 'B'), (1e6, 'M'), (1e3, 'k'), (1, '')):
        if a >= div * 0.9995:
            x = v / div
            text = ('%.3g' % x) if abs(x) < 1000 else '%.0f' % x
            if 'e' in text:
                text = '%.0f' % x
            if suffix and text.lstrip('-') == '1000' and div < 1e12:
                continue
            return text + suffix
    return '%.3g' % v


CHECK_WORDS = {'good': 'OK', 'warn': 'Warning', 'bad': 'Problem'}


def status_kind(ok):
    """Banner kind for a Result.status entry: bools from calculators, or an explicit 'good' / 'warn' / 'bad'."""
    if isinstance(ok, str):
        return ok if ok in CHECK_WORDS else 'warn'
    return 'good' if ok else 'bad'


def format_metric(m, precision=3):
    if m.kind == 'num':
        return fmt_num(m.value, precision)
    if m.kind == 'bool':
        return 'Yes' if m.value else 'No'
    return str(m.value)


_LEGACY = {
    'hydraulic_hp': ('Hydraulic power', 'HP'), 'input_hp': ('Input power', 'HP'), 'loss_hp': ('Power lost as heat', 'HP'),
    'I': ('Area moment of inertia', 'in⁴'), 'critical_lbf': ('Critical buckling load', 'lbf'),
    'allowable_lbf': ('Allowable load', 'lbf'),
    'cap_area': ('Cap-end area', 'in²'), 'annulus_area': ('Annulus area', 'in²'),
    'extend_gal': ('Extend volume', 'gal'), 'retract_gal': ('Retract volume', 'gal'),
    'extend_sec': ('Extend time', 's'), 'retract_sec': ('Retract time', 's'), 'cycle_sec': ('Full cycle time', 's'),
    'compressed_ft3_cycle': ('Compressed air per cycle', 'ft³'), 'free_air_scf_cycle': ('Free air per cycle', 'SCF'),
    'scfm': ('Air consumption', 'SCFM'),
    'hp': ('Shaft power', 'HP'), 'kw': ('Shaft power', 'kW'), 'torque_nm': ('Torque', 'N·m'),
    'gross_gal': ('Gross volume', 'gal'), 'usable_gal': ('Usable volume', 'gal'),
    'plate_area_ft2': ('Plate area', 'ft²'), 'six_face_weight_lb': ('Six-face plate weight', 'lb'),
}
_BOOL_TEXT = {
    'passes_euler': ('Applied load is within the allowable buckling load', 'Applied load exceeds the allowable buckling load'),
    'Within limit': ('Within the conduit fill limit', 'Exceeds the conduit fill limit'),
    'Tank fits in pan': ('The reservoir footprint fits inside the drip pan', 'The reservoir footprint is larger than the drip pan interior'),
    'Pan holds 110% of oil': ('Pan holds at least 110% of the reservoir oil', 'Pan holds less than 110% of the reservoir oil'),
}
_HERO = {'Cylinder Buckling': 'allowable_lbf', 'Hydraulic Cylinder Cycle Time': 'cycle_sec',
         'Hydraulic Cylinder': 'Extend force (lbf)', 'Pneumatic Cylinder': 'Extend force (lbf)',
         'Pressure Drop Calculator': 'Pressure drop (PSI)', 'Torque, RPM & Power': 'hp',
         'Reservoir / Drip Pan': 'Oil capacity at fill level (gal)', 'Conduit Fill': 'Recommended size'}


def _normalize_dict(name, raw):
    r = Result()
    hero_key = _HERO.get(name)
    r.notes.extend(raw.get('_notes', []))
    for level, text in raw.get('_checks', []):
        r.status.append((level, text))
    if raw.get('_table'):
        tbl = raw['_table']
        r.table = (list(tbl[0]), [list(row) for row in tbl[1]])
        r.table_units = list(tbl[2]) if len(tbl) > 2 else None
    if raw.get('_sweepable') is False:
        r.sweepable = False
    for i, (key, value) in enumerate(raw.items()):
        if key.startswith('_'):
            continue
        if key in _LEGACY:
            label, unit = _LEGACY[key]
        else:
            label, unit = split_label(key)
        if isinstance(value, bool):
            yes, no = _BOOL_TEXT.get(key, (label, 'Not ' + label.lower()))
            r.status.append((value, yes if value else no))
            continue
        if isinstance(value, (int, float)):
            r.metrics.append(Metric(label, value, unit, 'num'))
            if hero_key is not None and key == hero_key:
                r.hero = len(r.metrics) - 1
        else:
            r.metrics.append(Metric(label, value, unit, 'text'))
            if hero_key is not None and key == hero_key:
                r.hero = len(r.metrics) - 1
    return r


_WIRE_ROW = re.compile(r'^\s*(\S+) AWG\s+([\d.]+) V\s+\(([\d.]+)%\)', re.M)


def _normalize_wire(raw):
    r = Result()
    r.raw_text = raw
    r.sweepable = False
    m = re.search(r'Allowed voltage drop: ([\d.]+) V', raw)
    allowed = float(m.group(1)) if m else 0.0
    rows = _WIRE_ROW.findall(raw)
    if rows:
        gauge, drop, pct = rows[0]
        r.metrics = [Metric('Smallest passing gauge', gauge + ' AWG', '', 'text'),
                     Metric('Voltage drop', float(drop), 'V'), Metric('Drop of supply', float(pct), '%'),
                     Metric('Allowed drop', allowed, 'V')]
        r.table = (['Gauge (AWG)', 'Voltage drop (V)', 'Drop (%)'], [[g, d, p] for g, d, p in rows])
        r.status.append((True, '%d conductor size%s meet the target' % (len(rows), '' if len(rows) == 1 else 's')))
    else:
        r.metrics = [Metric('Allowed drop', allowed, 'V')]
        r.status.append((False, 'No listed conductor meets the target'))
    r.notes.append('Voltage drop alone does not establish code-compliant ampacity.')
    return r


def evaluate(name, fn, specs, values, precision=3):
    """Run a calculator. `specs` is the field list [(label, default_or_choices)], `values` the raw strings.
    Always returns a Result; Result.error is set on bad input."""
    r = Result()
    args = []
    for (label, default), value in zip(specs, values):
        if is_text(default):
            args.append(str(value))
        elif isinstance(default, list):
            try:
                args.append(float(value))
            except ValueError:
                args.append(value)
        else:
            try:
                args.append(parse_number(value))
            except ValueError:
                r.error = 'Enter a number for “%s”.' % split_label(label)[0]
                return r
    try:
        raw = fn(args)
    except (ValueError, ZeroDivisionError, OverflowError, AssertionError, TypeError, KeyError, IndexError) as e:
        r.error = (str(e) or 'Check that every input is inside its valid range.').strip("'")
        return r
    if isinstance(raw, dict):
        r = _normalize_dict(name, raw)
    elif name == 'Wire Gauge & Voltage Drop':
        r = _normalize_wire(str(raw))
    else:
        r.raw_text = str(raw)
        r.sweepable = False
    if name == 'Unit Converter' and len(args) > 1 and '→' in str(args[1]):
        for m in r.metrics:
            m.unit = str(args[1]).split('→')[1].strip()
    return r


# --------------------------------------------------------------------------- sensitivity sweeps
SWEEP_POINTS = 41


def metric_key(m):
    return '%s (%s)' % (m.label, m.unit) if m.unit else m.label


def is_linear(xs, ys, tol=1e-6):
    """True when y is a straight line of x (including constant). Too few points also counts: nothing to plot."""
    if len(xs) < 3:
        return True
    x0, x1, y0, y1 = xs[0], xs[-1], ys[0], ys[-1]
    if x1 == x0:
        return True
    scale = max(max(abs(y) for y in ys), 1e-12)
    slope = (y1 - y0) / (x1 - x0)
    return max(abs(y - (y0 + slope * (x - x0))) for x, y in zip(xs, ys)) <= tol * scale


def sweep_all(name, fn, specs, values, points=SWEEP_POINTS):
    """Sweep every numeric input +/-50 % and record each numeric output.
    Returns {input_index: {'xs': [...], 'series': {metric_key: [...]}, 'nonlinear': [metric_key, ...]}}.
    Outputs that are straight lines of the swept input are left out of 'nonlinear' (not worth charting)."""
    out = {}
    for idx, (_label, default) in enumerate(specs):
        if isinstance(default, list) or is_text(default) or idx >= len(values):
            continue
        try:
            v0 = parse_number(values[idx])
        except ValueError:
            continue
        lo, hi = (v0 * 0.5, v0 * 1.5) if v0 > 0 else ((v0 * 1.5, v0 * 0.5) if v0 < 0 else (0.0, 1.0))
        rows = []
        for k in range(points):
            x = lo + (hi - lo) * k / (points - 1)
            trial = list(values)
            trial[idx] = '%.12g' % x
            r = evaluate(name, fn, specs, trial)
            if r.error:
                continue
            rows.append((x, {metric_key(m): m.value for m in r.metrics if m.kind == 'num'}))
        if len(rows) < 3:
            continue
        keys = [k for k in rows[0][1] if all(k in vals for _x, vals in rows)]
        xs = [x for x, _v in rows]
        series = {k: [vals[k] for _x, vals in rows] for k in keys}
        out[idx] = {'xs': xs, 'series': series, 'nonlinear': [k for k in keys if not is_linear(xs, series[k])]}
    return out
