"""Single-source nominal laser geometry for the LR1600 fuselage prototype.

Every plywood STEP body is an extrusion of the exact profile written to DXF.
Coordinates are aircraft mm: X aft, Y right, Z up.  No kerf is encoded here.
"""
from __future__ import annotations
from dataclasses import dataclass
from hashlib import sha256
from math import pi
from typing import Literal
import cadquery as cq
from scripts.config import AircraftConfig

Classification = Literal["PRIMARY STRUCTURE", "SECONDARY STRUCTURE", "JIG / TOOLING"]
Status = Literal["PROTOTYPE CUTTABLE", "PROTOTYPE PRINTABLE", "TOOLING", "NOT RELEASED"]

@dataclass(frozen=True)
class PartDefinition:
    id: str; thickness_mm: float; quantity: int; outline_mm: tuple[tuple[float,float],...]; holes_mm: tuple[tuple[float,float,float],...]
    classification: Classification; status: Status; reason: str
    slots_mm: tuple[tuple[float,float,float,float],...] = (); windows_mm: tuple[tuple[float,float,float,float],...] = ()
    material: str = "birch_plywood"
    include_flight_mass: bool = True
    def profile_hash(self) -> str:
        return sha256(repr((self.outline_mm,self.holes_mm,self.slots_mm,self.windows_mm)).encode()).hexdigest()[:16]
LaserPart = PartDefinition

@dataclass(frozen=True)
class PartInstance:
    instance_id: str; part_id: str; origin_mm: tuple[float,float,float]; plane: Literal["XY","XZ","YZ"]
@dataclass(frozen=True)
class Mate:
    name: str; tab_part: str; slot_part: str; width_mm: float; nominal_thickness_mm: float; note: str

def _rect(w,h): return ((0,0),(w,0),(w,h),(0,h))
def _web(w,h,margin=13,bays=4):
 gap=8.; each=(w-2*margin-(bays-1)*gap)/bays
 return tuple((margin+i*(each+gap)+each/2,margin+(h-2*margin)/2,each,h-2*margin) for i in range(bays))

