#!/usr/bin/env python3
"""Generate parametric LR1600 wing ribs and inspection drawings.

All dimensions are millimetres.  The generated contours are preliminary
laser-cutting geometry and must be checked against a physical skin/spar sample
before cutting structural parts.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable

try:  # Supports both `python scripts/generate_wing.py` and pytest imports.
    from config import DEFAULT_CONFIG_PATH, AircraftConfig, load_aircraft_config
except ImportError:
    from scripts.config import DEFAULT_CONFIG_PATH, AircraftConfig, load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "generated"


@dataclass(frozen=True)
class WingParameters:
    # Planform
    span_mm: float
    root_chord_mm: float
    tip_chord_mm: float
    airfoil: str
    dihedral_deg_per_panel: float
    tip_washout_deg: float
    twist_axis_fraction: float

    # Structure
    skin_thickness_mm: float
    ordinary_rib_thickness_mm: float
    root_rib_thickness_mm: float
    rib_pitch_mm: float
    spar_fraction: float
    spar_outer_diameter_mm: float
    spar_hole_clearance_mm: float

    # Controls (reference geometry; not cut into the rib at this stage)
    aileron_span_mm: float
    aileron_chord_mm: float
    aileron_inboard_offset_mm: float

    # Flight loads
    aircraft_mass_kg: float
    design_load_factor_g: float
    gravity_m_s2: float

    @property
    def panel_span_mm(self) -> float:
        """Equal removable panels are derived from the full span."""
        return self.span_mm / 2.0


def wing_parameters_from_config(config: AircraftConfig) -> WingParameters:
    """Map the common typed configuration to the generator's complete model."""
    return WingParameters(
        span_mm=config.wing.span_mm,
        root_chord_mm=config.wing.root_chord_mm,
        tip_chord_mm=config.wing.tip_chord_mm,
        airfoil=config.wing.airfoil,
        dihedral_deg_per_panel=config.wing.dihedral_deg_per_panel,
        tip_washout_deg=config.wing.washout_deg,
        twist_axis_fraction=config.wing.twist_axis_fraction,
        skin_thickness_mm=config.materials.skin_foam_mm,
        ordinary_rib_thickness_mm=config.materials.rib_foam_mm,
        root_rib_thickness_mm=config.materials.root_rib_plywood_mm,
        rib_pitch_mm=config.wing.rib_pitch_mm,
        spar_fraction=config.spar.chord_position,
        spar_outer_diameter_mm=config.spar.outer_diameter_mm,
        spar_hole_clearance_mm=config.spar.hole_clearance_mm,
        aileron_span_mm=config.wing.aileron_span_mm,
        aileron_chord_mm=config.wing.aileron_chord_mm,
        aileron_inboard_offset_mm=config.wing.aileron_inboard_offset_mm,
        aircraft_mass_kg=config.aircraft.target_mass_kg,
        design_load_factor_g=config.aircraft.design_load_factor_g,
        gravity_m_s2=config.aircraft.gravity_m_s2,
    )


Point = tuple[float, float]


def read_airfoil(path: Path) -> list[Point]:
    """Read a UIUC .dat file and return one ordered closed-outline point list.

    The supplied Clark Y is in Lednicer's two-surface layout: each surface runs
    from leading edge to trailing edge.  It must be reordered before treating
    it as a polygon.
    """
    groups: list[list[Point]] = []
    current: list[Point] = []
    for line in path.read_text(encoding="ascii").splitlines():
        fields = line.strip().split()
        if not fields:
            if current:
                groups.append(current)
                current = []
            continue
        if len(fields) != 2:
            continue
        try:
            x, z = (float(value) for value in fields)
        except ValueError:
            continue
        # The Clark Y file has a "61 61" point-count line.
        if 0.0 <= x <= 1.0 and -1.0 <= z <= 1.0:
            current.append((x, z))
    if current:
        groups.append(current)
    if len(groups) >= 2 and math.dist(groups[0][0], groups[1][0]) < 1e-9:
        # Upper: LE -> TE, lower: LE -> TE.  Form TE(upper) -> LE -> TE(lower).
        points = list(reversed(groups[0])) + groups[1][1:]
    else:
        points = [point for group in groups for point in group]
    if len(points) < 20:
        raise ValueError(f"Expected airfoil coordinates in {path}, got {len(points)}")
    if math.dist(points[0], points[-1]) < 1e-9:
        points.pop()
    return points


AIRFOIL_FILES = {"clark_y": ROOT / "data" / "airfoils" / "clarky.dat"}


