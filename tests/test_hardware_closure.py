from pathlib import Path

import pytest

from scripts.config import ConfigurationError, load_aircraft_config
from scripts.hardware import load_hardware_config
from scripts.hardware_closure import (bus_current_a, constant_power_sag_current_a,
                                      endurance_h, make_summary, wire_loss_w)


ROOT = Path(__file__).resolve().parents[1]


def baseline():
    return load_aircraft_config(ROOT / "config" / "aircraft.yaml"), load_hardware_config(ROOT / "config" / "hardware.yaml")


def test_manifest_is_typed_and_has_no_duplicate_mass_source_in_aircraft_yaml():
    aircraft, hardware = baseline()
    assert hardware.component("propulsion_motor").mass_g == pytest.approx(195.0)
    assert all(component.mass_g is None for component in aircraft.mass_budget.components)
    assert len({component.id for component in hardware.components}) == len(hardware.components)


def test_motor_esc_prop_and_battery_meet_selected_preliminary_envelopes():
    aircraft, hardware = baseline()
    summary = make_summary(aircraft, hardware)
    checks = summary["requirement_checks"]
    assert checks["motor_partial_kv_current_datasheet_screen"]
    assert not checks["motor_mass_within_original_120_180g_envelope"]
    assert not checks["motor_prop_6s_apc14x10_operating_point_validated"]
    assert checks["esc_satisfies_continuous_and_burst_envelope"]
    assert checks["selected_14in_prop_current_460mm_boom_spacing_valid"]
    assert checks["15in_is_not_baseline"]
    battery = summary["battery_electrical"]
    assert battery["topology"] == "6S2P"
    assert max(row["per_cell_current_a"] for row in battery["rows"]) <= 30.0


def test_power_energy_relations_and_hotel_load_are_physical():
    assert bus_current_a(420.0, 21.0) == pytest.approx(20.0)
    assert bus_current_a(420.0, 21.0) < bus_current_a(420.0, 14.0)
    assert wire_loss_w(20.0, .01) == pytest.approx(4 * wire_loss_w(10.0, .01))
    assert endurance_h(100.0, 150.0) < endurance_h(100.0, 135.0)
    assert constant_power_sag_current_a(685.0, 21.6, .102) > bus_current_a(685.0, 21.0)
    with pytest.raises(ValueError):
        bus_current_a(1.0, 0.0)
    with pytest.raises(ValueError):
        endurance_h(0.0, 1.0)


def test_estimated_mass_is_below_target_but_explicitly_fails_cg_closure():
    aircraft, hardware = baseline()
    summary = make_summary(aircraft, hardware)
    mass = summary["mass_budget"]
    assert mass["resolved_non_fuselage_components"]["mass_g"] <= aircraft.aircraft.target_mass_g
    assert mass["remaining_fuselage_group_constraint_g"] > 0
    solver = summary["cg_closure"]["battery_x_solver"]
    first_flight = next(row for row in solver if row["fuselage_group_x_assumption_mm"] == -100.0 and row["target_mac_fraction"] == .25)
    assert not first_flight["inside_current_tray_travel"]
    assert "No 24-28%" in summary["cg_closure"]["result"]
    residuals = mass["structural_sensitivity_remaining_fuselage_g"]
    assert residuals["low"] > residuals["central"] > residuals["high"] > 0
    current = summary["cg_closure"]["current_tray_estimated_cg_with_favourable_minus_100mm_fuselage_group"]
    assert [row["estimated_cg_x_mm"] for row in current] == pytest.approx([166.1483, 173.9483, 181.7483], abs=.001)


def test_manifest_rejects_missing_selected_evidence(tmp_path: Path):
    source = ROOT / "config" / "hardware.yaml"
    broken = tmp_path / "hardware.yaml"
    broken.write_text(source.read_text(encoding="utf-8").replace("manufacturer: KDE Direct", "manufacturer: null", 1), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_hardware_config(broken)
