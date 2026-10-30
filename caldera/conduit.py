"""Conduit fill with mixed conductor sizes, plus a recommended trade size. Pure Python.

Data follows NEC Chapter 9: Table 1 (fill limits), Table 4 (conduit internal area) and Table 5 / Table 8
(conductor areas, approximate). Always verify against the code edition that applies to the job.

Conductors are passed as one text value so they save, re-open and compare like any other input:
    "3 × 12 AWG THHN; 1 × 10 AWG Bare; 2 × 0.05 in² Other"
"""
import math
import re

# NEC Ch. 9 Table 4: total internal area (in²) by trade size
CONDUITS = {
    'EMT': {'1/2': 0.304, '3/4': 0.533, '1': 0.864, '1-1/4': 1.496, '1-1/2': 2.036, '2': 3.356, '2-1/2': 5.858,
            '3': 8.846, '3-1/2': 11.545, '4': 14.753},
    'RMC (rigid)': {'1/2': 0.314, '3/4': 0.549, '1': 0.887, '1-1/4': 1.526, '1-1/2': 2.071, '2': 3.408,
                    '2-1/2': 4.866, '3': 7.499, '3-1/2': 10.010, '4': 12.882, '5': 20.212, '6': 29.158},
    'IMC': {'1/2': 0.342, '3/4': 0.586, '1': 0.959, '1-1/4': 1.647, '1-1/2': 2.225, '2': 3.630, '2-1/2': 5.135,
            '3': 7.922, '3-1/2': 10.584, '4': 13.631},
    'PVC Schedule 40': {'1/2': 0.285, '3/4': 0.508, '1': 0.832, '1-1/4': 1.453, '1-1/2': 1.986, '2': 3.291,
                        '2-1/2': 4.695, '3': 7.268, '3-1/2': 9.737, '4': 12.554, '5': 19.761, '6': 28.567},
    'PVC Schedule 80': {'1/2': 0.217, '3/4': 0.409, '1': 0.688, '1-1/4': 1.237, '1-1/2': 1.711, '2': 2.874,
                        '2-1/2': 4.119, '3': 6.442, '3-1/2': 8.688, '4': 11.258, '5': 17.855, '6': 25.598},
    'Flexible metal (FMC)': {'1/2': 0.317, '3/4': 0.533, '1': 0.817, '1-1/4': 1.277, '1-1/2': 1.858,
                             '2': 3.269, '2-1/2': 4.909, '3': 7.069, '3-1/2': 9.621, '4': 12.566},
    'Liquidtight metal (LFMC)': {'1/2': 0.314, '3/4': 0.541, '1': 0.873, '1-1/4': 1.528,
                                 '1-1/2': 1.981, '2': 3.246, '2-1/2': 4.881, '3': 7.475, '3-1/2': 9.731, '4': 12.692},
}
CONDUIT_TYPES = list(CONDUITS)
ALL_TRADE_SIZES = ['1/2', '3/4', '1', '1-1/4', '1-1/2', '2', '2-1/2', '3', '3-1/2', '4', '5', '6']
RECOMMEND = 'Recommend smallest'

SIZES = ['18', '16', '14', '12', '10', '8', '6', '4', '3', '2', '1', '1/0', '2/0', '3/0', '4/0',
         '250', '300', '350', '400', '500', '600', '750']
