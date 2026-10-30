"""Additional engineering estimators for the Qt migration. Values are preliminary."""
import math

from . import conduit, units
from .toolmeta import Choice, Text, Toggle

# Recommended hydraulic line velocities (ft/s), after the Parker hose-sizing nomograph. (min, max)
LINE_TYPES = {
    'Pressure line (up to 3,000 PSI)': (7.0, 20.0),
    'Pressure line (above 3,000 PSI)': (15.0, 25.0),
    'Return line': (10.0, 15.0),
    'Pump suction (inlet) line': (2.0, 4.0),
}
LINE_ADVICE = {
    'Pump suction (inlet) line': 'Keep suction velocity low so the pump inlet does not starve and cavitate. Use a short, '
                                 'straight, large suction line and avoid suction strainers that add restriction.',
    'Return line': 'Faster return flow is tolerated, but high velocity raises back-pressure and heat and can aerate the '
                   'tank. Terminate returns below the oil level, away from the suction.',
    'Pressure line (up to 3,000 PSI)': 'Higher velocity means smaller, cheaper hose but more pressure drop and heat.',
    'Pressure line (above 3,000 PSI)': 'Higher velocity means smaller, cheaper hose but more pressure drop and heat.',
}
# hose dash size -> nominal inside diameter (in)
HOSE_DASH = [(-4, 0.25, '1/4"'), (-5, 0.3125, '5/16"'), (-6, 0.375, '3/8"'), (-8, 0.5, '1/2"'), (-10, 0.625, '5/8"'),
             (-12, 0.75, '3/4"'), (-16, 1.0, '1"'), (-20, 1.25, '1-1/4"'), (-24, 1.5, '1-1/2"'), (-32, 2.0, '2"'),
             (-40, 2.5, '2-1/2"'), (-48, 3.0, '3"')]


def _vel(gpm, d):
    return 0.3208 * gpm / (math.pi * d * d / 4)            # ft/s


def _min_id(gpm, v):
    return math.sqrt(4 * 0.3208 * gpm / v / math.pi)


def _hose_for(d):
    for dash, nominal, text in HOSE_DASH:
        if nominal >= d - 1e-9:
            return '%d (%s)' % (dash, text)
    return 'larger than -48 (3"): use pipe or parallel lines'


def _range_text(lo, hi):
    if units.metric():
        return '%.1f–%.1f m/s' % (lo * 0.3048, hi * 0.3048)
    return '%g–%g ft/s' % (lo, hi)


def line_velocity(q, d, kind):
    if q < 0 or d <= 0:
        raise ValueError('Flow must be zero or more and the inside diameter greater than zero.')
    kind = kind if kind in LINE_TYPES else 'Pressure line (up to 3,000 PSI)'
    v = _vel(q, d)
    lo, hi = LINE_TYPES[kind]
    need = _min_id(q, hi) if q > 0 else 0.0
    out = {'Velocity (ft/s)': v, 'Velocity (m/s)': v * 0.3048,
           'Recommended for this line': _range_text(lo, hi),
           'Smallest inside diameter at max velocity (in)': need,
           'Smallest hose': _hose_for(need) if q > 0 else '—',
           'Max flow in this ID at max velocity (GPM)': hi * math.pi * d * d / 4 / 0.3208}
    checks = []
    what = kind[0].lower() + kind[1:]
    if v > hi * 1.25:
        checks.append(('bad', 'Too fast for a %s: %s against a recommended maximum of %s. Use at least a %s line.'
                       % (what, units.q(v, 'ft/s', 1), units.q(hi, 'ft/s', 1), _hose_for(need))))
    elif v > hi:
        checks.append(('warn', 'Slightly above the recommended maximum for a %s (%s vs %s). Expect extra pressure '
                               'drop and heat; consider %s.' % (what, units.q(v, 'ft/s', 1), units.q(hi, 'ft/s', 1),
                                                                 _hose_for(need))))
    elif v < lo and q > 0:
        checks.append(('good', 'Below the usual range for a %s (%s): fine for flow, but the line is larger and costlier '
                               'than it needs to be.' % (what, units.q(v, 'ft/s', 1))))
    else:
        checks.append(('good', 'Within the recommended %s for a %s.' % (_range_text(lo, hi), what)))
    rows = []
    for name, (a, b) in LINE_TYPES.items():
        rows.append([name, _range_text(a, b), round(b * math.pi * d * d / 4 / 0.3208, 2),
                     round(_min_id(q, b), 3) if q > 0 else 0.0, _hose_for(_min_id(q, b)) if q > 0 else '—'])
    out['_table'] = (['Line type', 'Recommended velocity', 'Max flow in this ID (GPM)', 'Min ID for this flow (in)',
                      'Smallest hose'], rows, [None, None, 'GPM', 'in', None])
    out['_checks'] = checks
    out['_notes'] = [LINE_ADVICE[kind],
                     'Recommended ranges follow the Parker hose-sizing nomograph (petroleum oil up to 315 SUS at 100 °F). '
                     'Hose dash sizes are nominal inside diameters; tube and pipe IDs depend on wall thickness, so use '
                     'the actual ID.']
    return out

