import pytest

from scripts.config import load_aircraft_config
from scripts.packaging_study import (BATTERY_STUDY_CASES, battery_x_for_target_cg_mm, cg_shift_for_battery_translation_mm,
                                     cg_x_mm, internal_payload_envelope, make_summary)


def test_battery_translation_shifts_configuration_cg_monotonically():
    case = BATTERY_STUDY_CASES[2]
    assert cg_x_mm(1640, 75, case, 40) < cg_x_mm(1640, 75, case, 70)
    assert cg_shift_for_battery_translation_mm(case.mass_g, 2400, 30) > 0


def test_battery_target_solution_returns_target_cg():
    case = BATTERY_STUDY_CASES[1]
    target, non_battery_mass, non_battery_x = 70.0, 1810.0, 72.0
    battery_x = battery_x_for_target_cg_mm(non_battery_mass, non_battery_x, case, target)
    assert cg_x_mm(non_battery_mass, non_battery_x, case, battery_x) == pytest.approx(target)


@pytest.mark.parametrize("call", [lambda: cg_shift_for_battery_translation_mm(0, 2400, 10), lambda: cg_shift_for_battery_translation_mm(2500, 2400, 10)])
def test_invalid_battery_mass_is_rejected(call):
    with pytest.raises(ValueError):
        call()


def test_packaging_study_keeps_actual_battery_window_tbd_without_mass_ledger_closure():
    summary = make_summary(load_aircraft_config())
    assert summary["status"].startswith("study_cases_only")
    assert summary["internal_payload_envelope_mm"]["battery_adjustment_travel_mm"] == 60.0
    assert any("non-battery resolved mass" in item for item in summary["tbd"])


def test_internal_envelope_reserves_serviceable_battery_and_avionics_volume():
    envelope = internal_payload_envelope()
    assert envelope["minimum_internal_width_mm"] >= 75.0
    assert envelope["battery_bay_length_mm"] >= 280.0