@lru_cache(maxsize=None)
def airfoil_points(name: str) -> tuple[Point, ...]:
    """Resolve the airfoil explicitly selected in aircraft.yaml."""
    try:
        return tuple(read_airfoil(AIRFOIL_FILES[name]))
    except KeyError as error:
        raise ValueError(f"No airfoil file is registered for {name!r}") from error


def signed_area(points: list[Point]) -> float:
    return 0.5 * sum(
        x1 * y2 - x2 * y1
        for (x1, y1), (x2, y2) in zip(points, points[1:] + points[:1])
    )


def unit(vector: Point) -> Point:
    length = math.hypot(*vector)
    if length < 1e-12:
        raise ValueError("Zero-length segment in profile")
    return vector[0] / length, vector[1] / length


def offset_inward(points: list[Point], distance: float) -> list[Point]:
    """Miter-offset a closed profile toward its interior by ``distance``.

    This represents the inner surface of a constant-thickness sheet.  At the
    sharp trailing edge and tight leading edge this remains an engineering
    approximation, intentionally flagged in docs/wing.md for sample fitting.
    """
    orientation = 1.0 if signed_area(points) > 0 else -1.0
    result: list[Point] = []
    count = len(points)
    for index, current in enumerate(points):
        previous = points[(index - 1) % count]
        following = points[(index + 1) % count]
        prev_dir = unit((current[0] - previous[0], current[1] - previous[1]))
        next_dir = unit((following[0] - current[0], following[1] - current[1]))
        # Left normal for CCW, right normal for CW, both point to the interior.
        n_prev = (-prev_dir[1] * orientation, prev_dir[0] * orientation)
        n_next = (-next_dir[1] * orientation, next_dir[0] * orientation)
        miter = unit((n_prev[0] + n_next[0], n_prev[1] + n_next[1]))
        denominator = max(0.1, abs(miter[0] * n_next[0] + miter[1] * n_next[1]))
        result.append((current[0] + miter[0] * distance / denominator,
                       current[1] + miter[1] * distance / denominator))
    return result


def chord_at(span_station_mm: float, p: WingParameters) -> float:
    return p.root_chord_mm + (p.tip_chord_mm - p.root_chord_mm) * span_station_mm / p.panel_span_mm


def washout_at(span_station_mm: float, p: WingParameters) -> float:
    return p.tip_washout_deg * span_station_mm / p.panel_span_mm


def rotate(point: Point, degrees: float, origin: Point) -> Point:
    radians = math.radians(degrees)
    cosine, sine = math.cos(radians), math.sin(radians)
    x, z = point[0] - origin[0], point[1] - origin[1]
    return (origin[0] + x * cosine - z * sine,
            origin[1] + x * sine + z * cosine)


def airfoil_at_chord(chord_mm: float, twist_deg: float, p: WingParameters) -> list[Point]:
    """Scale the exact normalized Clark Y coordinates to a chord and twist it."""
    scaled = [(x * chord_mm, z * chord_mm) for x, z in airfoil_points(p.airfoil)]
    axis = (p.twist_axis_fraction * chord_mm, 0.0)
    return [rotate(point, twist_deg, axis) for point in scaled]


def rib_contour(station_mm: float, p: WingParameters) -> list[Point]:
    """Return the rib outside contour, i.e. the inside face of the 3 mm skins."""
    chord = chord_at(station_mm, p)
    theoretical = airfoil_at_chord(chord, washout_at(station_mm, p), p)
    return offset_inward(theoretical, p.skin_thickness_mm)


def camber_z_at(x: float, chord_mm: float, twist_deg: float, p: WingParameters) -> float:
    """Linearly interpolate the mean line, after profile scaling and twist."""
    profile = airfoil_at_chord(chord_mm, twist_deg, p)
    # The reordered polygon runs upper TE -> LE -> lower TE. Find intersections
    # on the whole polygon; vertical-line crossings give upper/lower surfaces.
    crossings: list[float] = []
    for a, b in zip(profile, profile[1:] + profile[:1]):
        if min(a[0], b[0]) <= x <= max(a[0], b[0]) and abs(a[0] - b[0]) > 1e-9:
            fraction = (x - a[0]) / (b[0] - a[0])
            crossings.append(a[1] + fraction * (b[1] - a[1]))
    if len(crossings) < 2:
        # At a sharp endpoint use nearest available point; spar never uses this.
        return min(profile, key=lambda q: abs(q[0] - x))[1]
    return (min(crossings) + max(crossings)) / 2.0


