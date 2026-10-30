"""Seal material screening data. General guidance for seal-material *families*; the exact compound, fluid additives,
temperature, pressure and seal design decide real compatibility. Not an approval of any product."""

MATERIALS = ['NBR / Buna-N', 'HNBR', 'FKM (fluorocarbon)', 'EPDM', 'Polyurethane (AU / EU)', 'PTFE (filled)',
             'Silicone (VMQ)', 'Fluorosilicone (FVMQ)', 'Neoprene (CR)', 'Polyacrylate (ACM)', 'FFKM (perfluoro)',
             'Acetal / nylon (back-up, wear rings)']

RATING_TEXT = {'good': 'Generally compatible', 'conditional': 'Conditional', 'bad': 'Generally unsuitable',
               'unknown': 'Insufficient data'}
SYMBOL = {'good': '✓', 'conditional': '~', 'bad': '✗', 'unknown': '?'}

# fluid -> (ISO 6743-4 / common class, short description, {material: (tag, note)})
_G, _C, _B, _U = 'good', 'conditional', 'bad', 'unknown'
FLUIDS = {
    'Mineral oil (HH, HL, HM, HV)': ('HM / HV', 'Petroleum hydraulic oil, the most common fluid.', {
        'NBR / Buna-N': (_G, 'Standard choice for mineral oil, about −30 to 100 °C (−22 to 212 °F).'),
        'HNBR': (_G, 'Use when NBR runs too hot or sees ozone; to about 150 °C.'),
        'FKM (fluorocarbon)': (_G, 'For hot systems; check low-temperature limit (often −20 °C / −4 °F).'),
        'EPDM': (_B, 'Swells badly in petroleum oils. Never use with mineral oil.'),
        'Polyurethane (AU / EU)': (_G, 'Excellent for rod seals and wipers; keep below about 90 °C.'),
        'PTFE (filled)': (_G, 'Inert; needs an elastomer energizer to seal.'),
        'Silicone (VMQ)': (_C, 'Moderate swell and poor wear; static only.'),
        'Fluorosilicone (FVMQ)': (_G, 'Good, but static only and costly.'),
        'Neoprene (CR)': (_C, 'Moderate swell; acceptable for some low-duty uses.'),
        'Polyacrylate (ACM)': (_G, 'Good in hot oil (to about 150 °C); poor with water and in the cold.'),
        'FFKM (perfluoro)': (_G, 'Works, but rarely justified on cost.'),
        'Acetal / nylon (back-up, wear rings)': (_G, 'Standard back-up and wear-ring materials.')}),
    'High-water fluids (HFA, HFB)': ('HFA / HFB', 'Oil-in-water and water-in-oil emulsions (fire resistant).', {
        'NBR / Buna-N': (_G, 'Usual choice; keep below about 60 °C (140 °F).'),
        'HNBR': (_G, 'Good; better heat and ageing resistance than NBR.'),
        'FKM (fluorocarbon)': (_C, 'Usable, but swells in hot water; rarely worth the cost here.'),
        'EPDM': (_B, 'The oil phase swells EPDM.'),
        'Polyurethane (AU / EU)': (_C, 'Standard PU hydrolyses in water; use a hydrolysis-resistant grade under 50 °C.'),
        'PTFE (filled)': (_G, 'Compatible; check fillers (bronze can corrode).'),
        'Silicone (VMQ)': (_C, 'Static only.'),
        'Fluorosilicone (FVMQ)': (_C, 'Static only; confirm with supplier.'),
        'Neoprene (CR)': (_C, 'Fair; verify for the exact emulsion.'),
        'Polyacrylate (ACM)': (_B, 'Poor water resistance.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_C, 'Nylon absorbs water and swells; acetal is preferred.')}),
    'Water glycol (HFC)': ('HFC', 'Water + glycol fire-resistant fluid (about 35–45 % water).', {
        'NBR / Buna-N': (_G, 'Common choice; keep below about 60 °C (140 °F).'),
        'HNBR': (_G, 'Good; verify with the fluid supplier.'),
        'FKM (fluorocarbon)': (_C, 'Not recommended hot; standard FKM degrades in hot water-based fluid.'),
        'EPDM': (_G, 'Good in water glycol, but only if no mineral oil is present.'),
        'Polyurethane (AU / EU)': (_C, 'Hydrolysis risk; use only a grade approved for HFC, under 50 °C.'),
        'PTFE (filled)': (_G, 'Compatible; avoid bronze fillers.'),
        'Silicone (VMQ)': (_C, 'Static only.'),
        'Fluorosilicone (FVMQ)': (_C, 'Static only; confirm with supplier.'),
        'Neoprene (CR)': (_C, 'Fair; verify for the fluid.'),
        'Polyacrylate (ACM)': (_B, 'Poor water resistance.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_C, 'Acetal preferred; nylon swells with water.')}),
    'Phosphate ester (HFDR)': ('HFDR', 'Synthetic fire-resistant fluid (e.g. turbine EHC, aviation).', {
        'NBR / Buna-N': (_B, 'Attacked by phosphate esters.'),
        'HNBR': (_B, 'Not suitable.'),
        'FKM (fluorocarbon)': (_G, 'Usual choice for industrial HFDR; not for aviation types.'),
        'EPDM': (_G, 'Standard for aviation phosphate esters; check industrial grades.'),
        'Polyurethane (AU / EU)': (_B, 'Not suitable.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_C, 'Static only; verify.'),
        'Fluorosilicone (FVMQ)': (_C, 'Verify with supplier.'),
        'Neoprene (CR)': (_B, 'Not suitable.'),
        'Polyacrylate (ACM)': (_B, 'Not suitable.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_C, 'Verify; some grades are attacked.')}),
    'Polyol ester (HFDU)': ('HFDU', 'Synthetic ester fire-resistant fluid.', {
        'NBR / Buna-N': (_C, 'Swell depends on the ester and the NBR compound.'),
        'HNBR': (_G, 'Generally good.'),
        'FKM (fluorocarbon)': (_G, 'Usual choice.'),
        'EPDM': (_B, 'Swells in esters.'),
        'Polyurethane (AU / EU)': (_C, 'Hydrolysis-resistant grades only, kept dry and cool.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_B, 'Not suitable.'),
        'Fluorosilicone (FVMQ)': (_C, 'Verify with supplier.'),
        'Neoprene (CR)': (_B, 'Not suitable.'),
        'Polyacrylate (ACM)': (_C, 'Verify with supplier.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_G, 'Generally fine.')}),
    'Vegetable oil (HETG)': ('HETG', 'Biodegradable triglyceride (e.g. rapeseed) oil.', {
        'NBR / Buna-N': (_G, 'Good below about 60–70 °C; the oil oxidises and ages seals faster when hot.'),
        'HNBR': (_G, 'Good.'),
        'FKM (fluorocarbon)': (_G, 'Good.'),
        'EPDM': (_B, 'Not suitable.'),
        'Polyurethane (AU / EU)': (_G, 'Good below about 60 °C.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_B, 'Not suitable.'),
        'Fluorosilicone (FVMQ)': (_C, 'Verify.'),
        'Neoprene (CR)': (_C, 'Fair.'),
        'Polyacrylate (ACM)': (_C, 'Verify.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_G, 'Generally fine.')}),
    'Synthetic ester (HEES)': ('HEES', 'Biodegradable synthetic ester.', {
        'NBR / Buna-N': (_C, 'Some NBR compounds shrink or swell; ask the fluid maker for approved compounds.'),
        'HNBR': (_G, 'Good.'),
        'FKM (fluorocarbon)': (_G, 'Good, often the safest choice.'),
        'EPDM': (_B, 'Not suitable.'),
        'Polyurethane (AU / EU)': (_C, 'Hydrolysis-resistant grades only; keep water content low.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_B, 'Not suitable.'),
        'Fluorosilicone (FVMQ)': (_C, 'Verify.'),
        'Neoprene (CR)': (_B, 'Not suitable.'),
        'Polyacrylate (ACM)': (_C, 'Verify.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_G, 'Generally fine.')}),
    'Polyglycol (HEPG / PAG)': ('HEPG', 'Biodegradable polyalkylene glycol. Do not mix with mineral oil.', {
        'NBR / Buna-N': (_C, 'Depends on the PAG type and compound.'),
        'HNBR': (_C, 'Verify.'),
        'FKM (fluorocarbon)': (_C, 'Some PAGs attack FKM; verify.'),
        'EPDM': (_C, 'Often good with water-soluble PAG; verify.'),
        'Polyurethane (AU / EU)': (_B, 'Not suitable.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_C, 'Verify.'),
        'Fluorosilicone (FVMQ)': (_C, 'Verify.'),
        'Neoprene (CR)': (_C, 'Verify.'),
        'Polyacrylate (ACM)': (_B, 'Not suitable.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_C, 'Verify.')}),
    'PAO synthetic (HEPR)': ('HEPR', 'Polyalphaolefin synthetic hydrocarbon (cold-climate oils).', {
        'NBR / Buna-N': (_G, 'Good; PAO can shrink some seals slightly.'),
        'HNBR': (_G, 'Good.'),
        'FKM (fluorocarbon)': (_G, 'Good.'),
        'EPDM': (_B, 'Not suitable.'),
        'Polyurethane (AU / EU)': (_G, 'Good.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_C, 'Static only.'),
        'Fluorosilicone (FVMQ)': (_G, 'Good, static only.'),
        'Neoprene (CR)': (_C, 'Fair.'),
        'Polyacrylate (ACM)': (_G, 'Good.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_G, 'Generally fine.')}),
    'Water': ('—', 'Plain or treated water.', {
        'NBR / Buna-N': (_G, 'Good in cold water (below about 80 °C).'),
        'HNBR': (_G, 'Good, including warm water.'),
        'FKM (fluorocarbon)': (_C, 'Standard FKM swells in hot water and steam; special grades exist.'),
        'EPDM': (_G, 'Excellent, including hot water and steam.'),
        'Polyurethane (AU / EU)': (_C, 'Hydrolysis-resistant grades only, under 50 °C.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_C, 'Static only.'),
        'Fluorosilicone (FVMQ)': (_C, 'Static only.'),
        'Neoprene (CR)': (_G, 'Good in cold water.'),
        'Polyacrylate (ACM)': (_B, 'Poor water resistance.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_C, 'Acetal preferred; nylon swells.')}),
    'Diesel / fuel oil': ('—', 'Diesel, kerosene and fuel oils (not gasoline blends).', {
        'NBR / Buna-N': (_G, 'Good, especially high-acrylonitrile grades.'),
        'HNBR': (_G, 'Good.'),
        'FKM (fluorocarbon)': (_G, 'Best choice for fuels.'),
        'EPDM': (_B, 'Not suitable.'),
        'Polyurethane (AU / EU)': (_C, 'Verify; some swell.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_B, 'Not suitable.'),
        'Fluorosilicone (FVMQ)': (_G, 'Good, static only.'),
        'Neoprene (CR)': (_C, 'Fair.'),
        'Polyacrylate (ACM)': (_C, 'Verify.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_G, 'Generally fine.')}),
    'Brake fluid (glycol, DOT 3 / 4)': ('—', 'Glycol-ether brake fluid. Not DOT 5 silicone fluid.', {
        'NBR / Buna-N': (_B, 'Not suitable.'),
        'HNBR': (_B, 'Not suitable.'),
        'FKM (fluorocarbon)': (_B, 'Not suitable.'),
        'EPDM': (_G, 'Standard brake-system material.'),
        'Polyurethane (AU / EU)': (_B, 'Not suitable.'),
        'PTFE (filled)': (_G, 'Compatible.'),
        'Silicone (VMQ)': (_C, 'Verify.'),
        'Fluorosilicone (FVMQ)': (_B, 'Not suitable.'),
        'Neoprene (CR)': (_C, 'Fair.'),
        'Polyacrylate (ACM)': (_B, 'Not suitable.'),
        'FFKM (perfluoro)': (_G, 'Compatible.'),
        'Acetal / nylon (back-up, wear rings)': (_C, 'Verify.')}),
}

# material -> (temperature range °C (lo, hi), typical hardness, strengths, watch out for)
GUIDE = {
    'NBR / Buna-N': ((-30, 100), '70–90 Shore A', 'Low cost, good wear, the default for mineral oil.',
                     'Ozone and sunlight, phosphate esters, brake fluid, heat above ~100 °C.'),
    'HNBR': ((-35, 150), '70–90 Shore A', 'Stronger and more heat- and ozone-resistant than NBR.',
             'Cost; phosphate esters; brake fluid.'),
    'FKM (fluorocarbon)': ((-20, 200), '70–90 Shore A', 'Heat, fuels and most oils; low compression set.',
                          'Cold (special low-temp grades exist), hot water / steam, brake fluid, ketones.'),
    'EPDM': ((-50, 150), '60–90 Shore A', 'Water, steam, glycols, brake fluid, weather.',
             'Any petroleum oil or grease, even as an assembly lube.'),
    'Polyurethane (AU / EU)': ((-35, 90), '90–95 Shore A', 'Outstanding wear and extrusion resistance: rod seals, '
                               'wipers, piston seals.', 'Hydrolysis in hot water-based fluids; heat above ~90 °C.'),
    'PTFE (filled)': ((-200, 260), 'Rigid (55–65 Shore D)', 'Almost universal chemical resistance, very low friction.',
                      'Not elastic: needs an O-ring or spring energizer; creeps (cold flow).'),
    'Silicone (VMQ)': ((-60, 230), '40–80 Shore A', 'Very wide temperature range, food grades.',
                       'Poor tear and abrasion resistance: static seals only.'),
    'Fluorosilicone (FVMQ)': ((-60, 175), '40–80 Shore A', 'Fuel and oil resistance with silicone’s cold flexibility.',
                              'Static only; costly; brake fluid.'),
    'Neoprene (CR)': ((-40, 120), '50–90 Shore A', 'Weather, ozone, refrigerants; moderate oil resistance.',
                      'Not for phosphate esters, esters or fuels.'),
    'Polyacrylate (ACM)': ((-20, 150), '60–80 Shore A', 'Hot mineral oils and transmission fluids.',
                           'Water, glycols, cold, steam.'),
    'FFKM (perfluoro)': ((-15, 320), '70–90 Shore A', 'Resists almost every fluid, very high temperature.',
                         'Very expensive; usually overkill for hydraulics.'),
    'Acetal / nylon (back-up, wear rings)': ((-40, 110), 'Rigid', 'Back-up rings stop extrusion; wear rings carry '
                                             'side load.', 'Not a seal by itself; nylon absorbs water.'),
}

TIPS = [
    ('Pressure and hardness', '70 Shore A O-rings suit most service to about 1,500 PSI (100 bar) with normal clearances. '
                              'Above that, use 90 Shore A and / or back-up rings so the seal does not extrude into the gap.'),
    ('Dynamic vs static', 'Rod and piston seals need wear resistance: PU, NBR, HNBR, FKM or PTFE. Silicone, '
                          'fluorosilicone and neoprene belong in static seals.'),
    ('Temperature', 'Ranges shown are typical for the polymer family. A specific compound can be narrower or wider; '
                    'check the low end as well as the high end.'),
    ('Changing fluids', 'Swapping between mineral oil and a fire-resistant or biodegradable fluid usually means new seals '
                        'and a thorough flush. PAG (polyglycol) must never be mixed with mineral oil.'),
    ('Assembly lube', 'Lubricate O-rings with the system fluid or a compatible grease. Petroleum grease on EPDM causes '
                      'swelling and failure.'),
]


def _matrix():
    out = {}
    for fluid, (_cls, _desc, rows) in FLUIDS.items():
        out[fluid] = [(m, RATING_TEXT[rows[m][0]], rows[m][1], rows[m][0]) for m in MATERIALS if m in rows]
    return out


# fluid -> [(material, rating text, note, tag)]  (the shape the UI has always used)
SEAL_MATRIX = _matrix()
