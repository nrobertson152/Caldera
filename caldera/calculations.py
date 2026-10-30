"""Pure calculation functions. Preliminary estimates, not design approval."""
import math
from . import legacy_calculations as legacy

CONVERSIONS = {'in → mm':25.4,'mm → in':1/25.4,'PSI → bar':0.0689475729,'bar → PSI':1/0.0689475729,'GPM → L/min':3.785411784,'L/min → GPM':1/3.785411784,'HP → kW':0.745699872,'kW → HP':1/0.745699872,'gal → L':3.785411784,'L → gal':1/3.785411784,'°F → °C':None,'°C → °F':None}

def convert(value,unit):
    if unit=='°F → °C':return (value-32)*5/9
    if unit=='°C → °F':return value*9/5+32
    return value*CONVERSIONS[unit]

def motor(hp,volts,eff,pf,phase):
    if volts<=0 or not 0<eff<=100 or not 0<pf<=1 or hp<0:raise ValueError('Check voltage, power, efficiency, and power factor.')
    kw=hp*0.745699872; kw_in=kw/(eff/100); amps=kw_in*1000/(volts*pf*(math.sqrt(3) if phase=='3-phase' else 1))
    return {'Output power (kW)':kw,'Input power (kW)':kw_in,'Estimated current (A)':amps}

def pump(d,rpm,psi,ve,me):
    if min(d,rpm,psi)<0 or not 0<ve<=100 or not 0<me<=100:raise ValueError('Check displacement, speed, pressure, and efficiencies.')
    gpm_theoretical=d*rpm/3785.411784; gpm=gpm_theoretical*ve/100; hp=psi*gpm/1714
    return {'Theoretical flow (GPM)':gpm_theoretical,'Actual flow (GPM)':gpm,'Hydraulic output (HP)':hp,'Shaft input (HP)':hp/(me/100)}

def wire(amps,length,voltage,maxdrop,material,temp):
    if amps<=0 or length<0 or voltage<=0 or not 0<maxdrop<=100:raise ValueError('Check current, length, voltage, and maximum drop.')
    awg=[('18',6.385),('16',4.016),('14',2.525),('12',1.588),('10',0.999),('8',0.6282),('6',0.3951),('4',0.2485),('3',0.197),('2',0.1563),('1',0.1239),('1/0',0.0983),('2/0',0.0779),('3/0',0.0618),('4/0',0.049)]
    factor=(1 if material=='Copper' else 1.64)*(1+0.00393*(temp-20))
    rows=[(g,amps*2*length*r*factor/1000) for g,r in awg]
    eligible=[(g,d) for g,d in rows if d/voltage*100<=maxdrop]
    return 'Allowed voltage drop: {:.4f} V\n\n{}'.format(voltage*maxdrop/100, '\n'.join(f'{g:>4} AWG  {drop:.4f} V  ({drop/voltage*100:.2f}%)' for g,drop in eligible[:8]) or 'No listed gauge meets the target.')+'\n\nVoltage drop alone does not establish code-compliant ampacity.'
