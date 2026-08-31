from pathlib import Path

from scripts.generate_previews import DETAIL_FILES, TEST_DETAIL_FILES, VIEW_FILES, generate_previews
from scripts.generate_test_coupons import dbox_root_geometry, generate as generate_test_coupons
from scripts.generate_wing import generate as generate_wing


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "aircraft.yaml"


def test_preview_generation_is_disposable_and_contains_current_drawings(tmp_path: Path):
    generated = tmp_path / "generated"
    generate_wing(CONFIG, generated)
    generate_test_coupons(CONFIG, generated / "test_coupons")
    previews = generated / "previews"
    paths = generate_previews(generated, previews)

    assert set(VIEW_FILES).issubset(paths)
    assert paths["index"].name == "index.html"
    assert all(path.is_file() and path.stat().st_size > 0 for path in paths.values())
    index = paths["index"].read_text(encoding="utf-8")
    for filename in [*VIEW_FILES.values(), *DETAIL_FILES.values(), *TEST_DETAIL_FILES.values()]:
        assert filename in index
    for filename in DETAIL_FILES.values():
        assert (previews / filename).read_bytes() == (generated / filename).read_bytes()


def test_test_coupon_generation_is_nominal_and_uses_typed_aircraft_geometry(tmp_path: Path):
    output = tmp_path / "test_coupons"
    paths = generate_test_coupons(CONFIG, output)
    manifest = paths["manifest"].read_text(encoding="utf-8")
    assert "TEST-ONLY / NOMINAL / NO KERF / NOT FLIGHT PART" in manifest
    assert "MAT-DENS-100" in manifest and "DBOX-A-RIB-X000" in manifest
    assert "GLUE-CB-LAP-160x25" in manifest and "PLY-BEND-240x25-BIRCH2-FACE-GRAIN-LONG" in manifest
    assert (output / "DBOX-A-RIB-X000.dxf").is_file()
    assert (output / "DBOX-A-FOAM3-UPPER-SKIN.dxf").is_file()
    assert (output / "DBOX-TORQUE-ARM-250.dxf").is_file()
    dbox_manifest = (output / "dbox_article_manifest.json").read_text(encoding="utf-8")
    assert "flight_representative_constituents" in dbox_manifest
    assert "fixture_mass_g" in dbox_manifest
    assert 'width="100.000mm"' in (output / "MAT-DENS-100.svg").read_text(encoding="utf-8")


def test_dbox_root_geometry_is_intersected_from_typed_clark_y_profile():
    geometry = dbox_root_geometry(CONFIG)
    assert geometry["root_chord_mm"] == 250.0
    assert geometry["spar_x_mm"] == 75.0
    assert abs(geometry["upper_spar_z_mm"] - 22.6701) < 0.001
    assert abs(geometry["lower_spar_z_mm"] + 6.576975) < 0.001
    assert abs(geometry["closure_height_mm"] - 29.247075) < 0.001
    assert abs(geometry["skin_developed_length_mm"] - 158.914915) < 0.001
    assert abs(geometry["upper_skin_developed_length_mm"] + geometry["lower_skin_developed_length_mm"] - geometry["skin_developed_length_mm"]) < 1e-9


def test_preview_code_has_no_aircraft_parameter_or_snapshot_input():
    source = (ROOT / "scripts" / "generate_previews.py").read_text(encoding="utf-8")
    assert "load_aircraft_config" not in source
    assert "parameters.json" not in source
