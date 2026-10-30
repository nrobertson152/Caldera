"""Reference tables shown on the Reference Tables page. Qt-free.

Each section is a list of tables: (title, headers, rows, note). Values are common published figures; always check
the governing standard, code edition or manufacturer data for design work."""
from fractions import Fraction

CONVERSIONS = [
    ('Length', '1 in', '25.4 mm'), ('Length', '1 ft', '0.3048 m'), ('Length', '1 mile', '1.609344 km'),
    ('Area', '1 in²', '645.16 mm²'), ('Area', '1 ft²', '0.09290304 m²'),
    ('Volume', '1 US gal', '3.785411784 L'), ('Volume', '1 US gal', '231 in³'), ('Volume', '1 ft³', '7.480519 US gal'),
    ('Volume', '1 ft³', '28.316847 L'), ('Volume', '1 L', '61.0237 in³'), ('Volume', '1 Imperial gal', '1.20095 US gal'),
    ('Flow', '1 GPM', '3.785411784 L/min'), ('Flow', '1 GPM', '0.227125 m³/h'), ('Flow', '1 CFM', '28.316847 L/min'),
    ('Flow', '1 CFM', '1.699011 m³/h'), ('Flow', '1 GPM', '0.133681 CFM'),
    ('Pressure', '1 PSI', '6.894757293 kPa'), ('Pressure', '1 bar', '14.5038 PSI'), ('Pressure', '1 MPa', '145.038 PSI'),
    ('Pressure', '1 atm', '14.696 PSI'), ('Pressure', '1 inHg', '0.491154 PSI'), ('Pressure', '1 ft of water', '0.433527 PSI'),
    ('Pressure', '1 kgf/cm²', '14.2233 PSI'),
    ('Force', '1 lbf', '4.448221615 N'), ('Force', '1 kgf', '9.80665 N'), ('Force', '1 ton (US)', '2,000 lbf'),
    ('Torque', '1 lb·ft', '1.355817948 N·m'), ('Torque', '1 lb·in', '0.112985 N·m'), ('Torque', '1 lb·ft', '12 lb·in'),
    ('Power', '1 HP', '0.745699872 kW'), ('Power', '1 HP', '550 ft·lbf/s'), ('Power', '1 HP', '2,544.43 BTU/h'),
    ('Power', '1 kW', '3,412.14 BTU/h'), ('Power', '1 ton refrigeration', '12,000 BTU/h'),
    ('Energy', '1 BTU', '1.055056 kJ'), ('Energy', '1 kWh', '3,412.14 BTU'),
    ('Mass', '1 lb', '0.45359237 kg'), ('Mass', '1 oz', '28.349523 g'),
    ('Density', '1 lb/in³', '27.6799 g/cm³'), ('Density', '1 lb/gal', '0.119826 kg/L'),
    ('Velocity', '1 ft/s', '0.3048 m/s'), ('Velocity', '1 mph', '1.466667 ft/s'),
    ('Temperature', '°C', '(°F − 32) × 5/9'), ('Temperature', '°F', '°C × 9/5 + 32'), ('Temperature', 'K', '°C + 273.15'),
    ('Viscosity', '1 cSt', '1 mm²/s'), ('Viscosity', 'SUS (≥ 75 cSt)', '≈ cSt × 4.635'),
]


def _fraction_rows():
    rows = []
    for n in range(1, 65):
        f = Fraction(n, 64)
        if f.denominator > 16 and n >= 8:           # 1/64" steps below 1/8", then 1/16" steps
            continue
        whole = '%d/%d"' % (f.numerator, f.denominator) if f < 1 else '1"'
        rows.append([whole, '%.4f' % float(f), '%.3f' % (float(f) * 25.4)])
    return rows


FRACTIONS = _fraction_rows()

