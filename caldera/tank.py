"""Reservoir + drip pan sizing. Pure Python, US customary units (inches, gallons, pounds).

Conventions
- Reservoir L x W x H are OUTSIDE dimensions (how sheet-metal tanks are specified).
- Wall thickness is either a sheet gauge or a fractional plate size (1/8" to 1/2"). A gauge number means a different
  thickness for each material family, because each uses its own gauge standard:
    carbon / HSLA steel  - Manufacturers' Standard Gauge
    galvanized steel     - galvanized sheet gauge (includes the zinc coating)
    stainless steel      - the common stainless sheet chart
    aluminum             - Brown & Sharpe (AWG) gauge
- The drip pan is a flat sheet. The optional drip rail is a wall standing on the pan around its edge, made from the
  pan's material. Containment capacity therefore comes from the rail height.
"""
from . import units

GAUGES = [28, 26, 24, 22, 20, 18, 16, 14, 13, 12, 11, 10, 8, 7]               # thin -> thick
PLATES = {'1/8"': 0.125, '3/16"': 0.1875, '1/4"': 0.25, '5/16"': 0.3125, '3/8"': 0.375, '1/2"': 0.5}
THICKNESS_LABELS = ['%d ga' % g for g in GAUGES] + list(PLATES)
GAUGE_LABELS = THICKNESS_LABELS                                                # older name, kept for imports

# gauge -> thickness (in), per gauge standard
GAUGE_TABLES = {
    'msg': {7: 0.1793, 8: 0.1644, 10: 0.1345, 11: 0.1196, 12: 0.1046, 13: 0.0897, 14: 0.0747, 16: 0.0598,
            18: 0.0478, 20: 0.0359, 22: 0.0299, 24: 0.0239, 26: 0.0179, 28: 0.0149},
    'galv': {8: 0.1681, 10: 0.1382, 11: 0.1233, 12: 0.1084, 13: 0.0934, 14: 0.0785, 16: 0.0635, 18: 0.0516,
             20: 0.0396, 22: 0.0336, 24: 0.0276, 26: 0.0217, 28: 0.0187},
    'ss': {7: 0.1875, 8: 0.1719, 10: 0.1406, 11: 0.1250, 12: 0.1094, 13: 0.0938, 14: 0.0781, 16: 0.0625,
           18: 0.0500, 20: 0.0375, 22: 0.0312, 24: 0.0250, 26: 0.0187, 28: 0.0156},
    'al': {7: 0.1443, 8: 0.1285, 10: 0.1019, 11: 0.0907, 12: 0.0808, 13: 0.0720, 14: 0.0641, 16: 0.0508,
           18: 0.0403, 20: 0.0320, 22: 0.0253, 24: 0.0201, 26: 0.0159, 28: 0.0126},
}
GAUGE_STANDARD_NAMES = {'msg': "Manufacturers' Standard Gauge", 'galv': 'galvanized sheet gauge',
                        'ss': 'stainless sheet gauge', 'al': 'Brown & Sharpe (aluminum) gauge'}

# name -> gauge standard, density (lb/in^3), min yield (ksi), 3D colour, family
MATERIAL_DATA = {
    'Carbon steel (A36)':     dict(gauge='msg', density=0.284, yield_ksi=36, color='#7d8da1', family='steel'),
    'HSLA steel (A572 Gr 50)': dict(gauge='msg', density=0.284, yield_ksi=50, color='#6e7d90', family='steel'),
    'Galvanized steel (G90)': dict(gauge='galv', density=0.284, yield_ksi=33, color='#a7b4bf', family='steel'),
    'Stainless 304':          dict(gauge='ss', density=0.289, yield_ksi=30, color='#c4ccd6', family='stainless'),
    'Stainless 316':          dict(gauge='ss', density=0.289, yield_ksi=30, color='#b9c4cf', family='stainless'),
    'Aluminum 5052-H32':      dict(gauge='al', density=0.0968, yield_ksi=28, color='#d9dfe4', family='aluminum'),
    'Aluminum 6061-T6':       dict(gauge='al', density=0.0975, yield_ksi=35, color='#cdd5dc', family='aluminum'),
}
MATERIALS = list(MATERIAL_DATA)
ALIASES = {'Carbon steel': 'Carbon steel (A36)', 'Stainless steel': 'Stainless 304'}     # names used before 1.1
THICKNESS = {m: GAUGE_TABLES[d['gauge']] for m, d in MATERIAL_DATA.items()}
DENSITY = {m: d['density'] for m, d in MATERIAL_DATA.items()}
OIL_LB_PER_GAL = 7.3                                              # ~0.875 specific gravity hydraulic oil
GAL_IN3 = 231.0

