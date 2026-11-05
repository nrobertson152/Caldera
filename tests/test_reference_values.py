"""Reference values: every calculator against an answer worked out independently of its code.

Run with  python3 tests/test_reference_values.py  (no Qt needed).

Each expected value is derived another way than the calculator does it: through SI units, from a different but
equivalent formula (Hagen-Poiseuille for laminar pressure drop, v = sqrt(2 dP / rho) for an orifice, P = T omega for
shaft power), or from published tables (NEC, AWG). A calculator that agrees with its own formula but not with the
physics fails here. Values go through `toolmeta.evaluate`, the same path the window uses."""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))  # repo root, so `caldera` imports without installing
import math

from caldera.registry import TOOLS
from caldera.toolmeta import evaluate, fill_inputs

# SI conversion factors (exact or NIST)
IN = 0.0254                      # m
FT = 0.3048                      # m
GAL = 3.785411784e-3             # m^3 (US gallon)
PSI = 6894.757293168             # Pa
LBF = 4.4482216152605            # N
HP = 745.69987158227             # W
CFM = 4.719474432e-4             # m^3/s per ft^3/min
G_WATER = 999.0                  # kg/m^3, water at about 15 C (the 29.84 orifice constant assumes this)
CHECKS = 0


def run(name, values):
    specs, fn = TOOLS[name]
    full = fill_inputs(specs, [str(v) for v in values])
    r = evaluate(name, fn, specs, full)
    assert not r.error, (name, r.error)
    out = {}
    for m in r.metrics:                       # 'Label' and, for metrics that share a label, 'Label (unit)'
        out.setdefault(m.label, m.value)
        out['%s (%s)' % (m.label, m.unit) if m.unit else m.label] = m.value
    return out, r


def close(actual, expected, rel=1e-3, what=''):
    global CHECKS
    CHECKS += 1
    assert math.isclose(actual, expected, rel_tol=rel), '%s: got %r, expected %r' % (what, actual, expected)


# ---- Unit converter
m, _ = run('Unit Converter', [1, 'in → mm']); close(m['Converted value'], 25.4, 1e-12, 'in->mm')
m, _ = run('Unit Converter', [100, '°F → °C']); close(m['Converted value'], 37.7777778, 1e-7, 'F->C')
m, _ = run('Unit Converter', [1000, 'PSI → bar']); close(m['Converted value'], 1000 * PSI / 1e5, 1e-9, 'psi->bar')

# ---- Motor: 125 HP, 460 V, 93 %, PF 0.88, three-phase
m, _ = run('Motor & Electrical Power', [125, 460, 93, 0.88, '3-phase'])
p_in = 125 * HP / 0.93
close(m['Input power'], p_in / 1000, 1e-6, 'motor input kW')
close(m['Estimated current'], p_in / (math.sqrt(3) * 460 * 0.88), 1e-6, 'motor 3-phase amps')
m, _ = run('Motor & Electrical Power', [1, 230, 80, 0.8, '1-phase'])
close(m['Estimated current'], HP / 0.8 / (230 * 0.8), 1e-6, 'motor 1-phase amps')

# ---- Pump: 250 cc/rev at 1800 rpm, 2500 psi, 90 % / 90 %
m, _ = run('Hydraulic Pump & Motor', [250, 1800, 2500, 90, 90])
q_th = 250e-6 * 1800 / 60                                   # m^3/s
close(m['Theoretical flow'], q_th * 60 / GAL, 1e-6, 'pump theoretical GPM')
q = q_th * 0.9
close(m['Hydraulic output'], 2500 * PSI * q / HP, 1e-3, 'pump hydraulic HP')         # 1714 is a rounded constant
close(m['Shaft input'], 2500 * PSI * q / HP / 0.9, 1e-3, 'pump shaft HP')

# ---- Hydraulic power: 1714 psi x 1 GPM = 1 HP (the defining constant), and 2500 psi x 30 GPM
m, _ = run('Hydraulic Power & Efficiency', [2500, 30, 0.9])
close(m['Hydraulic power'], 2500 * PSI * 30 * GAL / 60 / HP, 1e-3, 'hydraulic HP')
close(m['Input power'], 2500 * PSI * 30 * GAL / 60 / HP / 0.9, 1e-3, 'hydraulic input HP')

