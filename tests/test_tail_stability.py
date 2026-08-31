from pathlib import Path

import pytest
import yaml

from scripts.config import load_aircraft_config
from scripts.tail_stability import (
    geometry_from_config,
    horizontal_tail_volume,
    make_summary,
    mac_fraction_to_x_mm,
    neutral_point_mac,
    prop_boom_has_clearance,
    required_boom_axis_spacing_m,
    static_margin_mac,
    trapezoid_area_m2,
    vertical_tail_volume,
    x_mm_to_mac_fraction,
)


ROOT = Path(__file__).resolve().parents[1]


def test_tail_volumes_follow_their_definitions():
    assert trapezoid_area_m2(.7, .09, .09) == pytest.approx(.063)
    assert horizontal_tail_volume(.063, .65, .36, 225.925926 / 1000) == pytest.approx(.50348, rel=2e-5)
    assert vertical_tail_volume(.03795, .65, .36, 1.6) == pytest.approx(.0428, rel=2e-3)


def test_increasing_tail_arm_reduces_area_for_same_horizontal_volume():
    short = .50 * .36 * (225.925926 / 1000) / .55
    long = .50 * .36 * (225.925926 / 1000) / .75
    assert long < short


def test_reducing_tail_effectiveness_moves_neutral_point_forward():
    kwargs = dict(wing_ac_mac=.25, wing_lift_slope_per_rad=4.8, tail_lift_slope_per_rad=5.0,
                  tail_volume=.50, downwash_gradient=.45, fuselage_neutral_point_shift_mac=-.02)
    assert neutral_point_mac(**kwargs, tail_efficiency=.78) < neutral_point_mac(**kwargs, tail_efficiency=.92)


def test_static_margin_has_consistent_sign_and_cg_conversion_round_trips():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    assert static_margin_mac(.48, .28) == pytest.approx(.20)
    assert static_margin_mac(.28, .48) < 0
    x = mac_fraction_to_x_mm(config, .28)
    assert x_mm_to_mac_fraction(config, x) == pytest.approx(.28)


def test_twin_fin_geometry_is_symmetric_and_total_area_is_explicit():
    tail = geometry_from_config(load_aircraft_config(ROOT / "config/aircraft.yaml"))
    assert tail.vertical_total_area_m2 == pytest.approx(2 * tail.fin_area_each_m2)
    assert tail.boom_y_m == pytest.approx(-(-tail.boom_y_m))


def test_tail_geometry_is_read_from_typed_source_config():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    tail = geometry_from_config(config)
    assert tail.arm_m * 1000 == pytest.approx(config.tail.tail_arm_mm)
    assert tail.horizontal_area_m2 == pytest.approx(config.tail.horizontal.area_m2)
    assert tail.vertical_total_area_m2 == pytest.approx(config.tail.vertical.total_area_m2)


def test_selected_cg_is_validated_against_derived_trim_and_static_margin_limits():
    summary = make_summary(load_aircraft_config(ROOT / "config/aircraft.yaml"))
    cg = summary["design_cg_envelope"]
    assert cg["forward_mac"] >= cg["derived_forward_trim_limit_mac"]
    assert cg["aft_mac"] <= cg["derived_aft_static_margin_limit_mac"]
    assert cg["static_margin_mac_range_across_sensitivity"]["aft_mac"]["minimum"] >= .05
    assert summary["first_flight_recommendation"]["static_margin_mac_sensitivity_range"]["minimum"] >= .08


def test_low_re_tail_slope_and_twin_fin_sensitivity_are_explicit():
    summary = make_summary(load_aircraft_config(ROOT / "config/aircraft.yaml"))
    slopes = {case["tail_lift_slope_per_rad"] for case in summary["stability_sensitivity"]}
    assert slopes == {3.4, 4.2, 4.9}
    assert summary["twin_fin_screening"]["selected_geometry_cn_beta_proxy_range"]["minimum"] >= .025


def test_no_numerical_stability_result_when_tail_inputs_are_unresolved(tmp_path: Path):
    document = yaml.safe_load((ROOT / "config/aircraft.yaml").read_text(encoding="utf-8"))
    document["tail"] = {"status": "tbd", "tail_arm_mm": None, "horizontal": None, "vertical": None}
    document["booms"]["status"] = "tbd"
    document["booms"]["lateral_offset_mm"] = document["booms"]["axis_z_mm"] = None
    document["cg"]["initial_envelope"] = {"status": "tbd", "x_mac_fraction_min": None, "x_mac_fraction_max": None, "basis": None}
    document["cg"]["first_flight_recommendation"] = {"status": "tbd", "x_mac_fraction": None, "basis": None}
    path = tmp_path / "unresolved.yaml"; path.write_text(yaml.safe_dump(document), encoding="utf-8")
    with pytest.raises(ValueError, match="requires defined preliminary tail"):
        make_summary(load_aircraft_config(path))


def test_radial_prop_boom_clearance_is_not_just_a_diameter_rule():
    # A 356 mm disk with a 10 mm boom radius and 30 mm clearance needs 435.6 mm
    # axis spacing at z=0.  The actual radial criterion also accepts an offset.
    assert required_boom_axis_spacing_m(propeller_diameter_m=.3556, boom_radius_m=.01, required_clearance_m=.030) == pytest.approx(.4356)
    assert prop_boom_has_clearance(propeller_diameter_m=.3556, boom_y_m=.22, boom_z_m=.02, boom_radius_m=.01, required_clearance_m=.030)


def test_larger_propeller_requires_no_less_clearance():
    small = required_boom_axis_spacing_m(propeller_diameter_m=.254, boom_radius_m=.01, required_clearance_m=.015)
    large = required_boom_axis_spacing_m(propeller_diameter_m=.381, boom_radius_m=.01, required_clearance_m=.015)
    assert large > small


@pytest.mark.parametrize("call", [
    lambda: horizontal_tail_volume(0, .65, .36, .226),
    lambda: vertical_tail_volume(.04, 0, .36, 1.6),
    lambda: trapezoid_area_m2(.7, -.09, .09),
    lambda: required_boom_axis_spacing_m(propeller_diameter_m=.3, boom_radius_m=0, required_clearance_m=.01),
])
def test_invalid_geometry_inputs_fail_loudly(call):
    with pytest.raises(ValueError):
        call()
