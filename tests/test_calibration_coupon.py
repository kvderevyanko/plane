from pathlib import Path

from cad.common.calibration_coupon import generate
from scripts.build import dxf_bounds_mm, validate_coupon_dxf, validate_coupon_svg
from scripts.config import load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]


def test_aircraft_parameters_are_millimetres():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    assert config.project.units == "mm"
    assert config.wing.span_mm == 1600


def test_coupon_exports_and_scale(tmp_path: Path):
    paths = generate(tmp_path)
    assert all(path.exists() and path.stat().st_size > 0 for path in paths.values())
    validate_coupon_dxf(paths["dxf"])
    validate_coupon_svg(paths["svg"])
    assert dxf_bounds_mm(paths["dxf"]) == (0.0, 0.0, 100.0, 50.0)