def spar_center(station_mm: float, p: WingParameters) -> Point:
    chord = chord_at(station_mm, p)
    twist = washout_at(station_mm, p)
    x = p.spar_fraction * chord
    return x, camber_z_at(x, chord, twist, p)


def rib_stations(p: WingParameters) -> list[float]:
    bays = round(p.panel_span_mm / p.rib_pitch_mm)
    if not math.isclose(bays * p.rib_pitch_mm, p.panel_span_mm, abs_tol=1e-6):
        raise ValueError("panel_span_mm must be an integer multiple of rib_pitch_mm")
    return [index * p.rib_pitch_mm for index in range(bays + 1)]


def svg_path(points: Iterable[Point]) -> str:
    points = list(points)
    return "M " + " L ".join(f"{x:.3f},{-z:.3f}" for x, z in points) + " Z"


def write_svg(path: Path, outline: list[Point], spar: Point, title: str,
              p: WingParameters) -> None:
    xs, zs = zip(*outline)
    radius = p.spar_outer_diameter_mm / 2.0 + p.spar_hole_clearance_mm
    margin = 12.0
    min_x, max_x = min(xs) - margin, max(xs) + margin
    min_y, max_y = -max(zs) - margin, -min(zs) + margin
    width, height = max_x - min_x, max_y - min_y
    path.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" height="{height:.3f}mm" viewBox="{min_x:.3f} {min_y:.3f} {width:.3f} {height:.3f}">
  <title>{title}</title>
  <g fill="none" stroke="#000000" stroke-width="0.1">
    <path d="{svg_path(outline)}"/>
    <circle cx="{spar[0]:.3f}" cy="{-spar[1]:.3f}" r="{radius:.3f}"/>
  </g>
  <text x="{min_x + 2:.3f}" y="{min_y + 5:.3f}" font-size="3" fill="#000">{title}</text>
</svg>
''', encoding="utf-8")


def dxf_polyline(points: list[Point], layer: str = "CUT") -> str:
    pairs = ["0\nLWPOLYLINE\n8\n" + layer + "\n90\n" + str(len(points)) + "\n70\n1\n"]
    for x, z in points:
        pairs.append(f"10\n{x:.5f}\n20\n{-z:.5f}\n")
    return "".join(pairs)


def write_dxf(path: Path, outline: list[Point], spar: Point, p: WingParameters) -> None:
    radius = p.spar_outer_diameter_mm / 2.0 + p.spar_hole_clearance_mm
    body = dxf_polyline(outline)
    body += f"0\nCIRCLE\n8\nCUT\n10\n{spar[0]:.5f}\n20\n{-spar[1]:.5f}\n40\n{radius:.5f}\n"
    header = "0\nSECTION\n2\nHEADER\n9\n$INSUNITS\n70\n4\n0\nENDSEC\n"
    path.write_text(header + "0\nSECTION\n2\nENTITIES\n" + body + "0\nENDSEC\n0\nEOF\n", encoding="ascii")


def write_plan_svg(path: Path, stations: list[float], p: WingParameters) -> None:
    margin = 40.0
    width, height = p.root_chord_mm + 2 * margin, p.panel_span_mm + 2 * margin
    root_x = margin
    def leading_edge(y: float) -> float:
        return root_x + 0.5 * (p.root_chord_mm - chord_at(y, p))
    lines = []
    for y in stations:
        x = leading_edge(y)
        chord = chord_at(y, p)
        lines.append(f'<line x1="{x:.3f}" y1="{margin + y:.3f}" x2="{x + chord:.3f}" y2="{margin + y:.3f}"/>')
    aileron_y0 = p.aileron_inboard_offset_mm
    aileron_y1 = aileron_y0 + p.aileron_span_mm
    aileron_x0 = leading_edge(aileron_y0) + chord_at(aileron_y0, p) - p.aileron_chord_mm
    aileron_x1 = leading_edge(aileron_y1) + chord_at(aileron_y1, p) - p.aileron_chord_mm
    outline = [(leading_edge(0), margin), (leading_edge(p.panel_span_mm), margin + p.panel_span_mm),
               (leading_edge(p.panel_span_mm) + p.tip_chord_mm, margin + p.panel_span_mm),
               (leading_edge(0) + p.root_chord_mm, margin)]
    path.write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}mm" height="{height:.3f}mm" viewBox="0 0 {width:.3f} {height:.3f}">
  <title>LR1600 one-panel plan view</title>
  <g fill="none" stroke="#000" stroke-width="0.2"><path d="M {' L '.join(f'{x:.3f},{y:.3f}' for x,y in outline)} Z"/>{''.join(lines)}</g>
  <line x1="{aileron_x0:.3f}" y1="{margin + aileron_y0:.3f}" x2="{aileron_x1:.3f}" y2="{margin + aileron_y1:.3f}" stroke="#d00" stroke-width="0.4"/>
  <text x="5" y="15" font-size="7">One removable panel — 800 mm; red: proposed aileron hinge line</text>
</svg>
''', encoding="utf-8")