HOSE = [
    ['-4', '1/4"', '6.4', '7/16-20', '7/16-20'], ['-5', '5/16"', '7.9', '1/2-20', '1/2-20'],
    ['-6', '3/8"', '9.5', '9/16-18', '9/16-18'], ['-8', '1/2"', '12.7', '3/4-16', '3/4-16'],
    ['-10', '5/8"', '15.9', '7/8-14', '7/8-14'], ['-12', '3/4"', '19.1', '1-1/16-12', '1-1/16-12'],
    ['-16', '1"', '25.4', '1-5/16-12', '1-5/16-12'], ['-20', '1-1/4"', '31.8', '1-5/8-12', '1-5/8-12'],
    ['-24', '1-1/2"', '38.1', '1-7/8-12', '1-7/8-12'], ['-32', '2"', '50.8', '2-1/2-12', '2-1/2-12'],
]
ISO_VG = [['ISO VG 15', '13.5 – 16.5'], ['ISO VG 22', '19.8 – 24.2'], ['ISO VG 32', '28.8 – 35.2'],
          ['ISO VG 46', '41.4 – 50.6'], ['ISO VG 68', '61.2 – 74.8'], ['ISO VG 100', '90 – 110'],
          ['ISO VG 150', '135 – 165']]
CLEANLINESS = [['Servo valves', '16/14/11'], ['Proportional valves', '17/15/12'],
               ['Variable piston pumps', '17/15/13'], ['Vane and fixed piston pumps', '18/16/13'],
               ['Gear pumps', '19/17/14'], ['Directional and pressure valves', '19/17/14'],
               ['Cylinders', '20/18/15']]
VELOCITY = [['Pump suction (inlet)', '2 – 4', '0.6 – 1.2'], ['Return', '10 – 15', '3.0 – 4.6'],
            ['Pressure, up to 3,000 PSI', '7 – 20', '2.1 – 6.1'], ['Pressure, above 3,000 PSI', '15 – 25', '4.6 – 7.6']]

MOTOR_FLA = [  # NEC Table 430.250, three-phase induction motors, full-load amps
    ['1', '4.2', '2.1'], ['1-1/2', '6.0', '3.0'], ['2', '6.8', '3.4'], ['3', '9.6', '4.8'], ['5', '15.2', '7.6'],
    ['7-1/2', '22', '11'], ['10', '28', '14'], ['15', '42', '21'], ['20', '54', '27'], ['25', '68', '34'],
    ['30', '80', '40'], ['40', '104', '52'], ['50', '130', '65'], ['60', '154', '77'], ['75', '192', '96'],
    ['100', '248', '124'], ['125', '312', '156'], ['150', '360', '180'], ['200', '480', '240']]
AMPACITY = [  # NEC Table 310.16, copper, not more than 3 current-carrying conductors, 30 °C ambient
    ['14', '15', '20', '25'], ['12', '20', '25', '30'], ['10', '30', '35', '40'], ['8', '40', '50', '55'],
    ['6', '55', '65', '75'], ['4', '70', '85', '95'], ['3', '85', '100', '115'], ['2', '95', '115', '130'],
    ['1', '110', '130', '145'], ['1/0', '125', '150', '170'], ['2/0', '145', '175', '195'], ['3/0', '165', '200', '225'],
    ['4/0', '195', '230', '260'], ['250 kcmil', '215', '255', '290'], ['300 kcmil', '240', '285', '320'],
    ['350 kcmil', '260', '310', '350'], ['500 kcmil', '320', '380', '430']]

PIPE = [  # NPS, OD, Sch 40 ID, Sch 80 ID (in), NPT threads per inch
    ['1/8', '0.405', '0.269', '0.215', '27'], ['1/4', '0.540', '0.364', '0.302', '18'],
    ['3/8', '0.675', '0.493', '0.423', '18'], ['1/2', '0.840', '0.622', '0.546', '14'],
    ['3/4', '1.050', '0.824', '0.742', '14'], ['1', '1.315', '1.049', '0.957', '11.5'],
    ['1-1/4', '1.660', '1.380', '1.278', '11.5'], ['1-1/2', '1.900', '1.610', '1.500', '11.5'],
    ['2', '2.375', '2.067', '1.939', '11.5'], ['2-1/2', '2.875', '2.469', '2.323', '8'],
    ['3', '3.500', '3.068', '2.900', '8']]
BOLT_TORQUE = [  # SAE J429, coarse thread, dry (unlubricated), typical lb·ft
    ['1/4-20', '8', '12'], ['5/16-18', '17', '25'], ['3/8-16', '30', '45'], ['7/16-14', '50', '70'],
    ['1/2-13', '75', '110'], ['9/16-12', '110', '150'], ['5/8-11', '150', '220'], ['3/4-10', '260', '380'],
    ['7/8-9', '430', '600'], ['1-8', '640', '900']]

