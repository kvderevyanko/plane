#!/usr/bin/env python3
"""Generate reproducible LR1600 *test-only* material-validation articles.

No aircraft production geometry is emitted.  DXF and SVG nominal geometry is
in millimetres; article dimensions are owned by cad/test_coupons/parameters.yaml.
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path
from typing import Iterable

import ezdxf
import yaml
import cadquery as cq

try:
    from config import DEFAULT_CONFIG_PATH, load_aircraft_config
    from generate_wing import airfoil_at_chord
except ImportError:
    from scripts.config import DEFAULT_CONFIG_PATH, load_aircraft_config
    from scripts.generate_wing import airfoil_at_chord

ROOT = Path(__file__).resolve().parents[1]
PARAMETERS = ROOT / "cad" / "test_coupons" / "parameters.yaml"
DEFAULT_OUTPUT = ROOT / "generated" / "test_coupons"
WARNING = "TEST-ONLY / NOMINAL / NO KERF / NOT FLIGHT PART"

def load_test_parameters(path: Path = PARAMETERS) -> dict:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("units") != "mm":
        raise ValueError("test-coupon parameters must be a mm mapping")
    return data

def rect(x: float, y: float, width: float, height: float) -> list[tuple[float, float]]:
    return [(x,y), (x+width,y), (x+width,y+height), (x,y+height)]

def write_dxf(path: Path, polygons: Iterable[list[tuple[float,float]]], circles: Iterable[tuple[float,float,float]] = (), scores: Iterable[tuple[tuple[float,float],tuple[float,float]]] = ()) -> None:
    doc = ezdxf.new("R2010"); doc.header["$INSUNITS"] = 4; space = doc.modelspace()
    for polygon in polygons: space.add_lwpolyline(polygon, close=True, dxfattribs={"layer":"TEST_CUT"})
    for x,y,r in circles: space.add_circle((x,y), r, dxfattribs={"layer":"TEST_CUT"})
    for start, end in scores: space.add_line(start, end, dxfattribs={"layer":"TEST_SCORE"})
    doc.saveas(path)

def write_svg(path: Path, polygons: Iterable[list[tuple[float,float]]], circles: Iterable[tuple[float,float,float]] = (), scores: Iterable[tuple[tuple[float,float],tuple[float,float]]] = ()) -> None:
    polygons, circles, scores = list(polygons), list(circles), list(scores)
    all_points = [p for poly in polygons for p in poly] + [(x-r,y-r) for x,y,r in circles] + [(x+r,y+r) for x,y,r in circles]
    lo_x, lo_y = min(x for x,_ in all_points), min(y for _,y in all_points); hi_x, hi_y = max(x for x,_ in all_points), max(y for _,y in all_points)
    width, height = hi_x-lo_x, hi_y-lo_y
    paths = ''.join('<path d="M '+' L '.join(f'{x:.3f},{height-(y-lo_y):.3f}' for x,y in poly)+' Z"/>' for poly in polygons)
    holes = ''.join(f'<circle cx="{x-lo_x:.3f}" cy="{height-(y-lo_y):.3f}" r="{r:.3f}"/>' for x,y,r in circles)
    score_svg = ''.join(f'<line x1="{a[0]-lo_x:.3f}" y1="{height-(a[1]-lo_y):.3f}" x2="{b[0]-lo_x:.3f}" y2="{height-(b[1]-lo_y):.3f}" stroke="#06c" stroke-dasharray="1,1"/>' for a,b in scores)
    path.write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" height="{height:.3f}mm" viewBox="0 0 {width:.3f} {height:.3f}"><title>{WARNING}</title><g fill="none" stroke="#000" stroke-width="0.1">{paths}{holes}</g>{score_svg}</svg>\n', encoding="utf-8")

def emit(output: Path, name: str, polygons: list[list[tuple[float,float]]], circles: list[tuple[float,float,float]], material: str, quantity: int, purpose: str, records: list[dict], scores: list[tuple[tuple[float,float],tuple[float,float]]] | None = None) -> None:
    write_dxf(output / f"{name}.dxf", polygons, circles, scores or []); write_svg(output / f"{name}.svg", polygons, circles, scores or [])
    xs=[x for p in polygons for x,_ in p]; ys=[y for p in polygons for _,y in p]
    records.append({"id":name,"material":material,"quantity":quantity,"purpose":purpose,"warning":WARNING,"width_mm":round(max(xs)-min(xs),3),"height_mm":round(max(ys)-min(ys),3),"dxf":f"{name}.dxf","svg":f"{name}.svg"})

def write_stl(path: Path, solid: cq.Workplane) -> None:
    """STL exports are restricted to disposable printed test pieces."""
    cq.exporters.export(solid, str(path))
    if not path.is_file() or path.stat().st_size == 0:
        raise RuntimeError(f"STL export failed: {path}")

def _deduplicate(points: list[tuple[float, float]]) -> list[tuple[float, float]]:
    result: list[tuple[float, float]] = []
    for point in points:
        if not result or math.dist(point, result[-1]) > 1e-9:
            result.append(point)
    return result

def dbox_root_geometry(config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, object]:
    """Return exact root Clark-Y LE-to-spar closed-cell geometry in mm.

    The two airfoil surfaces are intersected analytically at the spar x; no
    test-artifact dimension is hardcoded from a previous generated snapshot.
    """
    cfg = load_aircraft_config(config_path)
    chord = cfg.wing.root_chord_mm
    spar_x = cfg.spar.chord_position * chord
    parameters = type("AirfoilParameters", (), {"airfoil": cfg.wing.airfoil, "twist_axis_fraction": cfg.wing.twist_axis_fraction})()
    profile = airfoil_at_chord(chord, 0.0, parameters)
    le_index = min(range(len(profile)), key=lambda i: profile[i][0])
    upper, lower = profile[:le_index + 1], profile[le_index:]

    def at_spar(surface: list[tuple[float, float]]) -> tuple[float, float]:
        hits: list[float] = []
        for a, b in zip(surface, surface[1:]):
            if min(a[0], b[0]) <= spar_x <= max(a[0], b[0]) and not math.isclose(a[0], b[0]):
                hits.append(a[1] + (b[1] - a[1]) * (spar_x - a[0]) / (b[0] - a[0]))
        if not hits:
            raise ValueError("Clark-Y surface did not intersect configured spar station")
        return spar_x, sum(hits) / len(hits)

    upper_spar, lower_spar = at_spar(upper), at_spar(lower)
    upper_path = _deduplicate([upper_spar, *[point for point in upper if point[0] < spar_x]])
    lower_path = _deduplicate([*[point for point in lower if point[0] < spar_x], lower_spar])
    # upper spar → LE → lower spar; DXF closure is the birch spar closure.
    skin_path = _deduplicate(upper_path + lower_path)
    upper_developed = sum(math.dist(a, b) for a, b in zip(upper_path, upper_path[1:]))
    lower_developed = sum(math.dist(a, b) for a, b in zip(lower_path, lower_path[1:]))
    skin_developed = upper_developed + lower_developed
    closure = abs(upper_spar[1] - lower_spar[1])
    return {
        "root_chord_mm": chord, "spar_x_mm": spar_x,
        "upper_spar_z_mm": upper_spar[1], "lower_spar_z_mm": lower_spar[1],
        "closure_height_mm": closure, "skin_developed_length_mm": skin_developed,
        "upper_skin_developed_length_mm": upper_developed, "lower_skin_developed_length_mm": lower_developed,
        "skin_path": skin_path, "closed_rib_outline": skin_path + [upper_spar],
    }

def generate(config_path: Path = DEFAULT_CONFIG_PATH, output: Path = DEFAULT_OUTPUT, parameters_path: Path = PARAMETERS) -> dict[str, Path]:
    cfg = load_aircraft_config(config_path); p = load_test_parameters(parameters_path); output.mkdir(parents=True, exist_ok=True)
    for old in output.glob("*.*"): old.unlink()
    rec: list[dict] = []
    for side in p["density_squares_mm"]:
        emit(output, f"MAT-DENS-{side}", [rect(0,0,side,side)], [], "foam or plywood; cut n>=3 per material", 3, "density coupon", rec)
    bend=p["plywood_bend"]
    plywood_materials = {"POPLAR2": "poplar 2 mm", "BIRCH2": "birch 2 mm", "BIRCH3": "birch 3 mm"}
    for plywood in plywood_materials:
        for grain, description in (("FACE-GRAIN-LONG", "face grain parallel to strip"), ("FACE-GRAIN-CROSS", "face grain transverse to strip")):
            emit(output, f"PLY-BEND-240x25-{plywood}-{grain}", [rect(0,0,bend["length_mm"],bend["width_mm"])], [], plywood_materials[plywood], 3, f"three-point bending strip; {description}", rec)
    bear=p["plywood_bearing"]; circles=[(25+i*25,bear["width_mm"]/2,d/2) for i,d in enumerate(bear["hole_diameters_mm"])]
    for plywood in plywood_materials:
        for grain, description in (("FACE-GRAIN-LONG", "face grain parallel to strip"), ("FACE-GRAIN-CROSS", "face grain transverse to strip")):
            emit(output, f"PLY-BEAR-100x30-{plywood}-{grain}", [rect(0,0,bear["length_mm"],bear["width_mm"])], circles, plywood_materials[plywood], 3, f"bearing and hole-crushing coupon; {description}", rec)
    lap=p["glue_lap"]
    for family, material in (("FF", "foam to foam"), ("FB", "foam to birch 2"), ("BB", "birch 2 to birch 2"), ("CB", "carbon tube to birch 2 fixture stock")):
        emit(output, f"GLUE-{family}-LAP-160x25", [rect(0,0,lap["length_mm"],lap["width_mm"])], [], material, 3, "lap-joint strip; blue TEST_SCORE marks the 25x25 registration overlap", rec, [((0,0),(25,0)),((25,0),(25,25))])
    # 14-mm cradle pair and catches: birch-3 fixture parts, not flight hardware.
    cradle=[rect(0,0,50,35)]; emit(output,"SPAR-EI-CRADLE-14",cradle,[(25,27,7)],"birch 3",2,"14-mm spar support/centre saddle, drill/cut opening",rec)
    emit(output,"SPAR-EI-GUARDED-CATCH",[rect(0,0,60,50)],[],"birch 3 / foam padding",2,"catch below spar; fixture only",rec)
    # Joiner printed rings only establish rough handling fit; never acceptance gauges.
    for diameter in p["joiner_gauges_mm"]:
        emit(output,f"JOINER-ROUGH-RING-{diameter:.2f}",[rect(0,0,24,24)],[(12,12,diameter/2)],"3D-print or laser test gauge",1,"ROUGH fit indication only; verify actual rod by caliper",rec)
        write_stl(output / f"JOINER-ROUGH-RING-{diameter:.2f}.stl", cq.Workplane("XY").circle(12).circle(diameter/2).extrude(5))
    sf=p["socket_fixture"]; emit(output,"SOCKET-BIRCH2-PLATE",[rect(0,0,sf["plate_length_mm"],sf["plate_width_mm"])],[],"birch 2",4,"representative joiner/socket plate template",rec)
    emit(output,"SOCKET-GUARDED-FIXTURE",[rect(0,0,160,80)],[],"birch 3 fixture stock",2,"shielded socket proof-test fixture side plate",rec)
    # D-box geometry is always derived at generation time from typed config.
    dbox_geometry = dbox_root_geometry(config_path)
    dbox = dbox_geometry["closed_rib_outline"]
    skin_length = dbox_geometry["skin_developed_length_mm"]
    closure_height = dbox_geometry["closure_height_mm"]
    # Test-only trim allowance permits hand fitting at both skin/closure edges.
    closure_blank_height = closure_height + 2.5
    for variant, material in (("A","foam-only control"),("B","foam + light +/-45 glass candidate"),("C","foam + +/-45 carbon candidate")):
        for station in p["dbox"]["rib_stations_mm"]:
            role = "end bulkhead" if station in (0, p["dbox"]["span_mm"]) else "internal rib"
            emit(output,f"DBOX-{variant}-RIB-X{station:03.0f}",[dbox],[],"foam 5 for ribs",1,f"{p['dbox']['span_mm']:.0f}-mm closed D-box bay {role} at x={station:.0f} mm; variant {variant}: {material}",rec)
        emit(output,f"DBOX-{variant}-BIRCH2-CLOSURE",[rect(0,0,p["dbox"]["span_mm"],closure_blank_height)],[],"birch 2",1,f"spar closure raw height {closure_height:.3f} mm + 2.5-mm test trim allowance; variant {variant}: {material}",rec)
        emit(output,f"DBOX-{variant}-FOAM3-UPPER-SKIN",[rect(0,0,p["dbox"]["span_mm"],dbox_geometry["upper_skin_developed_length_mm"])],[],"foam 3",1,f"upper-surface developed root Clark-Y skin; variant {variant}: {material}",rec)
        emit(output,f"DBOX-{variant}-FOAM3-LOWER-SKIN",[rect(0,0,p["dbox"]["span_mm"],dbox_geometry["lower_skin_developed_length_mm"])],[],"foam 3",1,f"lower-surface developed root Clark-Y skin; variant {variant}: {material}",rec)
        emit(output,f"DBOX-{variant}-BIRCH3-END-BULKHEAD",[dbox],[],"birch 3 test-fixture material",2,"stiff end bulkheads/clamp interfaces at x=0 and x=300; TEST ARTICLE ONLY",rec)
    emit(output,"DBOX-TORQUE-ARM-250",[rect(0,0,250,25)],[(15,12.5,3)],"birch 3 test-fixture material",1,"250-mm torque arm for closed-cell GJ test; fixture only",rec)
    emit(output,"DBOX-GUARDED-TORSION-FIXTURE",[rect(0,0,140,100)],[],"birch 3 test-fixture material",2,"guarded fixed/free-end fixture plates for closed-cell torsion test",rec)
    lw=p["lw_rib_test"]; tab=lw["end_tab_mm"]
    lw_outline=[(0,0),(tab,0),(tab,(lw["height_mm"]-10)/2),(lw["length_mm"]-tab,(lw["height_mm"]-10)/2),(lw["length_mm"]-tab,0),(lw["length_mm"],0),(lw["length_mm"],lw["height_mm"]),(lw["length_mm"]-tab,lw["height_mm"]),(lw["length_mm"]-tab,(lw["height_mm"]+10)/2),(tab,(lw["height_mm"]+10)/2),(tab,lw["height_mm"]),(0,lw["height_mm"])]
    emit(output,"LW-RIB-TEST-180x20",[lw_outline],[],"LW-PLA print reference",3,"180x20x2 rib-like coupon with 10-mm end tabs; see print manifest",rec)
    # A deliberately simple printed rib-like beam: material characterization,
    # not a flight rib.  The printed wall/infill specification is in its manifest.
    # Build the same reduced-waist/tab geometry as a 2-mm solid reference;
    # slicer walls/infill below define the actual printable specimen.
    points=[(x,z) for x,z in lw_outline]
    write_stl(output / "LW-RIB-TEST-180x20.stl", cq.Workplane("XZ").polyline(points).close().extrude(lw["thickness_mm"]))
    (output/"lw_rib_test_manifest.json").write_text(json.dumps({"id":"LW-RIB-TEST-180x20","quantity":3,"geometry_mm":lw,"recommended_start":{"layer_height_mm":0.20,"line_width_mm":0.45,"walls":3,"infill":"10-15% gyroid at end-tab transitions only; otherwise no infill","orientation":"layers normal to the rib plane"},"status":"TEST CANDIDATE ONLY; filament temperature and flow are user inputs"},indent=2)+"\n",encoding="utf-8")
    with (output/"manifest.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rec[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rec)
    dbox_manifest = {"warning": WARNING, "article_kind":"actual root closed cell; measured GJ of the complete article, not effective material G", "variant_annotations": {"A":"foam-only control", "B":"foam + light +/-45 glass candidate", "C":"foam + +/-45 carbon candidate"}, "geometry_from_typed_aircraft_loader": {key: value for key, value in dbox_geometry.items() if key not in {"skin_path", "closed_rib_outline"}}, "span_mm": p["dbox"]["span_mm"], "rib_stations_mm": p["dbox"]["rib_stations_mm"], "flight_representative_constituents":{"foam3_upper_skin":1,"foam3_lower_skin":1,"foam5_contour_ribs":4,"birch2_spar_closure":1,"reinforcement":"variant-specific","retained_adhesive_resin":"measured"}, "test_fixture_only_constituents":{"birch3_end_bulkheads_clamp_interfaces":2,"torque_arm_250mm":"shared removable fixture","guarded_torsion_fixture":"shared removable fixture"}, "mass_recording": {"required_fields_g": ["foam_skin_before_g", "foam_ribs_before_g", "birch_closure_before_g", "reinforcement_dry_g", "retained_adhesive_resin_g", "complete_article_mass_g", "fixture_mass_g", "flight_representative_mass_g"], "definitions":{"complete_article_mass_g":"weighed assembled test D-box, including any attached birch-3 end bulkheads/clamp interfaces but excluding separate torque arm/guard unless deliberately attached","fixture_mass_g":"mass of all test-fixture-only material included in complete_article_mass_g; record zero only if none is included","flight_representative_mass_g":"complete_article_mass_g - fixture_mass_g; this is the only complete-article mass eligible for wing scaling","external_fixture_mass_g":"optional record for removable torque arm/guard; never include in flight_representative_mass_g"}, "scaling_basis":"Scale only flight_representative_mass_g for this exact root closed-cell geometry; never scale fixture-only mass into the wing budget."}}
    (output/"dbox_article_manifest.json").write_text(json.dumps(dbox_manifest, indent=2)+"\n",encoding="utf-8")
    (output/"README.txt").write_text(f"{WARNING}\nGenerated from cad/test_coupons/parameters.yaml. DBOX root profile/chord/spar and all developed dimensions come only from typed config/aircraft.yaml.\n",encoding="utf-8")
    return {"manifest":output/"manifest.csv", "readme":output/"README.txt", "dbox":output/"DBOX-A-RIB-X000.svg"}

if __name__ == "__main__":
    result=generate(); print(f"Generated test-only coupon files in {DEFAULT_OUTPUT} ({result['manifest'].name})")