def write_manifest(path: Path, stations: list[float], p: WingParameters) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["id", "station_mm", "chord_mm", "washout_deg", "dihedral_z_mm", "spar_x_mm", "spar_z_mm", "material", "thickness_mm"])
        writer.writeheader()
        for index, station in enumerate(stations):
            material = "birch plywood (root reinforcement)" if index == 0 else "foam"
            thickness = p.root_rib_thickness_mm if index == 0 else p.ordinary_rib_thickness_mm
            spar_x, spar_z = spar_center(station, p)
            writer.writerow({
                "id": f"R{index:02d}", "station_mm": f"{station:.3f}",
                "chord_mm": f"{chord_at(station, p):.3f}", "washout_deg": f"{washout_at(station, p):.4f}",
                "dihedral_z_mm": f"{station * math.tan(math.radians(p.dihedral_deg_per_panel)):.3f}",
                "spar_x_mm": f"{spar_x:.3f}", "spar_z_mm": f"{spar_z:.3f}",
                "material": material, "thickness_mm": f"{thickness:.3f}",
            })


def write_wing_stations(path: Path, stations: list[float], p: WingParameters) -> None:
    """Write the full-wing reference geometry; y and z are relative to centreline."""
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=["panel", "rib_id", "y_mm", "z_dihedral_mm", "chord_mm", "washout_deg", "leading_edge_x_mm", "spar_x_mm", "spar_z_mm"])
        writer.writeheader()
        for sign, panel in ((-1.0, "LH"), (1.0, "RH")):
            for index, station in enumerate(stations):
                chord = chord_at(station, p)
                spar_x, spar_z = spar_center(station, p)
                writer.writerow({
                    "panel": panel, "rib_id": f"R{index:02d}", "y_mm": f"{sign * station:.3f}",
                    "z_dihedral_mm": f"{station * math.tan(math.radians(p.dihedral_deg_per_panel)):.3f}",
                    "chord_mm": f"{chord:.3f}", "washout_deg": f"{washout_at(station, p):.4f}",
                    # Centre the trapezoid on its root chord for unambiguous 3-D placement.
                    "leading_edge_x_mm": f"{(p.root_chord_mm - chord) / 2.0:.3f}",
                    "spar_x_mm": f"{spar_x:.3f}", "spar_z_mm": f"{spar_z:.3f}",
                })


def generate(config_path: Path = DEFAULT_CONFIG_PATH, output: Path = OUTPUT) -> WingParameters:
    """Generate wing artifacts from YAML and return the exact model used."""
    parameters = wing_parameters_from_config(load_aircraft_config(config_path))
    output.mkdir(parents=True, exist_ok=True)
    # Delete only generator-owned detail files, so a changed rib pitch cannot
    # leave stale laser files alongside the rebuilt set.
    for pattern in ("rib_*.svg", "rib_*.dxf"):
        for old_file in output.glob(pattern):
            old_file.unlink()
    stations = rib_stations(parameters)
    for index, station in enumerate(stations):
        contour = rib_contour(station, parameters)
        spar = spar_center(station, parameters)
        chord = chord_at(station, parameters)
        twist = washout_at(station, parameters)
        suffix = "root" if index == 0 else "tip" if index == len(stations) - 1 else f"station_{station:03.0f}"
        title = f"LR1600 R{index:02d} {suffix}: chord {chord:.1f} mm, twist {twist:.3f} deg"
        write_svg(output / f"rib_{index:02d}_{suffix}.svg", contour, spar, title, parameters)
        write_dxf(output / f"rib_{index:02d}_{suffix}.dxf", contour, spar, parameters)
    write_plan_svg(output / "panel_plan.svg", stations, parameters)
    write_manifest(output / "rib_manifest.csv", stations, parameters)
    write_wing_stations(output / "wing_stations.csv", stations, parameters)
    (output / "parameters.json").write_text(json.dumps(asdict(parameters), ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return parameters


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LR1600 wing artifacts from aircraft.yaml")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT)
    args = parser.parse_args()
    parameters = generate(args.config, args.output)
    print(f"Generated {len(rib_stations(parameters))} ribs in {args.output}/")


if __name__ == "__main__":
    main()
