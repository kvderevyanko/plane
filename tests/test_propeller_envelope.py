from pathlib import Path

import pytest

from scripts.config import load_aircraft_config
from scripts.propeller_envelope import (
    disk_loading_n_m2,
    make_summary,
    motor_shaft_torque_nm,
    pitch_speed_km_h,
    prop_disk_area_m2,
    radial_clearance_margin_m,
    required_no_load_kv_rpm_per_v,
    rpm_for_pitch_speed,
    tip_speed_m_s,
)


ROOT = Path(__file__).resolve().parents[1]


def test_propeller_kinematics_are_dimensionally_consistent():
    assert pitch_speed_km_h(10.0, 7200.0) == pytest.approx(109.728)
    assert rpm_for_pitch_speed(10.0, 109.728) == pytest.approx(7200.0)
    assert prop_disk_area_m2(.3556) == pytest.approx(.099315, rel=2e-4)
    assert tip_speed_m_s(.3556, 8000.0) == pytest.approx(148.95, rel=2e-3)


def test_disk_loading_and_torque_increase_with_thrust_and_power():
    assert disk_loading_n_m2(8.0, .33) > disk_loading_n_m2(6.0, .33)
    assert motor_shaft_torque_nm(400.0, 6500.0) > motor_shaft_torque_nm(200.0, 6500.0)


def test_cruise_torque_uses_propeller_efficiency_between_aerodynamic_and_shaft_power():
    summary = make_summary(load_aircraft_config(ROOT / "config/aircraft.yaml"))
    torque = summary["motor_implications"]["shaft_torque"]
    assert torque["central_cruise_shaft_power_w_with_propeller_efficiency_0_65"]["70_km_h"] == pytest.approx(
        torque["central_cruise_aerodynamic_power_w"]["70_km_h"] / .65,
    )


def test_higher_voltage_requires_lower_kv_for_the_same_loaded_rpm():
    assert required_no_load_kv_rpm_per_v(7500.0, 21.0, .8) < required_no_load_kv_rpm_per_v(7500.0, 14.0, .8)


def test_current_boom_geometry_accepts_12_to_14_in_and_rejects_15_in_screen():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    summary = make_summary(config)
    cases = {case["diameter_in"]: case for case in summary["propeller_working_envelope"]}
    assert all(cases[diameter]["boom_radial_clearance_screen"]["passes"] for diameter in (12.0, 13.0, 14.0))
    assert radial_clearance_margin_m(.381, .230, 0.0) < 0


def test_preferred_propeller_and_motor_envelopes_come_from_typed_configuration():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    summary = make_summary(config)
    selected = summary["known_from_config"]["selected_preliminary_propeller"]
    assert selected["diameter_mm"] == pytest.approx([config.propulsion.propeller.diameter_min_mm, config.propulsion.propeller.diameter_max_mm])
    assert summary["preferred_preliminary_envelope"]["selected_motor_kv_rpm_per_v"] == pytest.approx([config.propulsion.motor.kv_min_rpm_per_v, config.propulsion.motor.kv_max_rpm_per_v])


@pytest.mark.parametrize("call", [
    lambda: prop_disk_area_m2(0),
    lambda: pitch_speed_km_h(0, 7000),
    lambda: tip_speed_m_s(.33, 0),
    lambda: disk_loading_n_m2(-1, .33),
    lambda: required_no_load_kv_rpm_per_v(7000, 0, .8),
])
def test_invalid_propeller_inputs_fail_loudly(call):
    with pytest.raises(ValueError):
        call()
