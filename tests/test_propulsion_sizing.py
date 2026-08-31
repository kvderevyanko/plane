from pathlib import Path

import pytest

from scripts.config import load_aircraft_config
from scripts.propulsion_sizing import (Efficiency, electrical_power_w, endurance_hours, evaluate_flight_point,
                                       ground_range_km, kmh_to_mps, load_clean_cases, make_summary, mps_to_kmh,
                                       still_air_range_km)


ROOT = Path(__file__).resolve().parents[1]


def test_speed_power_energy_conversions_are_dimensionally_consistent():
    assert kmh_to_mps(72) == pytest.approx(20)
    assert mps_to_kmh(20) == pytest.approx(72)
    assert endurance_hours(150, 100) == pytest.approx(1.5)
    assert still_air_range_km(1.5, 20) == pytest.approx(108)


@pytest.mark.parametrize("call", [lambda: kmh_to_mps(-1), lambda: endurance_hours(0, 1), lambda: endurance_hours(1, -1), lambda: ground_range_km(1, 10, 10)])
def test_invalid_inputs_fail_loudly(call):
    with pytest.raises(ValueError): call()


def test_drag_mass_and_efficiency_change_power_in_the_expected_direction():
    config, cases = load_aircraft_config(ROOT / "config/aircraft.yaml"), load_clean_cases()
    efficient, inefficient = Efficiency(.82, .93, .99), Efficiency(.68, .82, .97)
    base = evaluate_flight_point(config, cases, mass_kg=2.4, speed_m_s=20, parasitic_cda_m2=.012, efficiency=efficient)
    more_drag = evaluate_flight_point(config, cases, mass_kg=2.4, speed_m_s=20, parasitic_cda_m2=.018, efficiency=efficient)
    more_mass = evaluate_flight_point(config, cases, mass_kg=2.8, speed_m_s=20, parasitic_cda_m2=.012, efficiency=efficient)
    lower_efficiency = evaluate_flight_point(config, cases, mass_kg=2.4, speed_m_s=20, parasitic_cda_m2=.012, efficiency=inefficient)
    assert more_drag.aerodynamic_power_w > base.aerodynamic_power_w
    assert more_mass.aerodynamic_power_w > base.aerodynamic_power_w
    assert lower_efficiency.electrical_total_w > base.electrical_total_w


def test_hotel_load_and_headwind_reduce_endurance_and_range():
    efficiency = Efficiency(.75, .90, .985)
    assert electrical_power_w(100, efficiency, 20) > electrical_power_w(100, efficiency, 0)
    assert endurance_hours(200, electrical_power_w(100, efficiency, 20)) < endurance_hours(200, electrical_power_w(100, efficiency, 0))
    assert ground_range_km(2, 20, 8) < still_air_range_km(2, 20)


def test_climb_rate_increases_required_thrust_and_shaft_power():
    config, cases, efficiency = load_aircraft_config(ROOT / "config/aircraft.yaml"), load_clean_cases(), Efficiency(.65, .87, .98)
    level = evaluate_flight_point(config, cases, mass_kg=2.4, speed_m_s=60 / 3.6, parasitic_cda_m2=.012, efficiency=efficiency)
    climb = evaluate_flight_point(config, cases, mass_kg=2.4, speed_m_s=60 / 3.6, parasitic_cda_m2=.012, efficiency=efficiency, climb_rate_m_s=3)
    assert climb.required_thrust_n > level.required_thrust_n
    assert climb.shaft_power_w > level.shaft_power_w


def test_output_explicitly_keeps_hardware_unselected_when_inputs_are_tbd():
    summary = make_summary(load_aircraft_config(ROOT / "config/aircraft.yaml"), load_clean_cases())
    assert all(value is None for key, value in summary["hardware_selection"].items() if key != "status")
    assert "battery chemistry, series count, voltage sag curve, capacity and mass" in summary["tbd"]