def calculate(name,a):
    x=[float(v) if not isinstance(v,str) or v.replace('.','',1).replace('-','',1).isdigit() else v for v in a]
    if name=='Conduit Fill':
        kind,size,rows,nipple=a
        size=('%g' % size) if isinstance(size,float) else str(size)
        return conduit.conduit_fill(kind,size,rows,nipple)
    if name=='Hydraulic Cylinder':
        b,r,s,p,q=x;assert b>r>=0 and s>=0 and p>=0 and q>0
        cap=math.pi*b*b/4;ann=math.pi*(b*b-r*r)/4
        return {'Extend force (lbf)':cap*p,'Retract force (lbf)':ann*p,'Extend time (s)':cap*s/231/q*60,'Retract time (s)':ann*s/231/q*60,'Cap area (in²)':cap,'Annulus area (in²)':ann}
    if name=='Hydraulic Motor':
        d,p,r,ve,me=x;assert d>0 and p>=0 and r>=0 and 0<ve<=100 and 0<me<=100
        return {'Torque (lb-ft)':p*(d/16.387064)/(2*math.pi)*me/100/12,'Flow (GPM)':d*r/3785.411784/(ve/100),'Output HP':p*d*r/3785.411784/(1714)*me/100}
    if name=='Heat Load & Cooler Sizing':
        pressure,flow,loss,margin=x;assert pressure>=0 and flow>=0 and 0<=loss<=100 and margin>=0
        hp=pressure*flow/1714*loss/100;return {'Heat load (HP)':hp,'Heat load (kW)':hp*0.7457,'Cooler target (kW)':hp*0.7457*(1+margin/100)}
    if name=='Hydraulic Accumulator':
        p1,p2,p0,v2,n=x;assert 0<p0<p1<p2 and v2>0 and n>0
        # Gas volume required for requested discharge between p2 and p1
        ratio=(p0/p1)**(1/n)-(p0/p2)**(1/n)
        return {'Required gas volume (gal)':v2/ratio,'Precharge pressure (PSI)':p0,'Gas exponent':n}
    if name=='Pneumatic Cylinder':
        b,r,p,stroke,flow=x;assert b>r>=0 and p>=0 and stroke>=0 and flow>0
        cap=math.pi*b*b/4;ann=math.pi*(b*b-r*r)/4
        return {'Extend force (lbf)':cap*p,'Retract force (lbf)':ann*p,'Extend time (s)':cap*stroke/1728/flow*60,'Retract time (s)':ann*stroke/1728/flow*60}
    if name=='Compressed Air Horsepower':
        scfm,p1,p2,eff=x;assert scfm>=0 and p1>0 and p2>=p1 and 0<eff<=100
        kw=(scfm*0.00047194745)*p1*6894.757293*math.log(p2/p1)/(eff/100)/1000
        return {'Idealized isothermal input (kW)':kw,'Input (HP)':kw/0.745699872}
    if name=='Line Velocity':
        q,d=x[0],x[1]
        return line_velocity(q,d,x[2] if len(x)>2 else 'Pressure line (up to 3,000 PSI)')
    if name=='Pressure Drop Calculator':
        q,d,L,sg,nu,rough=x;assert q>0 and d>0 and L>=0 and sg>0 and nu>0 and rough>=0
        velocity=q*6.30901964e-5/(math.pi*(d*.0254)**2/4);Re=velocity*d*.0254/(nu*1e-6)
        f=64/Re if Re<2300 else .25/(math.log10((rough*.001)/(3.7*d*.0254)+5.74/Re**.9)**2)
        pa=f*(L*.3048/(d*.0254))*(sg*1000)*velocity**2/2
        return {'Velocity (m/s)':velocity,'Reynolds number':Re,'Darcy friction factor':f,'Pressure drop (PSI)':pa/6894.757293}
    if name=='Orifice Flow Estimate':
        d,dp,sg,cd=x;assert d>0 and dp>=0 and sg>0 and 0<cd<=1
        return {'Flow (GPM)':29.84*cd*d*d*math.sqrt(dp/sg),'Area (in²)':math.pi*d*d/4}
    if name=='Labor Savings':
        old,new,cycles,rate=x;assert old>=0 and new>=0 and cycles>=0 and rate>=0
        hours=(old-new)*cycles/60;return {'Hours saved':hours,'Labor savings ($)':hours*rate}
    raise KeyError(name)