# ---- Cylinder buckling: 1 in solid rod, E = 30e6 psi, K = 1, SF = 2, Sy = 50 ksi
d, E, sy = 1.0, 30e6, 50e3
area, inertia, rg = math.pi * d * d / 4, math.pi * d ** 4 / 64, d / 4
m, r = run('Cylinder Buckling', [d, 30, E, 1, 2, 2000, sy])         # KL/r = 120 > Cc = 108.8: Euler
assert m['Buckling method'].startswith('Euler'), m['Buckling method']
close(m['Slenderness ratio'], 30 / rg, 1e-9, 'buckling KL/r')
close(m['Transition slenderness'], math.sqrt(2 * math.pi ** 2 * E / sy), 1e-9, 'buckling Cc')
close(m['Critical buckling load'], math.pi ** 2 * E * inertia / 30 ** 2, 1e-9, 'Euler Pcr')
close(m['Allowable load'], math.pi ** 2 * E * inertia / 30 ** 2 / 2, 1e-9, 'Euler allowable')
m, r = run('Cylinder Buckling', [d, 10, E, 1, 2, 2000, sy])         # KL/r = 40: Johnson governs
assert m['Buckling method'].startswith('Johnson'), m['Buckling method']
lam = 10 / rg
johnson = area * (sy - sy ** 2 * lam ** 2 / (4 * math.pi ** 2 * E))   # Johnson parabola, textbook form
close(m['Critical buckling load'], johnson, 1e-9, 'Johnson Pcr')
euler_short = math.pi ** 2 * E * inertia / 10 ** 2
assert m['Critical buckling load'] < euler_short and m['Critical buckling load'] < area * sy  # never above yield
assert any(level == 'warn' for level, _ in r.status), r.status
# continuity at the transition: Johnson and Euler meet at KL/r = Cc
cc = math.sqrt(2 * math.pi ** 2 * E / sy)
l_cc = cc * rg
mj, _ = run('Cylinder Buckling', [d, l_cc * 0.999999, E, 1, 1, 0, sy])
me, _ = run('Cylinder Buckling', [d, l_cc * 1.000001, E, 1, 1, 0, sy])
close(mj['Critical buckling load'], me['Critical buckling load'], 1e-4, 'Euler/Johnson continuity')

# ---- Hydraulic cylinder cycle time: 4 in bore, 2 in rod, 24 in stroke, 10 GPM each way
m, _ = run('Hydraulic Cylinder Cycle Time', [4, 2, 24, 10, 10])
v_ext = math.pi * (4 * IN) ** 2 / 4 * 24 * IN
v_ret = math.pi * ((4 * IN) ** 2 - (2 * IN) ** 2) / 4 * 24 * IN
q = 10 * GAL / 60
close(m['Extend time'], v_ext / q, 1e-9, 'cycle extend s')
close(m['Retract time'], v_ret / q, 1e-9, 'cycle retract s')

# ---- Pneumatic air consumption: 3 in bore, 1 in rod, 12 in stroke, 90 psig, 10 cycles/min
m, _ = run('Pneumatic Air Consumption', [3, 1, 12, 90, 10, 14.7])
swept = (math.pi * 9 / 4 + math.pi * (9 - 1) / 4) * 12 / 1728            # ft^3, extend + retract
close(m['Air consumption'], swept * (90 + 14.7) / 14.7 * 10, 1e-9, 'air SCFM')

# ---- Pneumatic cylinder: supply flow is free air (SCFM)
m, _ = run('Pneumatic Cylinder', [3, 1, 90, 12, 5])
close(m['Extend force'], 90 * math.pi * 9 / 4, 1e-9, 'pneumatic extend force')
free_extend = math.pi * 9 / 4 * 12 / 1728 * (90 + 14.7) / 14.7            # SCF to fill the cap end at 90 psig
close(m['Extend time'], free_extend / 5 * 60, 1e-9, 'pneumatic extend s')
# consistency: the free air per cycle equals what Pneumatic Air Consumption says for one cycle
air, _ = run('Pneumatic Air Consumption', [3, 1, 12, 90, 1, 14.7])
close(m['Free air per cycle'], air['Air consumption'], 1e-9, 'pneumatic vs air consumption')

# ---- Torque and power: P = T * omega
m, _ = run('Torque, RPM & Power', [100, 1800])
close(m['Shaft power (HP)'], 100 * LBF * FT * 1800 * 2 * math.pi / 60 / HP, 1e-6, 'torque HP')
close(m['Shaft power (kW)'], 100 * LBF * FT * 1800 * 2 * math.pi / 60 / 1000, 1e-6, 'torque kW')
close(m['Torque (N·m)'], 100 * LBF * FT, 1e-9, 'torque N m')

