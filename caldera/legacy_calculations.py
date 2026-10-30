"""Engineering calculation routines."""
import math

def positive(value, label, allow_zero=False):
    try: v = float(value)
    except (TypeError, ValueError): raise ValueError(f'{label} must be a number.')
    if not math.isfinite(v) or (v < 0 if allow_zero else v <= 0): raise ValueError(f'{label} must be {"nonnegative" if allow_zero else "positive"} and finite.')
    return v

def hydraulic_power(psi, gpm, efficiency):
    psi=positive(psi,'Pressure',True); gpm=positive(gpm,'Flow',True); e=positive(efficiency,'Efficiency')
    if e>1: raise ValueError('Efficiency must be 0–1.')
    hp=psi*gpm/1714.0
    return {'hydraulic_hp':hp,'input_hp':hp/e,'loss_hp':hp*(1/e-1)}

def cylinder_buckling(diameter, unsupported_length, E, K, safety_factor, applied_load):
    d=positive(diameter,'Diameter'); L=positive(unsupported_length,'Unsupported length'); E=positive(E,'Modulus')
    K=positive(K,'End factor'); sf=positive(safety_factor,'Safety factor'); load=positive(applied_load,'Load',True)
    I=math.pi*d**4/64
    critical=math.pi**2*E*I/(K*L)**2
    return {'I':I,'critical_lbf':critical,'allowable_lbf':critical/sf,'passes_euler':load<=critical/sf}

def cylinder_cycle(bore, rod, stroke, gpm_extend, gpm_retract):
    b=positive(bore,'Bore'); r=positive(rod,'Rod',True); s=positive(stroke,'Stroke'); qe=positive(gpm_extend,'Extend flow'); qr=positive(gpm_retract,'Retract flow')
    if r>=b: raise ValueError('Rod diameter must be less than bore diameter.')
    cap=math.pi*b*b/4; ann=math.pi*(b*b-r*r)/4
    ve=cap*s/231; vr=ann*s/231
    return {'cap_area':cap,'annulus_area':ann,'extend_gal':ve,'retract_gal':vr,'extend_sec':ve/qe*60,'retract_sec':vr/qr*60,'cycle_sec':(ve/qe+vr/qr)*60}

def air_consumption(bore, rod, stroke, psig, cycles_per_min, atm_psia=14.7):
    b=positive(bore,'Bore'); r=positive(rod,'Rod',True); s=positive(stroke,'Stroke'); p=positive(psig,'Gauge pressure',True); c=positive(cycles_per_min,'Cycles/min',True)
    atm=positive(atm_psia,'Reference atmospheric pressure')
    if r>=b: raise ValueError('Rod diameter must be less than bore diameter.')
    swept=math.pi/4*(2*b*b-r*r)*s/1728
    scf=swept*(p+atm)/atm
    return {'compressed_ft3_cycle':swept,'free_air_scf_cycle':scf,'scfm':scf*c}

def torque_power(torque_lbft, rpm):
    t=positive(torque_lbft,'Torque',True); n=positive(rpm,'RPM',True)
    hp=t*n*2*math.pi/(60*550)
    return {'hp':hp,'kw':hp*0.745699872,'torque_nm':t*1.3558179483}

def tank_estimate(length,width,height,thickness,density,freeboard=0):
    l=positive(length,'Length'); w=positive(width,'Width'); h=positive(height,'Height'); t=positive(thickness,'Thickness'); den=positive(density,'Density'); fb=positive(freeboard,'Freeboard',True)
    if fb>=h: raise ValueError('Freeboard must be less than internal height.')
    area=2*(l*w+l*h+w*h)/144
    return {'gross_gal':l*w*h/231,'usable_gal':l*w*(h-fb)/231,'plate_area_ft2':area,'six_face_weight_lb':area*t/12*1728*den}
