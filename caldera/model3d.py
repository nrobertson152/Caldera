"""Tiny dependency-free 3D for Caldera's reservoir / drip pan preview.

A scene is a list of parts (boxes and cylinders, in inches: x = length, y = width, z = up). `project()` rotates the
scene, back-face culls, depth-sorts and returns flat 2D polygons ready to paint - no OpenGL, no numpy, no Qt.
"""
import math

from . import tank, units

# real, common objects used as a size reference (inches)
REFERENCES = {
    'Soda can (12 oz)': dict(kind='cyl', r0=1.30, r1=1.30, h=4.83, color='#d9453d', label='12 oz can, 2.6 in dia × 4.83 in', metric='355 mL can, 66 mm dia × 123 mm'),
    '5-gallon bucket': dict(kind='cyl', r0=5.25, r1=6.0, h=14.5, color='#e8832f', label='5-gal bucket, 12 in dia × 14.5 in', metric='19 L bucket, 305 mm dia × 368 mm'),
    'Pallet (48 × 40 in)': dict(kind='box', size=(48.0, 40.0, 5.5), color='#b98a55', label='GMA pallet, 48 × 40 × 5.5 in', metric='GMA pallet, 1219 × 1016 × 140 mm'),
    'None': None,
}
VIEWS = ['Reservoir', 'Drip pan', 'Drip rail']
STEEL = {m: d['color'] for m, d in tank.MATERIAL_DATA.items()}


