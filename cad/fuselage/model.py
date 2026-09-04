"""Derived nominal skeleton geometry for the LR1600 fuselage prototype v1.

The module intentionally makes primary laser geometry from the typed aircraft
configuration.  It is a dry-assembly prototype, not a production skin model.
All coordinates are aircraft mm, X aft, Y right, Z up.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from scripts.config import AircraftConfig
import cadquery as cq

Classification = Literal["PRIMARY STRUCTURE", "SECONDARY STRUCTURE", "JIG / TOOLING"]
Status = Literal["PROTOTYPE CUTTABLE", "PROTOTYPE PRINTABLE", "TOOLING", "NOT RELEASED"]


@dataclass(frozen=True)
class LaserPart:
    id: str
    thickness_mm: float
    quantity: int
    outline_mm: tuple[tuple[float, float], ...]
    holes_mm: tuple[tuple[float, float, float], ...]
    classification: Classification
    status: Status
    reason: str
    slots_mm: tuple[tuple[float, float, float, float], ...] = ()


def _rectangle(width: float, height: float) -> tuple[tuple[float, float], ...]:
    return ((0, 0), (width, 0), (width, height), (0, height))


def laser_parts(config: AircraftConfig) -> tuple[LaserPart, ...]:
    p = config.fuselage_prototype
    if not p.is_defined:
        return ()
    # 2-mm webs/formers deliberately stay light.  Slots are nominal 3.2 mm
    # for 3-mm perpendicular webs; final fit comes from the calibration coupon.
    parts: list[LaserPart] = [
        LaserPart("FUS-KEEL-L", 2, 1, _rectangle(840, 54), ((15, 27, 4), (205, 27, 4), (325, 27, 4), (460, 27, 4), (650, 27, 4), (820, 27, 4)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "lower longitudinal shear web, port; continuous from forward battery stop to boom bay"),
        LaserPart("FUS-KEEL-R", 2, 1, _rectangle(840, 54), ((15, 27, 4), (205, 27, 4), (325, 27, 4), (460, 27, 4), (650, 27, 4), (820, 27, 4)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "lower longitudinal shear web, starboard; continuous from forward battery stop to boom bay"),
        LaserPart("FUS-SIDE-L", 2, 1, _rectangle(560, 92), ((150, 18, 3.2), (270, 18, 3.2), (405, 18, 3.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "port upper side shear web"),
        LaserPart("FUS-SIDE-R", 2, 1, _rectangle(560, 92), ((150, 18, 3.2), (270, 18, 3.2), (405, 18, 3.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "starboard upper side shear web"),
        LaserPart("FUS-FMR-N170", 2, 1, _rectangle(132, 128), ((31, 112, 5.2), (101, 112, 5.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "battery rail locating former"),
        LaserPart("FUS-FMR-S200", 2, 1, _rectangle(132, 128), ((31, 112, 5.2), (101, 112, 5.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "servo/avionics shear former"),
        LaserPart("FUS-BAT-RAIL-L", 2, 1, _rectangle(255, 18), ((100, 9, 4), (111, 9, 4), (122, 9, 4), (133, 9, 4), (144, 9, 4), (155, 9, 4)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "battery rail with six 11-mm indexed centres; rail end fixing holes are in N170/W055 formers"),
        LaserPart("FUS-BAT-RAIL-R", 2, 1, _rectangle(255, 18), ((100, 9, 4), (111, 9, 4), (122, 9, 4), (133, 9, 4), (144, 9, 4), (155, 9, 4)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "battery rail with six 11-mm indexed centres; rail end fixing holes are in N170/W055 formers"),
        LaserPart("FUS-BAT-FINE-CLAMP-L", 2, 1, _rectangle(80, 20), ((10, 10, 4.2),), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "port fine-adjust rail clamp; 55-mm continuous slot permits exact CG setting between coarse indices", ((40, 10, 55, 4.2),)),
        LaserPart("FUS-BAT-FINE-CLAMP-R", 2, 1, _rectangle(80, 20), ((10, 10, 4.2),), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "starboard fine-adjust rail clamp; 55-mm continuous slot permits exact CG setting between coarse indices", ((40, 10, 55, 4.2),)),
        LaserPart("FUS-BAT-FWD-STOP", 3, 1, _rectangle(112, 48), ((24, 24, 4.2), (88, 24, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "positive forward pack stop bonded/bolted into continuous lower keel at X=-465 face"),
        LaserPart("FUS-BAT-AFT-STOP", 3, 1, _rectangle(112, 32), ((24, 16, 4.2), (88, 16, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "removable positive aft pack stop indexed to rail; no retention credit from hatch"),
        LaserPart("FUS-BAT-STRAP-ANCHOR-F", 3, 2, _rectangle(28, 42), ((14, 12, 4.2), (14, 30, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "forward independent 20-mm strap anchor pair, 44.4-N proof per strap"),
        LaserPart("FUS-BAT-STRAP-ANCHOR-A", 3, 2, _rectangle(28, 42), ((14, 12, 4.2), (14, 30, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "aft independent 20-mm strap anchor pair, 44.4-N proof per strap"),
        LaserPart("FUS-HATCH-RAIL-L", 2, 1, _rectangle(230, 18), (), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "top opening port primary perimeter rail; overlaps N170 and W055 formers"),
        LaserPart("FUS-HATCH-RAIL-R", 2, 1, _rectangle(230, 18), (), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "top opening starboard primary perimeter rail; overlaps N170 and W055 formers"),
        LaserPart("FUS-SERVO-TRAY", 2, 1, _rectangle(118, 74), ((30, 20, 2.2), (88, 20, 2.2), (30, 54, 2.2), (88, 54, 2.2)), "SECONDARY STRUCTURE", "PROTOTYPE CUTTABLE", "removable three-servo support"),
        LaserPart("FUS-MOTOR-PLATE", 3, 1, _rectangle(p.motor_plate_width_mm, p.motor_plate_height_mm), ((p.motor_plate_width_mm / 2 - 16, p.motor_plate_height_mm / 2 - 16, 3.2), (p.motor_plate_width_mm / 2 + 16, p.motor_plate_height_mm / 2 - 16, 3.2), (p.motor_plate_width_mm / 2 - 16, p.motor_plate_height_mm / 2 + 16, 3.2), (p.motor_plate_width_mm / 2 + 16, p.motor_plate_height_mm / 2 + 16, 3.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "replaceable universal candidate-class motor plate"),
        LaserPart("FUS-GEAR-DOUBLER-L", 3, 1, _rectangle(135, 72), ((24, 36, 4.2), (111, 36, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "main gear double-shear box side, port"),
        LaserPart("FUS-GEAR-DOUBLER-R", 3, 1, _rectangle(135, 72), ((24, 36, 4.2), (111, 36, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "main gear double-shear box side, starboard"),
        LaserPart("FUS-GEAR-SPREADER-F", 3, 1, _rectangle(132, 44), ((35, 22, 4.2), (97, 22, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "main gear root transverse spreader"),
        LaserPart("FUS-GEAR-SPREADER-A", 3, 1, _rectangle(132, 44), ((35, 22, 4.2), (97, 22, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "main gear root transverse spreader"),
        LaserPart("FUS-GEAR-CLAMP-LAND", 3, 2, _rectangle(62, 44), ((16, 22, 4.2), (46, 22, 4.2)), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "replaceable GFRP leg clamp land, two-bolt double shear"),
        LaserPart("FUS-GEAR-SHIM-3P5", 0.5, 2, _rectangle(62, 20), ((16, 10, 4.2), (46, 10, 4.2)), "SECONDARY STRUCTURE", "PROTOTYPE PRINTABLE", "0.5-mm PETG/G10 removable shim for 3.5-mm specimen; not laser plywood"),
        LaserPart("FUS-GEAR-SHIM-4P0", 1.0, 2, _rectangle(62, 20), ((16, 10, 4.2), (46, 10, 4.2)), "SECONDARY STRUCTURE", "PROTOTYPE PRINTABLE", "1.0-mm PETG/G10 removable shim for 4.0-mm specimen; not laser plywood"),
        LaserPart("FUS-NOSE-INDEX-BLOCK", 3, 1, ((0, 0), (46, 0), (46, 52), (29, 52), (29, 64), (17, 64), (17, 52), (0, 52)), ((23, 26, 5.2),), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "positive 12-mm keyed anti-rotation index; no steering freedom"),
        LaserPart("FUS-NOSE-INDEX-DOUBLER", 3, 2, _rectangle(58, 68), ((29, 26, 5.2),), "PRIMARY STRUCTURE", "PROTOTYPE CUTTABLE", "nose strut indexed box doubler"),
        LaserPart("FUS-NOSE-INDEX-TANG-GAUGE", 3, 1, _rectangle(46, 64), ((23, 26, 5.2),), "JIG / TOOLING", "TOOLING", "mating 12-mm tang drilling gauge; flight tang is metal, not printed or plywood"),
        LaserPart("FUS-BOOM-SADDLE-F-L", 3, 1, _rectangle(62, 46), ((31, 23, 4.2),), "PRIMARY STRUCTURE", "NOT RELEASED", "placeholder only: tube OD TBD; no load credit, requires radiused liner/saddle"),
        LaserPart("FUS-BOOM-SADDLE-F-R", 3, 1, _rectangle(62, 46), ((31, 23, 4.2),), "PRIMARY STRUCTURE", "NOT RELEASED", "placeholder only: tube OD TBD; no load credit, requires radiused liner/saddle"),
        LaserPart("FUS-BOOM-SADDLE-A-L", 3, 1, _rectangle(62, 46), ((31, 23, 4.2),), "PRIMARY STRUCTURE", "NOT RELEASED", "placeholder only: tube OD TBD; no load credit, requires radiused liner/saddle"),
        LaserPart("FUS-BOOM-SADDLE-A-R", 3, 1, _rectangle(62, 46), ((31, 23, 4.2),), "PRIMARY STRUCTURE", "NOT RELEASED", "placeholder only: tube OD TBD; no load credit, requires radiused liner/saddle"),
        LaserPart("TOOL-DATUM-FMR", 3, 2, _rectangle(180, 160), ((90, 80, 6),), "JIG / TOOLING", "TOOLING", "removable datum-board former; centre-hole references symmetry line"),
        LaserPart("TOOL-BOOM-GAUGE", 3, 1, _rectangle(540, 80), ((40, 40, 6), (500, 40, 6)), "JIG / TOOLING", "TOOLING", "boom symmetry / 460-mm axis separation gauge"),
    ]
    return tuple(parts)


def longeron_paths(config: AircraftConfig) -> tuple[tuple[str, tuple[float, float, float], tuple[float, float, float]], ...]:
    """Actual 5×3 stock centre paths; cut 10 mm long for trim at assembly."""
    p = config.fuselage_prototype
    y = p.inner_width_mm / 2 - p.longeron_width_mm / 2
    return (
        ("FUS-LONGERON-LOWER-L", (-475, -y, p.lower_keel_z_mm), (365, -y, p.lower_keel_z_mm)),
        ("FUS-LONGERON-LOWER-R", (-475, y, p.lower_keel_z_mm), (365, y, p.lower_keel_z_mm)),
        ("FUS-LONGERON-UPPER-L", (-170, -y, p.upper_longeron_z_mm), (410, -y, p.upper_longeron_z_mm)),
        ("FUS-LONGERON-UPPER-R", (-170, y, p.upper_longeron_z_mm), (410, y, p.upper_longeron_z_mm)),
    )


def part_station_trace() -> dict[str, tuple[float, float, float]]:
    """Assembly datum placements for critical parts (X, Y, Z), never a second editable source."""
    return {
        "FUS-NOSE-INDEX-BLOCK": (-285.0, 0.0, -70.0),
        "FUS-FMR-N170": (-170.0, 0.0, 0.0),
        "FUS-GEAR-DOUBLER-L": (65.0, -70.0, -48.0),
        "FUS-GEAR-DOUBLER-R": (65.0, 70.0, -48.0),
        "FUS-GEAR-SPREADER-F": (65.0, 0.0, -48.0),
        "FUS-GEAR-SPREADER-A": (200.0, 0.0, -48.0),
        "FUS-BOOM-SADDLE-F-L": (285.0, -230.0, 0.0),
        "FUS-BOOM-SADDLE-F-R": (285.0, 230.0, 0.0),
        "FUS-BOOM-SADDLE-A-L": (365.0, -230.0, 0.0),
        "FUS-BOOM-SADDLE-A-R": (365.0, 230.0, 0.0),
        "FUS-MOTOR-PLATE": (410.0, 0.0, 50.0),
    }


def structural_assembly(config: AircraftConfig) -> dict[str, cq.Workplane]:
    """Real nominal assembly solids, keyed to aircraft datums.

    These are intentionally simple solids (not an aerodynamic shell), but every
    named item has a placement and intersects its intended adjoining structure.
    """
    p = config.fuselage_prototype
    solids: dict[str, cq.Workplane] = {}
    # Eight transverse station formers; battery-opening stations are U-webs.
    for x in p.stations_x_mm:
        former = cq.Workplane("YZ").box(2 if x not in {-55, 65, 130, 285, 365} else 3, p.inner_width_mm, 132).translate((x, 0, -4))
        if x in {-285, -170}:
            former = former.cut(cq.Workplane("YZ").box(5, 100, 95).translate((x, 0, 42)))
        solids[f"FUS-FORMER-X{x:+.0f}"] = former
    # Continuous lower shear webs and actual rectangular longerons.
    solids["FUS-LOWER-KEEL"] = cq.Workplane("XY").box(840, p.inner_width_mm, 2).translate((-55, 0, p.lower_keel_z_mm))
    for name, start, end in longeron_paths(config):
        solids[name] = cq.Workplane("XY").box(end[0] - start[0], p.longeron_width_mm, p.longeron_height_mm).translate(((start[0] + end[0]) / 2, start[1], start[2]))
    # 3-mm wing/gear transfer frames and double-shear pocket volume.
    solids["FUS-WING-TRANSFER-FRAME"] = cq.Workplane("XY").box(120, p.inner_width_mm, 92).translate((5, 0, -20))
    solids["FUS-GEAR-BOX"] = cq.Workplane("XY").box(p.main_gear_box_x_max_mm-p.main_gear_box_x_min_mm, 92, 42).translate(((p.main_gear_box_x_max_mm+p.main_gear_box_x_min_mm)/2, 0, -48))
    solids["FUS-GEAR-LEG-POCKET"] = cq.Workplane("XY").box(68, 4.2, 20).translate((132.5, 0, -58))
    # Captured keyed nose socket: mating tang is constrained by 12-mm square key.
    solids["FUS-NOSE-KEY-SOCKET"] = cq.Workplane("XY").box(46, 22, 64).translate((-285, 0, -48)).cut(cq.Workplane("XY").box(12, 24, 18).translate((-285, 0, -20)))
    # Battery tray and stops are solid placements; the hatch/removal corridor is above.
    solids["FUS-BATTERY-TRAY"] = cq.Workplane("XY").box(230, 95, 3).translate((-360, 0, -55))
    solids["FUS-BATTERY-FWD-STOP"] = cq.Workplane("XY").box(3, 95, 35).translate((-465, 0, -38))
    solids["FUS-BATTERY-AFT-STOP"] = cq.Workplane("XY").box(3, 95, 28).translate((-255, 0, -40))
    # Motor cross-member includes shear keys/cooling opening rather than a loose plate.
    solids["FUS-MOTOR-CROSSMEMBER"] = cq.Workplane("XY").box(3, p.motor_plate_width_mm, p.motor_plate_height_mm).translate((365, 0, 50)).cut(cq.Workplane("YZ").circle(22).extrude(5).translate((362.5, 0, 50)))
    solids["FUS-MOTOR-PLATE"] = cq.Workplane("XY").box(3, p.motor_plate_width_mm, p.motor_plate_height_mm).translate((410, 0, 50))
    return solids


def battery_removal_sweep(config: AircraftConfig) -> cq.Workplane:
    """Union of vertical pack sweeps at both rail limits, including 20-mm cable headroom."""
    b, p = config.battery, config.fuselage_prototype
    lower = cq.Workplane("XY").box(b.package_length_mm, b.package_width_mm, 160).translate((p.battery_rail_x_min_mm, 0, 25))
    upper = cq.Workplane("XY").box(b.package_length_mm, b.package_width_mm, 160).translate((p.battery_rail_x_max_mm, 0, 25))
    return lower.union(upper)


def validate_geometry(config: AircraftConfig) -> list[str]:
    """Deterministic manufacturability checks used by build and tests."""
    errors: list[str] = []
    parts = laser_parts(config)
    for part in parts:
        if part.status == "PROTOTYPE CUTTABLE":
            if min(max(x for x, _ in part.outline_mm), max(y for _, y in part.outline_mm)) < 12:
                errors.append(f"{part.id}: fragile minimum outline")
            for x, y, diameter in part.holes_mm:
                if min(x, y, max(px for px, _ in part.outline_mm)-x, max(py for _, py in part.outline_mm)-y) < diameter:
                    errors.append(f"{part.id}: bolt edge distance")
            for x, y, width, height in part.slots_mm:
                # Slot is specified centre/overall size.  Keep a minimum
                # one-slot-height ligament at every outer edge.
                if min(x - width / 2, y - height / 2, max(px for px, _ in part.outline_mm) - (x + width / 2), max(py for _, py in part.outline_mm) - (y + height / 2)) < height:
                    errors.append(f"{part.id}: slot bounds or edge distance")
    if config.fuselage_prototype.battery_rail_x_min_mm > -384.78:
        errors.append("battery rail does not reach 24% target")
    if config.fuselage_integration.battery_hatch_width_mm < config.battery.package_width_mm + 40:
        errors.append("battery hatch lacks side clearance")
    return errors


def mass_estimate(config: AircraftConfig) -> dict[str, float]:
    """Nominal dry CAD mass, explicitly separate from measured/ledger mass.

    Birch is 700 kg/m³ and pultruded carbon 1550 kg/m³; adhesive and hardware
    are explicit 12% and 35-g prototype allowances respectively.
    """
    birch_g_mm3, carbon_g_mm3 = .000700, .001550
    plywood_g = 0.0
    for part in laser_parts(config):
        if part.status != "PROTOTYPE CUTTABLE":
            continue
        width, height = max(x for x, _ in part.outline_mm), max(y for _, y in part.outline_mm)
        area = width * height - sum(3.14159265 * (d / 2) ** 2 for _, _, d in part.holes_mm)
        area -= sum(w * h for _, _, w, h in part.slots_mm)
        plywood_g += area * part.thickness_mm * part.quantity * birch_g_mm3
    carbon_g = sum((end[0] - start[0]) * config.fuselage_prototype.longeron_width_mm * config.fuselage_prototype.longeron_height_mm * carbon_g_mm3 for _, start, end in longeron_paths(config))
    adhesive_g = .12 * (plywood_g + carbon_g)
    hardware_g = 35.0
    return {"birch_dry_g": plywood_g, "carbon_dry_g": carbon_g, "adhesive_allowance_g": adhesive_g, "fastener_allowance_g": hardware_g, "cad_structural_total_g": plywood_g + carbon_g + adhesive_g + hardware_g}
