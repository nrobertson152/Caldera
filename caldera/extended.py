"""Additional engineering estimators for the Qt migration. Values are preliminary."""
import math

def calculate(name,a):
    x=[float(v) if not isinstance(v,str) or v.replace('.','',1).replace('-','',1).isdigit() else v for v in a]
    if name=='Conduit Fill':
        n,area,internal,limit=x; assert internal>0 and n>=0 and area>=0
        fill=n*area/internal*100;return {'Conductor area (in²)':n*area,'Fill (%)':fill,'Maximum (%)':limit,'Within limit':fill<=limit}
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
        q,d=x;assert q>=0 and d>0
        ips=q*231/60/(math.pi*d*d/4);return {'Velocity (ft/s)':ips/12,'Velocity (m/s)':ips*0.0254}
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
'Conduit Fill':[('Conductors','6'),('Area each (in²)','0.0133'),('Internal area (in²)','0.304'),('Maximum fill (%)','40')],
'Hydraulic Cylinder':[('Bore (in)','2.5'),('Rod (in)','1.25'),('Stroke (in)','12'),('Pressure (PSI)','2500'),('Flow (GPM)','10')],
'Hydraulic Motor':[('Displacement (cc/rev)','250'),('Pressure (PSI)','2500'),('Speed (RPM)','1800'),('Volumetric efficiency (%)','90'),('Mechanical efficiency (%)','90')],
'Heat Load & Cooler Sizing':[('System pressure (PSI)','2500'),('Flow (GPM)','20'),('Estimated loss (%)','15'),('Cooler margin (%)','20')],
'Hydraulic Accumulator':[('Minimum pressure (PSIA)','1500'),('Maximum pressure (PSIA)','2500'),('Precharge (PSIA)','1200'),('Usable discharge (gal)','1'),('Polytropic exponent','1.4')],
'Pneumatic Cylinder':[('Bore (in)','3'),('Rod (in)','1'),('Pressure (PSIG)','90'),('Stroke (in)','12'),('Flow (CFM)','5')],
'Compressed Air Horsepower':[('Flow (SCFM)','100'),('Inlet absolute pressure (PSIA)','14.7'),('Outlet absolute pressure (PSIA)','114.7'),('Efficiency (%)','75')],
'Line Velocity':[('Flow (GPM)','20'),('Inside diameter (in)','1')],
'Pressure Drop Calculator':[('Flow (GPM)','20'),('Inside diameter (in)','1'),('Length (ft)','50'),('Specific gravity','0.87'),('Viscosity (cSt)','32'),('Roughness (mm)','0.045')],
'Orifice Flow Estimate':[('Diameter (in)','0.125'),('Pressure differential (PSI)','100'),('Specific gravity','0.87'),('Discharge coefficient','0.62')],
'Labor Savings':[('Old cycle time (min)','20'),('New cycle time (min)','12'),('Cycles','100'),('Hourly rate ($)','35')],
}
