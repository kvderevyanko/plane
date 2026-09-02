import json
from pathlib import Path

import pytest

from scripts.analyze_wing_aero_mass_sensitivity import build_summary, write_outputs
from scripts.config import load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]


def test_2600g_aero_sensitivity_keeps_canonical_mass_and_scales_required_cl():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    assert config.aircraft.target_mass_g == 2400
    summary = build_summary()
    reference = summary["cases"]["2400g"]
    sensitivity = summary["cases"]["2600g"]
    assert reference["wing_loading_g_dm2"] == pytest.approx(66.6667, rel=1e-5)
    assert sensitivity["wing_loading_g_dm2"] == pytest.approx(72.2222, rel=1e-5)
    for reference_point, sensitivity_point in zip(reference["points"], sensitivity["points"]):
        assert sensitivity_point["required_cl"] / reference_point["required_cl"] == pytest.approx(2600 / 2400)


def test_aero_sensitivity_reproduces_stalls_and_drag_direction():
    summary = build_summary()
    reference = summary["cases"]["2400g"]
    sensitivity = summary["cases"]["2600g"]
    assert reference["strict_clean_stall"]["speed_km_h"] == pytest.approx(34.49, abs=.03)
    assert sensitivity["strict_clean_stall"]["speed_km_h"] == pytest.approx(35.91, abs=.03)
    assert reference["conservative_realistic_stall_engineering_sensitivity"] == pytest.approx(37.55, abs=.03)
    assert sensitivity["conservative_realistic_stall_engineering_sensitivity"] == pytest.approx(39.09, abs=.03)
    assert sensitivity["points"][0]["induced_drag_n"] > reference["points"][0]["induced_drag_n"]
    assert sensitivity["points"][-1]["total_wing_drag_n"] > reference["points"][-1]["total_wing_drag_n"]


def test_aero_mass_sensitivity_outputs_are_consistent(tmp_path: Path):
    summary = build_summary()
    output = tmp_path / "aero_mass.json"
    write_outputs(summary, output)
    saved = json.loads(output.read_text(encoding="utf-8"))
    lines = output.with_suffix(".csv").read_text(encoding="utf-8").splitlines()
    assert saved["scope"]["canonical_target_mass_g"] == 2400
    assert len(lines) == 11
    assert "total_wing_drag_n" in lines[0]