EXTRA={
'Conduit Fill':[('Conduit type',Choice(conduit.CONDUIT_TYPES,'EMT')),('Trade size',Choice([conduit.RECOMMEND]+conduit.ALL_TRADE_SIZES,conduit.RECOMMEND)),
                ('Conductors',Text(conduit.DEFAULT_ROWS)),('Nipple, 24 in or shorter (60 % fill)',Toggle(False))],
'Hydraulic Cylinder':[('Bore (in)','2.5'),('Rod (in)','1.25'),('Stroke (in)','12'),('Pressure (PSI)','2500'),('Flow (GPM)','10')],
'Hydraulic Motor':[('Displacement (cc/rev)','250'),('Pressure (PSI)','2500'),('Speed (RPM)','1800'),('Volumetric efficiency (%)','90'),('Mechanical efficiency (%)','90')],
'Heat Load & Cooler Sizing':[('System pressure (PSI)','2500'),('Flow (GPM)','20'),('Estimated loss (%)','15'),('Cooler margin (%)','20')],
'Hydraulic Accumulator':[('Minimum pressure (PSIA)','1500'),('Maximum pressure (PSIA)','2500'),('Precharge (PSIA)','1200'),('Usable discharge (gal)','1'),('Polytropic exponent','1.4')],
'Pneumatic Cylinder':[('Bore (in)','3'),('Rod (in)','1'),('Pressure (PSIG)','90'),('Stroke (in)','12'),('Flow (CFM)','5')],
'Compressed Air Horsepower':[('Flow (SCFM)','100'),('Inlet absolute pressure (PSIA)','14.7'),('Outlet absolute pressure (PSIA)','114.7'),('Efficiency (%)','75')],
'Line Velocity':[('Flow (GPM)','20'),('Inside diameter (in)','1'),('Line type',Choice(list(LINE_TYPES),'Pressure line (up to 3,000 PSI)'))],
'Pressure Drop Calculator':[('Flow (GPM)','20'),('Inside diameter (in)','1'),('Length (ft)','50'),('Specific gravity','0.87'),('Viscosity (cSt)','32'),('Roughness (mm)','0.045')],
'Orifice Flow Estimate':[('Diameter (in)','0.125'),('Pressure differential (PSI)','100'),('Specific gravity','0.87'),('Discharge coefficient','0.62')],
'Labor Savings':[('Old cycle time (min)','20'),('New cycle time (min)','12'),('Cycles','100'),('Hourly rate ($)','35')],
}
