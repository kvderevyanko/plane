#!/usr/bin/env python3
"""Parametric LR1600 propulsion and energy requirement sizing.

This is deliberately a requirements model, not a component selector.
The aircraft geometry continues to come from ``config/aircraft.yaml``; the
existing clean XFOIL polars provide only the wing contribution.  A transparent
CdA sweep represents all remaining aircraft parasite drag until its geometry
can be defined and tested.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import AircraftConfig, load_aircraft_config
from scripts.run_airfoil_analysis import RHO, required_cl, wing_curve_at_speed


SPEEDS_KM_H = (60.0, 70.0, 80.0, 90.0)
MASSES_G = (2200.0, 2400.0, 2600.0, 2800.0)
CLIMB_RATES_M_S = (2.0, 3.0, 4.0)
CLIMB_STUDY_SPEEDS_KM_H = (60.0,)
USABLE_ENERGY_WH = (100.0, 150.0, 200.0, 250.0)
PARASITIC_CDA_M2 = (0.006, 0.012, 0.020)
PROPELLER_EFFICIENCY = (0.55, 0.65, 0.75)
MOTOR_EFFICIENCY = (0.80, 0.87, 0.90)
ESC_EFFICIENCY = (0.97, 0.98, 0.99)
# No LR1600 value is assumed.  The function accepts any future measured bus
# load; the committed result uses 0 W only as a clearly-labelled propulsion
# reference, not an aircraft endurance claim.
HOTEL_LOAD_W_STUDY = (0.0,)
HEADWINDS_M_S = (0.0, 5.0, 8.0, 10.0, 12.0)
OSWALD_E = 0.90
INTEGRATION_POWER_MARGIN = 1.25
_WING_DRAG_CACHE: dict[tuple[int, AircraftConfig, float, float, float], float] = {}


@dataclass(frozen=True)
class Efficiency:
    propeller: float
    motor: float
    esc: float

    @property
    def total(self) -> float:
        return self.propeller * self.motor * self.esc


@dataclass(frozen=True)
class FlightPoint:
    mass_kg: float
    speed_m_s: float
    parasitic_cda_m2: float
    wing_drag_n: float
    parasitic_drag_n: float
    total_drag_n: float
    required_thrust_n: float
    aerodynamic_power_w: float
    shaft_power_w: float
    electrical_propulsion_w: float
    electrical_total_w: float
    climb_rate_m_s: float
    hotel_load_w: float
    efficiency: Efficiency


def kmh_to_mps(speed_km_h: float) -> float:
    if speed_km_h < 0:
        raise ValueError("speed must not be negative")
    return speed_km_h / 3.6


def mps_to_kmh(speed_m_s: float) -> float:
    if speed_m_s < 0:
        raise ValueError("speed must not be negative")
    return speed_m_s * 3.6


def dynamic_pressure(speed_m_s: float, rho_kg_m3: float = RHO) -> float:
    if speed_m_s <= 0 or rho_kg_m3 <= 0:
        raise ValueError("speed and density must be positive")
    return 0.5 * rho_kg_m3 * speed_m_s**2


def electrical_power_w(shaft_power_w: float, efficiency: Efficiency, hotel_load_w: float = 0.0) -> float:
    if shaft_power_w < 0 or hotel_load_w < 0:
        raise ValueError("power inputs must not be negative")
    if not all(0 < value <= 1 for value in (efficiency.propeller, efficiency.motor, efficiency.esc)):
        raise ValueError("all efficiencies must be in (0, 1]")
    return shaft_power_w / efficiency.total + hotel_load_w


def endurance_hours(usable_energy_wh: float, electrical_total_w: float) -> float:
    if usable_energy_wh <= 0 or electrical_total_w <= 0:
        raise ValueError("usable energy and electrical power must be positive")
    return usable_energy_wh / electrical_total_w


def still_air_range_km(endurance_h: float, true_airspeed_m_s: float) -> float:
    if endurance_h < 0 or true_airspeed_m_s <= 0:
        raise ValueError("endurance must not be negative and speed must be positive")
    return endurance_h * mps_to_kmh(true_airspeed_m_s)


def ground_range_km(endurance_h: float, true_airspeed_m_s: float, headwind_m_s: float) -> float:
    if headwind_m_s < 0:
        raise ValueError("headwind must not be negative")
    groundspeed = true_airspeed_m_s - headwind_m_s
    if groundspeed <= 0:
        raise ValueError("headwind must be lower than true airspeed")
    return endurance_h * mps_to_kmh(groundspeed)


def load_clean_cases(analysis_root: Path = ROOT / "analysis" / "aero") -> list[dict[str, Any]]:
    """Read existing clean polar artefacts; no XFOIL execution occurs here."""
    summary = json.loads((analysis_root / "summary.json").read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    for item in summary["two_d_cases"]:
        if item["scenario"] != "clean":
            continue
        path = ROOT / item["parsed_csv"]
        with path.open(newline="", encoding="utf-8") as stream:
            rows = [{key: float(value) if key != "source" else value for key, value in row.items()} for row in csv.DictReader(stream)]
        cases.append({"reynolds": item["reynolds"], "scenario": "clean", "rows": rows})
    if not cases:
        raise ValueError("no clean wing polar cases are available")
    return cases


def _interpolate_curve_at_cl(curve: list[dict[str, float]], cl_target: float) -> float:
    """Return the profile CD at required CL without post-stall extrapolation."""
    ordered = sorted(curve, key=lambda sample: sample["cl"])
    for low, high in zip(ordered, ordered[1:]):
        if low["cl"] <= cl_target <= high["cl"]:
            fraction = (cl_target - low["cl"]) / (high["cl"] - low["cl"])
            return low["profile_cd_area_weighted"] + fraction * (high["profile_cd_area_weighted"] - low["profile_cd_area_weighted"])
    raise ValueError(f"required CL {cl_target:.3f} is outside the supported clean wing curve")


def wing_drag_n(config: AircraftConfig, clean_cases: list[dict[str, Any]], mass_kg: float, speed_m_s: float, oswald_e: float = OSWALD_E) -> float:
    if mass_kg <= 0 or speed_m_s <= 0 or not 0 < oswald_e <= 1:
        raise ValueError("mass, speed, and Oswald efficiency must be positive")
    key = (id(clean_cases), config, mass_kg, speed_m_s, oswald_e)
    cached = _WING_DRAG_CACHE.get(key)
    if cached is not None:
        return cached
    cl = required_cl(mass_kg, speed_m_s, config.wing.area_m2, config.aircraft.gravity_m_s2)
    curve = wing_curve_at_speed(config, clean_cases, "clean", oswald_e, speed_m_s)
    profile_cd = _interpolate_curve_at_cl(curve, cl)
    aspect_ratio = (config.wing.span_mm / 1000.0) ** 2 / config.wing.area_m2
    induced_cd = cl**2 / (math.pi * oswald_e * aspect_ratio)
    result = dynamic_pressure(speed_m_s) * config.wing.area_m2 * (profile_cd + induced_cd)
    _WING_DRAG_CACHE[key] = result
    return result


def evaluate_flight_point(config: AircraftConfig, clean_cases: list[dict[str, Any]], *, mass_kg: float, speed_m_s: float,
                          parasitic_cda_m2: float, efficiency: Efficiency, hotel_load_w: float = 0.0,
                          climb_rate_m_s: float = 0.0) -> FlightPoint:
    if mass_kg <= 0 or speed_m_s <= 0 or parasitic_cda_m2 < 0 or climb_rate_m_s < 0:
        raise ValueError("mass/speed must be positive; CdA and climb rate must not be negative")
    wing = wing_drag_n(config, clean_cases, mass_kg, speed_m_s)
    parasite = dynamic_pressure(speed_m_s) * parasitic_cda_m2
    total_drag = wing + parasite
    climb_thrust = mass_kg * config.aircraft.gravity_m_s2 * climb_rate_m_s / speed_m_s
    required_thrust = total_drag + climb_thrust
    aerodynamic = total_drag * speed_m_s
    shaft = aerodynamic + mass_kg * config.aircraft.gravity_m_s2 * climb_rate_m_s
    electrical_propulsion = electrical_power_w(shaft, efficiency)
    electrical_total = electrical_power_w(shaft, efficiency, hotel_load_w)
    return FlightPoint(mass_kg, speed_m_s, parasitic_cda_m2, wing, parasite, total_drag, required_thrust,
                       aerodynamic, shaft, electrical_propulsion, electrical_total, climb_rate_m_s,
                       hotel_load_w, efficiency)


def _point_dict(point: FlightPoint) -> dict[str, Any]:
    result = asdict(point)
    result["speed_km_h"] = mps_to_kmh(point.speed_m_s)
    result["efficiency"]["total"] = point.efficiency.total
    return result


def _range(values: Iterable[float]) -> dict[str, float]:
    values = list(values)
    return {"min": min(values), "max": max(values)}


def make_summary(config: AircraftConfig, clean_cases: list[dict[str, Any]]) -> dict[str, Any]:
    efficiency_cases = tuple(Efficiency(*values) for values in (
        (min(PROPELLER_EFFICIENCY), min(MOTOR_EFFICIENCY), min(ESC_EFFICIENCY)),
        (0.65, 0.87, 0.98),
        (max(PROPELLER_EFFICIENCY), max(MOTOR_EFFICIENCY), max(ESC_EFFICIENCY)),
    ))
    nominal_efficiency = efficiency_cases[1]
    cruise = []
    for speed_km_h in SPEEDS_KM_H:
        speed = kmh_to_mps(speed_km_h)
        points = [evaluate_flight_point(config, clean_cases, mass_kg=config.aircraft.target_mass_kg, speed_m_s=speed,
                                        parasitic_cda_m2=cda, efficiency=eff, hotel_load_w=hotel)
                  for cda in PARASITIC_CDA_M2 for eff in efficiency_cases for hotel in HOTEL_LOAD_W_STUDY]
        nominal = evaluate_flight_point(config, clean_cases, mass_kg=config.aircraft.target_mass_kg, speed_m_s=speed,
                                        parasitic_cda_m2=PARASITIC_CDA_M2[1], efficiency=nominal_efficiency, hotel_load_w=0.0)
        cruise.append({"speed_km_h": speed_km_h, "nominal_energy_only": _point_dict(nominal),
                       "thrust_n": _range(point.required_thrust_n for point in points),
                       "shaft_power_w": _range(point.shaft_power_w for point in points),
                       "electrical_total_w_including_hotel_study": _range(point.electrical_total_w for point in points)})

    climb = []
    for speed_km_h in CLIMB_STUDY_SPEEDS_KM_H:
        for rate in CLIMB_RATES_M_S:
            points = [evaluate_flight_point(config, clean_cases, mass_kg=config.aircraft.target_mass_kg,
                                             speed_m_s=kmh_to_mps(speed_km_h), parasitic_cda_m2=cda,
                                             efficiency=eff, hotel_load_w=hotel, climb_rate_m_s=rate)
                      for cda in PARASITIC_CDA_M2 for eff in efficiency_cases for hotel in HOTEL_LOAD_W_STUDY]
            climb.append({"speed_km_h": speed_km_h, "climb_rate_m_s": rate,
                          "thrust_n": _range(point.required_thrust_n for point in points),
                          "shaft_power_w": _range(point.shaft_power_w for point in points),
                          "electrical_total_w_including_hotel_study": _range(point.electrical_total_w for point in points)})

    mass_feedback = []
    for mass_g in MASSES_G:
        for speed_km_h in SPEEDS_KM_H:
            points = [evaluate_flight_point(config, clean_cases, mass_kg=mass_g / 1000.0, speed_m_s=kmh_to_mps(speed_km_h),
                                             parasitic_cda_m2=cda, efficiency=eff)
                      for cda in PARASITIC_CDA_M2 for eff in efficiency_cases]
            mass_feedback.append({"mass_g": mass_g, "speed_km_h": speed_km_h,
                                  "thrust_n": _range(point.required_thrust_n for point in points),
                                  "electrical_propulsion_w": _range(point.electrical_propulsion_w for point in points)})

    energy = []
    # Nominal CdA/efficiency is only the central study case; hotel remains an explicit input sweep.
    for energy_wh in USABLE_ENERGY_WH:
        for speed_km_h in SPEEDS_KM_H:
            for hotel in HOTEL_LOAD_W_STUDY:
                point = evaluate_flight_point(config, clean_cases, mass_kg=config.aircraft.target_mass_kg,
                                              speed_m_s=kmh_to_mps(speed_km_h), parasitic_cda_m2=PARASITIC_CDA_M2[1],
                                              efficiency=nominal_efficiency, hotel_load_w=hotel)
                hours = endurance_hours(energy_wh, point.electrical_total_w)
                energy.append({"usable_energy_wh": energy_wh, "speed_km_h": speed_km_h, "hotel_load_w": hotel,
                               "electrical_total_w": point.electrical_total_w, "endurance_h": hours,
                               "still_air_range_km": still_air_range_km(hours, point.speed_m_s)})

    headwind = []
    # Display case rather than a range guarantee: 200 Wh, 70 km/h TAS, nominal drag/efficiency, no unresolved hotel load.
    point = evaluate_flight_point(config, clean_cases, mass_kg=config.aircraft.target_mass_kg, speed_m_s=kmh_to_mps(70),
                                  parasitic_cda_m2=PARASITIC_CDA_M2[1], efficiency=nominal_efficiency)
    hours = endurance_hours(200.0, point.electrical_total_w)
    for wind in HEADWINDS_M_S:
        headwind.append({"usable_energy_wh": 200.0, "tas_km_h": 70.0, "headwind_m_s": wind,
                         "groundspeed_km_h": mps_to_kmh(point.speed_m_s - wind),
                         "range_km": ground_range_km(hours, point.speed_m_s, wind)})

    peak_min = min(entry["electrical_total_w_including_hotel_study"]["min"] for entry in climb)
    peak_base = max(entry["electrical_total_w_including_hotel_study"]["max"] for entry in climb)
    continuous_min = min(entry["electrical_total_w_including_hotel_study"]["min"] for entry in cruise)
    continuous_base = max(entry["electrical_total_w_including_hotel_study"]["max"] for entry in cruise)
    return {
        "schema": "lr1600-propulsion-sizing-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "source_inputs": {"aircraft_yaml": "config/aircraft.yaml", "wing_aero_summary": "analysis/aero/summary.json",
                          "wing_clean_polars": "analysis/aero/parsed/*_clean.csv"},
        "known": {"target_mass_g": config.aircraft.target_mass_g, "wing_area_m2": config.wing.area_m2,
                  "mission_airspeed_km_h": list(SPEEDS_KM_H), "wing_only_aero_status": "not used as full-aircraft drag"},
        "design_assumptions": {"atmosphere": "ISA sea level", "rho_kg_m3": RHO, "oswald_e": OSWALD_E,
            "parasitic_cda_m2": list(PARASITIC_CDA_M2), "parasitic_drag_formula": "D_parasitic = 0.5*rho*V^2*CdA",
            "propeller_efficiency": list(PROPELLER_EFFICIENCY), "motor_efficiency": list(MOTOR_EFFICIENCY),
            "esc_efficiency": list(ESC_EFFICIENCY), "hotel_load_battery_bus_w": None,
            "hotel_load_result_treatment": "0 W results are propulsion-only references; replace with measured battery-bus average load for aircraft endurance/range.",
            "climb_study_speed_km_h": list(CLIMB_STUDY_SPEEDS_KM_H),
            "integration_power_margin_factor": INTEGRATION_POWER_MARGIN,
            "battery_energy_definition": "usable energy already excludes the future battery reserve/unusable fraction; it is not pack nominal energy"},
        "tbd": ["mission endurance and range", "battery chemistry, series count, voltage sag curve, capacity and mass",
                "final hotel-load inventory and duty cycle", "motor, ESC, propeller and their measured maps", "fuselage/tail/boom geometry and measured full-aircraft CdA",
                "launch method and ground-run inputs", "propeller clearance and maximum diameter", "initial CG"],
        "hardware_selection": {"motor": None, "esc": None, "propeller": None, "battery": None,
                               "status": "intentionally unselected while TBD inputs remain"},
        "cruise_2400g": cruise, "climb_2400g": climb, "mass_feedback": mass_feedback,
        "energy_budget_nominal_drag_efficiency": energy, "headwind_display_case": headwind,
        "requirement_envelope": {"continuous_electrical_power_w_propulsion_only": {"minimum": continuous_min, "maximum": continuous_base,
            "selection_guidance": continuous_base * INTEGRATION_POWER_MARGIN},
            "peak_electrical_power_w_for_2_to_4_m_s_climb_propulsion_only": {"minimum": peak_min, "maximum": peak_base,
            "selection_guidance": peak_base * INTEGRATION_POWER_MARGIN},
            "launch": {"hand_launch": "TBD: demonstrate positive excess thrust at release/transition airspeed with the selected propeller map.",
                       "ground_takeoff": "TBD: requires rolling resistance, runway, rotation/liftoff speed and propeller static-thrust data; not numerically claimed."}},
        "limitations": ["CdA is a sizing sweep, not a measured LR1600 value.", "Wing contribution comes from clean XFOIL-derived polars and a finite-wing induced-drag estimate.",
                        "Static thrust, propeller RPM, current, voltage sag and thermal limits require selected hardware maps.",
                        "Energy/range values are still-air study estimates, not guaranteed mission range."],
    }


def make_plots(summary: dict[str, Any], output: Path) -> None:
    plots = output / "plots"; plots.mkdir(parents=True, exist_ok=True)
    cruise = summary["cruise_2400g"]
    speeds = [row["speed_km_h"] for row in cruise]
    fig, axis = plt.subplots(figsize=(7, 4.5)); axis.fill_between(speeds, [r["electrical_total_w_including_hotel_study"]["min"] for r in cruise], [r["electrical_total_w_including_hotel_study"]["max"] for r in cruise], alpha=.25, label="sensitivity envelope")
    axis.plot(speeds, [r["nominal_energy_only"]["electrical_total_w"] for r in cruise], marker="o", label="central energy-only case")
    axis.set(xlabel="True airspeed (km/h)", ylabel="Electrical power (W)", title="LR1600 cruise electrical power"); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "cruise_electrical_power.png", dpi=150); plt.close(fig)
    energy = summary["energy_budget_nominal_drag_efficiency"]
    fig, axes = plt.subplots(1, 2, figsize=(10, 4.5))
    for speed in SPEEDS_KM_H:
        subset = [r for r in energy if r["speed_km_h"] == speed and r["hotel_load_w"] == 0]
        axes[0].plot([r["usable_energy_wh"] for r in subset], [r["endurance_h"] for r in subset], marker="o", label=f"{speed:.0f} km/h")
        axes[1].plot([r["usable_energy_wh"] for r in subset], [r["still_air_range_km"] for r in subset], marker="o", label=f"{speed:.0f} km/h")
    axes[0].set(xlabel="Usable energy (Wh)", ylabel="Endurance (h)", title="Energy study (hotel = 0 W)"); axes[1].set(xlabel="Usable energy (Wh)", ylabel="Still-air range (km)", title="Energy study (hotel = 0 W)")
    for axis in axes: axis.grid(True, alpha=.3); axis.legend()
    fig.tight_layout(); fig.savefig(plots / "endurance_and_range.png", dpi=150); plt.close(fig)
    feedback = summary["mass_feedback"]
    fig, axis = plt.subplots(figsize=(7, 4.5))
    for speed in SPEEDS_KM_H:
        subset = [r for r in feedback if r["speed_km_h"] == speed]
        axis.plot([r["mass_g"] for r in subset], [r["electrical_propulsion_w"]["max"] for r in subset], marker="o", label=f"{speed:.0f} km/h")
    axis.set(xlabel="Aircraft mass (g)", ylabel="Electrical propulsion power, high case (W)", title="Mass feedback"); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "power_vs_mass.png", dpi=150); plt.close(fig)
    wind = summary["headwind_display_case"]
    fig, axis = plt.subplots(figsize=(7, 4.5)); axis.plot([r["headwind_m_s"] for r in wind], [r["range_km"] for r in wind], marker="o")
    axis.set(xlabel="Headwind (m/s)", ylabel="Ground range (km)", title="Headwind sensitivity: 200 Wh / 70 km/h display case"); axis.grid(True, alpha=.3); fig.tight_layout(); fig.savefig(plots / "headwind_sensitivity.png", dpi=150); plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "propulsion"); parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args()
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    result = make_summary(config, load_clean_cases())
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if not args.no_plots: make_plots(result, args.output)
    print(f"LR1600 propulsion sizing: {args.output / 'summary.json'}")


if __name__ == "__main__":
    main()
