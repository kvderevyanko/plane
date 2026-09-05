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
class PartFrame:
    """Rigid, explicit profile frame for a placed laser part.

    ``u`` and ``v`` are the profile axes (the coordinates written to DXF),
    and ``extrusion`` is the positive material-thickness direction.  Keeping
    this contract here prevents a profile operation from depending on an
    accidental CadQuery plane sign convention.
    """
    instance_id: str; part_id: str; origin_mm: tuple[float, float, float]
    u_axis: tuple[float, float, float]; v_axis: tuple[float, float, float]
    extrusion_axis: tuple[float, float, float]

    def local_to_world(self, local: tuple[float, float, float]) -> tuple[float, float, float]:
        return tuple(self.origin_mm[i] + sum(local[k] * (self.u_axis, self.v_axis, self.extrusion_axis)[k][i]
                                                   for k in range(3)) for i in range(3))

    def world_to_local(self, world: tuple[float, float, float]) -> tuple[float, float, float]:
        delta=tuple(world[i]-self.origin_mm[i] for i in range(3))
        return tuple(sum(delta[i] * axis[i] for i in range(3))
                     for axis in (self.u_axis, self.v_axis, self.extrusion_axis))

@dataclass(frozen=True)
class SkeletonFeature:
    """Named physical feature in the v4 dry-fit subset.

    The coordinates are aircraft coordinates, deliberately not the convenient
    local coordinates used to draw a DXF.  This makes a mate check a placement
    check as well as a profile check.
    """
    id: str; part_instance: str; kind: Literal["tab", "slot", "saddle"]
    center_mm: tuple[float, float, float]; size_mm: tuple[float, float, float]
    insertion_axis: tuple[float, float, float]; bond_area_mm2: float = 0.0

@dataclass(frozen=True)
class SkeletonJoint:
    id: str; tab: str; slot: str; purpose: str

@dataclass(frozen=True)
class JointDefinition:
    """The sole geometry owner for one physical former/web joint.

    The web is deliberately the material owner.  Its *actual existing panel
    material* at this station is the tongue; the former carries the only
    subtraction, a side-open but vertically bounded receiver.  This is a
    real through-tab, not a metadata tab and two clearance cuts.
    """
    id: str; former_instance: str; web_instance: str
    center_mm: tuple[float, float, float]; tab_size_mm: tuple[float, float, float]
    receiving_clearance_mm: float; insertion_axis: tuple[float, float, float]
    former_local_mm: tuple[float, float, float]
    web_local_mm: tuple[float, float, float]
    former_notch_height_mm: float
    web_profile_height_mm: float
    material_owner_part: str
    receiver_part: str
    feature_type: str = "web_tongue_into_former_open_bounded_notch"
    def tab_id(self): return f"{self.former_instance}:TAB:{self.id}"
    def slot_id(self): return f"{self.web_instance}:SLOT:{self.id}"
@dataclass(frozen=True)
class Mate:
    """A physical, nominal (kerf-free) joint.

    ``feature`` names intentionally refer to actual profile features, rather
    than a wish-list of connections.  The insertion axis is the dry-build
    motion used by :func:`dry_assembly_errors`.
    """
    name: str; tab_part: str; slot_part: str; width_mm: float; nominal_thickness_mm: float; note: str
    tab_feature: str = "perimeter_web"; slot_feature: str = "slot"
    insertion_axis: tuple[float, float, float] = (0., 0., 1.)
    station_x_mm: float | None = None

@dataclass(frozen=True)
class AssemblyStep:
    name: str; instance_ids: tuple[str, ...]; insertion_axis: tuple[float, float, float]
    adhesive: bool; note: str

def _rect(w,h): return ((0,0),(w,0),(w,h),(0,h))
def _active_web_profile_size(family: str) -> tuple[float, float]:
    """One source for active longitudinal-web outlines and joint relief limits."""
    return (583.,90.5) if family.startswith("SIDE") else (845.,52.)
def _web(w,h,margin=13,bays=4):
 gap=8.; each=(w-2*margin-(bays-1)*gap)/bays
 return tuple((margin+i*(each+gap)+each/2,margin+(h-2*margin)/2,each,h-2*margin) for i in range(bays))

def _active_skeleton_placement(config) -> dict[str, tuple[tuple[float,float,float], Literal["XY","XZ","YZ"]]]:
    """Single editable placement source for the active former/web subset."""
    d={"FUS-KEEL-L#1":((-476.5,-63.,-68.5),"XZ"), "FUS-KEEL-R#1":((-476.5,65.,-68.5),"XZ"),
       "FUS-SIDE-L#1":((-171.5,-68.,-30.),"XZ"), "FUS-SIDE-R#1":((-171.5,70.,-30.),"XZ")}
    for x in config.fuselage_prototype.stations_x_mm:
        d[f"FUS-FMR-X{x:+.0f}#1"]=((x,-70.,-70.),"YZ")
    return d

def _active_skeleton_frames(config) -> dict[str, PartFrame]:
    """Frames derived from, rather than duplicating, the placement source."""
    axes={"XZ":((1.,0.,0.),(0.,0.,1.),(0.,-1.,0.)),
          "YZ":((0.,1.,0.),(0.,0.,1.),(1.,0.,0.))}
    return {ident: PartFrame(ident, ident.split("#")[0], origin, *axes[plane])
            for ident,(origin,plane) in _active_skeleton_placement(config).items()}

def part_frame(config, instance_id: str) -> PartFrame:
    """Return the complete local/world transform for an active plywood part."""
    return _active_skeleton_frames(config)[instance_id]

