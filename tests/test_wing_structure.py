import math
from pathlib import Path

import pytest

from scripts.analyze_wing_structure import (
    analyze,
    cantilever_deflection,
    elliptic_load,
    proof_schedule,
    solid_rod_properties,
    tube_properties,
)
from scripts.config import load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]


def test_14x12_section_properties_have_expected_si_values():
    props = tube_properties(.014, .012)
    assert props["area_m2"] * 1e6 == pytest.approx(40.8407, rel=1e-5)
    assert props["second_moment_m4"] * 1e12 == pytest.approx(867.865, rel=1e-5)
    assert props["section_modulus_m3"] * 1e9 == pytest.approx(123.981, rel=1e-5)
    assert solid_rod_properties(.0115)["area_m2"] > props["area_m2"]


def test_elliptic_load_integrates_and_has_expected_root_moment():
    load = elliptic_load(.8, 47.07192)
    assert load["shear_n"][0] == pytest.approx(47.07192, rel=2e-5)
    assert load["moment_nm"][0] == pytest.approx(47.07192 * 4 * .8 / (3 * math.pi), rel=3e-4)
    assert load["moment_nm"][-1] == 0.0
    assert all(left >= right for left, right in zip(load["moment_nm"], load["moment_nm"][1:]))


def test_zero_load_and_deflection_sanity():
    load = elliptic_load(.8, 0.0)
    assert max(load["q_n_m"] + load["shear_n"] + load["moment_nm"]) == 0.0
    assert cantilever_deflection(load["moment_nm"], .001, 70e9, 1e-9)[-1] == 0.0
    nonzero = elliptic_load(.8, 40.0)
    delta = cantilever_deflection(nonzero["moment_nm"], .001, 70e9, 8.68e-10)
    assert delta[-1] > 0
    assert delta[-1] < .1


def test_deflection_integrator_matches_independent_uniform_load_cantilever_formula():
    length, distributed_load, modulus, second_moment, points = .8, 30.0, 70e9, 8.68e-10, 801
    spacing = length / (points - 1)
    moment = [distributed_load * (length - index * spacing) ** 2 / 2 for index in range(points)]
    numerical = cantilever_deflection(moment, spacing, modulus, second_moment)[-1]
    analytical = distributed_load * length**4 / (8 * modulus * second_moment)
    assert numerical == pytest.approx(analytical, rel=2e-5)


def test_proof_schedule_preserves_distributed_panel_load():
    load = elliptic_load(.8, 47.07192)
    zones = proof_schedule(load, 9.80665)
    assert len(zones) == 5
    assert sum(zone["load_at_100_percent_n"] for zone in zones) == pytest.approx(47.07192, rel=2e-5)
    assert zones[0]["load_at_100_percent_n"] > zones[-1]["load_at_100_percent_n"]


def test_analysis_reads_typed_yaml_not_generated_snapshot(tmp_path: Path):
    source = (ROOT / "scripts/analyze_wing_structure.py").read_text(encoding="utf-8")
    assert "generated/parameters.json" not in source
    changed = tmp_path / "aircraft.yaml"
    changed.write_text((ROOT / "config/aircraft.yaml").read_text(encoding="utf-8").replace("target_mass_g: 2600", "target_mass_g: 2500"), encoding="utf-8")
    result, _ = analyze(load_aircraft_config(changed))
    assert result["load_case"]["design_total_lift_n"] == pytest.approx(2.5 * 9.80665 * 4)
    assert result["main_spar"]["root_bending_moment_nm"] > 16


def test_current_material_availability_and_structural_high_finding_regressions():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    assert config.materials.plywood_structural_mm == (2.0, 3.0)
    result, _ = analyze(config)
    budget = result["mass_budget"]["items_g"]
    expected_skin_low = 4 * (.8 * (.25 + .2) / 2) * .003 * 30 * 1000
    assert budget["foam_3mm_skins_top_and_bottom"][0] == pytest.approx(expected_skin_low)
    assert result["dbox_twist_screening"]["cm_abs"] == pytest.approx(.0839)
    assert result["dbox_twist_screening"]["speed_cases_deg"]["100"]["reinforced_dbox_minimum_g300_deg"] < 2.01
    socket = result["joiner"]["socket_screening"]
    assert socket["minimum_tube_wall_mm"] == pytest.approx(.9)
    assert socket["screening_sf"]["birch_net_tension"] > 1.5