# ---- Wire voltage drop: published AWG resistances (ohm / 1000 ft at 20 C)
m, r = run('Wire Gauge & Voltage Drop', [15, 50, 24, 3, 'Copper', '20', 'DC / single-phase'])
assert m['Smallest passing gauge'] == '6 AWG', m['Smallest passing gauge']      # 8 AWG gives 3.9 %
close(m['Voltage drop'], 15 * 2 * 50 * 0.3951 / 1000, 1e-3, '6 AWG DC drop')
m, r = run('Wire Gauge & Voltage Drop', [30, 200, 480, 3, 'Copper', '75', 'Three-phase'])
r75 = 1 + 0.00393 * 55
rows = {g: float(v) for g, v, _ in r.table[1]}
close(rows['10'], math.sqrt(3) * 30 * 200 * 0.999 * r75 / 1000, 1e-3, '10 AWG three-phase drop')
assert any('three-phase' in n for n in r.notes), r.notes

# ---- Conduit fill: NEC Chapter 9 (Table 4 EMT, Table 5 THHN, Table 8 bare)
m, r = run('Conduit Fill', ['EMT', 'Recommend smallest', '3 × 12 AWG THHN; 1 × 12 AWG Bare', 'No'])
assert m['Recommended size'].startswith('1/2'), m['Recommended size']
close(m['Total conductor area'], 3 * 0.0133 + 0.006, 1e-6, 'conduit conductor area')
close(m['Fill of recommended size'], (3 * 0.0133 + 0.006) / 0.304 * 100, 1e-6, 'conduit fill % of 1/2 EMT')
close(m['Allowed fill'], 40, 1e-12, 'NEC limit for 3+ conductors')

# ---- Hydraulic cylinder: 2.5 in bore, 1.25 in rod, 12 in stroke, 2500 psi, 10 GPM
m, _ = run('Hydraulic Cylinder', [2.5, 1.25, 12, 2500, 10])
a_cap = math.pi * (2.5 * IN) ** 2 / 4
a_ann = math.pi * ((2.5 * IN) ** 2 - (1.25 * IN) ** 2) / 4
close(m['Extend force'], 2500 * PSI * a_cap / LBF, 1e-9, 'cylinder extend lbf')
close(m['Retract force'], 2500 * PSI * a_ann / LBF, 1e-9, 'cylinder retract lbf')
close(m['Extend time'], a_cap * 12 * IN / (10 * GAL / 60), 1e-9, 'cylinder extend s')

# ---- Hydraulic motor: 250 cc/rev, 2500 psi, 1800 rpm, 90 % / 90 %
m, _ = run('Hydraulic Motor', [250, 2500, 1800, 90, 90])
t_nm = 2500 * PSI * 250e-6 / (2 * math.pi) * 0.9                       # N m
close(m['Torque'], t_nm / (LBF * FT), 1e-6, 'motor torque lb-ft')
close(m['Flow'], 250e-6 * 1800 / 60 / 0.9 * 60 / GAL, 1e-6, 'motor flow GPM')
close(m['Output HP'], t_nm * 1800 * 2 * math.pi / 60 / HP, 1e-3, 'motor output HP')    # P = T omega

# ---- Heat load: 2500 psi, 20 GPM, 15 % lost, 20 % margin
m, _ = run('Heat Load & Cooler Sizing', [2500, 20, 15, 20])
heat_w = 2500 * PSI * 20 * GAL / 60 * 0.15
close(m['Heat load (kW)'], heat_w / 1000, 1e-3, 'heat load kW')
close(m['Heat load (HP)'], heat_w / HP, 1e-3, 'heat load HP')
close(m['Cooler target (kW)'], heat_w * 1.2 / 1000, 1e-3, 'cooler target kW')

# ---- Accumulator: polytropic gas between p1 and p2 (absolute)
m, _ = run('Hydraulic Accumulator', [1500, 2500, 1200, 1, 1.4])
# V0 p0^(1/n) = V1 p1^(1/n) = V2 p2^(1/n), and V1 - V2 = 1 gal
v0 = 1 / ((1200 / 1500) ** (1 / 1.4) - (1200 / 2500) ** (1 / 1.4))
close(m['Required gas volume'], v0, 1e-9, 'accumulator V0')
v1, v2 = v0 * (1200 / 1500) ** (1 / 1.4), v0 * (1200 / 2500) ** (1 / 1.4)
close(v1 - v2, 1.0, 1e-9, 'accumulator discharge check')

