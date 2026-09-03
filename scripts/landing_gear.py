#!/usr/bin/env python3
"""Deterministic preliminary LR1600 rough-field gear and prop-clearance screen."""
from __future__ import annotations
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.config import load_aircraft_config
from scripts.hardware import load_hardware_config

WHEEL_GEAR_IDS = ("main_landing_gear", "nose_landing_gear", "landing_gear_fasteners")


def _required_mass_g(hardware, component_id: str) -> float:
    mass_g = hardware.component(component_id).mass_g
    if mass_g is None:
        raise ValueError(f"{component_id} needs a mass estimate")
    return float(mass_g)

def summary() -> dict:
    c = load_aircraft_config()
    hardware = load_hardware_config()
    g, gear = c.aircraft.gravity_m_s2, c.ground_operations
    assert gear.nose_architecture is not None
    assert gear.static_propeller_axis_height_mm is not None and gear.propeller_diameter_mm is not None
    static = gear.static_propeller_axis_height_mm - gear.propeller_diameter_mm / 2
    compression, attitude, one_wheel, rut, wear = 18.0, (gear.main_wheel_x_mm - c.propulsion.propeller_plane_x_mm) * -1.0, 5.0, 20.0, 5.0
    attitude_loss = abs(attitude) * __import__('math').sin(__import__('math').radians(gear.rotation_tail_down_deg))
    full = static - compression - attitude_loss - one_wheel - rut - wear
    w = c.aircraft.target_mass_kg * g
    return {"schema":"lr1600-landing-gear-v3", "status":"preliminary_design_estimate_not_certification",
      "input":{"mtow_g":c.aircraft.target_mass_g,"main_wheel_diameter_mm":gear.main_wheel_diameter_mm,"nose_wheel_diameter_mm":gear.nose_wheel_diameter_mm,"goal_mm":gear.dynamic_tip_clearance_goal_mm},
      "prop_clearance_mm":{"static":static,"compressed":static-compression,"tail_low":static-compression-attitude_loss,"one_main":static-compression-attitude_loss-one_wheel,"full_rough":full,"deductions":{"compression":compression,"tail_low_attitude":attitude_loss,"one_main":one_wheel,"rut":rut,"wear_build":wear}},
      "loads_n":{"normal_main":w*2*.9/2*1.35,"rough_main":w*3.5*.85/2*1.35,"one_main_governing":w*3.5*1.35,"taxi_main":w*2.5*1.35,"nose_proof":60.0,"side_longitudinal_proof":35.0},
      "nose_architecture":{
        "heading":gear.nose_architecture.heading,
        "anti_rotation":gear.nose_architecture.anti_rotation,
        "compliance":gear.nose_architecture.compliance,
        "seasonal_axle_interface":gear.nose_architecture.seasonal_axle_interface,
        "yaw_freedom":gear.nose_architecture.yaw_freedom,
        "excluded_items":["steering_linkage","steering_servo_connection","servo_saver","steering_arm","steering_cable","yaw_stops"]},
      "masses_g":{
        "wheel_gear":sum(_required_mass_g(hardware, item_id) for item_id in WHEEL_GEAR_IDS),
        "ski_module_replacing_wheels":_required_mass_g(hardware, "winter_ski_module")},
      "passes_goal":full >= gear.dynamic_tip_clearance_goal_mm}

def main() -> None:
    out=ROOT/'analysis'/'landing-gear'/'summary.json'; out.parent.mkdir(parents=True,exist_ok=True); out.write_text(json.dumps(summary(),indent=2)+'\n'); print(out)
if __name__=='__main__': main()