# NEC Ch. 9 Table 5 (and Table 8 for bare): approximate area (in²) per conductor
INSULATIONS = {
    'THHN / THWN-2': {'18': 0.0055, '16': 0.0072, '14': 0.0097, '12': 0.0133, '10': 0.0211, '8': 0.0366,
                      '6': 0.0507, '4': 0.0824, '3': 0.0973, '2': 0.1158, '1': 0.1562, '1/0': 0.1855, '2/0': 0.2223,
                      '3/0': 0.2679, '4/0': 0.3237, '250': 0.3970, '300': 0.4608, '350': 0.5242, '400': 0.5863,
                      '500': 0.7073, '600': 0.8676, '750': 1.0496},
    'XHHW / XHHW-2': {'14': 0.0139, '12': 0.0181, '10': 0.0243, '8': 0.0437, '6': 0.0590, '4': 0.0814, '3': 0.0962,
                      '2': 0.1146, '1': 0.1534, '1/0': 0.1825, '2/0': 0.2190, '3/0': 0.2642, '4/0': 0.3197,
                      '250': 0.3904, '300': 0.4536, '350': 0.5166, '400': 0.5782, '500': 0.6984, '600': 0.8709,
                      '750': 1.0532},
    'THW / TW': {'14': 0.0139, '12': 0.0181, '10': 0.0243, '8': 0.0437, '6': 0.0726, '4': 0.0973, '3': 0.1134,
                 '2': 0.1333, '1': 0.1901, '1/0': 0.2223, '2/0': 0.2624, '3/0': 0.3117, '4/0': 0.3718, '250': 0.4596,
                 '300': 0.5281, '350': 0.5958, '400': 0.6619, '500': 0.7901, '600': 0.9729},
    'Bare copper (stranded)': {'14': 0.004, '12': 0.006, '10': 0.011, '8': 0.017, '6': 0.027, '4': 0.042, '3': 0.053,
                               '2': 0.067, '1': 0.087, '1/0': 0.109, '2/0': 0.137, '3/0': 0.173, '4/0': 0.219},
}
INSULATION_TYPES = list(INSULATIONS) + ['Other (enter area)']
SHORT = {'THHN / THWN-2': 'THHN', 'XHHW / XHHW-2': 'XHHW', 'THW / TW': 'THW', 'Bare copper (stranded)': 'Bare',
         'Other (enter area)': 'Other'}
LONG = {v: k for k, v in SHORT.items()}
DEFAULT_ROWS = '3 × 12 AWG THHN; 1 × 12 AWG Bare'


def size_text(size):
    return '%s kcmil' % size if size.isdigit() and int(size) >= 250 else '%s AWG' % size


def conductor_area(insulation, size):
    table = INSULATIONS.get(insulation)
    if table is None:
        raise ValueError('Unknown insulation “%s”.' % insulation)
    if size not in table:
        raise ValueError('No %s data for %s. Pick another size or insulation.' % (insulation, size_text(size)))
    return table[size]


# ---------------------------------------------------------------- text encoding of the conductor list
_ROW = re.compile(r'^\s*(\d+)\s*[×x*]\s*([\d/.]+)\s*(AWG|kcmil|in²|in2)\s+(.+?)\s*$', re.I)


def parse_rows(text):
    """'3 × 12 AWG THHN; 2 × 0.05 in² Other' -> [(qty, insulation, size_or_None, area_each)]"""
    rows = []
    for part in str(text).split(';'):
        if not part.strip():
            continue
        m = _ROW.match(part)
        if not m:
            raise ValueError('Could not read conductor entry “%s”.' % part.strip())
        qty, size, unit, ins = int(m.group(1)), m.group(2), m.group(3).lower(), m.group(4).strip()
        ins = LONG.get(ins, ins)
        if unit.startswith('in'):
            area = float(size)
            if area <= 0:
                raise ValueError('Conductor area must be greater than zero.')
            rows.append((qty, 'Other (enter area)', None, area))
        else:
            rows.append((qty, ins, size, conductor_area(ins, size)))
    return rows


def format_rows(rows):
    """Inverse of parse_rows: [(qty, insulation, size_or_None, area)] -> text."""
    parts = []
    for qty, ins, size, area in rows:
        if size is None or ins == 'Other (enter area)':
            parts.append('%d × %s in² Other' % (qty, ('%.4f' % area).rstrip('0').rstrip('.')))
        else:
            parts.append('%d × %s %s' % (qty, size_text(size), SHORT.get(ins, ins)))
    return '; '.join(parts)


def fill_limit(n, nipple=False):
    """NEC Ch. 9 Table 1: 53 % for one conductor, 31 % for two, 40 % for three or more; 60 % in a nipple (≤ 24 in)."""
    if nipple:
        return 60.0
    return 53.0 if n == 1 else (31.0 if n == 2 else 40.0)