# ---- Compressed air: isothermal compression of 100 SCFM from 14.7 to 114.7 psia, 75 %
m, _ = run('Compressed Air Horsepower', [100, 14.7, 114.7, 75])
mass_term = 14.7 * PSI * 100 * CFM                                       # p_std * Q_std (W), = m R T
close(m['Idealized isothermal input'], mass_term * math.log(114.7 / 14.7) / 0.75 / 1000, 1e-6, 'air kW')
# second stage: inlet at 29.4 psia. Same mass flow, so p1 Q1 is still p_std Q_std (Boyle)
m2, _ = run('Compressed Air Horsepower', [100, 29.4, 114.7, 75])
close(m2['Idealized isothermal input'], mass_term * math.log(114.7 / 29.4) / 0.75 / 1000, 1e-6, 'air kW 2nd stage')

# ---- Line velocity: 20 GPM in a 1 in bore
m, _ = run('Line Velocity', [20, 1, 'Pressure line (up to 3,000 PSI)'])
close(m['Velocity'], 20 * GAL / 60 / (math.pi * IN ** 2 / 4) / FT, 1e-3, 'line velocity ft/s')

# ---- Pressure drop: laminar, checked against Hagen-Poiseuille (dP = 128 mu L Q / (pi D^4))
m, _ = run('Pressure Drop Calculator', [20, 1, 50, 0.87, 32, 0.045])
mu = 32e-6 * 870                                                         # Pa s
q = 20 * 6.30901964e-5
hp_dp = 128 * mu * 50 * FT * q / (math.pi * IN ** 4)
assert m['Reynolds number'] < 2300
close(m['Pressure drop'], hp_dp / PSI, 1e-6, 'laminar pressure drop')
# turbulent: Colebrook-White (solved by iteration) agrees with Swamee-Jain within its ~1 % accuracy
m, _ = run('Pressure Drop Calculator', [60, 1, 50, 0.87, 10, 0.045])
re_, f_sj = m['Reynolds number'], m['Darcy friction factor']
f = 0.02
for _ in range(50):
    f = (-2 * math.log10(0.045e-3 / (3.7 * IN) + 2.51 / (re_ * math.sqrt(f)))) ** -2
close(f_sj, f, 2e-2, 'turbulent friction factor')

# ---- Orifice: Q = Cd A sqrt(2 dP / rho)
m, _ = run('Orifice Flow Estimate', [0.125, 100, 0.87, 0.62])
q_si = 0.62 * math.pi * (0.125 * IN) ** 2 / 4 * math.sqrt(2 * 100 * PSI / (0.87 * G_WATER))
close(m['Flow'], q_si * 60 / GAL, 2e-3, 'orifice GPM')

# ---- Labor savings
m, _ = run('Labor Savings', [20, 12, 100, 35])
close(m['Hours saved'], 800 / 60, 1e-12, 'hours saved')

# ---- Reservoir: 36 x 24 x 24 in outside, 11 ga carbon steel (0.1196 in, MSG), closed top, 80 % full
m, _ = run('Reservoir / Drip Pan', [36, 24, 24, '11 ga', 'Carbon steel (A36)', 80, 'Yes', 72, 48, '3/16"',
                                     'Carbon steel (A36)', 'Yes', '11 ga', 8])
t = 0.1196
inside = (36 - 2 * t) * (24 - 2 * t) * (24 - 2 * t)                      # in^3
close(m['Oil capacity at fill level'], inside * 0.8 / 231, 1e-6, 'reservoir oil gal')

# ---- Validation says what is wrong (and survives python -O, unlike assert)
for name, values, words in (('Hydraulic Cylinder', [2, 3, 12, 2500, 10], 'smaller than the bore'),
                            ('Hydraulic Accumulator', [1500, 1200, 1300, 1, 1.4], 'precharge'),
                            ('Orifice Flow Estimate', [0.125, 100, 0.87, 1.5], 'Discharge coefficient'),
                            ('Pneumatic Cylinder', [3, 1, 90, 12, 0], 'Supply flow')):
    specs, fn = TOOLS[name]
    err = evaluate(name, fn, specs, fill_inputs(specs, [str(v) for v in values])).error
    assert err and words in err, (name, err)

# ---- Saved inputs from before an input was added still open (the new input takes its default)
specs, _ = TOOLS['Cylinder Buckling']
assert fill_inputs(specs, ['1', '30', '30000000', '1', '2', '2000']) == ['1', '30', '30000000', '1', '2', '2000', '50000']
assert fill_inputs(specs, ['0'] * 8) is None
wire_specs, _ = TOOLS['Wire Gauge & Voltage Drop']
assert fill_inputs(wire_specs, ['15', '50', '24', '3', 'Copper', '20'])[-1] == 'DC / single-phase'

print('Reference values: %d checks passed across %d calculators' % (CHECKS, len(TOOLS)))
