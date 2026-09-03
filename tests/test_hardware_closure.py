from pathlib import Path

import pytest

from scripts.config import ConfigurationError, load_aircraft_config
from scripts.cg_integration import make_summary as make_cg_summary
from scripts.hardware import load_hardware_config
from scripts.hardware_closure import (bus_current_a, constant_power_sag_current_a,
                                      endurance_h, wire_loss_w)


ROOT = Path(__file__).resolve().parents[1]


def baseline():
    return load_aircraft_config(ROOT / "config" / "aircraft.yaml"), load_hardware_config(ROOT / "config" / "hardware.yaml")


def test_manifest_is_typed_and_has_no_duplicate_mass_source_in_aircraft_yaml():
    aircraft, hardware = baseline()
    assert hardware.component("propulsion_motor").mass_g == pytest.approx(145.0)
    assert all(component.mass_g is None for component in aircraft.mass_budget.components)
    assert len({component.id for component in hardware.components}) == len(hardware.components)


def test_typed_packaging_envelopes_match_the_single_hardware_manifest():
    aircraft, hardware = baseline()
    forward_servos = {servo.id: servo for servo in aircraft.fuselage_integration.forward_servos}
    for component_id, envelope in forward_servos.items():
        item = hardware.component(component_id)
        assert (item.x_mm, item.y_mm, item.z_mm) == pytest.approx((envelope.x_mm, envelope.y_mm, envelope.z_mm))
    for envelope in aircraft.avionics.components:
        item = hardware.component(envelope.id)
        assert (item.length_mm, item.width_mm, item.height_mm) == pytest.approx((
            envelope.length_mm, envelope.width_mm, envelope.height_mm,
        ))
        assert (item.x_mm, item.y_mm, item.z_mm) == pytest.approx((envelope.x_mm, envelope.y_mm, envelope.z_mm))


def test_preliminary_motor_prop_and_p60b_branch_are_explicitly_not_procurement_locks():
    aircraft, hardware = baseline()
    assert hardware.component("propulsion_motor").status == "design_estimate"
    assert hardware.component("propulsion_propeller").limits["diameter_in"] == 13.0
    battery = hardware.component("flight_battery")
    assert battery.limits["topology"] == "6S1P"
    assert battery.mass_g == pytest.approx(503.0)
    assert hardware.component("propulsion_propeller").status == "design_estimate"


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


def test_unified_ledger_closes_baseline_without_ballast_and_reports_payload_limits():
    summary = make_cg_summary()
    assert summary["conclusions"]["wheels_25_percent_without_ballast"]
    assert summary["mass_budget"]["wheels"]["central_g"] < summary["design_mass_case_g"]
    wheel_case = summary["cg_cases"]["wheels"]
    wheels = wheel_case["battery_positions"]
    assert wheels[1]["cg_percent_mac"] == pytest.approx(25.2992, abs=1e-4)
    assert summary["mass_budget"]["wheels"]["central_g"] == pytest.approx(2533.53)
    assert summary["mass_budget"]["skis_central_g"] == pytest.approx(2569.53)
    assert summary["battery"]["rail_mm"]["forward"] > wheel_case["battery_x_for_targets_mm"]["24_percent_mac"]
    assert summary["battery"]["rail_mm"]["forward"] <= wheel_case["battery_x_for_targets_mm"]["25_percent_mac"]
    hd = summary["cg_cases"]["wheels_with_hd"]["battery_x_for_targets_mm"]
    assert hd["25_percent_mac"] > summary["battery"]["rail_mm"]["nominal"]
    assert hd["28_percent_mac"] > summary["battery"]["rail_mm"]["aft"]


def test_nose_gear_ledger_removes_steering_hardware_and_preserves_ski_moment():
    _, hardware = baseline()
    nose = hardware.component("nose_landing_gear")
    ski = hardware.component("winter_ski_module")
    assert nose.mass_g == pytest.approx(52.0)
    assert nose.limits["wheel_diameter_mm"] == 75
    assert nose.limits["heading"] == "fixed aircraft +X"
    assert nose.limits["yaw_freedom"] == "locked by positive mechanical indexing"
    assert nose.limits["seasonal_axle_interface"] == "wheel or freely pitch-pivoting nose ski"
    assert ski.mass_g == pytest.approx(232.0)
    assert ski.x_mm == pytest.approx((238.0 * 10.0 - 6.0 * -218.0) / 232.0, abs=.01)
    assert ski.limits["nose_ski_freedom"] == "free pitch pivot, yaw locked"
    assert "steerable" not in nose.model.lower()


def test_manifest_rejects_missing_selected_evidence(tmp_path: Path):
    source = ROOT / "config" / "hardware.yaml"
    broken = tmp_path / "hardware.yaml"
    broken.write_text(source.read_text(encoding="utf-8").replace("manufacturer: Hobbywing", "manufacturer: null", 1), encoding="utf-8")
    with pytest.raises(ConfigurationError):
        load_hardware_config(broken)
