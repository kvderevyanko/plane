import pytest

from scripts.config import load_aircraft_config
from scripts.powertrain_structure import (
    MOTOR_PEAK_RPM_SCREEN,
    battery_retention_case,
    inertial_force_n,
    make_summary,
    motor_shaft_torque_nm,
    structural_battery_study_cases,
)


def test_battery_retention_load_increases_with_mass_and_proof_factor():
    config = load_aircraft_config()
    light = battery_retention_case(structural_battery_study_cases()[0], config)
    heavy = battery_retention_case(structural_battery_study_cases()[-1], config)
    assert heavy["landing_ejection_6g_assumption_n_per_principal_direction"] > light["landing_ejection_6g_assumption_n_per_principal_direction"]
    assert heavy["proof_load_n_per_principal_direction"] == pytest.approx(
        1.5 * heavy["landing_ejection_6g_assumption_n_per_principal_direction"]
    )
    assert heavy["two_primary_stops_nominal_share_n"] == pytest.approx(heavy["proof_load_n_per_principal_direction"] / 2.0)


def test_inertial_load_and_motor_torque_relations_are_physical():
    assert inertial_force_n(1420.0, 6.0, 9.80665) == pytest.approx(83.552647)
    assert motor_shaft_torque_nm(571.0, MOTOR_PEAK_RPM_SCREEN) > motor_shaft_torque_nm(400.0, MOTOR_PEAK_RPM_SCREEN)
    assert motor_shaft_torque_nm(571.0, 8000.0) < motor_shaft_torque_nm(571.0, MOTOR_PEAK_RPM_SCREEN)


@pytest.mark.parametrize("call", [lambda: inertial_force_n(0, 4, 9.8), lambda: inertial_force_n(100, 0, 9.8), lambda: motor_shaft_torque_nm(100, 0)])
def test_invalid_structural_screen_inputs_are_rejected(call):
    with pytest.raises(ValueError):
        call()


def test_summary_uses_typed_aircraft_geometry_and_keeps_selection_tbd():
    config = load_aircraft_config()
    summary = make_summary(config)
    known = summary["known_from_aircraft_config"]
    assert known["target_mass_g"] == pytest.approx(config.aircraft.target_mass_g)
    assert known["boom_center_spacing_mm"] == pytest.approx(2.0 * config.booms.lateral_offset_mm)
    assert summary["pusher_motor_interface"]["proof_framework"]["limit"].startswith("The present 10.05-N")
    assert any("selected motor" in value for value in summary["tbd_before_release"])
