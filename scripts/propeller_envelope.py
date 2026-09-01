#!/usr/bin/env python3
"""LR1600 pusher propeller working-envelope screening.

This companion to :mod:`scripts.propulsion_sizing` deliberately does *not*
predict a particular propeller's thrust.  The available aircraft model gives
the required thrust and shaft-power envelope, while propeller geometry, RPM,
pitch-speed and motor-KV relations are kinematic requirements.  A measured
propeller/motor map at installed airspeed is still required before hardware
selection.
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import AircraftConfig, load_aircraft_config
from scripts.propulsion_sizing import (
    Efficiency,
    PARASITIC_CDA_M2,
    evaluate_flight_point,
    kmh_to_mps,
    load_clean_cases,
)


INCH_M = 0.0254
RHO_KG_M3 = 1.225
SPEED_OF_SOUND_M_S = 340.0
CRUISE_SPEEDS_KM_H = (60.0, 70.0, 80.0, 90.0)
MAX_CRUISE_SPEED_KM_H = max(CRUISE_SPEEDS_KM_H)
PITCH_SPEED_MARGIN = (1.15, 1.35)
BOOM_OD_M_SCREEN = 0.020
BOOM_CLEARANCE_M_SCREEN = 0.030
# These ranges screen fixed-pitch working points.  They are not propeller SKUs.
STUDY_PROPS = (
    (12.0, (8500.0, 10000.0), (7.0, 8.0, 9.0), "fallback / higher-RPM"),
    (13.0, (7200.0, 9000.0), (8.0, 9.0, 10.0), "preferred study"),
    (14.0, (6500.0, 8200.0), (9.0, 10.0, 11.0), "preferred study; lowest disk loading"),
)
# Architecture comparison inputs only.  They are loaded-voltage study cases,
# not a battery selection or a discharge-curve substitute.
LOADED_BUS_VOLTAGE_BY_SERIES = {4: 14.0, 6: 21.0}
LOADED_RPM_FRACTION = (0.75, 0.85)
MOTOR_EFFICIENCY_STUDY = 0.87
ESC_EFFICIENCY_STUDY = 0.98
ELECTRICAL_POWER_SCREEN_W = (490.0, 670.0)


@dataclass(frozen=True)
class PropStudy:
    diameter_in: float
    rpm_range: tuple[float, float]
    pitch_in_values: tuple[float, ...]
    integration_note: str

    @property
    def diameter_m(self) -> float:
        return self.diameter_in * INCH_M


def _positive(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def prop_disk_area_m2(diameter_m: float) -> float:
    """Circular swept-disk area; spinner and blade-root blockage are TBD."""
    _positive(diameter_m, "diameter")
    return math.pi * diameter_m**2 / 4.0


def tip_speed_m_s(diameter_m: float, rpm: float) -> float:
    """Helical effects are excluded: this is the rotational tip component."""
    return math.pi * _positive(diameter_m, "diameter") * _positive(rpm, "rpm") / 60.0


def pitch_speed_km_h(pitch_in: float, rpm: float) -> float:
    """No-slip geometric pitch speed, not the actual aircraft airspeed."""
    return _positive(pitch_in, "pitch") * INCH_M * _positive(rpm, "rpm") * 60.0 / 1000.0


def rpm_for_pitch_speed(pitch_in: float, pitch_speed_km_h_target: float) -> float:
    return _positive(pitch_speed_km_h_target, "pitch speed") * 1000.0 / (_positive(pitch_in, "pitch") * INCH_M * 60.0)


def disk_loading_n_m2(thrust_n: float, diameter_m: float) -> float:
    return _positive(thrust_n, "thrust") / prop_disk_area_m2(diameter_m)


def motor_shaft_torque_nm(shaft_power_w: float, rpm: float) -> float:
    angular_speed = 2.0 * math.pi * _positive(rpm, "rpm") / 60.0
    return _positive(shaft_power_w, "shaft power") / angular_speed


def required_no_load_kv_rpm_per_v(rpm: float, loaded_voltage_v: float, loaded_rpm_fraction: float) -> float:
    """Required no-load Kv to obtain a loaded RPM under an explicit sag factor."""
    if not 0 < loaded_rpm_fraction <= 1:
        raise ValueError("loaded RPM fraction must be in (0, 1]")
    return _positive(rpm, "rpm") / (_positive(loaded_voltage_v, "loaded voltage") * loaded_rpm_fraction)


def radial_clearance_margin_m(
    diameter_m: float,
    boom_axis_y_m: float,
    boom_axis_z_m: float,
    boom_outer_diameter_m: float = BOOM_OD_M_SCREEN,
    required_clearance_m: float = BOOM_CLEARANCE_M_SCREEN,
) -> float:
    """Margin from a prop-disk edge to a boom, using actual radial distance."""
    _positive(diameter_m, "diameter")
    _positive(boom_outer_diameter_m, "boom outer diameter")
    if required_clearance_m < 0:
        raise ValueError("required clearance must not be negative")
    radial_distance = math.hypot(boom_axis_y_m, boom_axis_z_m)
    return radial_distance - (diameter_m / 2.0 + boom_outer_diameter_m / 2.0 + required_clearance_m)


def _range(values: list[float]) -> dict[str, float]:
    return {"minimum": min(values), "maximum": max(values)}


def _matching_pitch_combinations(study: PropStudy, pitch_speed_targets: tuple[float, float]) -> list[dict[str, float]]:
    """Pitch/RPM combinations whose no-slip pitch speed covers 90 km/h with margin."""
    combinations: list[dict[str, float]] = []
    for pitch in study.pitch_in_values:
        rpm_for_low = rpm_for_pitch_speed(pitch, pitch_speed_targets[0])
        rpm_for_high = rpm_for_pitch_speed(pitch, pitch_speed_targets[1])
        compatible_low = max(study.rpm_range[0], rpm_for_low)
        compatible_high = min(study.rpm_range[1], rpm_for_high)
        if compatible_low <= compatible_high:
            combinations.append({
                "pitch_in": pitch,
                "rpm_for_minimum_pitch_speed": rpm_for_low,
                "rpm_for_maximum_pitch_speed": rpm_for_high,
                "compatible_rpm_range": {"minimum": compatible_low, "maximum": compatible_high},
            })
    return combinations


def _preferred_rpm_schedule(pitches_in: tuple[float, ...]) -> list[dict[str, Any]]:
    """No-slip pitch-speed scheduling for the typed preferred pitch band."""
    schedule: list[dict[str, Any]] = []
    for speed_km_h in CRUISE_SPEEDS_KM_H:
        target = (speed_km_h * PITCH_SPEED_MARGIN[0], speed_km_h * PITCH_SPEED_MARGIN[1])
        by_pitch = []
        for pitch in pitches_in:
            by_pitch.append({
                "pitch_in": pitch,
                "rpm": {"minimum": rpm_for_pitch_speed(pitch, target[0]),
                        "maximum": rpm_for_pitch_speed(pitch, target[1])},
            })
        schedule.append({"TAS_km_h": speed_km_h,
                         "target_no_slip_pitch_speed_km_h": {"minimum": target[0], "maximum": target[1]},
                         "by_pitch": by_pitch})
    return schedule


def _thrust_requirements(config: AircraftConfig) -> dict[str, Any]:
    clean_cases = load_clean_cases()
    # Thrust is independent of prop/motor/ESC efficiency in this aircraft-force
    # calculation.  The arbitrary valid object only satisfies the shared API.
    efficiency = Efficiency(.65, .87, .98)
    cruise: list[dict[str, Any]] = []
    for speed_km_h in CRUISE_SPEEDS_KM_H:
        points = [evaluate_flight_point(config, clean_cases, mass_kg=config.aircraft.target_mass_kg,
                                        speed_m_s=kmh_to_mps(speed_km_h), parasitic_cda_m2=cda,
                                        efficiency=efficiency)
                  for cda in PARASITIC_CDA_M2]
        cruise.append({"speed_km_h": speed_km_h,
                       "required_thrust_n": _range([point.required_thrust_n for point in points]),
                       "central_cda_required_thrust_n": points[1].required_thrust_n})
    climb = [evaluate_flight_point(config, clean_cases, mass_kg=config.aircraft.target_mass_kg,
                                   speed_m_s=kmh_to_mps(60.0), parasitic_cda_m2=cda,
                                   efficiency=efficiency, climb_rate_m_s=4.0)
             for cda in PARASITIC_CDA_M2]
    return {
        "cruise": cruise,
        "60_km_h_4_m_s_climb_study": {
            "required_thrust_n": _range([point.required_thrust_n for point in climb]),
            "central_cda_required_thrust_n": climb[1].required_thrust_n,
        },
    }


def make_summary(config: AircraftConfig) -> dict[str, Any]:
    if not config.booms.is_defined or config.booms.lateral_offset_mm is None or config.booms.axis_z_mm is None:
        raise ValueError("propeller envelope requires defined preliminary boom axes")
    if not config.propulsion.is_defined or config.propulsion.propeller is None or config.propulsion.motor is None:
        raise ValueError("propeller envelope requires defined preliminary propulsion requirements")
    configured_propeller = config.propulsion.propeller
    configured_motor = config.propulsion.motor
    configured_diameters_in = (configured_propeller.diameter_min_mm / 25.4, configured_propeller.diameter_max_mm / 25.4)
    configured_pitches_in = (configured_propeller.pitch_min_mm / 25.4, configured_propeller.pitch_max_mm / 25.4)
    thrust = _thrust_requirements(config)
    pitch_speed_targets = tuple(multiplier * MAX_CRUISE_SPEED_KM_H for multiplier in PITCH_SPEED_MARGIN)
    all_cruise_thrust = [row["required_thrust_n"][bound] for row in thrust["cruise"] for bound in ("minimum", "maximum")]
    peak_thrust = thrust["60_km_h_4_m_s_climb_study"]["required_thrust_n"]["maximum"]
    propeller_cases: list[dict[str, Any]] = []
    for diameter_in, rpm_range, pitch_values, note in STUDY_PROPS:
        study = PropStudy(diameter_in, rpm_range, pitch_values, note)
        clearance_margin = radial_clearance_margin_m(study.diameter_m, config.booms.lateral_offset_mm / 1000.0,
                                                     config.booms.axis_z_mm / 1000.0)
        propeller_cases.append({
            "diameter_in": diameter_in,
            "diameter_mm": study.diameter_m * 1000.0,
            "integration_note": note,
            "disk_area_m2": prop_disk_area_m2(study.diameter_m),
            "rpm_study_range": {"minimum": rpm_range[0], "maximum": rpm_range[1]},
            "pitch_in_study_values": list(pitch_values),
            "tip_speed_m_s": _range([tip_speed_m_s(study.diameter_m, rpm) for rpm in rpm_range]),
            "tip_mach_isa_screen": _range([tip_speed_m_s(study.diameter_m, rpm) / SPEED_OF_SOUND_M_S for rpm in rpm_range]),
            "pitch_speed_km_h_full_study_bounds": _range([pitch_speed_km_h(pitch, rpm)
                                                            for pitch in pitch_values for rpm in rpm_range]),
            "pitch_speed_covering_90_km_h_with_margin": {
                "target_km_h": {"minimum": pitch_speed_targets[0], "maximum": pitch_speed_targets[1]},
                "pitch_rpm_combinations": _matching_pitch_combinations(study, pitch_speed_targets),
            },
            "required_thrust_disk_loading_n_m2": {
                "cruise_60_to_90_km_h_cda_sensitivity": _range([disk_loading_n_m2(value, study.diameter_m)
                                                                  for value in all_cruise_thrust]),
                "60_km_h_4_m_s_climb_high_cda_study": disk_loading_n_m2(peak_thrust, study.diameter_m),
            },
            "boom_radial_clearance_screen": {
                "screen_boom_OD_mm": BOOM_OD_M_SCREEN * 1000.0,
                "required_clearance_mm": BOOM_CLEARANCE_M_SCREEN * 1000.0,
                "margin_mm": clearance_margin * 1000.0,
                "passes": clearance_margin >= 0,
            },
        })

    # Torque depends on which point in the fixed-pitch working schedule is
    # selected.  The low end uses the 13/14 inch cruise range; the peak uses
    # the low end of the 14-inch range, which is conservative for torque.
    shaft_power_by_screen = [power * MOTOR_EFFICIENCY_STUDY * ESC_EFFICIENCY_STUDY for power in ELECTRICAL_POWER_SCREEN_W]
    central_aero_power = {"70_km_h": 74.93325367141362, "80_km_h": 109.08079088454167}
    central_shaft_power = {name: power / 0.65 for name, power in central_aero_power.items()}
    torque = {
        "central_cruise_aerodynamic_power_w": central_aero_power,
        "central_cruise_shaft_power_w_with_propeller_efficiency_0_65": central_shaft_power,
        "central_cruise_torque_nm": {
            "70_km_h_at_6500_to_7200_rpm": _range([motor_shaft_torque_nm(central_shaft_power["70_km_h"], rpm) for rpm in (6500.0, 7200.0)]),
            "80_km_h_at_7000_to_8000_rpm": _range([motor_shaft_torque_nm(central_shaft_power["80_km_h"], rpm) for rpm in (7000.0, 8000.0)]),
        },
        "electrical_power_integration_screen": [
            {"electrical_power_w": electrical, "motor_shaft_power_w": shaft,
             "torque_nm_at_6500_rpm": motor_shaft_torque_nm(shaft, 6500.0)}
            for electrical, shaft in zip(ELECTRICAL_POWER_SCREEN_W, shaft_power_by_screen)
        ],
    }
    kv_implications: dict[str, Any] = {}
    for series_count, voltage in LOADED_BUS_VOLTAGE_BY_SERIES.items():
        kv_cases = [required_no_load_kv_rpm_per_v(rpm, voltage, fraction)
                    for _, rpm_range, _, _ in STUDY_PROPS[1:] for rpm in rpm_range for fraction in LOADED_RPM_FRACTION]
        kv_implications[f"{series_count}S"] = {
            "loaded_voltage_study_v": voltage,
            "loaded_rpm_fraction_study": list(LOADED_RPM_FRACTION),
            "required_no_load_kv_for_13_to_14_in_rpm_envelope": _range(kv_cases),
        }

    return {
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "preliminary_design_assumption; no commercial propeller, motor, or battery selected",
        "known_from_config": {
            "target_mass_g": config.aircraft.target_mass_g,
            "boom_axis_y_mm_each": [-config.booms.lateral_offset_mm, config.booms.lateral_offset_mm],
            "boom_axis_z_mm": config.booms.axis_z_mm,
            "boom_center_spacing_mm": 2.0 * config.booms.lateral_offset_mm,
            "selected_preliminary_propeller": {
                "diameter_mm": [configured_propeller.diameter_min_mm, configured_propeller.diameter_max_mm],
                "pitch_mm": [configured_propeller.pitch_min_mm, configured_propeller.pitch_max_mm],
                "cruise_rpm": [configured_propeller.cruise_rpm_min, configured_propeller.cruise_rpm_max],
            },
            "selected_preliminary_motor_kv_rpm_per_v": [configured_motor.kv_min_rpm_per_v, configured_motor.kv_max_rpm_per_v],
        },
        "method_limits": [
            "Aircraft required thrust comes from the existing wing-polar plus full-aircraft CdA sensitivity model.",
            "Pitch speed is no-slip geometric pitch speed; it is not a propeller thrust or efficiency prediction.",
            "Disk loading uses required aircraft thrust divided by ideal swept-disk area; it excludes induced inflow and blade geometry.",
            "A measured thrust/power/RPM/airspeed map and installed thermal test remain mandatory before hardware selection.",
        ],
        "design_assumptions": {
            "air_density_kg_m3": RHO_KG_M3,
            "maximum_cruise_TAS_km_h": MAX_CRUISE_SPEED_KM_H,
            "pitch_speed_margin_over_maximum_TAS": list(PITCH_SPEED_MARGIN),
            "screen_boom_outer_diameter_mm": BOOM_OD_M_SCREEN * 1000.0,
            "screen_boom_clearance_mm": BOOM_CLEARANCE_M_SCREEN * 1000.0,
            "loaded_bus_voltage_by_architecture_study_v": LOADED_BUS_VOLTAGE_BY_SERIES,
            "loaded_rpm_fraction": list(LOADED_RPM_FRACTION),
            "motor_efficiency_for_power_to_torque_screen": MOTOR_EFFICIENCY_STUDY,
            "esc_efficiency_for_power_to_torque_screen": ESC_EFFICIENCY_STUDY,
        },
        "aircraft_thrust_requirement": thrust,
        "propeller_working_envelope": propeller_cases,
        "preferred_preliminary_envelope": {
            "diameter_in": list(configured_diameters_in),
            "preferred_pitch_in": list(configured_pitches_in),
            "configured_cruise_rpm": [configured_propeller.cruise_rpm_min, configured_propeller.cruise_rpm_max],
            "rpm_schedule_for_60_to_90_km_h_TAS": _preferred_rpm_schedule(configured_pitches_in),
            "top_speed_rpm_screen": {"13_in": [7200.0, 9000.0], "14_in": [6500.0, 8200.0]},
            "selected_motor_kv_rpm_per_v": [configured_motor.kv_min_rpm_per_v, configured_motor.kv_max_rpm_per_v],
            "basis": "13–14 inch reduces required disk loading relative to 12 inch while passing the current 460 mm radial-clearance screen.  The shared 9–10 inch pitch band spans the 60–90 km/h pitch-speed screen at throttle-dependent RPM.  14 inch has only about 12 mm screen margin, so actual boom Z, prop plane, deflection, spinner and mount geometry must be verified.",
        },
        "motor_implications": {"shaft_torque": torque, "kv_by_voltage_architecture": kv_implications},
        "tbd_before_selection": [
            "Measured propeller thrust, power, RPM and efficiency map versus 60–90 km/h airspeed.",
            "Installed propeller plane, boom Z offset, local boom deflection and spinner/mount geometry.",
            "Actual loaded-voltage curve, motor resistance/current limit and thermal capability.",
            "Noise, blade count, pitch geometry and motor shaft/adaptor interface.",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "aircraft.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "powertrain" / "propeller_envelope.json")
    args = parser.parse_args()
    summary = make_summary(load_aircraft_config(args.config))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
