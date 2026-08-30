from pathlib import Path

import pytest

from scripts.config import load_aircraft_config
from scripts.run_airfoil_analysis import AIRFOIL, cleanup_raw_side_artifacts, engineering_ncrit5_estimates, load_airfoil_coordinates, merge_direct_sweeps, reliable_pre_peak_rows, required_cl, reynolds_number, sha256, stall_speed_m_s


ROOT = Path(__file__).resolve().parents[1]


def test_clark_y_coordinates_are_normalized_and_immutable_source_file():
    coordinates = load_airfoil_coordinates(AIRFOIL)
    assert len(coordinates) == 122
    assert coordinates[0] == (0.0, 0.0)
    assert max(x for x, _ in coordinates) == pytest.approx(1.0)
    assert sha256(AIRFOIL) == "bd1822f02d71bf66357774ec58279ff26f75f911414cded2fb34cafd15935f13"


def test_reynolds_required_cl_and_stall_speed_have_si_dimensions():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    assert reynolds_number(50 / 3.6, config.wing.mean_aerodynamic_chord_mm / 1000) == pytest.approx(214862, rel=3e-4)
    assert required_cl(config.aircraft.target_mass_kg, 70 / 3.6, config.wing.area_m2, config.aircraft.gravity_m_s2) == pytest.approx(.2824, rel=2e-3)
    assert stall_speed_m_s(config.aircraft.target_mass_kg, config.wing.area_m2, 1.0, config.aircraft.gravity_m_s2) * 3.6 == pytest.approx(37.20, rel=2e-3)


def test_analysis_uses_typed_yaml_config_not_generated_snapshot(tmp_path: Path):
    config_path = tmp_path / "aircraft.yaml"
    config_path.write_text((ROOT / "config/aircraft.yaml").read_text(encoding="utf-8").replace("target_mass_g: 2400", "target_mass_g: 2500"), encoding="utf-8")
    config = load_aircraft_config(config_path)
    assert config.aircraft.target_mass_kg == 2.5
    assert config.wing.area_m2 == pytest.approx(.36)


def test_analysis_code_has_no_generated_snapshot_input_dependency():
    source = (ROOT / "scripts/run_airfoil_analysis.py").read_text(encoding="utf-8")
    assert "generated/parameters.json" not in source
    assert "load_aircraft_config(DEFAULT_CONFIG_PATH)" in source


def test_stall_branch_excludes_post_peak_xfoil_points():
    rows = [{"alpha_deg": 8.0, "cl": 1.1}, {"alpha_deg": 10.0, "cl": 1.3}, {"alpha_deg": 12.0, "cl": 1.2}]
    assert reliable_pre_peak_rows(rows) == rows[:2]


def test_direct_reverse_sweep_only_fills_missing_raw_alpha_rows(tmp_path: Path):
    base = {"cd": .01, "cm": -.05, "cdp": .008, "xtr_top": .8, "xtr_bottom": .8}
    forward = {"reynolds": 150000, "scenario": "realistic_model", "sweep": "forward", "raw_polar": "forward.polar", "input": "forward.in", "log": "forward.log", "metrics": {"points": 1, "missing_alpha_deg": [1.0]}, "rows": [{**base, "alpha_deg": 0.0, "cl": .2}]}
    reverse = {"reynolds": 150000, "scenario": "realistic_model", "sweep": "reverse", "raw_polar": "reverse.polar", "input": "reverse.in", "log": "reverse.log", "metrics": {}, "rows": [{**base, "alpha_deg": 0.0, "cl": .1}, {**base, "alpha_deg": 1.0, "cl": .3}]}
    result = merge_direct_sweeps(forward, reverse, tmp_path)
    assert [(row["alpha_deg"], row["cl"], row["source"]) for row in result["rows"]] == [(0.0, .2, "forward"), (1.0, .3, "reverse")]
    assert result["forward_metrics"] == forward["metrics"]
    assert result["metrics"]["points"] == 2
    assert result["metrics"]["last_converged_alpha_deg"] == 1.0
    assert result["metrics"]["reverse_only_points"] == 1
    assert 1.0 not in result["metrics"]["missing_alpha_deg"]
    assert b"\r\n" not in (tmp_path / "parsed" / "clarky_re150000_realistic_model_combined.csv").read_bytes()


def test_cleanup_raw_side_artifacts_preserves_only_documented_names(tmp_path: Path):
    raw = tmp_path / "raw"; raw.mkdir()
    allowed = ["clarky.xfoil.dat", "clarky_re150000_clean.in", "clarky_re150000_clean.log", "clarky_re150000_realistic_model_reverse.polar"]
    for name in allowed + [":00.bl", "clarky_re150000_reali", "junk"]: (raw / name).write_text("x")
    cleanup_raw_side_artifacts(tmp_path)
    assert sorted(path.name for path in raw.iterdir()) == sorted(allowed)


def test_engineering_ncrit5_estimate_has_documented_raw_factor_and_formula():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    cases = [
        {"scenario": "clean", "reynolds": 200000, "metrics": {"reliable_pre_peak_clmax": 1.3965}},
        {"scenario": "realistic_model", "reynolds": 200000, "metrics": {"reliable_pre_peak_clmax": 1.3716}},
    ]
    estimate = engineering_ncrit5_estimates(config, cases, 1.163)
    assert estimate["ncrit_factor"] == pytest.approx(1.3716 / 1.3965)
    assert estimate["scenarios"]["nominal"]["clmax_wing"] == pytest.approx(1.126, abs=.002)
    assert estimate["classification"].startswith("engineering sensitivity")
