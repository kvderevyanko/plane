#!/usr/bin/env python3
"""Reproducible preliminary LR1600 fuselage/CG integration ledger.

Mass values live once in ``config/hardware.yaml``.  This script only selects
seasonal/payload configurations, translates the battery, and derives the JSON
report; every result remains a design estimate, never a weighed flight release.
"""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import replace
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import load_aircraft_config
from scripts.hardware import HardwareComponent, load_hardware_config
from scripts.mass_properties import calculate_mass_properties


WHEEL_IDS = {"main_landing_gear", "nose_landing_gear", "landing_gear_fasteners"}


def resolved_baseline(items: Iterable[HardwareComponent]) -> list[HardwareComponent]:
    return [item for item in items if item.status in {"selected_preliminary", "design_estimate"} and item.mass_g is not None]


def estimate(items: Iterable[HardwareComponent], battery_x_mm: float) -> dict[str, float]:
    components = []
    for item in items:
        assert item.mass_g is not None and item.x_mm is not None and item.y_mm is not None and item.z_mm is not None
        x_mm = battery_x_mm if item.id == "flight_battery" else item.x_mm
        components.append(replace(item.as_mass_component(), x_mm=x_mm))  # type: ignore[arg-type]
    result = calculate_mass_properties(components)
    assert result.estimated_total_mass_g is not None
    assert result.estimated_x_cg_mm is not None and result.estimated_y_cg_mm is not None and result.estimated_z_cg_mm is not None
    return {"mass_g": result.estimated_total_mass_g, "x_cg_mm": result.estimated_x_cg_mm,
            "y_cg_mm": result.estimated_y_cg_mm, "z_cg_mm": result.estimated_z_cg_mm}


def with_optional(items: list[HardwareComponent], hardware, *, skis: bool, hd: bool) -> list[HardwareComponent]:
    result = list(items)
    if skis:
        result = [item for item in result if item.id not in WHEEL_IDS]
        result.append(hardware.component("winter_ski_module"))
    if hd:
        result.append(hardware.component("hd_recording_payload"))
    return result


def battery_solution(items: list[HardwareComponent], target_x_mm: float) -> float:
    battery = next(item for item in items if item.id == "flight_battery")
    assert battery.mass_g is not None
    fixed = [item for item in items if item.id != "flight_battery"]
    fixed_mass = sum(float(item.mass_g) for item in fixed)
    fixed_moment = sum(float(item.mass_g) * float(item.x_mm) for item in fixed)
    return ((fixed_mass + battery.mass_g) * target_x_mm - fixed_moment) / battery.mass_g


def mass_range_central_items(items: list[HardwareComponent]) -> dict[str, float]:
    """Use only component-local ranges from the one editable ledger."""
    output = {}
    for index, label in enumerate(("low_g", "central_g", "high_g")):
        total = 0.0
        for item in items:
            if item.mass_g is None:
                continue
            range_g = item.limits.get("mass_range_g")
            if range_g is None:
                values = (float(item.mass_g),) * 3
            else:
                if not isinstance(range_g, list) or len(range_g) != 2 or not all(isinstance(value, (int, float)) for value in range_g):
                    raise ValueError(f"{item.id}.limits.mass_range_g must be [low, high]")
                values = (float(range_g[0]), float(item.mass_g), float(range_g[1]))
            total += values[index]
        output[label] = total
    return output


