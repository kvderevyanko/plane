#!/usr/bin/env python3
"""LR1600 preliminary battery/avionics packaging study.

This is an internal-volume and CG-kinematics study, not fuselage CAD and not
a hardware selection.  The cuboids are deliberately labelled study envelopes:
their values must be replaced by selected-pack measurements before any
fuselage geometry is released.  Aircraft reference data are read through the
typed configuration; no layout datum is introduced here.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import AircraftConfig, MassComponentConfig, load_aircraft_config
from scripts.mass_properties import calculate_mass_properties


@dataclass(frozen=True)
class Box:
    """Axis-aligned internal/component envelope in mm, centered in Y/Z."""

    length_mm: float
    width_mm: float
    height_mm: float

    def __post_init__(self) -> None:
        if min(self.length_mm, self.width_mm, self.height_mm) <= 0:
            raise ValueError("box dimensions must be positive")


@dataclass(frozen=True)
class BatteryStudyCase:
    usable_energy_wh: float
    mass_g: float
    envelope: Box

    def __post_init__(self) -> None:
        if self.usable_energy_wh <= 0 or self.mass_g <= 0:
            raise ValueError("battery energy and mass must be positive")


# Packaging study cases, not a chosen pack, chemistry, cell layout or mass
# ledger entry.  They simply reserve a removable rectangular volume across the
# requested usable-energy sweep.
BATTERY_STUDY_CASES = (
    BatteryStudyCase(100.0, 570.0, Box(150.0, 55.0, 42.0)),
    BatteryStudyCase(150.0, 850.0, Box(190.0, 65.0, 45.0)),
    BatteryStudyCase(200.0, 1140.0, Box(230.0, 70.0, 50.0)),
    BatteryStudyCase(250.0, 1420.0, Box(270.0, 75.0, 55.0)),
)
NON_BATTERY_MASS_STUDY_G = (1400.0, 1600.0, 1800.0, 2000.0)
NON_BATTERY_X_STUDY_MM = (50.0, 75.0, 100.0)

# The following are clearance/service allowances, never an external fuselage
# shape.  The payload envelope is intentionally rectangular and conservative.
BATTERY_SIDE_CLEARANCE_MM = 5.0
BATTERY_VERTICAL_CLEARANCE_MM = 5.0
BATTERY_END_CLEARANCE_MM = 15.0
AVIONICS_SERVICE_BAY = Box(150.0, 75.0, 45.0)
NOSE_FP_V_BAY = Box(85.0, 65.0, 45.0)
WING_ATTACHMENT_EXCLUSION_LENGTH_MM = 65.0


def cg_x_mm(non_battery_mass_g: float, non_battery_x_mm: float, battery: BatteryStudyCase, battery_x_mm: float) -> float:
    """Estimated configuration CG using the shared ledger calculator."""
    if non_battery_mass_g <= 0 or battery.mass_g <= 0:
        raise ValueError("masses must be positive")
    result = calculate_mass_properties((
        MassComponentConfig("study_non_battery", "Study non-battery remainder", "design_estimate", non_battery_mass_g, non_battery_x_mm, 0.0, 0.0, "center", None),
        MassComponentConfig("study_battery", "Study battery", "design_estimate", battery.mass_g, battery_x_mm, 0.0, 0.0, "center", None),
    ))
    if not result.has_estimated_configuration_cg or result.estimated_x_cg_mm is None:
        raise RuntimeError("battery CG study failed to produce an estimated configuration CG")
    return result.estimated_x_cg_mm


def battery_x_for_target_cg_mm(non_battery_mass_g: float, non_battery_x_mm: float, battery: BatteryStudyCase, target_cg_x_mm: float) -> float:
    """Solve the required battery CG location for a target aircraft CG."""
    if non_battery_mass_g <= 0 or battery.mass_g <= 0:
        raise ValueError("masses must be positive")
    return ((non_battery_mass_g + battery.mass_g) * target_cg_x_mm - non_battery_mass_g * non_battery_x_mm) / battery.mass_g


def cg_shift_for_battery_translation_mm(battery_mass_g: float, total_mass_g: float, translation_mm: float) -> float:
    """Exact rigid-configuration CG change from a longitudinal pack shift."""
    if battery_mass_g <= 0 or total_mass_g <= 0 or battery_mass_g > total_mass_g:
        raise ValueError("battery mass must be positive and no greater than total mass")
    return battery_mass_g / total_mass_g * translation_mm


def internal_payload_envelope(cases: tuple[BatteryStudyCase, ...] = BATTERY_STUDY_CASES[:2],
                              travel_min_mm: float = -30.0, travel_max_mm: float = 30.0) -> dict[str, float]:
    """Required *internal* packaging volume; it expressly defines no skin."""
    if not cases:
        raise ValueError("at least one battery case is required")
    max_box = max((case.envelope for case in cases), key=lambda box: box.length_mm * box.width_mm * box.height_mm)
    if travel_min_mm >= travel_max_mm:
        raise ValueError("battery travel minimum must be below maximum")
    battery_bay_length = max_box.length_mm + 2.0 * BATTERY_END_CLEARANCE_MM + (travel_max_mm - travel_min_mm)
    useful_length = NOSE_FP_V_BAY.length_mm + AVIONICS_SERVICE_BAY.length_mm + battery_bay_length + WING_ATTACHMENT_EXCLUSION_LENGTH_MM
    return {
        "minimum_internal_width_mm": 120.0,
        "minimum_internal_height_mm": 90.0,
        "battery_bay_length_mm": battery_bay_length,
        "useful_internal_fuselage_length_mm": useful_length,
        "battery_adjustment_travel_mm": travel_max_mm - travel_min_mm,
    }


def make_summary(config: AircraftConfig) -> dict[str, Any]:
    mac_le = config.wing.mean_aerodynamic_chord_leading_edge_x_mm
    mac = config.wing.mean_aerodynamic_chord_mm
    cg = config.cg.initial_envelope
    if not cg.is_defined or cg.x_mac_fraction_min is None or cg.x_mac_fraction_max is None:
        raise ValueError("battery CG study requires a defined initial design CG envelope")
    cg_band = (mac_le + cg.x_mac_fraction_min * mac, mac_le + cg.x_mac_fraction_max * mac)
    first_flight = config.cg.first_flight_recommendation.x_mac_fraction
    first_flight_x = None if first_flight is None else mac_le + first_flight * mac
    total_mass = config.aircraft.target_mass_g
    battery_config = config.battery
    if not battery_config.is_defined or battery_config.x_adjustment_min_mm is None or battery_config.x_adjustment_max_mm is None:
        raise ValueError("battery packaging study requires typed preliminary travel")
    travel_min, travel_max = battery_config.x_adjustment_min_mm, battery_config.x_adjustment_max_mm
    travel_points = tuple(travel_min + (travel_max - travel_min) * index / 6.0 for index in range(7))
    non_battery_sensitivity = []
    for case in BATTERY_STUDY_CASES:
        for non_battery_mass in NON_BATTERY_MASS_STUDY_G:
            for non_battery_x in NON_BATTERY_X_STUDY_MM:
                non_battery_sensitivity.append({
                    "battery_usable_energy_wh": case.usable_energy_wh,
                    "battery_mass_g": case.mass_g,
                    "non_battery_mass_g": non_battery_mass,
                    "non_battery_x_mm": non_battery_x,
                    "estimated_configuration_mass_g": non_battery_mass + case.mass_g,
                    "battery_x_for_design_cg_min_mm": battery_x_for_target_cg_mm(non_battery_mass, non_battery_x, case, cg_band[0]),
                    "battery_x_for_first_flight_cg_mm": None if first_flight_x is None else battery_x_for_target_cg_mm(non_battery_mass, non_battery_x, case, first_flight_x),
                    "battery_x_for_design_cg_max_mm": battery_x_for_target_cg_mm(non_battery_mass, non_battery_x, case, cg_band[1]),
                })
    return {
        "status": "study_cases_only_not_hardware_or_fuselage_geometry",
        "coordinate_system": "root-wing-LE datum; +X aft; mm",
        "cg_targets_mm": {"design_min": cg_band[0], "design_max": cg_band[1], "first_flight_preliminary": first_flight_x},
        "battery_study_cases": [asdict(case) for case in BATTERY_STUDY_CASES],
        "cg_translation_sensitivity_mm": {
            str(int(case.usable_energy_wh)): {
                str(int(shift)): cg_shift_for_battery_translation_mm(case.mass_g, total_mass, shift)
                for shift in travel_points
            } for case in BATTERY_STUDY_CASES
        },
        "non_battery_mass_cg_sensitivity": non_battery_sensitivity,
        "mass_properties_reuse_input_contract": {
            "required": ["resolved/design-estimate non_battery_mass_g", "resolved/design-estimate non_battery_x_mm", "battery mass_g", "battery X travel limits"],
            "calculation": "battery_x_for_target_cg_mm(non_battery_mass_g, non_battery_x_mm, battery_case, target_cg_x_mm)",
            "output_status": "estimated configuration CG only until every ledger item is measured/known",
        },
        "internal_payload_envelope_mm": internal_payload_envelope(travel_min_mm=travel_min, travel_max_mm=travel_max),
        "component_placement_constraints": {
            "battery": "principal movable mass; removable rail/tray; positive retention; no cell compression",
            "esc": "place in airflow near motor but upstream of propeller plane; minimize high-current loop",
            "flight_controller": "vibration-isolated near CG; serviceable; separated from high-current wiring",
            "gnss_compass": "remote from motor, ESC and high-current conductors; final separation requires hardware/EMI validation",
            "receiver_vtx": "separate antennas and keep VTX thermal load away from GNSS/receiver",
            "motor_propeller": "pusher X/Z plane remains TBD until typed propulsion geometry is selected",
        },
        "tbd": [
            "selected battery chemistry, cell layout, measured mass and outer dimensions",
            "non-battery resolved mass and X moment needed to solve an actual battery X window",
            "motor propeller plane, motor envelope and ESC envelope",
            "external fuselage skin, wing attachment geometry, hatch and retention proof load",
            "measured EMI separation, cooling flow and wiring/connector routing",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "packaging" / "summary.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(make_summary(load_aircraft_config()), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
