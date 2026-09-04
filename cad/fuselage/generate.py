"""Build laser and printable artifacts for the LR1600 fuselage prototype v1."""
from __future__ import annotations

import csv
import json
from pathlib import Path

import cadquery as cq
from cadquery import exporters
import ezdxf

from cad.fuselage.model import (LaserPart, assembly_mass_properties,
                                battery_removal_sweep, laser_parts, longeron_paths,
                                mating_interfaces, part_instances, part_station_trace,
                                structural_assembly, validate_geometry, mass_estimate,
                                assembly_sequence, dry_assembly_errors,
                                gear_leg_specimens, joint_validation_report,
                                longeron_support_report, nose_tang_envelope)
from scripts.config import load_aircraft_config


def _add_part(document: ezdxf.document.Drawing, part: LaserPart, offset: float) -> None:
    msp = document.modelspace()
    msp.add_lwpolyline([(x + offset, y) for x, y in part.outline_mm], close=True, dxfattribs={"layer": "CUT"})
    for x, y, diameter in part.holes_mm:
        msp.add_circle((x + offset, y), diameter / 2, dxfattribs={"layer": "CUT"})
    for x, y, width, height in (*part.slots_mm, *part.windows_mm):
        half_w, half_h = width / 2, height / 2
        msp.add_lwpolyline([(x + offset - half_w, y - half_h), (x + offset + half_w, y - half_h), (x + offset + half_w, y + half_h), (x + offset - half_w, y + half_h)], close=True, dxfattribs={"layer": "CUT"})
    msp.add_text(part.id, dxfattribs={"height": 4, "layer": "ETCH"}).set_placement((offset, -8))


def _write_sheet(parts: tuple[LaserPart, ...], path: Path) -> None:
    document = ezdxf.new("R2010")
    document.header["$INSUNITS"] = 4
    document.layers.add("CUT", color=1)
    document.layers.add("ETCH", color=3)
    offset = 0.0
    for part in parts:
        _add_part(document, part, offset)
        offset += max(x for x, _ in part.outline_mm) + 18.0
    path.parent.mkdir(parents=True, exist_ok=True)
    document.saveas(path)


def _battery_dummy(config) -> cq.Workplane:
    b = config.battery
    return cq.Workplane("XY").box(b.package_length_mm, b.package_width_mm, b.package_height_mm).edges().fillet(2)


def _prop_gauge(config) -> cq.Workplane:
    return cq.Workplane("YZ").circle(config.ground_operations.propeller_diameter_mm / 2).circle(10).extrude(3)


def _gear_shim(thickness_mm: float) -> cq.Workplane:
    return cq.Workplane("XY").box(62, 20, thickness_mm).faces(">Z").workplane().pushPoints([(-15, 0), (15, 0)]).hole(4.2)