FORMULAS = [
    ('Hydraulic power', 'HP = PSI × GPM / 1714'), ('Pump flow', 'GPM = cc/rev × RPM / 3785.41'),
    ('Pump input torque', 'lb·in = PSI × in³/rev / (2π × η_mech)'), ('Cylinder area', 'A = π d² / 4'),
    ('Cylinder force', 'F = P × A'), ('Cylinder speed', 'in/s = GPM × 3.85 / A (in²)'),
    ('Line velocity', 'ft/s = 0.3208 × GPM / A (in²)'), ('Reynolds number', 'Re = V D / ν'),
    ('Heat in oil', 'BTU/h = HP lost × 2,545'), ('Reservoir rule of thumb', 'Volume ≈ 2–3 × pump GPM (open loop)'),
    ('Accumulator (Boyle)', 'P₁ V₁ = P₂ V₂   (absolute pressures)'),
    ('Torque and power', 'HP = lb·ft × RPM / 5252.11'), ('Pneumatic air use', 'SCFM ≈ ft³/cycle × (PSIG + 14.7) / 14.7 × cycles/min'),
    ('Three-phase current', 'I = kW × 1000 / (√3 × V × PF × η)'), ('Single-phase current', 'I = W / (V × PF)'),
    ('Voltage drop (single phase / DC)', 'V = 2 × I × L × R'), ('Voltage drop (three phase)', 'V = √3 × I × L × R'),
    ('Ohm’s law', 'V = I × R      P = V × I = I² R'),
]

SECTIONS = {
    'Conversions': [('Unit conversions', ['QUANTITY', 'FROM', 'EQUALS'], CONVERSIONS, '')],
    'Fractions': [('Fraction, decimal and millimetre', ['FRACTION', 'DECIMAL (in)', 'MILLIMETRES'], FRACTIONS,
                   '1/16" steps, plus 1/64" steps below 1/8".')],
    'Hydraulic': [
        ('Recommended line velocity', ['LINE', 'ft/s', 'm/s'], VELOCITY,
         'After the Parker hose-sizing nomograph, for petroleum oil up to 315 SUS at 100 °F.'),
        ('Hose dash sizes and thread', ['DASH', 'HOSE ID', 'ID (mm)', 'JIC 37° THREAD', 'SAE O-RING BOSS THREAD'], HOSE,
         'Dash number = ID in sixteenths of an inch.'),
        ('ISO viscosity grades', ['GRADE', 'KINEMATIC VISCOSITY AT 40 °C (cSt)'], ISO_VG, 'ISO 3448: ±10 % of the grade.'),
        ('Typical cleanliness targets (ISO 4406)', ['COMPONENT', 'TARGET CODE'], CLEANLINESS,
         'Typical targets near 2,000–3,000 PSI. Use one code cleaner for higher pressure or critical machines; '
         'the component maker’s requirement governs.')],
    'Electrical': [
        ('Motor full-load current, three phase (NEC 430.250)', ['HP', '230 V (A)', '460 V (A)'], MOTOR_FLA,
         'Use table FLA, not nameplate, to size conductors and short-circuit protection. 208 V ≈ 230 V value × 1.1; '
         '575 V ≈ 460 V value × 0.8.'),
        ('Copper ampacity (NEC 310.16)', ['SIZE (AWG)', '60 °C', '75 °C', '90 °C'], AMPACITY,
         'Not more than three current-carrying conductors, 30 °C ambient. Small conductors are limited to 15 A (14), '
         '20 A (12) and 30 A (10) overcurrent protection; terminations are usually rated 75 °C.')],
    'Pipe & fasteners': [
        ('Steel pipe dimensions', ['NPS', 'OD (in)', 'SCH 40 ID (in)', 'SCH 80 ID (in)', 'NPT THREADS / in'], PIPE, ''),
        ('Bolt torque, SAE grade 5 and 8 (dry)', ['SIZE', 'GRADE 5 (lb·ft)', 'GRADE 8 (lb·ft)'], BOLT_TORQUE,
         'Typical values for clean, dry, unplated coarse threads. Lubricated or plated threads need about 20–25 % '
         'less. Manufacturer and joint design govern.')],
    'Formulas': [('Handy formulas', ['NAME', 'FORMULA'], FORMULAS, '')],
}