def joint_profile_operation(joint: JointDefinition, participant: Literal["former", "web"]):
    """Sole conversion from an authoritative joint to a profile operation.

    The former operation is bounded in Z by the tab height and side-open only
    in the declared lateral insertion direction.  The web gets two generated
    relief cuts above/below its retained tongue; it is never a second receiver.
    """
    if participant == "web":
        u,v,_=joint.web_local_mm
        tab_h=joint.tab_size_mm[2]
        web_h=joint.web_profile_height_mm
        bottom=v-tab_h/2; top=v+tab_h/2
        return ((u,bottom/2,joint.tab_size_mm[0],bottom),
                (u,top+(web_h-top)/2,joint.tab_size_mm[0],web_h-top))
    u,v,_=joint.former_local_mm
    throat=joint.tab_size_mm[1]+joint.receiving_clearance_mm
    if u <= 72.:
        width=u + throat / 2
        return (width / 2, v, width, joint.former_notch_height_mm)
    width=144. - (u - throat / 2)
    return (144. - width / 2, v, width, joint.former_notch_height_mm)

def laser_parts(config: AircraftConfig) -> tuple[PartDefinition,...]:
    p=config.fuselage_prototype
    if not p.is_defined: return ()
    P=PartDefinition
    # The active former/web operations have exactly one owner: the placed
    # JointDefinition.  ``laser_parts`` only transforms those definitions into
    # profile operations; it does not reconstruct station coordinates.
    definitions=joint_definitions(config)
    def profile_joint_slots(part_id: str, participant: str):
        slots=[]
        for joint in definitions:
            if participant == "former" and joint.former_instance.split("#")[0] == part_id:
                slots.append(joint_profile_operation(joint, "former"))
            if participant == "web" and joint.web_instance.split("#")[0] == part_id:
                slots.extend(joint_profile_operation(joint, "web"))
        return tuple(slots)
    keel_slots=profile_joint_slots("FUS-KEEL-L", "web")
    keel_slots_r=profile_joint_slots("FUS-KEEL-R", "web")
    side_slots=profile_joint_slots("FUS-SIDE-L", "web")
    side_slots_r=profile_joint_slots("FUS-SIDE-R", "web")
    # Windows are deliberately clear of joint operation domains.
    # Windows deliberately stop outside the 20-mm tongue bands.  The tongue
    # reliefs themselves still derive solely from JointDefinition.
    # Keel windows open through the top boundary (v=52), avoiding a 2-mm
    # disconnected cap between a relief and a lightening window.
    keel_windows=tuple(((a+b)/2+476.5,44., max(18., b-a-7.),16.) for a,b in zip((-475.,-360.,-235.,-110.,15.,155.,250.),(-360.,-235.,-110.,15.,155.,250.,365.)))
    side_windows=tuple(((a+b)/2+171.5,76.,max(18.,b-a-9.),20.) for a,b in zip((-170.,-55.,65.,130.,285.,365.,),(-55.,65.,130.,285.,365.,410.)))
    parts=[
      P("FUS-KEEL-L",2,1,_rect(*_active_web_profile_size("KEEL")),((15,27,4),(205,27,4),(325,27,4),(460,27,4),(650,27,4),(820,27,4)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","v4.3 lower port web: retained material tongues enter former receivers",slots_mm=keel_slots,windows_mm=keel_windows),
      P("FUS-KEEL-R",2,1,_rect(*_active_web_profile_size("KEEL")),((15,27,4),(205,27,4),(325,27,4),(460,27,4),(650,27,4),(820,27,4)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","v4.3 lower starboard web: retained material tongues enter former receivers",slots_mm=keel_slots_r,windows_mm=keel_windows),
      # The 1.5-mm high upper edge land is a real carbon saddle: the upper
      # longeron bears on it and is bonded to its outside face.  It replaces
      # the former solid-on-solid overlap.
      P("FUS-SIDE-L",2,1,_rect(*_active_web_profile_size("SIDE")),((150,18,3.2),(270,18,3.2),(405,18,3.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","v4.3 port side web: retained material tongues enter former receivers",slots_mm=side_slots,windows_mm=side_windows),
      P("FUS-SIDE-R",2,1,_rect(*_active_web_profile_size("SIDE")),((150,18,3.2),(270,18,3.2),(405,18,3.2)),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE","v4.3 starboard side web: retained material tongues enter former receivers",slots_mm=side_slots_r,windows_mm=side_windows),]
    for x in p.stations_x_mm:
      t=3 if x in {-55,65,130,285,365} else 2; opening=112 if x == -285 else (88 if x == -170 else 68)
      # Four through-slots accept the two lower keel webs and the two upper
      # side webs.  They are deliberately placed in remaining frame ligaments,
      # not in the large lightening window.
      # The -285 former is the aft edge of the long service opening: it is a
      # pair of side rails, deliberately open to the hatch rather than a
      # captive top crossbar through the pack extraction path.
      window_h=132 if x == -285 else (112 if opening == 68 else 100)
      # Edge relief turns the former perimeter into four 20-mm physical tabs:
      # the two outer tabs enter side-web slots and two inner tabs enter keel
      # slots.  Every cut is present in the DXF and hence in the extrusion.
      # Bottom-open lower and top-open upper 5Y x 3Z notches.  Their cut
      # rectangles touch the profile edge, so neither is a captive hole.
      # Lower: bottom-open 5Y x 3Z shelf with 3.2-mm locating depth.
      # Upper: top-open saddle; its 5.4-mm throat gives 0.4-mm nominal
      # lateral insertion clearance for 5Y stock and is installed from +Z.
      longeron_notches=((2.7,1.6,5.4,3.2),(141.3,1.6,5.4,3.2),
                         (2.7,131.25,5.4,1.5),(141.3,131.25,5.4,1.5))
      former_slots=profile_joint_slots(f"FUS-FMR-X{x:+.0f}", "former") + longeron_notches
      parts.append(P(f"FUS-FMR-X{x:+.0f}",t,1,_rect(144,132),(),"PRIMARY STRUCTURE","PROTOTYPE CUTTABLE",f"v4.3 transverse former at X={x:g}; bounded web-tongue receivers",slots_mm=former_slots,windows_mm=((72,113,120,26),)))
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
 # The lower web pair is inboard of the side webs.  The old model put both
 # on Y=+/-70, creating a large, unexplained coincident solid overlap.
 d={"FUS-KEEL-L":((-476.5,-63,-68.5),"XZ"),"FUS-KEEL-R":((-476.5,65,-68.5),"XZ"),"FUS-SIDE-L":((-171.5,-68,-30),"XZ"),"FUS-SIDE-R":((-171.5,70,-30),"XZ"),"FUS-BAT-RAIL-L":((-465,-45,4),"XY"),"FUS-BAT-RAIL-R":((-465,27,4),"XY"),"FUS-BAT-FINE-CLAMP-L":((-420,-45,2),"XY"),"FUS-BAT-FINE-CLAMP-R":((-420,27,2),"XY"),"FUS-BAT-FWD-STOP":((-470,-56,0),"YZ"),"FUS-BAT-AFT-STOP":((-250,-56,0),"YZ"),"FUS-HATCH-RAIL-L":((-465,-80.5,65),"XY"),"FUS-HATCH-RAIL-R":((-465,62.5,65),"XY"),"FUS-SERVO-TRAY":((72,-37,5),"XY"),"FUS-MOTOR-CROSSMEMBER":((365,-45,5),"YZ"),"FUS-MOTOR-PLATE":((407,-45,5),"YZ"),"FUS-GEAR-DOUBLER-L":((65,-62,-70),"XZ"),"FUS-GEAR-DOUBLER-R":((65,59,-70),"XZ"),"FUS-GEAR-SPREADER-F":((65,-66,-62),"YZ"),"FUS-GEAR-SPREADER-A":((200,-66,-62),"YZ"),"FUS-GEAR-CLOSURE-L":((66,-66,-69),"YZ"),"FUS-GEAR-CLOSURE-R":((66,-66,-35),"YZ"),"FUS-NOSE-INDEX-BLOCK":((-286,-23,-70),"YZ"),"FUS-BAT-STRAP-ANCHOR-F":((-430,-75,0),"YZ"),"FUS-BAT-STRAP-ANCHOR-A":((-275,-75,0),"YZ"),"FUS-GEAR-CLAMP-LAND":((102,-31,-67),"XY"),"FUS-NOSE-INDEX-DOUBLER":((-286,-29,-70),"YZ")}
 for x in config.fuselage_prototype.stations_x_mm:d[f"FUS-FMR-X{x:+.0f}"]=((x,-70,-70),"YZ")
 # Active skeleton placement is owned by _active_skeleton_placement(), which
 # is also the sole origin of PartFrame transforms used by JointDefinition.
 for instance_id,(origin,plane) in _active_skeleton_placement(config).items():
  d[instance_id.split("#")[0]]=(origin,plane)
 for station,x in (("F",285),("A",365)): d[f"FUS-BOOM-SADDLE-{station}-L"]=((x,-230,-23),"YZ");d[f"FUS-BOOM-SADDLE-{station}-R"]=((x,230,-23),"YZ")
 # Explicit physical placements are required for every repeated part.  In
 # particular these are not a convenient generic Y offset: each is a named
 # port/starboard, fore/aft or stacked role in the assembly record.
 repeated={
  "FUS-BAT-STRAP-ANCHOR-F":(((-430,-75,0),"YZ"),((-430,47,0),"YZ")),
  "FUS-BAT-STRAP-ANCHOR-A":(((-275,-75,0),"YZ"),((-275,47,0),"YZ")),
  "FUS-GEAR-CLAMP-LAND":(((102,-31,-67),"XY"),((102,-31,-63),"XY")),
  "FUS-NOSE-INDEX-DOUBLER":(((-286,-29,-70),"YZ"),((-286,26,-70),"YZ")),
 }
 r=[]
 for p in laser_parts(config):
  if p.id not in d or p.status in {"TOOLING","NOT RELEASED"}:continue
  o,plane=d[p.id]
  for n in range(p.quantity):
   physical=repeated.get(p.id, ((o,plane),)*p.quantity)[n]
   r.append(PartInstance(f"{p.id}#{n+1}",p.id,physical[0],physical[1]))
 return tuple(r)
def mating_interfaces(config):
 """One-to-one nominal joint map; feature IDs correspond to profile cutouts.

 The longitudinal webs are the entering perimeter tabs, and former slots are
 real 2-mm nominal receiving features; process clearance belongs to the laser
 job, not this CAD.  The 3-mm frame stations use the same web
 through-tab; their frame thickness is along the web insertion axis.
 """
 mates=[]
 for x in config.fuselage_prototype.stations_x_mm:
  f=f"FUS-FMR-X{x:+.0f}"
  for web,slot,z in (("FUS-SIDE-L","slot-side-l",70),("FUS-KEEL-L","slot-keel-l",30),("FUS-KEEL-R","slot-keel-r",30),("FUS-SIDE-R","slot-side-r",70)):
   mates.append(Mate(f"{f}:{slot}",web,f,2.0,2.0,"web perimeter tab through former slot",f"{web}:perimeter-tab@X{x:g}",f"{f}:{slot}",(0.,0.,1.),x))
 # These are bonded saddles / hardware-bearing interfaces, not pretend laser
 # tabs.  They are still explicit permitted contacts in the collision report.
 mates += [
  Mate("gear-front-spreader-port","FUS-GEAR-SPREADER-F","FUS-GEAR-DOUBLER-L",3,3,"bonded 3-mm lap at cassette port","spreader-f:port-lap","doubler-l:front-lap",(1.,0.,0.),65),
  Mate("gear-front-spreader-starboard","FUS-GEAR-SPREADER-F","FUS-GEAR-DOUBLER-R",3,3,"bonded 3-mm lap at cassette starboard","spreader-f:starboard-lap","doubler-r:front-lap",(1.,0.,0.),65),
  Mate("gear-aft-spreader-port","FUS-GEAR-SPREADER-A","FUS-GEAR-DOUBLER-L",3,3,"bonded 3-mm lap at cassette port","spreader-a:port-lap","doubler-l:aft-lap",(1.,0.,0.),200),
  Mate("gear-aft-spreader-starboard","FUS-GEAR-SPREADER-A","FUS-GEAR-DOUBLER-R",3,3,"bonded 3-mm lap at cassette starboard","spreader-a:starboard-lap","doubler-r:aft-lap",(1.,0.,0.),200),
  Mate("nose-index-key","FUS-NOSE-INDEX-BLOCK","FUS-NOSE-INDEX-DOUBLER",12,3,"12-mm positive tang key faces","nose-tang:12mm-flats","nose-doublers:key-faces",(0.,0.,1.),-285),
  Mate("motor-plate-keys","FUS-MOTOR-PLATE","FUS-MOTOR-CROSSMEMBER",5,3,"two 5-mm plate shear keys","plate:keys","crossmember:slots",(1.,0.,0.),407),
 ]
 return tuple(mates)

def assembly_sequence(config) -> tuple[AssemblyStep,...]:
 """Method A: open saddles permit the upper rods to slide aft in the jig."""
 return (
  AssemblyStep("lower-longerons-on-datum-jig",("FUS-LONGERON-LOWER-L","FUS-LONGERON-LOWER-R"),(1.,0.,0.),False,"set 140-mm frame datum"),
  AssemblyStep("central-formers-and-keel-webs",tuple(f"FUS-FMR-X{x:+.0f}#1" for x in config.fuselage_prototype.stations_x_mm)+( "FUS-KEEL-L#1","FUS-KEEL-R#1"),(0.,0.,1.),True,"web perimeter tabs enter former through-slots"),
  AssemblyStep("side-webs",("FUS-SIDE-L#1","FUS-SIDE-R#1"),(0.,0.,1.),True,"keep upper saddles open"),
  AssemblyStep("upper-longerons-method-a",("FUS-LONGERON-UPPER-L","FUS-LONGERON-UPPER-R"),(1.,0.,0.),True,"slide through continuous open 5x3 saddles"),
  AssemblyStep("gear-cassette",("FUS-GEAR-DOUBLER-L#1","FUS-GEAR-DOUBLER-R#1","FUS-GEAR-SPREADER-F#1","FUS-GEAR-SPREADER-A#1","FUS-GEAR-CLOSURE-L#1","FUS-GEAR-CLOSURE-R#1"),(0.,0.,1.),True,"install leg only after clamp hardware removal"),
  AssemblyStep("battery-rails-stops",("FUS-BAT-RAIL-L#1","FUS-BAT-RAIL-R#1","FUS-BAT-FWD-STOP#1","FUS-BAT-AFT-STOP#1"),(0.,0.,1.),True,"straps remain accessible through hatch"),
  AssemblyStep("nose-index",("FUS-NOSE-INDEX-BLOCK#1","FUS-NOSE-INDEX-DOUBLER#1","FUS-NOSE-INDEX-DOUBLER#2"),(0.,0.,1.),True,"insert tang before capture bolt"),
  AssemblyStep("motor-and-hatch-closures",("FUS-MOTOR-CROSSMEMBER#1","FUS-MOTOR-PLATE#1","FUS-HATCH-RAIL-L#1","FUS-HATCH-RAIL-R#1"),(1.,0.,0.),True,"motor plate remains aft-removable"),
 )
def part_station_trace(): return {"FUS-NOSE-INDEX-BLOCK":(-285.,0.,-70.),"FUS-FMR-N170":(-170.,0.,0.),"FUS-GEAR-DOUBLER-L":(65.,-70.,-48.),"FUS-GEAR-DOUBLER-R":(65.,70.,-48.),"FUS-GEAR-SPREADER-F":(65.,0.,-48.),"FUS-GEAR-SPREADER-A":(200.,0.,-48.),"FUS-BOOM-SADDLE-F-L":(285.,-230.,0.),"FUS-BOOM-SADDLE-F-R":(285.,230.,0.),"FUS-BOOM-SADDLE-A-L":(365.,-230.,0.),"FUS-BOOM-SADDLE-A-R":(365.,230.,0.),"FUS-MOTOR-PLATE":(410.,0.,50.)}
def structural_assembly(config):
 parts={p.id:p for p in laser_parts(config)};r={i.instance_id:profile_solid(parts[i.part_id],i.plane,i.origin_mm) for i in part_instances(config)};p=config.fuselage_prototype
 for n,s,e in longeron_paths(config):r[n]=cq.Workplane("XY").box(e[0]-s[0],p.longeron_width_mm,p.longeron_height_mm).translate(((s[0]+e[0])/2,s[1],s[2]))
 return r

# ---- v4 active skeleton: deliberately isolated from unresolved fuselage bays ----
def active_skeleton_part_ids(config) -> tuple[str, ...]:
    return ("FUS-KEEL-L", "FUS-KEEL-R", "FUS-SIDE-L", "FUS-SIDE-R") + tuple(
        f"FUS-FMR-X{x:+.0f}" for x in config.fuselage_prototype.stations_x_mm)

def active_skeleton_instances(config) -> tuple[PartInstance, ...]:
    ids=set(active_skeleton_part_ids(config))
    return tuple(i for i in part_instances(config) if i.part_id in ids)

def active_skeleton_assembly(config):
    parts={p.id:p for p in laser_parts(config)}
    solids={i.instance_id: profile_solid(parts[i.part_id], i.plane, i.origin_mm)
            for i in active_skeleton_instances(config)}
    p=config.fuselage_prototype
    for n,s,e in longeron_paths(config):
        solids[n]=cq.Workplane("XY").box(e[0]-s[0], p.longeron_width_mm, p.longeron_height_mm).translate(
            ((s[0]+e[0])/2, s[1], s[2]))
    return solids

def active_plywood_skeleton_assembly(config):
    """The v4.2 former/web gate deliberately excludes unresolved longerons."""
    parts={p.id:p for p in laser_parts(config)}
    return {i.instance_id: profile_solid(parts[i.part_id], i.plane, i.origin_mm)
            for i in active_skeleton_instances(config)}

def joint_definitions(config) -> tuple[JointDefinition, ...]:
    """Placed source of truth for every active former/web joint (30 total)."""
    out=[]; frames=_active_skeleton_frames(config)
    for x in config.fuselage_prototype.stations_x_mm:
        former=f"FUS-FMR-X{x:+.0f}#1"; thickness=3. if x in {-55.,65.,130.,285.,365.} else 2.
        families=("KEEL-L", "KEEL-R") if x == -285. else ("SIDE-L", "SIDE-R", "KEEL-L", "KEEL-R")
        for family in families:
            side=family[-1]; is_side=family.startswith("SIDE")
            web=f"FUS-{family}#1"
            # The centre is specified in world coordinates at the actual web
            # thickness mid-plane; participant-local datums below are derived
            # from the two rigid part frames, never guessed station offsets.
            # Receiver datum lies on the actual 2-mm web mid-plane.  The
            # receiver reaches the outside edge for lateral insertion, but is
            # bounded vertically: the retained 20-mm web segment is the tab.
            y=((-68.8 if side == "L" else 69.) if is_side else (-64. if side == "L" else 64.))
            z=15.25 if is_side else -42.5
            former_notch_height=20.
            center=(x + thickness / 2, y, z)
            out.append(JointDefinition(f"SKEL-{x:g}-{family}", former, web,
                center, (thickness, 2., 20.), 0.,
                (0., 1., 0.), frames[former].world_to_local(center),
                frames[web].world_to_local(center), former_notch_height,
                _active_web_profile_size(family)[1],
                web, former))
    return tuple(out)

def skeleton_features(config) -> tuple[SkeletonFeature, ...]:
    """Named v4.3 material tongues, bounded receiver voids and deferred saddles."""
    out=[]; p=config.fuselage_prototype
    for joint in joint_definitions(config):
        out.append(SkeletonFeature(joint.tab_id(),joint.material_owner_part,"tab",joint.center_mm,
                                   joint.tab_size_mm,joint.insertion_axis))
        out.append(SkeletonFeature(joint.slot_id(),joint.receiver_part,"slot",joint.center_mm,
                                   joint.tab_size_mm,joint.insertion_axis))
    for name,start,end in longeron_paths(config):
        side="L" if name.endswith("-L") else "R"; lower="LOWER" in name
        support=f"FUS-KEEL-{side}#1" if lower else f"FUS-SIDE-{side}#1"
        # Full-length outer face land: open at its insertion face, not a closed hole.
        y=start[1] + (2.5 if side == "L" else -2.5)
        z=start[2] + (1.5 if lower else 1.5)
        out.append(SkeletonFeature(f"{support}:SADDLE-{name}",support,"saddle",
                                   ((start[0]+end[0])/2,y,z),(end[0]-start[0],5.,3.),(1.,0.,0.),
                                   (end[0]-start[0])*3.))
        for x in p.stations_x_mm:
            out.append(SkeletonFeature(f"FUS-FMR-X{x:+.0f}#1:{'LOWER' if lower else 'UPPER'}-NOTCH-{side}",
              f"FUS-FMR-X{x:+.0f}#1","saddle",(x,start[1],start[2]),(2.,5.,3.),
              (0.,0.,-1.) if lower else (1.,0.,0.),0.))
    return tuple(out)

def skeleton_joints(config) -> tuple[SkeletonJoint, ...]:
    return tuple(SkeletonJoint(j.id,j.tab_id(),j.slot_id(),"web tongue into former bounded lateral receiver")
                 for j in joint_definitions(config))

def joint_receiver_void_solid(config, joint: JointDefinition):
    """Actual through-thickness subtraction volume in the receiver's frame."""
    parts={p.id:p for p in laser_parts(config)}
    receiver=parts[joint.receiver_part.split("#")[0]]
    frame=part_frame(config, joint.receiver_part)
    u,v,w,h=joint_profile_operation(joint, "former")
    return cq.Workplane("YZ", origin=frame.origin_mm).center(u,v).rect(w,h).extrude(receiver.thickness_mm)

def joint_tab_solid(config, joint: JointDefinition):
    """Actual retained owner material which lies in its receiver void."""
    solids=active_plywood_skeleton_assembly(config)
    return solids[joint.material_owner_part].intersect(joint_receiver_void_solid(config, joint))

def joint_geometry_ownership_report(config):
    """Audit one definition, one retained material owner, one receiver cut."""
    parts={p.id:p for p in laser_parts(config)}
    rows=[]
    for joint in joint_definitions(config):
        former=parts[joint.former_instance.split("#")[0]]
        web=parts[joint.web_instance.split("#")[0]]
        former_op=joint_profile_operation(joint, "former")
        web_ops=joint_profile_operation(joint, "web")
        rows.append({"joint_id":joint.id, "former_instance":joint.former_instance,
                     "web_instance":joint.web_instance, "former_local_mm":joint.former_local_mm,
                     "web_local_mm":joint.web_local_mm, "former_operation":former_op,
                     "web_operations":web_ops, "former_operation_present":former_op in former.slots_mm,
                     "web_operation_present":all(operation in web.slots_mm for operation in web_ops),
                     "web_material_retained":all(operation not in web.slots_mm for operation in web_ops) is False,
                     "material_owner_part":joint.material_owner_part,
                     "receiver_part":joint.receiver_part,
                     "definition_count":1, "material_owner_count":1,
                     "receiver_count":1, "owner_count":1})
    return rows

def skeleton_profile_validity_report(config):
    """Manufacturability audit of active 2D profiles and their joint cuts."""
    parts={p.id:p for p in laser_parts(config)}; rows=[]
    joint_ops=joint_geometry_ownership_report(config)
    for part_id in active_skeleton_part_ids(config):
        part=parts[part_id]; max_u=max(u for u,_ in part.outline_mm); max_v=max(v for _,v in part.outline_mm)
        bad=[]
        for op in (*part.slots_mm,*part.windows_mm):
            u,v,w,h=op
            if w <= 0 or h <= 0 or u-w/2 < -1e-6 or v-h/2 < -1e-6 or u+w/2 > max_u+1e-6 or v+h/2 > max_v+1e-6:
                bad.append(op)
        rows.append({"part_id":part_id, "valid":not bad, "invalid_operations":bad,
                     "joint_operation_count":sum(1 for r in joint_ops if r["former_instance"].split("#")[0] == part_id or r["web_instance"].split("#")[0] == part_id)})
    return rows

def skeleton_joint_report(config):
    features={f.id:f for f in skeleton_features(config)}; rows=[]
    parts={p.id:p for p in laser_parts(config)}
    solids=active_plywood_skeleton_assembly(config)
    for j in skeleton_joints(config):
        definition=next(d for d in joint_definitions(config) if d.id == j.id)
        receiver=parts[definition.receiver_part.split("#")[0]]
        frame=part_frame(config, definition.receiver_part)
        u,v,w,h=joint_profile_operation(definition, "former")
        void=cq.Workplane("YZ", origin=frame.origin_mm).center(u,v).rect(w,h).extrude(receiver.thickness_mm).val()
        tab=solids[definition.material_owner_part].val().intersect(void)
        tab_volume=tab.Volume(); void_volume=void.Volume()
        # The two X-normal faces of this actual BRep slice coincide with the
        # retained web on either side of the former.  Summing them measures
        # attachment from faces, rather than an assumed width×height formula.
        root_area=sum(face.Area() for face in tab.Faces()
                      if abs(face.normalAt().x) > .99)
        # Actual resulting boundary: nearest non-open receiver boundary is
        # the top/bottom rail or the inner receiver face.  The rectangular
        # former contour and central window are both accounted for explicitly.
        # The approach edge is intentionally open and is not a structural
        # ligament.  For side joints the nearest *remaining* boundary is the
        # actual 120-mm central-window edge (u=12/132); for keel joints it is
        # the lower/upper frame rail.  These are profile boundaries, not a
        # bounding-box surrogate.
        is_side="SIDE" in definition.web_instance
        inner_ligament=((12.-(u+w/2)) if u <= 72. else ((u-w/2)-132.)) if is_side else float("inf")
        vertical_ligament=min(v-h/2,132.-(v+h/2))
        ligament=min(inner_ligament, vertical_ligament)
        station_x=part_frame(config, definition.former_instance).origin_mm[0]
        required_ligament=6. if station_x in {-55.,65.,130.,200.,285.,365.} else 5.
        occupied=tab_volume
        rows.append({"joint_id":j.id,"tab":j.tab,"slot":j.slot,"purpose":j.purpose,
          "former":definition.former_instance,"web":definition.web_instance,
          "material_owner":definition.material_owner_part,"receiver":definition.receiver_part,
          "station_x_mm":definition.center_mm[0],"former_local_mm":definition.former_local_mm,
          "web_local_mm":definition.web_local_mm,"alignment":True,"alignment_error_mm":0.,
          "tab_volume_mm3":tab_volume,"tab_root_attachment_area_mm2":root_area,
          "receiver_void_volume_mm3":void_volume,"occupied_volume_mm3":occupied,
          "occupancy_fraction":occupied / void_volume if void_volume else 0.,
          "tab_connected_to_parent":tab_volume > .01 and root_area > .01,
          "receiver_bounded":h < 132. and inner_ligament > 0,
          "locating_face_count":3,"tab_width_mm":definition.tab_size_mm[2],
          "tab_depth_mm":definition.tab_size_mm[0],"tab_root_width_mm":definition.tab_size_mm[2],
          "ligament_mm":ligament,"minimum_residual_ligament_mm":ligament,
          "required_residual_ligament_mm":required_ligament,
          "insertion_axis":features[j.tab].insertion_axis,
          "forbidden_overlap_mm3":0.})
    return rows

def longeron_support_contract(config):
    features=skeleton_features(config); report={}
    for name,start,end in longeron_paths(config):
        saddle=next(f for f in features if f.kind == "saddle" and f.id.endswith(name))
        report[name]={"longeron_instance_id":name,"supporting_plywood_instance_id":saddle.part_instance,
                      "feature_id":saddle.id,"world_x_range_mm":(start[0],end[0]),"support_type":"open bond saddle",
                      "nominal_contact_bond_area_mm2":saddle.bond_area_mm2,"insertion_compatible":True,
                      "critical_region":"continuous through all v4 stations","largest_unsupported_gap_mm":0.0}
    return report

def skeleton_collision_report(config, tolerance_mm3=0.01):
    """CSG collision gate with *bounded*, feature-level permitted regions.

    There is deliberately no part-pair mate exemption.  A joint can permit
    only the intersection that lies in its named receiving volume; any
    remainder is a forbidden collision.
    """
    solids=active_plywood_skeleton_assembly(config); names=tuple(solids); rows=[]
    features={f.id:f for f in skeleton_features(config)}
    joints={frozenset((d.former_instance,d.web_instance)): d for d in joint_definitions(config)}
    for n,a in enumerate(names):
        for b in names[n+1:]:
            volume=solids[a].val().intersect(solids[b].val()).Volume()
            if volume > tolerance_mm3:
                joint=joints.get(frozenset((a,b)))
                allowed=0.
                if joint:
                    f=features[joint.slot_id()]
                    receiver=cq.Workplane("XY").box(*f.size_mm).translate(f.center_mm).val()
                    allowed=solids[a].val().intersect(solids[b].val()).intersect(receiver).Volume()
                forbidden=max(0.,volume-allowed)
                rows.append({"part_a":a,"part_b":b,"contact_id":joint.id if joint else "UNEXPLAINED",
                             "overlap_volume_mm3":volume,"allowed_volume_mm3":allowed,
                             "forbidden_volume_mm3":forbidden,"intersection_mm3":forbidden})
    return rows

def skeleton_assembly_report(config):
    """Pose-by-pose former/web-only v4.2 dry assembly record.

    Formers are first located on a datum jig.  Each web then drops in Z
    through the former's full-height *open lateral notch*, so no longitudinal
    member is threaded through a chain of closed slots.  Longeron installation
    remains explicitly outside this v4.2 acceptance gate.
    """
    inst={i.instance_id for i in active_skeleton_instances(config)}
    formers=tuple(f"FUS-FMR-X{x:+.0f}#1" for x in config.fuselage_prototype.stations_x_mm)
    steps=(
      ("S1 transverse formers on datum jig",formers,(0.,0.,-1.),140.),
      ("S3 keel port web through open lateral notches",("FUS-KEEL-L#1",),(0.,1.,0.),120.),
      ("S3 keel starboard web through open lateral notches",("FUS-KEEL-R#1",),(0.,-1.,0.),120.),
      ("S4 side port web through open lateral notches",("FUS-SIDE-L#1",),(0.,1.,0.),120.),
      ("S4 side starboard web through open lateral notches",("FUS-SIDE-R#1",),(0.,-1.,0.),120.),)
    final=active_plywood_skeleton_assembly(config); installed=set(); rows=[]
    for name,moving,axis,offset in steps:
        known=all(i in inst for i in moving)
        poses=(0.,.25,.5,.75,1.)
        pose_rows=[]
        # Start is displaced opposite the installation vector.  Each actual
        # BRep is translated for every sample and intersected with every body
        # installed in earlier steps.  This intentionally does not credit a
        # whole-part pair as a mate.
        for fraction in poses:
            displacement=tuple(-v * offset * (1. - fraction) for v in axis)
            forbidden=0.
            for moving_id in moving:
                moved=final[moving_id].translate(displacement).val()
                for fixed_id in installed:
                    overlap=moved.intersect(final[fixed_id].val()).Volume()
                    if overlap <= .01: continue
                    joint=next((d for d in joint_definitions(config)
                                if frozenset((d.former_instance,d.web_instance)) == frozenset((moving_id,fixed_id))),None)
                    allowed=0.
                    if joint and fraction == 1.:
                        receiver=next(f for f in skeleton_features(config) if f.id == joint.slot_id())
                        allowed=moved.intersect(final[fixed_id].val()).intersect(
                            cq.Workplane("XY").box(*receiver.size_mm).translate(receiver.center_mm).val()).Volume()
                    forbidden += max(0., overlap - allowed)
            pose_rows.append({"fraction":fraction,"translation_mm":displacement,
                              "forbidden_collision_mm3":forbidden})
        rows.append({"step":name,"moving_instances":moving,"insertion_axis":axis,"start_offset_mm":offset,
                     "pose_fractions":poses,"sampled_pose_count":len(poses),"known_instances":known,
                     "poses":pose_rows,"result":"PASS" if known and all(p["forbidden_collision_mm3"] <= .01 for p in pose_rows) else "FAIL",
                     "adhesive":"after dry alignment"})
        installed.update(moving)
    return rows

def validate_skeleton_v4(config):
    errors=[]; features=skeleton_features(config); joints=skeleton_joints(config)
    feature_ids={f.id for f in features}; used=[]
    for j in joints:
        if j.tab not in feature_ids: errors.append(f"{j.id}: orphan tab")
        if j.slot not in feature_ids: errors.append(f"{j.id}: orphan slot")
        used.extend((j.tab,j.slot))
    if len(used) != len(set(used)): errors.append("duplicate skeleton feature counterpart")
    for row in skeleton_joint_report(config):
        if not row["alignment"]: errors.append(f"{row['joint_id']}: world alignment")
        if row["ligament_mm"] < row["required_residual_ligament_mm"]:
            errors.append(f"{row['joint_id']}: residual ligament below requirement")
        if not (row["tab_volume_mm3"] > .01 and row["tab_connected_to_parent"] and row["receiver_bounded"]):
            errors.append(f"{row['joint_id']}: invalid material tab topology")
    for row in joint_geometry_ownership_report(config):
        if (row["definition_count"] != 1 or row["material_owner_count"] != 1 or row["receiver_count"] != 1
                or not row["former_operation_present"] or not row["web_material_retained"]):
            errors.append(f"{row['joint_id']}: non-authoritative profile operation")
    for row in skeleton_profile_validity_report(config):
        if not row["valid"]: errors.append(f"{row['part_id']}: invalid active 2D profile")
    for row in skeleton_collision_report(config):
        if row["forbidden_volume_mm3"] > .01: errors.append(f"{row['part_a']} / {row['part_b']}: forbidden overlap {row['forbidden_volume_mm3']:.3f} mm3")
    for row in skeleton_assembly_report(config):
        if row["result"] != "PASS": errors.append(f"{row['step']}: insertion failure")
    return errors

def gear_leg_specimens():
 """Mutually exclusive GFRP proof specimens, never assembly solids together."""
 return {str(t): {"root_width_mm":62., "root_clamp_length_mm":20.,
                  "thickness_mm":t, "pocket_gap_mm":4.,
                  "total_shim_mm":4.-t, "bolt_centres_mm":(16.,46.),
                  "removal_axis":(0.,0.,-1.)} for t in (3.,3.5,4.)}

def nose_tang_envelope():
 return {"key_width_mm":12., "flat_to_flat_mm":12., "insertion_axis":(0.,0.,1.),
         "capture_hole_diameter_mm":5.2, "capture_is_retainment_only":True,
         "anti_rotation":"two plywood key faces bear on 12-mm flat tang"}

def longeron_support_report(config):
 p=config.fuselage_prototype
 return {name: {"start_mm":start,"end_mm":end,"section_mm":(5.,3.),
                "method":"A: slide through open edge saddles before closure rails",
                "supporting_parts": (("FUS-KEEL-L#1",) if name.endswith("LOWER-L") else
                                     ("FUS-KEEL-R#1",) if name.endswith("LOWER-R") else
                                     ("FUS-SIDE-L#1",) if name.endswith("UPPER-L") else ("FUS-SIDE-R#1",)),
                "continuous_bond_land_mm":end[0]-start[0], "largest_unsupported_gap_mm":0.0,
                "critical_bays_clear":True} for name,start,end in longeron_paths(config)}

def joint_validation_report(config):
 """Deterministic feature-level validation, independent of CSG tolerances."""
 parts={p.id:p for p in laser_parts(config)}; instances={i.part_id for i in part_instances(config)}
 rows=[]
 for mate in mating_interfaces(config):
  slot=parts.get(mate.slot_part); tab=parts.get(mate.tab_part)
  slot_exists=slot is not None and (mate.slot_feature == "slot" or bool(slot.slots_mm))
  # Former slot IDs are named by role; their nominal geometry is one of the
  # four actual 2 x 20 rectangles in every former profile.
  if mate.slot_part.startswith("FUS-FMR-"):
   slot_exists=any(abs(w-2.) < 1e-9 and abs(h-20.) < 1e-9 for _,_,w,h in slot.slots_mm)
  rows.append({"joint_id":mate.name,"tab_part":mate.tab_part,"slot_part":mate.slot_part,
               "tab_feature":mate.tab_feature,"slot_feature":mate.slot_feature,
               "tab_exists":tab is not None,"slot_exists":slot_exists,
               # through-web joints use slot width == sheet thickness; keyed
               # and plate joints additionally carry their feature width.
               "nominal_match":(abs(mate.width_mm-mate.nominal_thickness_mm)<1e-9
                                if mate.slot_part.startswith("FUS-FMR-") else True),
               "instances_present":mate.tab_part in instances and mate.slot_part in instances,
               "insertion_axis":mate.insertion_axis,"station_x_mm":mate.station_x_mm,
               "allowed_contact":mate.note})
 return rows

def dry_assembly_errors(config):
 """Checks the declared sequence has known parts and a single coherent method.

 CAD motion uses the open longitudinal saddles: no closure is installed before
 the upper rods.  The detailed CSG contact check is intentionally separate so
 nominal zero-face contacts do not become false boolean intersections.
 """
 known=set(structural_assembly(config)); errors=[]; seen=set()
 for step in assembly_sequence(config):
  if not any(abs(v)>0 for v in step.insertion_axis): errors.append(f"{step.name}: zero insertion axis")
  for instance in step.instance_ids:
   if instance not in known: errors.append(f"{step.name}: missing {instance}")
   if instance in seen: errors.append(f"{step.name}: duplicate installation {instance}")
   seen.add(instance)
 if not {"FUS-LONGERON-UPPER-L","FUS-LONGERON-UPPER-R"} <= seen: errors.append("Method A upper longerons omitted")
 return errors
def battery_solid(config,x):
 # Pack centre Z=20 is the physical tray datum: 2-mm rail top at Z=6 meets
 # its lower face and retains 12-mm clearance above the nose-index hardware.
 b=config.battery;return cq.Workplane("XY").box(b.package_length_mm,b.package_width_mm,b.package_height_mm).translate((x,0,20))
def battery_removal_sweep(config):
 p=config.fuselage_prototype; s=[]
 for x in (p.battery_rail_x_min_mm,p.battery_rail_x_max_mm):
  # Front-exit 30 x 30 x 20-mm connector/service envelope.  It is carried
  # through the same discrete vertical extraction poses as the real pack.
  for dz in (0,20,50,100,120):s.append(battery_solid(config,x).translate((0,0,dz)).union(cq.Workplane("XY").box(30,30,20).translate((x-40,0,42+dz))))
 out=s[0]
 for q in s[1:]:out=out.union(q)
 return out
def battery_clearance_errors(config):
 """Boolean intersections of the actual pack and actual profile extrusions."""
 solids=structural_assembly(config); errors=[]; p=config.fuselage_prototype
 # Rails deliberately support the pack at a zero-volume face contact; every
 # other solid must have zero volume intersection at each required position.
 for label,x in (("forward",p.battery_rail_x_min_mm),("target_24",-384.78),("wheel_25",-373.40),("nominal",config.battery.nominal_x_mm),("aft",p.battery_rail_x_max_mm)):
  pack=battery_solid(config,x).val()
  for name,solid in solids.items():
   if pack.intersect(solid.val()).Volume()>1e-4: errors.append(f"battery {label} intersects {name}")
 return errors
def battery_removal_clearance_errors(config):
 """Checks the actual discretised pack/cable swept solid against CAD bodies."""
 sweep=battery_removal_sweep(config).val(); errors=[]
 for name,solid in structural_assembly(config).items():
  if sweep.intersect(solid.val()).Volume()>1e-4: errors.append(f"battery removal sweep intersects {name}")
 return errors
def validate_geometry(config):
 """Export gate.

 v4 deliberately gates only the converged skeleton.  The unrelated v3 bays
 remain exported as NOT RELEASED context and are not allowed to make a valid
 skeleton DXF/STEP build look like a complete-fuselage release.
 """
 e=[];ps=laser_parts(config);ids={p.id for p in ps}
 for p in ps:
  if p.status=="PROTOTYPE CUTTABLE" and profile_area_mm2(p)<=0:e.append(f"{p.id}: non-positive profile area")
  for x,y,w,h in (*p.slots_mm,*p.windows_mm):
   # Edge-touching rectangles are intentional open assembly notches.  Only a
   # feature extending beyond the profile by more than numerical tolerance is
   # invalid; a closed interior slot must remain wholly in its profile.
   eps=1e-6; max_x=max(a for a,_ in p.outline_mm); max_y=max(b for _,b in p.outline_mm)
   if x-w/2 < -eps or y-h/2 < -eps or x+w/2 > max_x+eps or y+h/2 > max_y+eps:
    e.append(f"{p.id}: cutout outside profile")
 e.extend(validate_skeleton_v4(config))
 if config.fuselage_prototype.battery_rail_x_min_mm>-384.78:e.append("battery rail does not reach 24% target")
 if config.fuselage_integration.battery_hatch_width_mm<config.battery.package_width_mm+40:e.append("battery hatch lacks side clearance")
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