def generate(root: Path) -> dict[str, Path]:
    """Generate downstream prototype artifacts; source geometry remains nominal."""
    config = load_aircraft_config(root / "config" / "aircraft.yaml")
    errors = validate_geometry(config)
    if errors:
        raise ValueError("fuselage prototype geometry invalid: " + "; ".join(errors))
    parts = laser_parts(config)
    laser = root / "build" / "fuselage" / "laser"
    paths = {
        "laser_2mm": laser / "2mm_birch" / "LR1600-fuselage-prototype-v1-2mm.dxf",
        "laser_3mm": laser / "3mm_birch" / "LR1600-fuselage-prototype-v1-3mm.dxf",
        "tooling": laser / "tooling" / "LR1600-fuselage-prototype-v1-tooling-3mm.dxf",
        "manifest": root / "build" / "fuselage" / "fuselage-prototype-v1-manifest.csv",
        "battery_dummy_stl": root / "build" / "fuselage" / "printable" / "FUS-BATTERY-DUMMY-P60B.stl",
        "prop_gauge_stl": root / "build" / "fuselage" / "printable" / "TOOL-PROP-13IN-CLEARANCE-GAUGE.stl",
        "gear_shim_3p5_stl": root / "build" / "fuselage" / "printable" / "FUS-GEAR-SHIM-3P5-0p5mm.stl",
        "gear_shim_4p0_stl": root / "build" / "fuselage" / "printable" / "FUS-GEAR-SHIM-4P0-1p0mm.stl",
        "assembly_step": root / "build" / "fuselage" / "step" / "LR1600-fuselage-prototype-v1-assembly.step",
        "assembly_svg": root / "build" / "fuselage" / "drawings" / "LR1600-fuselage-prototype-v1-assembly.svg",
    }
    _write_sheet(tuple(p for p in parts if p.thickness_mm == 2), paths["laser_2mm"])
    _write_sheet(tuple(p for p in parts if p.thickness_mm == 3 and p.status == "PROTOTYPE CUTTABLE"), paths["laser_3mm"])
    _write_sheet(tuple(p for p in parts if p.status == "TOOLING"), paths["tooling"])
    paths["manifest"].parent.mkdir(parents=True, exist_ok=True)
    with paths["manifest"].open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=("id", "thickness_mm", "quantity", "classification", "status", "profile_hash", "reason"))
        writer.writeheader()
        for part in parts:
            writer.writerow({"id": part.id, "thickness_mm": part.thickness_mm, "quantity": part.quantity, "classification": part.classification, "status": part.status, "profile_hash": part.profile_hash(), "reason": part.reason})
    assembly = structural_assembly(config)
    compound = cq.Compound.makeCompound([solid.val() for solid in assembly.values()])
    paths["assembly_step"].parent.mkdir(parents=True, exist_ok=True)
    exporters.export(compound, str(paths["assembly_step"]))
    paths["assembly_svg"].parent.mkdir(parents=True, exist_ok=True)
    paths["assembly_svg"].write_text("""<svg xmlns=\"http://www.w3.org/2000/svg\" width=\"910mm\" height=\"190mm\" viewBox=\"-500 -95 910 190\"><style>text{font:8px sans-serif}.p{fill:none;stroke:#183a55;stroke-width:2}.d{stroke:#b44;stroke-width:1}</style><rect class=\"p\" x=\"-500\" y=\"-90\" width=\"910\" height=\"180\"/><line class=\"d\" x1=\"-475\" y1=\"-68\" x2=\"365\" y2=\"-68\"/><line class=\"d\" x1=\"-475\" y1=\"68\" x2=\"365\" y2=\"68\"/><rect class=\"p\" x=\"-465\" y=\"-48\" width=\"210\" height=\"96\"/><rect class=\"p\" x=\"65\" y=\"-46\" width=\"135\" height=\"92\"/><line class=\"d\" x1=\"285\" y1=\"-90\" x2=\"285\" y2=\"90\"/><line class=\"d\" x1=\"365\" y1=\"-90\" x2=\"365\" y2=\"90\"/><text x=\"-460\" y=\"-58\">BATTERY TRAY / STOPS</text><text x=\"70\" y=\"-54\">MAIN GEAR BOX</text><text x=\"285\" y=\"-82\">BOOM STATIONS</text><text x=\"370\" y=\"40\">MOTOR CROSS-MEMBER</text></svg>""", encoding="utf-8")
    definitions = {part.id: {"profile_hash": part.profile_hash(), "thickness_mm": part.thickness_mm, "quantity": part.quantity, "status": part.status, "classification": part.classification, "include_flight_mass": part.include_flight_mass} for part in parts}
    instance_map = {}
    for instance in part_instances(config):
        instance_map.setdefault(instance.part_id, []).append({"instance_id": instance.instance_id, "origin_mm": instance.origin_mm, "plane": instance.plane})
    summary = {"status": "PROTOTYPE V3 — NOT RELEASED PENDING INDEPENDENT REVIEW", "geometry_contract": "DXF profile == STEP extrusion == geometry mass profile", "battery_rail_usable_centres_mm": [config.fuselage_prototype.battery_rail_x_min_mm, config.fuselage_prototype.battery_rail_x_max_mm], "part_station_trace_mm": part_station_trace(), "part_definitions": definitions, "part_instances": instance_map, "assembly_components": list(assembly), "mating_interfaces": [mate.__dict__ for mate in mating_interfaces(config)], "joint_validation": joint_validation_report(config), "dry_assembly_errors": dry_assembly_errors(config), "assembly_sequence": [step.__dict__ for step in assembly_sequence(config)], "longeron_support_report": longeron_support_report(config), "gear_leg_specimens": gear_leg_specimens(), "nose_tang_envelope": nose_tang_envelope(), "battery_removal_sweep_bbox_mm": [battery_removal_sweep(config).val().BoundingBox().xlen, battery_removal_sweep(config).val().BoundingBox().ylen, battery_removal_sweep(config).val().BoundingBox().zlen], "cad_mass_estimate_g": mass_estimate(config), "cad_mass_properties": assembly_mass_properties(config), "longerons": [{"id": n, "start_mm": a, "end_mm": b} for n, a, b in longeron_paths(config)]}
    paths["manifest"].with_suffix(".json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    paths["battery_dummy_stl"].parent.mkdir(parents=True, exist_ok=True)
    exporters.export(_battery_dummy(config), str(paths["battery_dummy_stl"]))
    exporters.export(_prop_gauge(config), str(paths["prop_gauge_stl"]))
    exporters.export(_gear_shim(.5), str(paths["gear_shim_3p5_stl"]))
    exporters.export(_gear_shim(1.0), str(paths["gear_shim_4p0_stl"]))
    return paths