# input order == registry field order
KEYS = ['tank_l', 'tank_w', 'tank_h', 'tank_ga', 'tank_mat', 'fill', 'top', 'pan_l', 'pan_w', 'pan_ga', 'pan_mat',
        'rail_on', 'rail_ga', 'rail_h']


def material(name):
    """Canonical material name (accepts the pre-1.1 'Carbon steel' / 'Stainless steel')."""
    name = ALIASES.get(str(name), str(name))
    if name not in MATERIAL_DATA:
        raise ValueError('Unknown material “%s”.' % name)
    return name


def thickness(mat, size):
    """Wall thickness in inches. `size` may be a gauge (14, '14', '14 ga') or a plate size ('1/4"')."""
    mat = material(mat)
    s = str(size).strip()
    if s in PLATES:
        return PLATES[s]
    try:
        g = int(float(s.split()[0]))
    except (ValueError, IndexError):
        raise ValueError('Unknown thickness “%s”.' % size)
    table = GAUGE_TABLES[MATERIAL_DATA[mat]['gauge']]
    if g not in table:
        raise ValueError('%d ga is not a standard %s size for %s. Choose another gauge or a plate thickness.'
                         % (g, GAUGE_STANDARD_NAMES[MATERIAL_DATA[mat]['gauge']], mat))
    return table[g]


def thickness_caption(mat, size):
    """'11 ga' -> '11 ga · 0.1196 in' (in the active unit system); unknown combinations get a short note."""
    try:
        t = thickness(mat, size)
    except ValueError:
        return '%s · not made in this material' % size
    if units.metric():
        return '%s · %.2f mm' % (size, t * 25.4)
    return '%s · %.4f in' % (size, t)


def params(a):
    """Turn the raw input list (numbers and strings) into one validated dict. Raises ValueError with a clear message."""
    if len(a) != len(KEYS):
        raise ValueError('Reservoir / Drip Pan needs %d inputs.' % len(KEYS))
    v = dict(zip(KEYS, a))
    for k in ('tank_l', 'tank_w', 'tank_h', 'fill', 'pan_l', 'pan_w', 'rail_h'):
        v[k] = float(v[k])
    for k in ('tank_mat', 'pan_mat'):
        v[k] = material(v[k])
    v['top'] = str(v['top']) == 'Yes'
    v['rail_on'] = str(v['rail_on']) == 'Yes'
    v['t_tank'] = thickness(v['tank_mat'], v['tank_ga'])
    v['t_pan'] = thickness(v['pan_mat'], v['pan_ga'])
    v['t_rail'] = thickness(v['pan_mat'], v['rail_ga']) if v['rail_on'] else 0.0   # the rail takes the pan's material
    if min(v['tank_l'], v['tank_w'], v['tank_h'], v['pan_l'], v['pan_w']) <= 0:
        raise ValueError('Lengths, widths and heights must be greater than zero.')
    if not 0 < v['fill'] <= 100:
        raise ValueError('Fill level must be between 0 and 100 %.')
    if 2 * v['t_tank'] >= min(v['tank_l'], v['tank_w'], v['tank_h']):
        raise ValueError('The reservoir is too small for this wall thickness.')
    if v['rail_on']:
        if v['rail_h'] <= 0:
            raise ValueError('Drip rail height must be greater than zero.')
        if 2 * v['t_rail'] >= min(v['pan_l'], v['pan_w']):
            raise ValueError('The drip pan is too small for this rail thickness.')
    return v


def _q(x, unit, digits=1):
    return units.q(x, unit, digits)


