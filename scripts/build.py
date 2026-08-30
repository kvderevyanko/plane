#!/usr/bin/env python3
"""Build LR1600 reproducible CAD artifacts and validate their scale."""

from __future__ import annotations

import sys
from pathlib import Path

import ezdxf
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from cad.common.calibration_coupon import HEIGHT_MM, WIDTH_MM, generate


def require(condition: bool, message: str) -> None:
    if not condition:
        raise ValueError(message)


def load_and_validate_config(path: Path) -> dict:
    config = yaml.safe_load(path.read_text(encoding="utf-8"))
    require(config["project"]["units"] == "mm", "Project units must be mm")
    require(config["wing"]["span"] > 0, "Wing span must be positive")
    require(config["wing"]["root_chord"] > 0 and config["wing"]["tip_chord"] > 0, "Wing chords must be positive")
    require(0 < config["spar"]["chord_position"] < 1, "Spar position must be a chord fraction")
    require(config["spar"]["outer_diameter"] > config["spar"]["inner_diameter"] > 0, "Invalid spar diameters")
    return config


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
    config = load_and_validate_config(ROOT / "config" / "aircraft.yaml")
    paths = generate(ROOT / "build")
    validate_coupon_dxf(paths["dxf"])
    validate_coupon_svg(paths["svg"])
    print(f"{config['project']['name']}: CAD build passed; calibration coupon is 100.000 × 50.000 mm.")
    for kind, path in paths.items():
        print(f"  {kind}: {path.relative_to(ROOT)} ({path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
