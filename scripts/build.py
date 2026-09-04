#!/usr/bin/env python3
"""Build LR1600 reproducible CAD artifacts and validate their scale."""

from __future__ import annotations

import sys
from pathlib import Path

import ezdxf

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cad.common.calibration_coupon import HEIGHT_MM, WIDTH_MM, generate
from cad.fuselage.generate import generate as generate_fuselage
from scripts.config import load_aircraft_config
from scripts.generate_test_coupons import generate as generate_test_coupons
from scripts.generate_previews import generate_previews
from scripts.generate_wing import generate as generate_wing
from scripts.mass_properties import calculate_mass_properties


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def dxf_bounds_mm(path: Path) -> tuple[float, float, float, float]:
    document = ezdxf.readfile(path)
    require(document.header.get("$INSUNITS") == 4, "DXF units must be millimetres")
    points: list[tuple[float, float]] = []
    for entity in document.modelspace():
        if entity.dxftype() == "LWPOLYLINE":
            points.extend((float(vertex[0]), float(vertex[1])) for vertex in entity.get_points())
            require(entity.closed, "Every laser polyline must be closed")
        elif entity.dxftype() == "CIRCLE":
            center, radius = entity.dxf.center, float(entity.dxf.radius)
            points.extend(((center.x - radius, center.y), (center.x + radius, center.y), (center.x, center.y - radius), (center.x, center.y + radius)))
        else:
            raise ValueError(f"Unsupported laser entity: {entity.dxftype()}")
    min_x, min_y = min(x for x, _ in points), min(y for _, y in points)
    max_x, max_y = max(x for x, _ in points), max(y for _, y in points)
    return min_x, min_y, max_x, max_y


def validate_coupon_dxf(path: Path) -> None:
    min_x, min_y, max_x, max_y = dxf_bounds_mm(path)
    tolerance = 0.001
    require(abs(min_x) < tolerance and abs(min_y) < tolerance, "DXF origin changed")
    require(abs((max_x - min_x) - WIDTH_MM) < tolerance, "DXF width is not 100 mm")
    require(abs((max_y - min_y) - HEIGHT_MM) < tolerance, "DXF height is not 50 mm")


def validate_coupon_svg(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    require('width="100.0mm"' in text and 'height="50.0mm"' in text, "SVG physical dimensions must be 100 × 50 mm")
    require('viewBox="0 0 100.0 50.0"' in text, "SVG viewBox mismatch")


def main() -> None:
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    mass_properties = calculate_mass_properties(config.mass_budget.components)
    paths = generate(ROOT / "build")
    fuselage_paths = generate_fuselage(ROOT)
    # Keep inspection drawings in sync with YAML before making their disposable
    # preview copies.  Neither output feeds a CAD generator.
    generate_wing(ROOT / "config" / "aircraft.yaml", ROOT / "generated")
    generate_test_coupons(ROOT / "config" / "aircraft.yaml", ROOT / "generated" / "test_coupons")
    previews = generate_previews(ROOT / "generated", ROOT / "generated" / "previews")
    validate_coupon_dxf(paths["dxf"])
    validate_coupon_svg(paths["svg"])
    print(f"{config.project.name}: CAD build passed; calibration coupon is 100.000 × 50.000 mm.")
    if mass_properties.is_final_aircraft_cg:
        print(
            "  mass properties: "
            f"{mass_properties.total_mass_g:.3f} g; CG "
            f"({mass_properties.x_cg_mm:.3f}, {mass_properties.y_cg_mm:.3f}, {mass_properties.z_cg_mm:.3f}) mm"
        )
    else:
        unresolved = ", ".join(component.id for component in mass_properties.unresolved_components)
        print(
            "  mass properties: aircraft CG is not final; "
            f"known subtotal {mass_properties.total_mass_g:.3f} g; unresolved: {unresolved or 'none'}"
        )
    for kind, path in paths.items():
        print(f"  {kind}: {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    for kind, path in fuselage_paths.items():
        print(f"  fuselage {kind}: {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")
    print(f"  previews: {previews['index'].relative_to(ROOT)}")


if __name__ == "__main__":
    main()