def smallest(kind, area, limit):
    for size, internal in CONDUITS[kind].items():
        if area <= internal * limit / 100 + 1e-12:
            return size
    return None


def conduit_fill(conduit_type, trade_size, rows_text, nipple):
    if conduit_type not in CONDUITS:
        raise ValueError('Choose a conduit type.')
    rows = parse_rows(rows_text)
    if not rows:
        raise ValueError('Add at least one conductor.')
    n = sum(q for q, *_ in rows)
    if n <= 0:
        raise ValueError('Add at least one conductor.')
    nipple = str(nipple) == 'Yes'
    total = sum(q * a for q, _i, _s, a in rows)
    limit = fill_limit(n, nipple)
    best = smallest(conduit_type, total, limit)
    out = {'Conductors': float(n), 'Total conductor area (in²)': total, 'Allowed fill (%)': limit,
           'Recommended size': ('%s" %s' % (best, conduit_type)) if best else 'Larger than the biggest %s' % conduit_type}
    checks = []
    if trade_size != RECOMMEND:
        if trade_size not in CONDUITS[conduit_type]:
            raise ValueError('%s" is not a standard size for %s.' % (trade_size, conduit_type))
        internal = CONDUITS[conduit_type][trade_size]
        fill = total / internal * 100
        out['Fill of %s" %s (%%)' % (trade_size, conduit_type)] = fill
        out['Spare allowable area (in²)'] = internal * limit / 100 - total
        if fill <= limit:
            checks.append(('good', '%s" %s is %.1f %% full, within the %.0f %% limit.' % (trade_size, conduit_type,
                                                                                         fill, limit)))
        else:
            checks.append(('bad', '%s" %s would be %.1f %% full, over the %.0f %% limit. Use %s.'
                           % (trade_size, conduit_type, fill, limit,
                              ('%s" or larger' % best) if best else 'parallel runs')))
    elif best:
        fill = total / CONDUITS[conduit_type][best] * 100
        out['Fill of recommended size (%)'] = fill
        checks.append(('good', '%s" %s is the smallest that fits: %.1f %% full against a %.0f %% limit.'
                       % (best, conduit_type, fill, limit)))
    else:
        checks.append(('bad', 'Even the largest %s exceeds the %.0f %% fill limit. Split the conductors into parallel '
                              'runs or use a larger raceway.' % (conduit_type, limit)))
    if n > 9 and not nipple:
        checks.append(('warn', 'More than 9 current-carrying conductors in one raceway need ampacity adjustment '
                               '(NEC 310.15(C)(1)); grounding conductors do not count.'))
    if nipple:
        checks.append(('warn', 'Nipple rule applied: 60 % fill is only allowed for a raceway 24 in or shorter, and the '
                               'conductors are exempt from adjustment factors only in that short length.'))
    if n == 2:
        checks.append(('warn', 'Two conductors are limited to 31 % fill, less than three would be. Adding a '
                               'third conductor can actually allow a smaller conduit.'))

    table_rows = []
    for kind in CONDUIT_TYPES:
        size = smallest(kind, total, limit)
        if size:
            table_rows.append([kind, size + '"', CONDUITS[kind][size], round(total / CONDUITS[kind][size] * 100, 1)])
        else:
            table_rows.append([kind, 'too large', '—', '—'])
    out['_table'] = (['Conduit', 'Smallest size', 'Area (in²)', 'Fill (%)'], table_rows,
                     [None, None, 'in²', None])
    out['_checks'] = checks
    detail = ', '.join('%d × %s' % (q, ('%s %s' % (size_text(s), SHORT.get(i, i))) if s else ('%.4g in²' % a))
                       for q, i, s, a in rows)
    out['_notes'] = ['Conductors: %s.' % detail,
                     'Areas from NEC Chapter 9 Tables 4, 5 and 8 (approximate). Equipment grounding conductors count '
                     'toward fill. Check the code edition and any local amendments that apply.']
    out['_sweepable'] = False
    return out
