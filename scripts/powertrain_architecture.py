#!/usr/bin/env python3
"""LR1600 preliminary powertrain and avionics architecture study.

This requirement model deliberately compares electrical architectures without
selecting commercial hardware.  It consumes the existing propulsion study's
central 70/80 km/h electrical power points and its integration screening
values.  ``config/aircraft.yaml`` remains the aircraft source of truth; the
numbers below are explicitly packaging/electrical design assumptions until
hardware measurements replace them.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import load_aircraft_config
from scripts.propulsion_sizing import (Efficiency, PARASITIC_CDA_M2,
                                       evaluate_flight_point, kmh_to_mps,
                                       load_clean_cases)


# The loaded voltages are deliberately conservative screening inputs, not pack
# discharge curves.  A selected pack must replace them with V(SOC, I, T).
VOLTAGE_ARCHITECTURES = (
    {"name": "4S", "nominal_v": 14.8, "loaded_v": 14.0, "max_charged_v": 16.8},
    {"name": "6S", "nominal_v": 22.2, "loaded_v": 21.0, "max_charged_v": 25.2},
)
HOTEL_LOAD_CASES_W = {"low": 7.0, "nominal": 15.0, "high": 25.0}
USABLE_ENERGY_WH = (100.0, 150.0, 200.0, 250.0)
USABLE_FRACTION = 0.80
COPPER_RESISTIVITY_OHM_MM2_PER_M = 0.01724
POWER_LEAD_ONE_WAY_M = 0.50
CONNECTOR_PAIR_RESISTANCE_OHM = 0.002
WIRE_LOSS_TARGET_FRACTION = 0.02
PROPOSED_HARNESS_AREA_MM2 = 2.5

# These are pack-level study bands, including interconnects and protection;
# they are not cell data nor procurement requirements.
CHEMISTRY_STUDY = {
    "li_ion": {"nominal_pack_wh_per_kg": (200.0, 240.0), "discharge": "verify cell and parallel-count voltage sag at 2.3--5.8C peak"},
    "lipo": {"nominal_pack_wh_per_kg": (150.0, 190.0), "discharge": "typically easier peak-current margin; verify actual pack C rating and sag"},
}


@dataclass(frozen=True)
class PowerCase:
    name: str
    propulsion_w: float
    hotel_w: float

    @property
    def total_w(self) -> float:
        return self.propulsion_w + self.hotel_w


def battery_current_a(power_w: float, loaded_voltage_v: float) -> float:
    """Battery-bus current for a positive electrical load and loaded voltage."""
    if power_w < 0 or loaded_voltage_v <= 0:
        raise ValueError("power must be non-negative and loaded voltage must be positive")
    return power_w / loaded_voltage_v


def wire_resistance_ohm(one_way_length_m: float, area_mm2: float) -> float:
    """Round-trip copper lead resistance, excluding connectors."""
    if one_way_length_m < 0 or area_mm2 <= 0:
        raise ValueError("length must be non-negative and area must be positive")
    return COPPER_RESISTIVITY_OHM_MM2_PER_M * (2.0 * one_way_length_m) / area_mm2


def wire_loss_w(current_a: float, one_way_length_m: float, area_mm2: float) -> float:
    if current_a < 0:
        raise ValueError("current must be non-negative")
    return current_a**2 * wire_resistance_ohm(one_way_length_m, area_mm2)


def connector_loss_w(current_a: float, connector_pair_resistance_ohm: float = CONNECTOR_PAIR_RESISTANCE_OHM) -> float:
    if current_a < 0 or connector_pair_resistance_ohm < 0:
        raise ValueError("current and resistance must be non-negative")
    return current_a**2 * connector_pair_resistance_ohm


def minimum_area_for_loss_mm2(current_a: float, one_way_length_m: float, power_w: float,
                               loss_fraction: float = WIRE_LOSS_TARGET_FRACTION) -> float:
    """Copper area that holds wire-only I²R loss within a power fraction."""
    if current_a < 0 or one_way_length_m < 0 or power_w <= 0 or not 0 < loss_fraction < 1:
        raise ValueError("invalid current, length, power, or loss fraction")
    allowed_loss_w = power_w * loss_fraction
    return COPPER_RESISTIVITY_OHM_MM2_PER_M * 2.0 * one_way_length_m * current_a**2 / allowed_loss_w


def usable_energy_wh(nominal_energy_wh: float, usable_fraction: float = USABLE_FRACTION) -> float:
    if nominal_energy_wh <= 0 or not 0 < usable_fraction <= 1:
        raise ValueError("nominal energy must be positive and usable fraction must be in (0, 1]")
    return nominal_energy_wh * usable_fraction


def endurance_hours(usable_energy_wh_value: float, electrical_power_w: float) -> float:
    if usable_energy_wh_value <= 0 or electrical_power_w <= 0:
        raise ValueError("energy and electrical power must be positive")
    return usable_energy_wh_value / electrical_power_w


def _central_propulsion_power(config: Any, clean_cases: list[dict[str, Any]], speed_km_h: float) -> float:
    point = evaluate_flight_point(
        config, clean_cases, mass_kg=config.aircraft.target_mass_kg,
        speed_m_s=kmh_to_mps(speed_km_h), parasitic_cda_m2=PARASITIC_CDA_M2[1],
        efficiency=Efficiency(0.65, 0.87, 0.98), hotel_load_w=0.0,
    )
    return point.electrical_propulsion_w


def _power_cases(config: Any, clean_cases: list[dict[str, Any]]) -> tuple[PowerCase, ...]:
    # 490/670 W originate from the existing propulsion integration screens;
    # 15 W is used for a comparable nominal-hotel electrical architecture case.
    return (
        PowerCase("70_kmh_central_cruise", _central_propulsion_power(config, clean_cases, 70.0), HOTEL_LOAD_CASES_W["nominal"]),
        PowerCase("80_kmh_central_cruise", _central_propulsion_power(config, clean_cases, 80.0), HOTEL_LOAD_CASES_W["nominal"]),
        PowerCase("490_w_climb_integration_screen", 490.0, HOTEL_LOAD_CASES_W["nominal"]),
        PowerCase("670_w_broader_screening_envelope", 670.0, HOTEL_LOAD_CASES_W["nominal"]),
    )


def _avionics_inventory() -> list[dict[str, Any]]:
    """Category-level inventory; no board, radio, or VTX is selected."""
    return [
        {"category": "flight_controller", "rail": "clean 5 V", "average_w": 2.0, "peak_w": 3.5, "status": "design_estimate", "emi": "vibration isolation; keep regulator noise low", "placement": "near CG, rigid protected bay"},
        {"category": "GNSS_compass", "rail": "clean 5 V", "average_w": 0.6, "peak_w": 1.2, "status": "design_estimate", "emi": "high sensitivity: away from motor, ESC, high-current loop and VTX", "placement": "upper forward/remote zone; final separation TBD"},
        {"category": "RC_receiver", "rail": "clean 5 V", "average_w": 0.35, "peak_w": 0.7, "status": "design_estimate", "emi": "antenna diversity and VTX/high-current separation", "placement": "forward avionics bay, accessible antennas"},
        {"category": "telemetry", "rail": "5 V or regulated radio rail", "average_w": 0.7, "peak_w": 1.5, "status": "design_estimate", "emi": "RF separation from receiver/GNSS", "placement": "avionics bay with external antenna routing"},
        {"category": "airspeed_sensor", "rail": "clean 5 V", "average_w": 0.2, "peak_w": 0.4, "status": "design_estimate", "emi": "low electrical sensitivity; pneumatic integrity matters", "placement": "near FC; pitot tube route must avoid kinks/leaks"},
        {"category": "current_voltage_sensor", "rail": "propulsion bus + signal", "average_w": 0.1, "peak_w": 0.2, "status": "design_estimate", "emi": "twisted/sensed routing, calibrated only after hardware selection", "placement": "battery-to-ESC high-current path"},
        {"category": "FPV_camera", "rail": "regulated video rail", "average_w": 0.8, "peak_w": 1.2, "status": "design_estimate", "emi": "avoid ESC noise; filtered rail", "placement": "nose bay"},
        {"category": "VTX", "rail": "regulated video rail", "average_w": 2.0, "peak_w": 5.0, "status": "design_estimate", "emi": "RF/thermal-sensitive; separated from GNSS/RX", "placement": "ventilated aft/side avionics zone, antenna clear of prop"},
        {"category": "servos_group", "rail": "dedicated regulated 6 V", "average_w": 3.0, "peak_w": 48.0, "status": "design_estimate", "emi": "high transient load; separate return from FC rail", "placement": "distributed; actual count/stall currents TBD"},
        {"category": "optional_recording", "rail": "regulated accessory rail", "average_w": 1.0, "peak_w": 2.0, "status": "tbd", "emi": "digital noise may need filtering", "placement": "forward payload bay"},
    ]


def make_summary(config: Any, clean_cases: list[dict[str, Any]]) -> dict[str, Any]:
    # The sweep retains both alternatives, while the typed config records the
    # currently selected preliminary architecture.  Refuse a silent mismatch
    # rather than presenting a stale study as aircraft data.
    if not config.propulsion.is_defined or config.propulsion.nominal_series_count != 6:
        raise ValueError("powertrain v1 requires the typed preliminary 6S propulsion architecture")
    if not config.electrical.is_defined or (config.electrical.propulsion_bus_nominal_voltage_v, config.electrical.propulsion_bus_loaded_min_voltage_v) != (22.2, 21.0):
        raise ValueError("typed electrical bus does not match the 6S 22.2/21.0 V powertrain-v1 study")
    if (config.electrical.hotel_load_low_w, config.electrical.hotel_load_nominal_w,
        config.electrical.hotel_load_high_w) != tuple(HOTEL_LOAD_CASES_W.values()):
        raise ValueError("typed hotel-load envelope does not match powertrain-v1 assumptions")
    cases = _power_cases(config, clean_cases)
    architecture: list[dict[str, Any]] = []
    for arch in VOLTAGE_ARCHITECTURES:
        entries = []
        for case in cases:
            current = battery_current_a(case.total_w, arch["loaded_v"])
            loss = wire_loss_w(current, POWER_LEAD_ONE_WAY_M, PROPOSED_HARNESS_AREA_MM2)
            connector_loss = connector_loss_w(current)
            entries.append({
                "case": case.name, "propulsion_w": case.propulsion_w, "hotel_w": case.hotel_w,
                "battery_bus_total_w": case.total_w, "current_a_at_loaded_v": current,
                "wire_loss_w_with_2_5_mm2_0_5_m_one_way": loss,
                "connector_loss_w_with_2_mohm_pair": connector_loss,
                "minimum_copper_area_mm2_for_2pct_wire_loss": minimum_area_for_loss_mm2(current, POWER_LEAD_ONE_WAY_M, case.total_w),
            })
        architecture.append({**arch, "cases": entries})

    endurance: list[dict[str, Any]] = []
    for speed in (60.0, 70.0, 80.0, 90.0):
        propulsion_w = _central_propulsion_power(config, clean_cases, speed)
        for hotel_name, hotel_w in HOTEL_LOAD_CASES_W.items():
            for energy_wh in USABLE_ENERGY_WH:
                hours = endurance_hours(energy_wh, propulsion_w + hotel_w)
                endurance.append({"speed_km_h": speed, "hotel_case": hotel_name, "hotel_battery_bus_w": hotel_w,
                                  "propulsion_w": propulsion_w, "usable_energy_wh": energy_wh,
                                  "total_electrical_w": propulsion_w + hotel_w, "endurance_h": hours,
                                  "still_air_range_km": hours * speed})

    chemistry = []
    # At a fixed nominal Wh and S count, pack C-rate is P / nominal_Wh; it is
    # intentionally shown without pretending to know an individual cell.
    broad_peak_power_w = cases[-1].total_w
    for chemistry_name, values in CHEMISTRY_STUDY.items():
        rows = []
        for usable_wh_value in USABLE_ENERGY_WH:
            nominal_wh = usable_wh_value / USABLE_FRACTION
            low_density, high_density = values["nominal_pack_wh_per_kg"]
            rows.append({"usable_energy_wh": usable_wh_value, "nominal_pack_energy_wh": nominal_wh,
                         "estimated_pack_mass_g": {"min": nominal_wh / high_density * 1000.0, "max": nominal_wh / low_density * 1000.0},
                         "broad_peak_pack_c_rate": broad_peak_power_w / nominal_wh})
        chemistry.append({"chemistry": chemistry_name, "nominal_pack_wh_per_kg": list(values["nominal_pack_wh_per_kg"]),
                          "discharge_note": values["discharge"], "energy_mass_cases": rows})

    inventory = _avionics_inventory()
    return {
        "schema": "lr1600-powertrain-architecture-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_inputs": {"aircraft_yaml": "config/aircraft.yaml", "propulsion_method": "scripts/propulsion_sizing.py central CdA=0.012 m2 / eta_total=0.55419"},
        "known": {"target_mass_g": config.aircraft.target_mass_g, "boom_spacing_mm": 460.0,
                  "pusher_prop_study_clearance": "12--14 in study disks pass previous clearance screen; 15 in does not"},
        "design_assumptions": {
            "loaded_voltage_screening_v": {row["name"]: row["loaded_v"] for row in VOLTAGE_ARCHITECTURES},
            "hotel_load_battery_bus_w": HOTEL_LOAD_CASES_W, "usable_energy_definition": "energy delivered at battery terminals after reserve/unusable fraction",
            "usable_fraction": USABLE_FRACTION, "power_lead_one_way_m": POWER_LEAD_ONE_WAY_M,
            "copper_resistivity_ohm_mm2_per_m": COPPER_RESISTIVITY_OHM_MM2_PER_M,
            "wire_loss_target_fraction": WIRE_LOSS_TARGET_FRACTION,
            "connector_pair_resistance_ohm": CONNECTOR_PAIR_RESISTANCE_OHM,
        },
        "voltage_architecture": architecture,
        "preliminary_architecture_selection": {
            "status": "initial_design_assumption", "selected": f"{config.propulsion.nominal_series_count}S propulsion bus", "reason": "At equal power 6S reduces current, I2R/connector loss and required copper area, and better supports lower-KV 12--14 in propeller operating points. 4S remains electrically feasible but its 670 W study current is about 49 A at 14 V loaded.",
            "not_selected_hardware": True,
        },
        "esc_requirement_envelope": {"minimum_voltage": "6S (25.2 V fully charged) plus verified transient margin", "continuous_current_a": 35.0,
                                      "short_burst_current_a": 45.0, "thermal": "measured continuous rating with forced/ram airflow at installed location",
                                      "bec": "Do not rely on ESC BEC for aircraft avionics; use dedicated regulated avionics/servo power."},
        "avionics_inventory": inventory,
        "hotel_load_envelope": {"battery_bus_continuous_w": HOTEL_LOAD_CASES_W, "servo_transient": {"regulated_6v_peak_w": 48.0, "note": "short-duration BEC sizing input; do not add as a continuous endurance load without duty data"}},
        "endurance_including_hotel": endurance,
        "chemistry_energy_mass_study": chemistry,
        "battery_direction": {"status": "preliminary_direction", "preferred": "Li-ion conditional on verified cell/parallel-count sag, temperature and peak current", "fallback": "LiPo when verified Li-ion cannot meet peak-current/sag and thermal requirements within mass/packaging limits", "not_a_pack_selection": True},
        "requirements_for_future_config": {
            "propulsion": {"status": "initial_design_assumption", "nominal_series_count": config.propulsion.nominal_series_count, "bus_loaded_v_screening": config.electrical.propulsion_bus_loaded_min_voltage_v,
                           "continuous_current_requirement_a": 35.0, "peak_current_requirement_a": 45.0},
            "electrical": {"hotel_battery_bus_w_low_nominal_high": list(HOTEL_LOAD_CASES_W.values()), "servo_rail": "dedicated regulated 6 V; final voltage/current follows selected servos", "avionics_rail": "independent clean regulated 5 V"},
            "battery": {"chemistry": "Li-ion preliminary direction, conditional", "usable_energy_study_wh": list(USABLE_ENERGY_WH), "usable_fraction": USABLE_FRACTION},
            "avionics": {"status": "inventory design estimates only; no pinout, connector, board or radio selected"},
        },
        "tbd": ["commercial motor, ESC, propeller, cells/pack, connector and wire data", "selected pack V(SOC,I,T), internal resistance, BMS/protection and charge policy",
                "servo count, voltage, measured stall/average current and BEC transient verification", "GNSS/compass, receiver, telemetry and VTX models/frequencies/antenna geometry",
                "final harness length, fusing, cooling, motor/ESC locations and EMI validation", "battery mass/dimensions/X range and estimated all-up CG"],
        "limitations": ["No commercial SKU, manufacturer maximum-W claim, static-thrust value, or final battery capacity is selected.",
                        "Hotel values are battery-bus design estimates, not measured aircraft consumption.",
                        "Voltage comparison uses a screening loaded voltage, not a cell discharge model."],
    }


def make_plots(summary: dict[str, Any], output: Path) -> None:
    plots = output / "plots"; plots.mkdir(parents=True, exist_ok=True)
    cases = [row["case"] for row in summary["voltage_architecture"][0]["cases"]]
    fig, axis = plt.subplots(figsize=(8, 4.5))
    for arch in summary["voltage_architecture"]:
        axis.plot(cases, [row["current_a_at_loaded_v"] for row in arch["cases"]], marker="o", label=arch["name"])
    axis.set(ylabel="Battery current (A)", title="Voltage-architecture current at loaded voltage")
    axis.tick_params(axis="x", rotation=18); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "current_vs_architecture.png", dpi=150); plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    energy = summary["endurance_including_hotel"]
    for hotel in HOTEL_LOAD_CASES_W:
        rows = [row for row in energy if row["speed_km_h"] == 70.0 and row["hotel_case"] == hotel]
        axes[0].plot([row["usable_energy_wh"] for row in rows], [row["endurance_h"] for row in rows], marker="o", label=hotel)
        axes[1].plot([row["usable_energy_wh"] for row in rows], [row["still_air_range_km"] for row in rows], marker="o", label=hotel)
    axes[0].set(xlabel="Usable energy (Wh)", ylabel="Endurance (h)", title="70 km/h central propulsion case")
    axes[1].set(xlabel="Usable energy (Wh)", ylabel="Still-air range (km)", title="70 km/h central propulsion case")
    for axis in axes: axis.grid(True, alpha=.3); axis.legend(title="hotel")
    fig.tight_layout(); fig.savefig(plots / "endurance_including_hotel.png", dpi=150); plt.close(fig)

    fig, axis = plt.subplots(figsize=(8, 4.5))
    for arch in summary["voltage_architecture"]:
        axis.plot(cases, [row["wire_loss_w_with_2_5_mm2_0_5_m_one_way"] for row in arch["cases"]], marker="o", label=arch["name"])
    axis.set(ylabel="Wire loss (W)", title="2.5 mm² copper, 0.5 m one-way lead")
    axis.tick_params(axis="x", rotation=18); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "wiring_loss_vs_architecture.png", dpi=150); plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "powertrain")
    parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    summary = make_summary(config, load_clean_cases())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.no_plots:
        make_plots(summary, args.output)
    print(f"LR1600 powertrain architecture: {args.output / 'summary.json'}")


if __name__ == "__main__":
    main()
