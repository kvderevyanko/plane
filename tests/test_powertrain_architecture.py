from pathlib import Path

import pytest

from scripts.config import load_aircraft_config
from scripts.powertrain_architecture import (battery_current_a, endurance_hours,
                                             load_clean_cases, make_summary,
                                             minimum_area_for_loss_mm2,
                                             usable_energy_wh, wire_loss_w)


ROOT = Path(__file__).resolve().parents[1]


def test_power_voltage_current_relation_and_higher_voltage_reduce_current():
    assert battery_current_a(210, 21) == pytest.approx(10)
    assert battery_current_a(210, 21) < battery_current_a(210, 14)


def test_wire_loss_is_i_squared_r_and_required_area_grows_with_current():
    assert wire_loss_w(20, .5, 2.5) == pytest.approx(4 * wire_loss_w(10, .5, 2.5))
    assert minimum_area_for_loss_mm2(30, .5, 600) > minimum_area_for_loss_mm2(20, .5, 600)


def test_usable_energy_and_hotel_load_relations():
    assert usable_energy_wh(250, .8) == pytest.approx(200)
    assert endurance_hours(200, 150) < endurance_hours(200, 135)


@pytest.mark.parametrize("call", [lambda: battery_current_a(-1, 21), lambda: battery_current_a(1, 0), lambda: wire_loss_w(-1, .5, 2.5), lambda: usable_energy_wh(0), lambda: endurance_hours(0, 1)])
def test_invalid_inputs_fail_loudly(call):
    with pytest.raises(ValueError):
        call()


def test_summary_selects_6s_without_hardware_and_has_hotel_sensitivity():
    summary = make_summary(load_aircraft_config(ROOT / "config/aircraft.yaml"), load_clean_cases())
    assert summary["preliminary_architecture_selection"]["selected"] == "6S propulsion bus"
    assert summary["preliminary_architecture_selection"]["not_selected_hardware"] is True
    case_4s = summary["voltage_architecture"][0]["cases"][-1]
    case_6s = summary["voltage_architecture"][1]["cases"][-1]
    assert case_6s["current_a_at_loaded_v"] < case_4s["current_a_at_loaded_v"]
    endurance = summary["endurance_including_hotel"]
    low = next(row for row in endurance if row["speed_km_h"] == 70 and row["usable_energy_wh"] == 200 and row["hotel_case"] == "low")
    high = next(row for row in endurance if row["speed_km_h"] == 70 and row["usable_energy_wh"] == 200 and row["hotel_case"] == "high")
    assert high["endurance_h"] < low["endurance_h"]
