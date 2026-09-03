#!/usr/bin/env python3
"""Deterministic LR1600 rough-field landing and prop-clearance screen.

This is a bounded integration calculation, not a certification calculation or
a spring-leg sizing program.  It keeps the one-main roll, rut and wear terms
separate so a clearance allowance cannot silently disappear from a report.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any

from scripts.config import AircraftConfig, load_aircraft_config

ROOT = Path(__file__).resolve().parents[1]
MAIN_COMPRESSION_MM = 18.0
ONE_MAIN_ROLL_MM = 5.0
RUT_OR_STONE_MM = 20.0
WEAR_BUILD_MM = 5.0
ROUGH_LANDING_G = 3.5
PROOF_FACTOR = 1.35


def make_summary(config: AircraftConfig) -> dict[str, Any]:
    ground = config.ground_operations
    if not ground.is_defined:
        raise ValueError("ground_operations must be defined")
    required = (ground.propeller_diameter_mm, ground.static_propeller_axis_height_mm,
                ground.main_wheel_x_mm, ground.rotation_tail_down_deg)
    if any(value is None for value in required):
        raise ValueError("ground_operations has incomplete clearance inputs")
    if ground.nose_architecture is None:
        raise ValueError("ground_operations needs a nose architecture")

    weight_n = config.aircraft.target_mass_kg * config.aircraft.gravity_m_s2
    static_tip = ground.static_propeller_axis_height_mm - ground.propeller_diameter_mm / 2.0
    compressed = static_tip - MAIN_COMPRESSION_MM
    prop_x = config.propulsion.propeller_plane_x_mm
    if prop_x is None:
        raise ValueError("propeller plane must be defined")
    tail_loss = (prop_x - ground.main_wheel_x_mm) * math.sin(math.radians(ground.rotation_tail_down_deg))
    tail_low = compressed - tail_loss
    one_main = tail_low - ONE_MAIN_ROLL_MM
    full_rough = one_main - RUT_OR_STONE_MM - WEAR_BUILD_MM

    return {
        "schema": "lr1600-landing-gear-calculation-v2",
        "status": "preliminary_bounded_screen_not_certification",
        "mass_case_g": config.aircraft.target_mass_g,
        "weight_n": weight_n,
        "loads_n": {
            "normal_2g_90pct_main_each_operational": weight_n * 2.0 * .90 / 2.0,
            "rough_3_5g_85pct_main_each_operational": weight_n * ROUGH_LANDING_G * .85 / 2.0,
            "one_main_3_5g_operational": weight_n * ROUGH_LANDING_G,
            "one_main_3_5g_proof": weight_n * ROUGH_LANDING_G * PROOF_FACTOR,
            "taxi_2_5g_one_main_proof": weight_n * 2.5 * PROOF_FACTOR,
            "nose_3g_40pct_operational": weight_n * 3.0 * .40,
            "nose_3g_40pct_proof": weight_n * 3.0 * .40 * PROOF_FACTOR,
        },
        "nose_architecture": {
            "heading": ground.nose_architecture.heading,
            "anti_rotation": ground.nose_architecture.anti_rotation,
            "compliance": ground.nose_architecture.compliance,
            "seasonal_axle_interface": ground.nose_architecture.seasonal_axle_interface,
            "yaw_freedom": ground.nose_architecture.yaw_freedom,
        },
        "clearance_mm": {
            "static": static_tip,
            "both_mains_compressed": compressed,
            "compressed_tail_low": tail_low,
            "one_main_roll": one_main,
            "rut_or_stone_deduction": RUT_OR_STONE_MM,
            "wear_build_deduction": WEAR_BUILD_MM,
            "full_rough": full_rough,
            "goal": ground.dynamic_tip_clearance_goal_mm,
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "aircraft.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "landing-gear" / "calculated_summary.json")
    args = parser.parse_args()
    result = make_summary(load_aircraft_config(args.config))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