def make_summary() -> dict:
    config, hardware = load_aircraft_config(), load_hardware_config()
    baseline = resolved_baseline(hardware.components)
    battery = hardware.component("flight_battery")
    targets = {f"{fraction * 100:.0f}_percent_mac": config.wing.mean_aerodynamic_chord_leading_edge_x_mm + fraction * config.wing.mean_aerodynamic_chord_mm
               for fraction in (.24, .25, .26, .28)}
    cases = {}
    for label, skis, hd in (("wheels", False, False), ("skis", True, False), ("wheels_with_hd", False, True)):
        items = with_optional(baseline, hardware, skis=skis, hd=hd)
        cases[label] = {
            "battery_x_for_targets_mm": {name: battery_solution(items, x) for name, x in targets.items()},
            "battery_positions": [
                {"position": name, "battery_x_mm": x, **estimate(items, x),
                 "cg_percent_mac": (estimate(items, x)["x_cg_mm"] - config.wing.mean_aerodynamic_chord_leading_edge_x_mm) / config.wing.mean_aerodynamic_chord_mm * 100.0}
                for name, x in (("forward_limit", hardware.battery_installation.x_min_mm),
                                ("nominal", hardware.battery_installation.x_nominal_mm),
                                ("aft_limit", hardware.battery_installation.x_max_mm))
            ],
        }
    wheel_nominal = cases["wheels"]["battery_positions"][1]
    wheel_targets = cases["wheels"]["battery_x_for_targets_mm"]
    rail = hardware.battery_installation
    closes_25 = rail.x_min_mm <= wheel_targets["25_percent_mac"] <= rail.x_max_mm
    return {
        "schema": "lr1600-fuselage-cg-integration-v1",
        "status": "complete_design_estimate_not_measured_or_flight_release",
        "coordinate_system": "wing root leading edge; +X aft; mm; masses g",
        "single_mass_source": "config/hardware.yaml components; this file is a derived report",
        "design_mass_case_g": config.aircraft.target_mass_g,
        "mac_reference": {"mac_mm": config.wing.mean_aerodynamic_chord_mm,
                          "mac_le_x_mm": config.wing.mean_aerodynamic_chord_leading_edge_x_mm,
                          "targets_x_mm": targets},
        "battery": {"model": battery.model, "mass_g": battery.mass_g,
                    "envelope_mm": {"x_length": battery.length_mm, "y_width": battery.width_mm, "z_height": battery.height_mm},
                    "rail_mm": {"forward": hardware.battery_installation.x_min_mm, "nominal": hardware.battery_installation.x_nominal_mm,
                                "aft": hardware.battery_installation.x_max_mm, "travel": hardware.battery_installation.x_max_mm - hardware.battery_installation.x_min_mm},
                    "removal": {"axis": hardware.battery_installation.removal_axis, "hatch_mm": [hardware.battery_installation.hatch_length_mm, hardware.battery_installation.hatch_width_mm, hardware.battery_installation.hatch_height_mm],
                                "status": "preliminary geometric reservation; physical mock-up and retention proof required"}},
        "mass_budget": {"central_components": [{"id": item.id, "mass_g": item.mass_g, "x_mm": item.x_mm, "y_mm": item.y_mm, "z_mm": item.z_mm}
                                                for item in baseline],
                        "wheels": mass_range_central_items(baseline),
                        "skis_central_g": estimate(with_optional(baseline, hardware, skis=True, hd=False), hardware.battery_installation.x_nominal_mm)["mass_g"],
                        "wheels_with_hd_central_g": estimate(with_optional(baseline, hardware, skis=False, hd=True), hardware.battery_installation.x_nominal_mm)["mass_g"],
                        "hd_payload_study_range_g": hardware.component("hd_recording_payload").limits["study_mass_range_g"]},
        "cg_cases": cases,
        "conclusions": {"wheels_25_percent_without_ballast": closes_25,
                        "working_2600g_coherent": closes_25 and wheel_nominal["mass_g"] <= config.aircraft.target_mass_g,
                        "margin_to_2600g_central_wheels": config.aircraft.target_mass_g - estimate(baseline, hardware.battery_installation.x_nominal_mm)["mass_g"],
                        "qualification_gates": ["weigh every assembly and obtain its actual moment", "prove pack retention and top-hatch removal with a physical dummy", "validate motor/13x10 combo, thermal behavior and vibration", "proof-test gear, wheel/skis interfaces and boom/motor hardpoints", "re-check all CG cases after selected hardware is weighed"]},
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "mass" / "summary.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(make_summary(), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output}")


if __name__ == "__main__":
    main()