def reservoir_drip(a):
    v = params(a)
    L, W, H, t = v['tank_l'], v['tank_w'], v['tank_h'], v['t_tank']
    rho_t, rho_p = DENSITY[v['tank_mat']], DENSITY[v['pan_mat']]

    # ---- reservoir
    inner_h = H - (2 * t if v['top'] else t)
    inner = (L - 2 * t) * (W - 2 * t) * inner_h
    gross_gal = inner / GAL_IN3
    oil_gal = gross_gal * v['fill'] / 100
    air_gal = gross_gal - oil_gal
    oil_depth = inner_h * v['fill'] / 100
    air_h = inner_h - oil_depth
    tank_wt = (L * W * H - inner) * rho_t
    tank_full = tank_wt + oil_gal * OIL_LB_PER_GAL

    # ---- drip pan and rail
    pl, pw, tp, tr = v['pan_l'], v['pan_w'], v['t_pan'], v['t_rail']
    pan_wt = pl * pw * tp * rho_p
    out = {
        'Tank internal volume (gal)': gross_gal,
        'Oil capacity at fill level (gal)': oil_gal,
        'Air gap volume (gal)': air_gal,
        'Air gap height (in)': air_h,
        'Oil depth (in)': oil_depth,
        'Tank wall thickness (in)': t,
        'Pan thickness (in)': tp,
        'Tank empty weight (lb)': tank_wt,
        'Tank weight full of oil (lb)': tank_full,
        'Drip pan weight (lb)': pan_wt,
    }
    notes = ['Reservoir dimensions are outside dimensions. Oil is taken as %.1f lb/gal. Tank is assumed to sit flat on '
             'the pan with no feet, and corner radii, bends and welds are ignored.' % OIL_LB_PER_GAL,
             'Gauges follow each material’s own standard (%s: %s; %s: %s).' % (
                 v['tank_mat'], GAUGE_STANDARD_NAMES[MATERIAL_DATA[v['tank_mat']]['gauge']],
                 v['pan_mat'], GAUGE_STANDARD_NAMES[MATERIAL_DATA[v['pan_mat']]['gauge']])]
    checks = []

    # ---- reservoir checks
    if v['fill'] >= 100 or air_h <= 0:
        checks.append(('bad', 'Zero air gap: the reservoir is filled to the top. Oil needs headspace for thermal '
                              'expansion, return surge and de-aeration, and a full tank will push oil out of the '
                              'breather. Lower the fill level.'))
    elif air_h < 1.0 or v['fill'] > 90:
        checks.append(('warn', 'Small air gap (%s above the oil, %.0f %% full). Leave more headspace for thermal '
                               'expansion and cylinder return volume; 80–90 %% full is a common upper limit.'
                       % (_q(air_h, 'in', 1), v['fill'])))
    if oil_depth < 4.0:
        checks.append(('warn', 'Shallow oil (%s deep). Make sure the pump suction stays submerged with margin, '
                               'including when cylinders are extended.' % _q(oil_depth, 'in', 1)))
    if not v['top']:
        checks.append(('warn', 'Open-top reservoir: oil is exposed to dirt and moisture. Most hydraulic reservoirs '
                               'need a sealed lid with a filtered breather.'))
    tank_fam = MATERIAL_DATA[v['tank_mat']]['family']
    if t < 0.075 and inner_h > 24:
        checks.append(('warn', 'Thin walls (%s) on a tall tank (%s inside). Wide flat panels this thin can bulge '
                               'and drum; consider stiffeners, baffles or a heavier wall.'
                       % (_q(t, 'in', 3), _q(inner_h, 'in', 0))))
    if tank_fam == 'aluminum' and t < 0.09:
        checks.append(('warn', 'Thin aluminum (%s) is hard to weld without burning through; 1/8" or heavier is '
                               'more practical for a welded tank.' % _q(t, 'in', 3)))

    # ---- pan / rail / containment checks
    fits = True
    if v['rail_on']:
        inner_pl, inner_pw = pl - 2 * tr, pw - 2 * tr
        rail_wt = (pl * pw - inner_pl * inner_pw) * v['rail_h'] * rho_p
        pan_gal = inner_pl * inner_pw * v['rail_h'] / GAL_IN3
        fits = (L <= inner_pl and W <= inner_pw) or (W <= inner_pl and L <= inner_pw)
        footprint = min(L * W, inner_pl * inner_pw)
        net_gal = max(0.0, (inner_pl * inner_pw - footprint) * v['rail_h'] / GAL_IN3)
        out.update({
            'Rail thickness (in)': tr,
            'Drip rail weight (lb)': rail_wt,
            'Pan assembly weight (lb)': pan_wt + rail_wt,
            'Drip pan capacity, empty (gal)': pan_gal,
            'Pan capacity with tank in place (gal)': net_gal,
        })
        if oil_gal > 0:
            out['Containment of tank oil (%)'] = net_gal / oil_gal * 100
        out['Total weight, tank full + pan (lb)'] = tank_full + pan_wt + rail_wt
        if not fits:
            checks.append(('bad', 'The reservoir footprint (%s × %s) does not fit inside the drip rail (%s × %s '
                                  'inside).' % (_q(L, 'in', 1), _q(W, 'in', 1), _q(inner_pl, 'in', 1),
                                                _q(inner_pw, 'in', 1))))
        elif net_gal < oil_gal:
            checks.append(('bad', 'The drip pan cannot contain the tank: it holds %s with the reservoir in place, but '
                                  'the reservoir holds %s of oil. Raise the rail or enlarge the pan.'
                           % (_q(net_gal, 'gal'), _q(oil_gal, 'gal'))))
        elif net_gal < 1.1 * oil_gal:
            checks.append(('warn', 'The pan holds the oil (%s vs %s) but less than 110 %%, a common secondary-'
                                   'containment rule. Check what applies to your site.'
                           % (_q(net_gal, 'gal'), _q(oil_gal, 'gal'))))
        else:
            checks.append(('good', 'The drip pan holds %.0f %% of the reservoir oil with the tank in place.'
                           % (net_gal / oil_gal * 100 if oil_gal else 0)))
        if net_gal < gross_gal and net_gal >= oil_gal:
            checks.append(('warn', 'If the reservoir were overfilled to the brim (%s) the pan could not hold it all.'
                           % _q(gross_gal, 'gal')))
        clear = min((inner_pl - L) / 2, (inner_pw - W) / 2) if fits else 0
        if fits and clear < 2:
            checks.append(('warn', 'Tight fit: only %s of clearance between the tank and the rail on each side. '
                                   'Leave room for drips, cleaning and welds.' % _q(max(clear, 0), 'in', 1)))
        if v['rail_h'] < 2:
            checks.append(('warn', 'A rail under %s tall is easy to overtop when the pan is moved or the floor is '
                                   'not level.' % _q(2, 'in', 0)))
        notes.append('Capacity with tank in place subtracts the reservoir footprint from the pan interior. Many '
                     'secondary-containment rules of thumb use 110 % of the largest container; confirm what applies to you.')
    else:
        out['Total weight, tank full + pan (lb)'] = tank_full + pan_wt
        fits = (L <= pl and W <= pw) or (W <= pl and L <= pw)
        checks.append(('bad', 'No drip rail: the pan is a flat plate and holds no liquid, so any leak or spill runs '
                              'onto the floor. Tick “Drip rail” to size containment.'))
        if not fits:
            checks.append(('bad', 'The reservoir footprint is larger than the drip pan.'))
    fams = {tank_fam, MATERIAL_DATA[v['pan_mat']]['family']}
    if 'aluminum' in fams and len(fams) > 1:
        checks.append(('warn', 'Aluminum touching steel or stainless can corrode galvanically where moisture '
                               'collects. Isolate the two metals (pads, coating or gasket).'))
    total = out['Total weight, tank full + pan (lb)']
    if total > 2000:
        checks.append(('warn', 'Heavy assembly (%s full). Check floor loading, lifting lugs and forklift capacity.'
                       % _q(total, 'lb', 0)))
    out['_checks'] = checks
    out['_notes'] = notes
    return out
