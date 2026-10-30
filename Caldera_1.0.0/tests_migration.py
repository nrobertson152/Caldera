"""Non-GUI migration regression checks."""
from caldera.seal_data import SEAL_MATRIX
from caldera import calculations as c
from caldera import legacy_calculations as l
from caldera.extended import EXTRA, calculate
assert len(SEAL_MATRIX)==4
assert all(len(rows)==7 for rows in SEAL_MATRIX.values())
assert all(len(row)==4 for rows in SEAL_MATRIX.values() for row in rows)
assert abs(c.convert(1,'in → mm')-25.4)<1e-9
assert abs(l.hydraulic_power(1714,1,1)['hydraulic_hp']-1)<1e-9
assert abs(l.torque_power(5252.113,1)['hp']-1)<0.001
for name,fields in EXTRA.items():
    values=[float(v) for _,v in fields]
    result=calculate(name,values)
    assert isinstance(result,dict) and result, name
print('Migration regression checks passed')