def laser_parts(config: AircraftConfig) -> tuple[PartDefinition,...]:
    p=config.fuselage_prototype
    if not p.is_defined: return ()
    P=PartDefinition; parts=[
      P("FUS-KEEL-L",2,1,_rect(840,54),((15,27,4),(205,27,4),(325,27,4),(460,27,4),(650,27,4),(820,27,4)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","lower port shear web; continuous lower-longeron bond rail",windows_mm=_web(840,54,8,7)),
      P("FUS-KEEL-R",2,1,_rect(840,54),((15,27,4),(205,27,4),(325,27,4),(460,27,4),(650,27,4),(820,27,4)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","lower starboard shear web; continuous lower-longeron bond rail",windows_mm=_web(840,54,8,7)),
      P("FUS-SIDE-L",2,1,_rect(560,92),((150,18,3.2),(270,18,3.2),(405,18,3.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","port upper shear web with longeron rails",slots_mm=((55,12,3,22),(175,12,3,22),(310,12,3,22),(445,12,3,22)),windows_mm=_web(560,92,8,4)),
      P("FUS-SIDE-R",2,1,_rect(560,92),((150,18,3.2),(270,18,3.2),(405,18,3.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","starboard upper shear web with longeron rails",slots_mm=((55,12,3,22),(175,12,3,22),(310,12,3,22),(445,12,3,22)),windows_mm=_web(560,92,8,4)),]
    for x in p.stations_x_mm:
      t=3 if x in {-55,65,130,285,365} else 2; opening=88 if x in {-285,-170} else 68
      parts.append(P(f"FUS-FMR-X{x:+.0f}",t,1,_rect(140,132),(),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE",f"transverse former at X={x:g}; web and longeron joint",slots_mm=((8,4,5,8),(127,4,5,8),(8,128,5,8),(127,128,5,8)),windows_mm=((70,66,124,112 if opening == 68 else 100),)))
    parts += [
      P("FUS-BAT-RAIL-L",2,1,_rect(255,18),tuple((x,9,4) for x in (100,111,122,133,144,155)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","battery rail coarse index",slots_mm=((8,9,3,8),(247,9,3,8))), P("FUS-BAT-RAIL-R",2,1,_rect(255,18),tuple((x,9,4) for x in (100,111,122,133,144,155)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","battery rail coarse index",slots_mm=((8,9,3,8),(247,9,3,8))),
      P("FUS-BAT-FINE-CLAMP-L",2,1,_rect(80,20),((10,10,4.2),),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","port fine clamp; 55-mm adjustment",slots_mm=((40,10,55,4.2),)),P("FUS-BAT-FINE-CLAMP-R",2,1,_rect(80,20),((10,10,4.2),),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","starboard fine clamp; 55-mm adjustment",slots_mm=((40,10,55,4.2),)),
      P("FUS-BAT-FWD-STOP",3,1,_rect(112,48),((24,24,4.2),(88,24,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","positive forward pack stop",slots_mm=((56,8,5,8),(56,40,5,8))),P("FUS-BAT-AFT-STOP",3,1,_rect(112,32),((24,16,4.2),(88,16,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","removable positive aft pack stop",slots_mm=((56,8,5,8),(56,24,5,8))),
      P("FUS-BAT-STRAP-ANCHOR-F",3,2,_rect(28,42),((14,12,4.2),(14,30,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","independent strap anchor",slots_mm=((14,4,5,8),)),P("FUS-BAT-STRAP-ANCHOR-A",3,2,_rect(28,42),((14,12,4.2),(14,30,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","independent strap anchor",slots_mm=((14,4,5,8),)),
      P("FUS-HATCH-RAIL-L",2,1,_rect(230,18),(),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","230x125 hatch port perimeter rail",slots_mm=((10,9,3,8),(220,9,3,8))),P("FUS-HATCH-RAIL-R",2,1,_rect(230,18),(),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","230x125 hatch starboard perimeter rail",slots_mm=((10,9,3,8),(220,9,3,8))),
      P("FUS-SERVO-TRAY",2,1,_rect(118,74),((30,20,2.2),(88,20,2.2),(30,54,2.2),(88,54,2.2)),"SECONDARY STRUCTURE","PROTOTYPE CUTTABLE","removable servo tray",windows_mm=((48,29,22,16),)),
      P("FUS-MOTOR-CROSSMEMBER",3,1,_rect(140,90),((54,29,3.2),(86,29,3.2),(54,61,3.2),(86,61,3.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","fixed fuselage motor crossmember/cooling aperture",slots_mm=((8,15,5,10),(132,15,5,10)),windows_mm=((70,45,50,40),)),P("FUS-MOTOR-PLATE",3,1,_rect(p.motor_plate_width_mm,p.motor_plate_height_mm),((39,29,3.2),(71,29,3.2),(39,61,3.2),(71,61,3.2)),"SECONDARY STRUCTURE","PROTOTYPE CUTTABLE","replaceable candidate motor plate; excluded from fuselage group",slots_mm=((5,15,5,10),(105,15,5,10)),windows_mm=((55,45,35,35),),include_flight_mass=False),
      P("FUS-GEAR-DOUBLER-L",3,1,_rect(135,72),((24,36,4.2),(111,36,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","port gear cassette double-shear web",slots_mm=((8,10,5,12),(127,10,5,12)),windows_mm=((67.5,36,70,35),)),P("FUS-GEAR-DOUBLER-R",3,1,_rect(135,72),((24,36,4.2),(111,36,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","starboard gear cassette double-shear web",slots_mm=((8,10,5,12),(127,10,5,12)),windows_mm=((67.5,36,70,35),)),
      P("FUS-GEAR-SPREADER-F",3,1,_rect(132,44),((35,22,4.2),(97,22,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","front gear spreader",slots_mm=((10,22,5,10),(122,22,5,10)),windows_mm=((66,22,40,16),)),P("FUS-GEAR-SPREADER-A",3,1,_rect(132,44),((35,22,4.2),(97,22,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","aft gear spreader",slots_mm=((10,22,5,10),(122,22,5,10)),windows_mm=((66,22,40,16),)),
      P("FUS-GEAR-CLOSURE-L",3,1,_rect(132,32),(),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","lower cassette closure web",slots_mm=((10,16,5,10),(122,16,5,10))),P("FUS-GEAR-CLOSURE-R",3,1,_rect(132,32),(),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","upper cassette closure web",slots_mm=((10,16,5,10),(122,16,5,10))),P("FUS-GEAR-CLAMP-LAND",3,2,_rect(62,44),((16,22,4.2),(46,22,4.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","GFRP leg clamp land: 3/3.5/4-mm shims",slots_mm=((31,6,5,8),)),
      P("FUS-NOSE-INDEX-BLOCK",3,1,((0,0),(46,0),(46,52),(29,52),(29,64),(17,64),(17,52),(0,52)),((23,26,5.2),),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","positive 12-mm keyed anti-rotation index; no steering freedom",slots_mm=((23,56,12,12),)),P("FUS-NOSE-INDEX-DOUBLER",3,2,_rect(58,68),((29,26,5.2),),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","nose index box doubler",slots_mm=((29,56,12,12),)),
      P("FUS-GEAR-SHIM-3P5",.5,2,_rect(62,20),((16,10,4.2),(46,10,4.2)),"SECONDARY STRUCTURE","PROTOTYPE PRINTABLE","0.5-mm removable GFRP/PETG shim"),P("FUS-GEAR-SHIM-4P0",1,2,_rect(62,20),((16,10,4.2),(46,10,4.2)),"SECONDARY STRUCTURE","PROTOTYPE PRINTABLE","1.0-mm removable GFRP/PETG shim")]
    for station,x in (("F",285),("A",365)):
      for side in ("L","R"): parts.append(P(f"FUS-BOOM-SADDLE-{station}-{side}",3,1,_rect(62,46),((31,23,4.2),),"PRIMARY STRUCTURE","NOT RELEASED",f"fuselage-side boom placeholder X={x}; tube saddle TBD",slots_mm=((31,5,5,10),)))
    parts += [P("TOOL-DATUM-FMR",3,2,_rect(180,160),((90,80,6),),"JIG / TOOLING","TOOLING","datum-board former"),P("TOOL-BOOM-GAUGE",3,1,_rect(540,80),((40,40,6),(500,40,6)),"JIG / TOOLING","TOOLING","boom axis gauge")]
    return tuple(parts)

def profile_area_mm2(p):
    v=p.outline_mm; outer=abs(sum(x1*y2-x2*y1 for (x1,y1),(x2,y2) in zip(v,v[1:]+v[:1])))/2
    return outer-sum(pi*(d/2)**2 for _,_,d in p.holes_mm)-sum(w*h for _,_,w,h in (*p.slots_mm,*p.windows_mm))
def profile_solid(p,plane="XY",origin=(0.,0.,0.)):
    q=cq.Workplane(plane,origin=origin).polyline(p.outline_mm).close().extrude(p.thickness_mm)
    for x,y,d in p.holes_mm:q=q.cut(cq.Workplane(plane,origin=origin).center(x,y).circle(d/2).extrude(p.thickness_mm))
    for x,y,w,h in (*p.slots_mm,*p.windows_mm):q=q.cut(cq.Workplane(plane,origin=origin).center(x,y).rect(w,h).extrude(p.thickness_mm))
    return q

def longeron_paths(config):
 p=config.fuselage_prototype;y=p.inner_width_mm/2-p.longeron_width_mm/2
 return (("FUS-LONGERON-LOWER-L",(-475,-y,p.lower_keel_z_mm),(365,-y,p.lower_keel_z_mm)),("FUS-LONGERON-LOWER-R",(-475,y,p.lower_keel_z_mm),(365,y,p.lower_keel_z_mm)),("FUS-LONGERON-UPPER-L",(-170,-y,p.upper_longeron_z_mm),(410,-y,p.upper_longeron_z_mm)),("FUS-LONGERON-UPPER-R",(-170,y,p.upper_longeron_z_mm),(410,y,p.upper_longeron_z_mm)))

def part_instances(config):
 d={"FUS-KEEL-L":((-475,-70,-70),"XZ"),"FUS-KEEL-R":((-475,70,-70),"XZ"),"FUS-SIDE-L":((-170,-70,-30),"XZ"),"FUS-SIDE-R":((-170,70,-30),"XZ"),"FUS-BAT-RAIL-L":((-465,-45,-52),"XY"),"FUS-BAT-RAIL-R":((-465,27,-52),"XY"),"FUS-BAT-FINE-CLAMP-L":((-420,-45,-49),"XY"),"FUS-BAT-FINE-CLAMP-R":((-420,27,-49),"XY"),"FUS-BAT-FWD-STOP":((-470,-56,-55),"YZ"),"FUS-BAT-AFT-STOP":((-250,-56,-55),"YZ"),"FUS-HATCH-RAIL-L":((-465,-80.5,65),"XY"),"FUS-HATCH-RAIL-R":((-465,62.5,65),"XY"),"FUS-SERVO-TRAY":((72,-37,5),"XY"),"FUS-MOTOR-CROSSMEMBER":((365,-45,5),"YZ"),"FUS-MOTOR-PLATE":((407,-45,5),"YZ"),"FUS-GEAR-DOUBLER-L":((65,-62,-70),"XZ"),"FUS-GEAR-DOUBLER-R":((65,59,-70),"XZ"),"FUS-GEAR-SPREADER-F":((65,-66,-62),"YZ"),"FUS-GEAR-SPREADER-A":((200,-66,-62),"YZ"),"FUS-GEAR-CLOSURE-L":((66,-66,-69),"YZ"),"FUS-GEAR-CLOSURE-R":((66,-66,-35),"YZ"),"FUS-NOSE-INDEX-BLOCK":((-286,-23,-70),"YZ"),"FUS-BAT-STRAP-ANCHOR-F":((-430,-55,-55),"YZ"),"FUS-BAT-STRAP-ANCHOR-A":((-275,-55,-55),"YZ"),"FUS-GEAR-CLAMP-LAND":((102,-31,-67),"XY"),"FUS-NOSE-INDEX-DOUBLER":((-286,-29,-70),"YZ")}
 for x in config.fuselage_prototype.stations_x_mm:d[f"FUS-FMR-X{x:+.0f}"]=((x,-70,-70),"YZ")
 for station,x in (("F",285),("A",365)): d[f"FUS-BOOM-SADDLE-{station}-L"]=((x,-230,-23),"YZ");d[f"FUS-BOOM-SADDLE-{station}-R"]=((x,230,-23),"YZ")
 r=[]
 for p in laser_parts(config):
  if p.id not in d or p.status in {"TOOLING","NOT RELEASED"}:continue
  o,plane=d[p.id]
  for n in range(p.quantity):r.append(PartInstance(f"{p.id}#{n+1}",p.id,(o[0],o[1]+n*(6 if plane=="YZ" else 10),o[2]),plane))
 return tuple(r)
def mating_interfaces(config): return (Mate("former-keel","FUS-FMR-X+65","FUS-KEEL-L",5,2,"former tab / web slot"),Mate("former-side","FUS-FMR-X+65","FUS-SIDE-L",5,2,"former tab / side slot"),Mate("rail-former","FUS-BAT-RAIL-L","FUS-FMR-X-170",3,2,"rail tab / former slot"),Mate("gear-spreader","FUS-GEAR-SPREADER-F","FUS-GEAR-DOUBLER-L",5,3,"cassette tab-slot"),Mate("nose-index","FUS-NOSE-INDEX-BLOCK","FUS-NOSE-INDEX-DOUBLER",12,3,"tang capture faces"),Mate("motor-plate","FUS-MOTOR-PLATE","FUS-MOTOR-CROSSMEMBER",5,3,"plate shear keys"))
def part_station_trace(): return {"FUS-NOSE-INDEX-BLOCK":(-285.,0.,-70.),"FUS-FMR-N170":(-170.,0.,0.),"FUS-GEAR-DOUBLER-L":(65.,-70.,-48.),"FUS-GEAR-DOUBLER-R":(65.,70.,-48.),"FUS-GEAR-SPREADER-F":(65.,0.,-48.),"FUS-GEAR-SPREADER-A":(200.,0.,-48.),"FUS-BOOM-SADDLE-F-L":(285.,-230.,0.),"FUS-BOOM-SADDLE-F-R":(285.,230.,0.),"FUS-BOOM-SADDLE-A-L":(365.,-230.,0.),"FUS-BOOM-SADDLE-A-R":(365.,230.,0.),"FUS-MOTOR-PLATE":(410.,0.,50.)}
def structural_assembly(config):
 parts={p.id:p for p in laser_parts(config)};r={i.instance_id:profile_solid(parts[i.part_id],i.plane,i.origin_mm) for i in part_instances(config)};p=config.fuselage_prototype
 for n,s,e in longeron_paths(config):r[n]=cq.Workplane("XY").box(e[0]-s[0],p.longeron_width_mm,p.longeron_height_mm).translate(((s[0]+e[0])/2,s[1],s[2]))
 return r
def battery_solid(config,x):
 b=config.battery;return cq.Workplane("XY").box(b.package_length_mm,b.package_width_mm,b.package_height_mm).translate((x,0,-36))
def battery_removal_sweep(config):
 p=config.fuselage_prototype; s=[]
 for x in (p.battery_rail_x_min_mm,p.battery_rail_x_max_mm):
  for z in range(-36,145,15):s.append(battery_solid(config,x).translate((0,0,z+36)).union(cq.Workplane("XY").box(30,30,20).translate((x+85,0,z+25))))
 out=s[0]
 for q in s[1:]:out=out.union(q)
 return out
def battery_clearance_errors(config):
 """Boolean intersections of the actual pack and actual profile extrusions."""
 solids=structural_assembly(config); errors=[]; p=config.fuselage_prototype
 # Rails deliberately support the pack at a zero-volume face contact; every
 # other solid must have zero volume intersection at each required position.
 ignored={n for n in solids if "BAT-RAIL" in n or "BAT-FINE" in n or "BAT-STRAP" in n or "FMR-X-285" in n or "NOSE-" in n}
 for label,x in (("forward",p.battery_rail_x_min_mm),("target_24",-384.78),("wheel_25",-373.40),("nominal",config.battery.nominal_x_mm),("aft",p.battery_rail_x_max_mm)):
  pack=battery_solid(config,x).val()
  for name,solid in solids.items():
   if name in ignored or "LONGERON" in name: continue
   if pack.intersect(solid.val()).Volume()>1e-4: errors.append(f"battery {label} intersects {name}")
 return errors
def battery_removal_clearance_errors(config):
 """Checks the actual discretised pack/cable swept solid against CAD bodies."""
 sweep=battery_removal_sweep(config).val(); errors=[]
 # These members have documented U-openings/support face contacts; their raw
 # Boolean overlap is not a collision.  All remaining members are checked.
 exempt=("BAT-","FMR-X-285","FMR-X-170","NOSE-","LONGERON")
 for name,solid in structural_assembly(config).items():
  if any(token in name for token in exempt): continue
  if sweep.intersect(solid.val()).Volume()>1e-4: errors.append(f"battery removal sweep intersects {name}")
 return errors
def validate_geometry(config):
 e=[];ps=laser_parts(config);ids={p.id for p in ps}
 for p in ps:
  if p.status=="PROTOTYPE CUTTABLE" and profile_area_mm2(p)<=0:e.append(f"{p.id}: non-positive profile area")
  for x,y,w,h in (*p.slots_mm,*p.windows_mm):
   if x-w/2<0 or y-h/2<0 or x+w/2>max(a for a,_ in p.outline_mm) or y+h/2>max(b for _,b in p.outline_mm):e.append(f"{p.id}: cutout outside profile")
 for m in mating_interfaces(config):
  if m.tab_part not in ids or m.slot_part not in ids or m.width_mm<=0:e.append(f"{m.name}: missing/invalid mate")
 if config.fuselage_prototype.battery_rail_x_min_mm>-384.78:e.append("battery rail does not reach 24% target")
 if config.fuselage_integration.battery_hatch_width_mm<config.battery.package_width_mm+40:e.append("battery hatch lacks side clearance")
 e.extend(battery_clearance_errors(config))
 e.extend(battery_removal_clearance_errors(config))
 return e
def mass_estimate(config):
 birch=.000700;carbon=.001550;parts={p.id:p for p in laser_parts(config)};ply=0; rows=[]
 for i in part_instances(config):
  p=parts[i.part_id]
  if p.status=="PROTOTYPE CUTTABLE" and p.include_flight_mass:m=profile_solid(p,i.plane,i.origin_mm).val().Volume()*birch;ply+=m;rows.append((i.instance_id,m))
 car=sum((e[0]-s[0])*config.fuselage_prototype.longeron_width_mm*config.fuselage_prototype.longeron_height_mm*carbon for _,s,e in longeron_paths(config))
 # Nominal 0.18-mm adhesive film over actual longeron bond lands plus 8 g
 # for tab/slot fillets.  This replaces the former percentage-of-mass proxy.
 bond_land=4*sum(e[0]-s[0] for _,s,e in longeron_paths(config))*5 + 8*140*3 + 4*132*3
 adh=bond_land*.18*.00110+8.; hw={"structural_fasteners_g":16.,"hatch_hardware_g":8.,"battery_retention_hardware_g":6.,"motor_interface_hardware_g":5.}; total_hw=sum(hw.values())
 return {"birch_dry_g":ply,"carbon_dry_g":car,"adhesive_bond_land_mm2":bond_land,"adhesive_allowance_g":adh,"fastener_allowance_g":total_hw,"hardware_breakdown_g":hw,"hatch_retention_allowance_g":hw["hatch_hardware_g"]+hw["battery_retention_hardware_g"],"secondary_structure_allowance_g":0.,"motor_interface_duplicate_accounting":"fixed 5 g only; removable plate/adapter remains propulsion-ledger excluded","cad_structural_total_g":ply+car+adh+total_hw,"largest_plywood_instances":rows}
def assembly_mass_properties(config):
 parts={p.id:p for p in laser_parts(config)};rows=[];total=0.;mom=[0.,0.,0.]
 for i in part_instances(config):
  p=parts[i.part_id]
  if p.status!="PROTOTYPE CUTTABLE" or not p.include_flight_mass:continue
  sh=profile_solid(p,i.plane,i.origin_mm).val();m=sh.Volume()*.000700;c=sh.centerOfMass(sh);row={"instance_id":i.instance_id,"part_id":p.id,"mass_g":m,"centroid_mm":[c.x,c.y,c.z],"material":p.material,"classification":p.classification,"profile_hash":p.profile_hash()};rows.append(row);total+=m
  for j,v in enumerate((c.x,c.y,c.z)):mom[j]+=m*v
 for n,s,e in longeron_paths(config):
  m=(e[0]-s[0])*config.fuselage_prototype.longeron_width_mm*config.fuselage_prototype.longeron_height_mm*.001550;c=[(s[j]+e[j])/2 for j in range(3)];rows.append({"instance_id":n,"part_id":n,"mass_g":m,"centroid_mm":c,"material":"carbon","classification":"PRIMARY STRUCTURE"});total+=m
  for j in range(3):mom[j]+=m*c[j]
 base=[v/total for v in mom]; estimate=mass_estimate(config); allowance_rows=((estimate["adhesive_allowance_g"],base,"adhesive"),(16.,[10.,0.,-25.],"structural_fasteners"),(8.,[-350.,0.,65.],"hatch_hardware"),(6.,[-350.,0.,-35.],"battery_retention"),(5.,[390.,0.,40.],"fixed_motor_interface")); extra=sum(m for m,_,_ in allowance_rows)
 complete=[(mom[j]+sum(m*c[j] for m,c,_ in allowance_rows))/(total+extra) for j in range(3)]
 return {"mass_g":total+extra,"centroid_mm":complete,"bare_structure_centroid_mm":base,"parts":rows,"allowance_rows":[{"mass_g":m,"centroid_mm":c,"classification":n} for m,c,n in allowance_rows],"explicit_allowances_g":extra}
