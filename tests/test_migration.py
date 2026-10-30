"""Non-GUI migration regression checks."""
import sys as _sys, pathlib as _pl
_sys.path.insert(0, str(_pl.Path(__file__).resolve().parents[1]))  # repo root, so `caldera` imports without installing
from caldera.seal_data import SEAL_MATRIX
from caldera import calculations as c
from caldera import legacy_calculations as l
from caldera.extended import EXTRA, calculate
from caldera.seal_data import MATERIALS as SEAL_MATERIALS
assert len(SEAL_MATRIX)>=4                                   # 4 fluid families in 1.0, 12 since 1.1
assert all(len(rows)==len(SEAL_MATERIALS) for rows in SEAL_MATRIX.values())
assert all(len(row)==4 for rows in SEAL_MATRIX.values() for row in rows)
assert abs(c.convert(1,'in → mm')-25.4)<1e-9
assert abs(l.hydraulic_power(1714,1,1)['hydraulic_hp']-1)<1e-9
assert abs(l.torque_power(5252.113,1)['hp']-1)<0.001
for name,fields in EXTRA.items():
    values=[v.default if isinstance(v,list) else (str(v) if v.__class__.__name__=='Text' else float(v)) for _,v in fields]
    result=calculate(name,values)
    assert isinstance(result,dict) and result, name
print('Migration regression checks passed')
