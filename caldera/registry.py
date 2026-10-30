"""Calculator registry: every calculator page, its input fields and the function that evaluates it.

Each entry is  name -> ([(label, default | [choices]), ...], fn(list_of_values) -> dict | str)."""
from . import calculations as c, legacy_calculations as l
from .extended import EXTRA, calculate as extra_calculate
from . import tank
from .toolmeta import Choice, Toggle

_GA = lambda d: Choice(tank.THICKNESS_LABELS, d)
_MAT = lambda: Choice(tank.MATERIALS, 'Carbon steel (A36)')

BASE={
 'Unit Converter':([('Value','1'),('Conversion',list(c.CONVERSIONS))],lambda a:{'Converted value':c.convert(a[0],a[1])}),
 'Motor & Electrical Power':([('Motor output (HP)','125'),('Voltage (V)','460'),('Efficiency (%)','93'),('Power factor','0.88'),('Phase',['3-phase','1-phase'])],lambda a:c.motor(*a)),
 'Hydraulic Pump & Motor':([('Displacement (cc/rev)','250'),('Speed (RPM)','1800'),('Pressure (PSI)','2500'),('Volumetric efficiency (%)','90'),('Mechanical efficiency (%)','90')],lambda a:c.pump(*a)),
 'Hydraulic Power & Efficiency':([('Pressure (PSI)','2500'),('Flow (GPM)','30'),('Efficiency (0–1)','0.9')],lambda a:l.hydraulic_power(*a)),
 'Cylinder Buckling':([('Diameter (in)','1'),('Unsupported length (in)','30'),('Modulus (PSI)','30000000'),('End factor','1'),('Safety factor','2'),('Applied load (lbf)','2000')],lambda a:l.cylinder_buckling(*a)),
 'Hydraulic Cylinder Cycle Time':([('Bore (in)','4'),('Rod (in)','2'),('Stroke (in)','24'),('Extend flow (GPM)','10'),('Retract flow (GPM)','10')],lambda a:l.cylinder_cycle(*a)),
 'Pneumatic Air Consumption':([('Bore (in)','3'),('Rod (in)','1'),('Stroke (in)','12'),('Pressure (PSIG)','90'),('Cycles/min','10'),('Atmospheric pressure (PSIA)','14.7')],lambda a:l.air_consumption(*a)),
 'Torque, RPM & Power':([('Torque (lb-ft)','100'),('RPM','1800')],lambda a:l.torque_power(*a)),
 'Reservoir / Drip Pan':([('Tank length (in)','36'),('Tank width (in)','24'),('Tank height (in)','24'),('Tank wall thickness',_GA('11 ga')),
   ('Tank material',_MAT()),('Fill level (%)','80'),('Closed top',Toggle(True)),
   ('Pan length (in)','72'),('Pan width (in)','48'),('Pan thickness',_GA('3/16"')),('Pan material',_MAT()),
   ('Drip rail',Toggle(True)),('Rail thickness',_GA('11 ga')),('Rail height (in)','8')],lambda a:tank.reservoir_drip(a)),
 'Wire Gauge & Voltage Drop':([('Load current (A)','15'),('One-way length (ft)','50'),('Supply voltage (V)','24'),('Max drop (%)','3'),('Conductor',['Copper','Aluminum']),('Temperature (°C)',['20','60','75','90'])],lambda a:c.wire(*a)),
}
TOOLS={**BASE,**{k:(v,lambda a,k=k:extra_calculate(k,a)) for k,v in EXTRA.items()}}

# Non-calculator pages that appear in navigation.
UTILITY_PAGES = ['Seal Compatibility', 'Reference Tables', 'Electrical Load Summary', 'Wire List / CSV Generator',
                 'Test Report Generator', 'Compare Calculations', 'Methodology']
TOOL_PAGES = [*TOOLS, *UTILITY_PAGES]
