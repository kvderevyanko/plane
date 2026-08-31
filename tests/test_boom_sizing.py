from pathlib import Path

import pytest

from scripts.boom_sizing import (CANDIDATES, candidate_analysis, cantilever_point_response, dynamic_pressure,
                                 make_summary, required_boom_center_spacing_mm, tube_properties)
from scripts.config import load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]


def test_circular_tube_properties_and_beam_response_are_physical():
    properties = tube_properties(.018, .016)
    assert properties["area_m2"] * 1e6 == pytest.approx(53.4071, rel=1e-5)
    assert properties["second_moment_m4"] * 1e12 == pytest.approx(1936.0065, rel=1e-5)
    response = cantilever_point_response(10, .65, 70e9, properties["second_moment_m4"])
    assert response["root_moment_nm"] == pytest.approx(6.5)
    assert response["tip_deflection_m"] > 0


@pytest.mark.parametrize("call", [lambda: tube_properties(.016, .016), lambda: tube_properties(-.016, .014), lambda: dynamic_pressure(0), lambda: required_boom_center_spacing_mm(0, 20, 30)])
def test_invalid_inputs_fail_loudly(call):
    with pytest.raises(ValueError):
        call()


def test_larger_propeller_needs_equal_or_greater_radial_clearance():
    ten_in = required_boom_center_spacing_mm(254, 20, 30)
    fourteen_in = required_boom_center_spacing_mm(355.6, 20, 30)
    assert fourteen_in > ten_in
    # A genuine vertical offset changes radial geometry rather than being ignored.
    assert required_boom_center_spacing_mm(355.6, 20, 30, 100) < fourteen_in


def test_selected_candidate_passes_stiffness_where_smaller_candidate_does_not():
    summary = make_summary(load_aircraft_config(ROOT / "config" / "aircraft.yaml"))
    sections = summary["candidate_sections"]
    assert not sections["16 x 14 mm"]["assessment"]["meets_minimum_EI_125_Nm2"]
    assert sections["18 x 16 mm"]["assessment"]["meets_minimum_EI_125_Nm2"]
    assert not sections["18 x 16 mm"]["assessment"]["meets_minimum_GJ_105_Nm2"]
    assert sections["20 x 18 mm"]["assessment"]["meets_minimum_GJ_105_Nm2"]
    assert sections["20 x 18 mm"]["loads"]["vertical_tip_deflection_mm"] < sections["18 x 16 mm"]["loads"]["vertical_tip_deflection_mm"]


def test_summary_reads_typed_tail_and_boom_geometry_not_private_copy():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    summary = make_summary(config)
    assert summary["selected_integration_geometry"]["tail_arm_mm"] == pytest.approx(config.tail.tail_arm_mm)
    assert summary["selected_integration_geometry"]["boom_center_spacing_mm"] == pytest.approx(2 * config.booms.lateral_offset_mm)
    assert summary["propeller_radial_clearance_screen"]["cases"][-1]["clears_selected_spacing_at_z0"] is False
    loads = summary["candidate_sections"]["18 x 16 mm"]["loads"]
    assert loads["common_tail_pitch_deg_limit_screen"] <= 2.0
    assert loads["common_tail_pitch_deg_normal_1g_proxy"] <= .5
    assert loads["differential_tail_pitch_deg_for_10pct_EI_mismatch"] <= .25
