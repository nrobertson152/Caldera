"""Reservoir + drip pan sizing. Pure Python, US customary units (inches, gallons, pounds).

Conventions
- Reservoir L x W x H are OUTSIDE dimensions (how sheet-metal tanks are specified).
- Sheet thickness comes from the gauge table for the chosen material. Carbon and stainless gauges are different
  standards (Manufacturers' Standard Gauge vs. the common stainless chart), so the same gauge number is a
  different thickness.
- The drip pan is a flat sheet. The optional drip rail is a wall standing on the pan around its edge, made from the
  pan's material. Containment capacity therefore comes from the rail height.
"""
import math

GAUGE_LABELS = ['7 ga', '8 ga', '10 ga', '11 ga', '12 ga', '13 ga', '14 ga', '16 ga', '18 ga', '20 ga', '22 ga',
                '24 ga', '26 ga', '28 ga']
MATERIALS = ['Carbon steel', 'Stainless steel']
# gauge -> thickness (in)
THICKNESS = {
    'Carbon steel': {7: 0.1793, 8: 0.1644, 10: 0.1345, 11: 0.1196, 12: 0.1046, 13: 0.0897, 14: 0.0747, 16: 0.0598,
                     18: 0.0478, 20: 0.0359, 22: 0.0299, 24: 0.0239, 26: 0.0179, 28: 0.0149},
    'Stainless steel': {7: 0.1875, 8: 0.1719, 10: 0.1406, 11: 0.1250, 12: 0.1094, 13: 0.0938, 14: 0.0781, 16: 0.0625,
                        18: 0.0500, 20: 0.0375, 22: 0.0312, 24: 0.0250, 26: 0.0187, 28: 0.0156},
}
DENSITY = {'Carbon steel': 0.284, 'Stainless steel': 0.289}      # lb/in^3
OIL_LB_PER_GAL = 7.3                                              # ~0.875 specific gravity hydraulic oil
GAL_IN3 = 231.0

# input order == registry field order
KEYS = ['tank_l', 'tank_w', 'tank_h', 'tank_ga', 'tank_mat', 'fill', 'top', 'pan_l', 'pan_w', 'pan_ga', 'pan_mat',
        'rail_on', 'rail_ga', 'rail_h']


def thickness(material, gauge):
    """Sheet thickness in inches. `gauge` may be 14, '14' or '14 ga'."""
    g = int(str(gauge).split()[0])
    try:
        return THICKNESS[material][g]
    except KeyError:
        raise ValueError('Unknown gauge %s for %s.' % (gauge, material))


def params(a):
    """Turn the raw input list (numbers and strings) into one validated dict. Raises ValueError with a clear message."""
    if len(a) != len(KEYS):
        raise ValueError('Reservoir / Drip Pan needs %d inputs.' % len(KEYS))
    v = dict(zip(KEYS, a))
    for k in ('tank_l', 'tank_w', 'tank_h', 'fill', 'pan_l', 'pan_w', 'rail_h'):
        v[k] = float(v[k])
    for k in ('tank_mat', 'pan_mat'):
        if v[k] not in MATERIALS:
            raise ValueError('Choose carbon or stainless steel.')
    v['top'] = str(v['top']) == 'Yes'
    v['rail_on'] = str(v['rail_on']) == 'Yes'
    v['t_tank'] = thickness(v['tank_mat'], v['tank_ga'])
    v['t_pan'] = thickness(v['pan_mat'], v['pan_ga'])
    v['t_rail'] = thickness(v['pan_mat'], v['rail_ga'])          # the rail takes the pan's material
    if min(v['tank_l'], v['tank_w'], v['tank_h'], v['pan_l'], v['pan_w']) <= 0:
        raise ValueError('Lengths, widths and heights must be greater than zero.')
    if not 0 < v['fill'] <= 100:
        raise ValueError('Fill level must be between 0 and 100 %.')
    if 2 * v['t_tank'] >= min(v['tank_l'], v['tank_w'], v['tank_h']):
        raise ValueError('The reservoir is too small for this steel thickness.')
    if v['rail_on']:
        if v['rail_h'] <= 0:
            raise ValueError('Drip rail height must be greater than zero.')
        if 2 * v['t_rail'] >= min(v['pan_l'], v['pan_w']):
            raise ValueError('The drip pan is too small for this rail thickness.')
    return v


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
    tank_wt = (L * W * H - inner) * rho_t
    tank_full = tank_wt + oil_gal * OIL_LB_PER_GAL

    # ---- drip pan and rail
    pl, pw, tp, tr = v['pan_l'], v['pan_w'], v['t_pan'], v['t_rail']
    pan_wt = pl * pw * tp * rho_p
    out = {
        'Tank internal volume (gal)': gross_gal,
        'Oil capacity at fill level (gal)': oil_gal,
        'Air gap volume (gal)': air_gal,
        'Air gap height (in)': inner_h - oil_depth,
        'Oil depth (in)': oil_depth,
        'Tank steel thickness (in)': t,
        'Tank empty weight (lb)': tank_wt,
        'Tank weight full of oil (lb)': tank_full,
        'Drip pan weight (lb)': pan_wt,
    }
    notes = ['Reservoir dimensions are outside dimensions. Oil is taken as %.1f lb/gal. Tank is assumed to sit flat on '
             'the pan with no feet, and corner radii, bends and welds are ignored.' % OIL_LB_PER_GAL]
    fits = True
    if v['rail_on']:
        inner_pl, inner_pw = pl - 2 * tr, pw - 2 * tr
        rail_wt = (pl * pw - inner_pl * inner_pw) * v['rail_h'] * rho_p
        pan_gal = inner_pl * inner_pw * v['rail_h'] / GAL_IN3
        fits = (L <= inner_pl and W <= inner_pw) or (W <= inner_pl and L <= inner_pw)
        footprint = min(L * W, inner_pl * inner_pw)
        net_gal = max(0.0, (inner_pl * inner_pw - footprint) * v['rail_h'] / GAL_IN3)
        out.update({
            'Drip rail weight (lb)': rail_wt,
            'Pan assembly weight (lb)': pan_wt + rail_wt,
            'Drip pan capacity, empty (gal)': pan_gal,
            'Pan capacity with tank in place (gal)': net_gal,
        })
        if oil_gal > 0:
            out['Containment of tank oil (%)'] = net_gal / oil_gal * 100
        out['Tank fits in pan'] = fits
        if oil_gal > 0:
            out['Pan holds 110% of oil'] = net_gal >= 1.1 * oil_gal
        out['Total weight, tank full + pan (lb)'] = tank_full + pan_wt + rail_wt
        notes.append('Capacity with tank in place subtracts the reservoir footprint from the pan interior. Many '
                     'secondary-containment rules of thumb use 110 % of the largest container; confirm what applies to you.')
    else:
        out['Total weight, tank full + pan (lb)'] = tank_full + pan_wt
        notes.append('Drip rail is off, so the pan is a flat plate and holds no liquid. Tick the rail option to size containment.')
        fits = (L <= pl and W <= pw) or (W <= pl and L <= pw)
        out['Tank fits in pan'] = fits
    out['_notes'] = notes
    return out
