#!/usr/bin/env python3
"""Evidence-backed LR1600 preliminary hardware and mass/CG closure screen.

The result is intentionally capable of declaring closure *blocked*.  A target
mass residual is a fuselage design constraint, not evidence of a finished
fuselage or a final measured CG.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.boom_sizing import required_boom_center_spacing_mm
from scripts.config import AircraftConfig, load_aircraft_config
from scripts.hardware import HardwareComponent, HardwareConfig, load_hardware_config
from scripts.mass_properties import calculate_mass_properties


def bus_current_a(power_w: float, voltage_v: float) -> float:
    if power_w < 0 or voltage_v <= 0:
        raise ValueError("power must be non-negative and voltage must be positive")
    return power_w / voltage_v


def wire_loss_w(current_a: float, resistance_ohm: float) -> float:
    if current_a < 0 or resistance_ohm < 0:
        raise ValueError("current and resistance must be non-negative")
    return current_a**2 * resistance_ohm


def endurance_h(usable_wh: float, electrical_w: float) -> float:
    if usable_wh <= 0 or electrical_w <= 0:
        raise ValueError("energy and power must be positive")
    return usable_wh / electrical_w


def constant_power_sag_current_a(power_w: float, open_circuit_voltage_v: float, pack_resistance_ohm: float) -> float:
    """Solve P = (Voc - I R) I for the physically lower-current root."""
    if power_w <= 0 or open_circuit_voltage_v <= 0 or pack_resistance_ohm <= 0:
        raise ValueError("power, voltage and resistance must be positive")
    discriminant = open_circuit_voltage_v**2 - 4.0 * pack_resistance_ohm * power_w
    if discriminant < 0:
        raise ValueError("constant-power load has no solution at this voltage/resistance")
    return (open_circuit_voltage_v - discriminant**.5) / (2.0 * pack_resistance_ohm)


def cg_target_x_mm(config: AircraftConfig, mac_fraction: float) -> float:
    return config.wing.mean_aerodynamic_chord_leading_edge_x_mm + mac_fraction * config.wing.mean_aerodynamic_chord_mm


def required_battery_x_mm(non_battery_mass_g: float, non_battery_moment_g_mm: float,
                          battery_mass_g: float, fuselage_mass_g: float,
                          fuselage_x_mm: float, target_cg_x_mm: float) -> float:
    if non_battery_mass_g <= 0 or battery_mass_g <= 0 or fuselage_mass_g < 0:
        raise ValueError("invalid mass input")
    return ((non_battery_mass_g + battery_mass_g + fuselage_mass_g) * target_cg_x_mm
            - non_battery_moment_g_mm - fuselage_mass_g * fuselage_x_mm) / battery_mass_g


def _ledger_components(hardware: HardwareConfig, *, include_battery: bool) -> tuple[HardwareComponent, ...]:
    return tuple(item for item in hardware.components
                 if item.status in {"selected_preliminary", "design_estimate"}
                 and item.mass_g is not None and (include_battery or item.id != "flight_battery"))


def _mass_properties(items: Iterable[HardwareComponent]) -> dict[str, Any]:
    components = tuple(item.as_mass_component() for item in items)
    if any(item is None for item in components):
        raise ValueError("resolved baseline component lacks CG data")
    result = calculate_mass_properties(components)  # type: ignore[arg-type]
    return {
        "mass_g": result.estimated_total_mass_g,
        "x_cg_mm": result.estimated_x_cg_mm,
        "y_cg_mm": result.estimated_y_cg_mm,
        "z_cg_mm": result.estimated_z_cg_mm,
        "component_ids": list(result.included_component_ids) + [item.id for item in result.design_estimate_components],
    }


def _battery_cells(hardware: HardwareConfig, config: AircraftConfig) -> dict[str, Any]:
    battery = hardware.component("flight_battery")
    limits = battery.limits
    voltage = config.electrical.propulsion_bus_loaded_min_voltage_v
    assert voltage is not None
    cases = {"70_kmh_central_cruise": 150.0, "80_kmh_central_cruise": 212.0,
             "490_w_climb_plus_15_w_hotel": 505.0, "670_w_broader_plus_15_w_hotel": 685.0}
    rows = []
    for name, power in cases.items():
        pack_current = bus_current_a(power, voltage)
        per_cell = pack_current / 2.0
        implicit_current = constant_power_sag_current_a(power, 21.6, .017 * 6.0)
        implicit_voltage = 21.6 - implicit_current * .017 * 6.0
        rows.append({"case": name, "battery_bus_w": power, "pack_current_a": pack_current,
                     "per_cell_current_a": per_cell,
                     "percent_of_documented_30a_continuous": per_cell / 30.0 * 100.0,
                     "first_order_cell_sag_v_at_17mohm_50pct_soc": per_cell * .017,
                     "first_order_6s_cell_only_sag_v": per_cell * .017 * 6.0,
                     "constant_power_cell_only_sag_solution_at_21_6v_50pct_soc": {
                         "pack_current_a": implicit_current, "per_cell_current_a": implicit_current / 2.0,
                         "loaded_pack_voltage_v": implicit_voltage,
                     }})
    return {"cell": "Molicel INR-18650-P30B", "topology": "6S2P", "rows": rows,
            "nominal_energy_wh_typical": limits["nominal_energy_wh_typical"],
            "usable_energy_wh_at_80_percent": limits["usable_energy_wh_at_80_percent"],
            "complete_pack_mass_g_design_estimate": battery.mass_g,
            "caveat": "DCIR sag is cell-only at documented 50% SOC; busbar, connector, temperature, aging and low-SOC effects require bench validation."}


def make_summary(config: AircraftConfig, hardware: HardwareConfig) -> dict[str, Any]:
    if not config.propulsion.is_defined or config.propulsion.motor is None or config.propulsion.propeller is None:
        raise ValueError("aircraft propulsion envelope must be defined")
    motor, esc, prop, battery = (hardware.component(item) for item in ("propulsion_motor", "propulsion_esc", "propulsion_propeller", "flight_battery"))
    assert motor.mass_g is not None and esc.mass_g is not None and prop.mass_g is not None and battery.mass_g is not None
    non_battery = _ledger_components(hardware, include_battery=False)
    baseline = _ledger_components(hardware, include_battery=True)
    non_battery_summary = _mass_properties(non_battery)
    baseline_summary = _mass_properties(baseline)
    target_mass = config.aircraft.target_mass_g
    residual = target_mass - float(baseline_summary["mass_g"])
    # This positive but small residual must cover the complete future fuselage
    # group.  -100 mm is intentionally a *sensitivity assumption*, not a skin.
    fuselage_x_sensitivity = (-200.0, -100.0, 0.0)
    target_fractions = (.24, .25, .26, .28)
    solver = []
    non_mass = float(non_battery_summary["mass_g"])
    non_moment = non_mass * float(non_battery_summary["x_cg_mm"])
    for fuselage_x in fuselage_x_sensitivity:
        for fraction in target_fractions:
            target = cg_target_x_mm(config, fraction)
            required_x = required_battery_x_mm(non_mass, non_moment, battery.mass_g, residual, fuselage_x, target)
            solver.append({"fuselage_group_x_assumption_mm": fuselage_x, "target_mac_fraction": fraction,
                           "target_cg_x_mm": target, "required_battery_x_mm": required_x,
                           "inside_current_tray_travel": hardware.battery_installation.x_min_mm <= required_x <= hardware.battery_installation.x_max_mm})
    cg_current_tray = []
    for battery_x in (hardware.battery_installation.x_min_mm, hardware.battery_installation.x_nominal_mm, hardware.battery_installation.x_max_mm):
        # Display a deliberately favourable but stated future-fuselage centroid.
        full_mass = non_mass + battery.mass_g + residual
        cg_x = (non_moment + battery.mass_g * battery_x + residual * -100.0) / full_mass
        cg_current_tray.append({"battery_x_mm": battery_x, "assumed_fuselage_group_x_mm": -100.0,
                                "estimated_cg_x_mm": cg_x,
                                "estimated_cg_mac_fraction": (cg_x - config.wing.mean_aerodynamic_chord_leading_edge_x_mm) / config.wing.mean_aerodynamic_chord_mm})
    clearance_required = required_boom_center_spacing_mm(prop.limits["diameter_in"] * 25.4, 20.0, 30.0, 0.0)
    motor_limits, esc_limits = motor.limits, esc.limits
    motor_kv_current_screen = (motor_limits["kv_rpm_per_v"] >= config.propulsion.motor.kv_min_rpm_per_v and
                motor_limits["kv_rpm_per_v"] <= config.propulsion.motor.kv_max_rpm_per_v and
                motor_limits["continuous_current_a_180_s_with_cooling"] >= config.propulsion.motor.peak_current_a)
    esc_ok = esc_limits["continuous_current_a"] >= config.propulsion.motor.continuous_current_a and esc_limits["burst_current_a"] >= config.propulsion.motor.peak_current_a
    return {
        "schema": "lr1600-hardware-baseline-mass-cg-v1",
        "status": "mass_and_cg_closure_blocked_before_fuselage_design; selected_hardware_is_preliminary_only",
        "source_inputs": {"aircraft": "config/aircraft.yaml", "hardware": "config/hardware.yaml", "mass_values": "hardware manifest only"},
        "selected_preliminary_hardware": {"propeller": {"model": prop.model, "mass_g": prop.mass_g, "source_url": prop.source_url},
                                            "motor": {"model": motor.model, "mass_g": motor.mass_g, "source_url": motor.source_url},
                                            "esc": {"model": esc.model, "mass_g": esc.mass_g, "source_url": esc.source_url},
                                            "battery": {"model": battery.model, "mass_g": battery.mass_g, "source_url": battery.source_url}},
        "requirement_checks": {"motor_partial_kv_current_datasheet_screen": motor_kv_current_screen,
                               "motor_mass_within_original_120_180g_envelope": motor.mass_g <= config.propulsion.motor.mass_max_g,
                               "motor_continuous_550w_evidence_closed": False,
                               "motor_prop_6s_apc14x10_operating_point_validated": False,
                               "esc_satisfies_continuous_and_burst_envelope": esc_ok,
                               "selected_14in_prop_boom_spacing_mm_required": clearance_required,
                               "selected_14in_prop_current_460mm_boom_spacing_valid": 460.0 > clearance_required,
                               "15in_is_not_baseline": required_boom_center_spacing_mm(381.0, 20.0, 30.0, 0.0) > 460.0},
        "battery_electrical": _battery_cells(hardware, config),
        "mass_budget": {"resolved_non_fuselage_components": baseline_summary, "target_mass_g": target_mass,
                        "remaining_fuselage_group_constraint_g": residual,
                        "structural_sensitivity_remaining_fuselage_g": {
                            "low": residual + (591.25 - 464.1) + (120.28 - 112.52) + (115.0 - 80.0),
                            "central": residual,
                            "high": residual - (718.4 - 591.25) - (128.04 - 120.28) - (150.0 - 115.0),
                        },
                        "motor_leads_disposition": "KDE 195g bare motor is used; its 250g with supplied leads/bullets is not added separately because the 85g wiring/connectors estimate explicitly includes motor leads/bullets. Confirm by measurement.",
                        "closure": "NOT a verified all-up mass: residual must contain shell/frame, tray, hatch, boom attachments, protection/skid and any omitted installation mass."},
        "cg_closure": {"current_tray_mm": {"min": hardware.battery_installation.x_min_mm, "nominal": hardware.battery_installation.x_nominal_mm, "max": hardware.battery_installation.x_max_mm},
                       "current_tray_estimated_cg_with_favourable_minus_100mm_fuselage_group": cg_current_tray,
                       "battery_x_solver": solver,
                       "result": "No 24-28% MAC target is reachable with the current X=0 +/-30 mm tray in the central ledger screen. No ballast-free initial-CG closure is claimed.",
                       "required_next_inputs": ["measured/analytical wing mass centroid", "empennage mass and centroid", "full installation/fuselage group mass moments", "actual pack build dimensions and mass"],
                       "provisional_packaging_reservation_only": "Do not set a new bay coordinate. Solver-only central sensitivity spans roughly X=-450 to -344 mm; obtain mass moments before reserving a physical rail/hatch."},
        "propeller_operating_screen": {"method": "UIUC Volume-4 APC14x10E coefficient data with T=Ct*rho*n^2*D^4 and P=Cp*rho*n^3*D^5; RPMs at 90 km/h use limited interpolation/extrapolation and are not a motor+prop test.",
                                       "uiuc_source_url": "https://m-selig.ae.illinois.edu/props/volume-4/data/apce_14x10_2148od_5983.txt",
                                       "central_cases": [{"speed_km_h": speed, "thrust_n": thrust, "rpm": rpm, "advance_ratio": j, "shaft_power_w": shaft, "eta": eta}
                                                         for speed, thrust, rpm, j, shaft, eta in ((60, 3.04, 4500, .625, 86, .805), (70, 3.85, 4900, .670, 95, .785), (80, 4.91, 5580, .672, 139, .782), (90, 6.13, 6265, .673, 196, .781))],
                                       "status": "screening_only; pusher operating point and APC RPM limit remain unvalidated"},
        "motor_shortlist": [{"model": "KDE4215XF-465", "status": "selected_candidate_pending_combo_validation", "kv": 465, "mass_g_bare": 195},
                            {"model": "KDE3520XF-400", "status": "fallback_pending_combo_validation", "kv": 400, "mass_g_bare": 190},
                            {"model": "AXI 4120/20 Gold Line V3", "status": "fallback_mass_penalty", "kv": 465, "mass_g": 315}],
        "hotel_load": {"low_w": 7.0, "nominal_w_hardware_backed_design_estimate": 16.0, "high_w": 25.0,
                       "servo_transient_w_theoretical_simultaneous_stall": 61.2,
                       "note": "Average servo power is not inferred from stall current."},
        "tbd": ["motor+APC14x10E 6S pusher bench map and installed thermal test", "APC current RPM limit verification", "exact fuse/anti-spark/monitor-only BMS and time-current validation", "ASP D-DLVR primary manual evidence", "actual pack, tray/hatch removal clearance and retention proof", "fuselage/empennage/wing measured mass moments", "RF legality, compass survey, antenna range and installed cooling"],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "hardware" / "summary.json")
    args = parser.parse_args()
    summary = make_summary(load_aircraft_config(), load_hardware_config())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    mass_output = ROOT / "analysis" / "mass" / "summary.json"
    mass_output.parent.mkdir(parents=True, exist_ok=True)
    mass_output.write_text(json.dumps(summary["mass_budget"] | {"cg_closure": summary["cg_closure"]}, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output} and {mass_output}")


if __name__ == "__main__":
    main()