def _mix(a, b, t):
    ca = [int(a[i:i + 2], 16) for i in (1, 3, 5)]
    cb = [int(b[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(round(x + (y - x) * t) for x, y in zip(ca, cb))


def box(lo, hi, color, alpha=1.0, layer=1):
    return dict(kind='box', lo=tuple(lo), hi=tuple(hi), color=color, alpha=alpha, layer=layer)


def cyl(cx, cy, z0, r0, r1, h, color, alpha=1.0, layer=1, segs=28):
    return dict(kind='cyl', c=(cx, cy, z0), r0=r0, r1=r1, h=h, color=color, alpha=alpha, layer=layer, segs=segs)


def _vis(t, big):
    """Visual wall thickness: true thickness, but never thinner than a legible sliver."""
    return max(t, 0.012 * big)


def _ring(L, W, tw, h, z0, color, layer=1):
    return [box((0, 0, z0), (L, tw, z0 + h), color, 1, layer), box((0, W - tw, z0), (L, W, z0 + h), color, 1, layer),
            box((0, tw, z0), (tw, W - tw, z0 + h), color, 1, layer), box((L - tw, tw, z0), (L, W - tw, z0 + h), color, 1, layer)]


def build_scene(view, v, reference='Soda can (12 oz)'):
    """`v` is the validated dict from tank.params(). Returns (parts, caption). parts may be empty (with a caption)."""
    parts, ref_label = [], ''
    if view == 'Reservoir':
        L, W, H, t = v['tank_l'], v['tank_w'], v['tank_h'], v['t_tank']
        col = STEEL[v['tank_mat']]
        big = max(L, W, H)
        vt = min(_vis(t, big), min(L, W, H) / 4)
        if v['top']:
            parts.append(box((0, 0, 0), (L, W, H), col))
        else:                                                    # open-top: floor + four walls so you can see inside
            parts.append(box((0, 0, 0), (L, W, vt), col))
            parts += _ring(L, W, vt, H - vt, vt, col)
        extent = (L, W, H)
        caption = 'Reservoir  %s × %s × %s %s  ·  %s' % (_n(L), _n(W), _n(H), _u(), v['tank_mat'])
    elif view == 'Drip pan':
        L, W = v['pan_l'], v['pan_w']
        big = max(L, W)
        col = STEEL[v['pan_mat']]
        vp = _vis(v['t_pan'], big)
        parts.append(box((0, 0, 0), (L, W, vp), col, 1, 0))      # layer 0: always drawn first (everything sits on it)
        if v['rail_on']:
            vr = min(_vis(v['t_rail'], big), min(L, W) / 4)
            parts += _ring(L, W, vr, v['rail_h'], vp, _mix(col, '#ffb36b', 0.35))
        # translucent ghost of the reservoir so you can judge fit
        tl, tw_, th = v['tank_l'], v['tank_w'], v['tank_h']
        ox, oy = (L - tl) / 2, (W - tw_) / 2
        parts.append(box((ox, oy, vp), (ox + tl, oy + tw_, vp + th), '#4aa3ff', 0.16))
        extent = (L, W, max(vp + (v['rail_h'] if v['rail_on'] else 0), vp + th))
        caption = 'Drip pan  %s × %s %s%s  ·  %s  (blue = reservoir footprint)' % (
            _n(L), _n(W), _u(), ('  ·  %s %s rail' % (_n(v['rail_h']), _u())) if v['rail_on'] else '  ·  no rail',
            v['pan_mat'])
    else:                                                        # Drip rail
        if not v['rail_on']:
            return [], 'Drip rail is switched off. Tick “Drip rail” to preview it.'
        L, W = v['pan_l'], v['pan_w']
        big = max(L, W)
        col = _mix(STEEL[v['pan_mat']], '#ffb36b', 0.35)
        vr = min(_vis(v['t_rail'], big), min(L, W) / 4)
        parts += _ring(L, W, vr, v['rail_h'], 0, col)
        extent = (L, W, v['rail_h'])
        caption = 'Drip rail  %s × %s %s  ·  %s %s tall  ·  %s' % (_n(L), _n(W), _u(), _n(v['rail_h']), _u(), v['pan_mat'])

    ref = REFERENCES.get(reference)
    if ref:
        gap = max(4.0, 0.06 * extent[0])
        if ref['kind'] == 'cyl':
            r = max(ref['r0'], ref['r1'])
            parts.append(cyl(extent[0] + gap + r, r + 2, 0, ref['r0'], ref['r1'], ref['h'], ref['color']))
        else:
            sx, sy, sz = ref['size']
            parts.append(box((extent[0] + gap, 0, 0), (extent[0] + gap + sx, sy, sz), ref['color']))
        ref_label = ref['metric'] if units.metric() else ref['label']
    if ref_label:
        caption += '   |   Reference: ' + ref_label
    return parts, caption


def _n(x):
    if units.metric():
        x *= 25.4
        return ('%.0f' % x) if x >= 100 else ('%.1f' % x).rstrip('0').rstrip('.')
    return ('%.2f' % x).rstrip('0').rstrip('.')


def _u():
    return 'mm' if units.metric() else 'in'


# --------------------------------------------------------------------------- geometry -> polygons
def _box_faces(p):
    (x0, y0, z0), (x1, y1, z1) = p['lo'], p['hi']
    P = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0), (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)]
    quads = [((0, 3, 2, 1), (0, 0, -1)), ((4, 5, 6, 7), (0, 0, 1)), ((0, 1, 5, 4), (0, -1, 0)),
             ((2, 3, 7, 6), (0, 1, 0)), ((1, 2, 6, 5), (1, 0, 0)), ((3, 0, 4, 7), (-1, 0, 0))]
    return [([P[i] for i in idx], n) for idx, n in quads]


def _cyl_faces(p):
    cx, cy, z0 = p['c']
    n, r0, r1, z1 = p['segs'], p['r0'], p['r1'], p['c'][2] + p['h']
    ring0 = [(cx + r0 * math.cos(2 * math.pi * i / n), cy + r0 * math.sin(2 * math.pi * i / n), z0) for i in range(n)]
    ring1 = [(cx + r1 * math.cos(2 * math.pi * i / n), cy + r1 * math.sin(2 * math.pi * i / n), z1) for i in range(n)]
    faces = [(list(reversed(ring0)), (0, 0, -1)), (ring1, (0, 0, 1))]
    for i in range(n):
        j = (i + 1) % n
        mid = 2 * math.pi * (i + 0.5) / n
        faces.append(([ring0[i], ring0[j], ring1[j], ring1[i]], (math.cos(mid), math.sin(mid), 0)))
    return faces


def part_faces(p):
    return _box_faces(p) if p['kind'] == 'box' else _cyl_faces(p)


def scene_bounds(parts):
    xs, ys, zs = [], [], []
    for p in parts:
        for pts, _n_ in part_faces(p):
            for x, y, z in pts:
                xs.append(x), ys.append(y), zs.append(z)
    if not xs:
        return (0, 0, 0), (1, 1, 1)
    return (min(xs), min(ys), min(zs)), (max(xs), max(ys), max(zs))


def _rot(pt, yaw, pitch, center):
    x, y, z = pt[0] - center[0], pt[1] - center[1], pt[2] - center[2]
    cy_, sy_ = math.cos(yaw), math.sin(yaw)
    x1, y1 = x * cy_ - y * sy_, x * sy_ + y * cy_
    cp, sp = math.cos(pitch), math.sin(pitch)
    return x1, y1 * cp - z * sp, y1 * sp + z * cp          # (screen x, depth, screen up)


_LIGHT = (-0.45, -0.65, 0.62)
_LL = math.sqrt(sum(c * c for c in _LIGHT))


def project(parts, yaw, pitch):
    """Rotate + shade + depth-sort. Returns dict(polys=[(pts2d, '#rrggbb', alpha)], grid=[(p, q)], bounds=(x0,y0,x1,y1)).
    2D coordinates are in inches with y pointing DOWN on screen, ready to scale. Back faces of opaque parts are culled."""
    lo, hi = scene_bounds(parts)
    center = ((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, (lo[2] + hi[2]) / 2)
    order = []
    for p in parts:
        faces = []
        for pts, n in part_faces(p):
            rp = [_rot(q, yaw, pitch, center) for q in pts]
            rn = _rot((n[0] + center[0], n[1] + center[1], n[2] + center[2]), yaw, pitch, center)
            if p['alpha'] >= 0.999 and rn[1] >= -1e-9:       # facing away from the camera
                continue
            depth = sum(q[1] for q in rp) / len(rp)
            lit = max(0.0, (rn[0] * _LIGHT[0] + rn[1] * _LIGHT[1] + rn[2] * _LIGHT[2]) / _LL)
            shade = 0.52 + 0.48 * lit
            faces.append((depth, [(q[0], -q[2]) for q in rp], shade))
        if not faces:
            continue
        faces.sort(key=lambda f: -f[0])                       # far -> near inside the part
        pdepth = sum(f[0] for f in faces) / len(faces)
        order.append((p['layer'], -pdepth, p, faces))
    order.sort(key=lambda o: (o[0], o[1]))                    # layer 0 first, then far -> near parts
    polys, xs, ys = [], [], []
    for _layer, _d, p, faces in order:
        for _depth, pts2, shade in faces:
            polys.append((pts2, _shade(p['color'], shade), p['alpha']))
            for x, y in pts2:
                xs.append(x), ys.append(y)
    grid = _grid(lo, hi, yaw, pitch, center)       # not part of the fit: the grid may run off-screen
    bounds = (min(xs), min(ys), max(xs), max(ys)) if xs else (0, 0, 1, 1)
    return dict(polys=polys, grid=grid, bounds=bounds)


def _shade(hex_color, k):
    c = [int(hex_color[i:i + 2], 16) for i in (1, 3, 5)]
    return '#%02x%02x%02x' % tuple(max(0, min(255, int(v * k))) for v in c)


def _grid(lo, hi, yaw, pitch, center):
    """A light 1-ft (or coarser) floor grid so scale is readable."""
    span = max(hi[0] - lo[0], hi[1] - lo[1], 1.0)
    step = 12.0 if span <= 96 else (24.0 if span <= 192 else 48.0)
    x0, x1 = math.floor((lo[0] - step) / step) * step, math.ceil((hi[0] + step) / step) * step
    y0, y1 = math.floor((lo[1] - step) / step) * step, math.ceil((hi[1] + step) / step) * step
    z = lo[2]
    lines = []
    x = x0
    while x <= x1 + 1e-6:
        lines.append(((x, y0, z), (x, y1, z)))
        x += step
    y = y0
    while y <= y1 + 1e-6:
        lines.append(((x0, y, z), (x1, y, z)))
        y += step
    out = []
    for a, b in lines:
        ra, rb = _rot(a, yaw, pitch, center), _rot(b, yaw, pitch, center)
        out.append(((ra[0], -ra[2]), (rb[0], -rb[2])))
    return out
