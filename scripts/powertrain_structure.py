#!/usr/bin/env python3
"""Structural screening for LR1600 battery retention and pusher-motor interface.

This module converts the existing battery packaging study and propulsion
requirement envelope into *load-interface requirements*.  It deliberately
does not select a pack, motor, ESC, tube, fastener, adhesive, or a production
motor mount.  All loads are preliminary design/proof screens; a selected
hardware installation still needs its own data, local stress checks and a
representative proof article.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import AircraftConfig, load_aircraft_config
from scripts.packaging_study import BATTERY_STUDY_CASES, BatteryStudyCase


# These are integration/proof assumptions, not aircraft source-of-truth load
# cases.  The 4 g manoeuvre value itself comes from aircraft.yaml.
BATTERY_LANDING_EJECTION_FACTOR_G = 6.0
STRUCTURAL_PROOF_FACTOR = 1.5
BATTERY_PRIMARY_LOAD_PATHS = 2
MOTOR_ELECTRICAL_POWER_SCREEN_W = (490.0, 670.0)
MOTOR_EFFICIENCY_SCREEN = 0.87
ESC_EFFICIENCY_SCREEN = 0.98
MOTOR_PEAK_RPM_SCREEN = 6500.0
MOTOR_DYNAMIC_THRUST_SCREEN_N = 10.05
MOTOR_MASS_STUDY_G = (120.0, 180.0, 220.0)
MOTOR_CG_OFFSET_FROM_MOUNT_MM = 60.0
# Gatekeeper-selected battery mass convention used by the energy/packaging
# trade: 220 Wh/kg nominal pack energy and 0.80 usable fraction, rounded to
# practical study masses.  It is a study assumption, not a mass-ledger entry.
BATTERY_RETENTION_STUDY_MASSES_G = (570.0, 850.0, 1140.0, 1420.0)


def structural_battery_study_cases() -> tuple[BatteryStudyCase, ...]:
    """Use common energy/envelope cases with the gatekeeper mass convention.

    This module owns only structural reactions.  It intentionally mirrors the
    shared packaging envelope dimensions but does not alter that module or the
    aircraft source of truth.
    """
    if len(BATTERY_STUDY_CASES) != len(BATTERY_RETENTION_STUDY_MASSES_G):
        raise ValueError("battery packaging and structural study cases must have equal lengths")
    return tuple(
        BatteryStudyCase(case.usable_energy_wh, mass_g, case.envelope)
        for case, mass_g in zip(BATTERY_STUDY_CASES, BATTERY_RETENTION_STUDY_MASSES_G)
    )


def _positive(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def inertial_force_n(mass_g: float, load_factor_g: float, gravity_m_s2: float) -> float:
    """Inertial force in one prescribed direction; mass is supplied in grams."""
    return _positive(mass_g, "mass") / 1000.0 * _positive(load_factor_g, "load factor") * _positive(gravity_m_s2, "gravity")


def motor_shaft_torque_nm(shaft_power_w: float, rpm: float) -> float:
    """Steady shaft reaction torque from mechanical shaft power and speed."""
    omega_rad_s = 2.0 * math.pi * _positive(rpm, "rpm") / 60.0
    return _positive(shaft_power_w, "shaft power") / omega_rad_s


def battery_retention_case(case: BatteryStudyCase, config: AircraftConfig) -> dict[str, Any]:
    """Return direction-independent tray-retention load requirements.

    The six-g landing/ejection case is explicitly a packaging assumption.  It
    supplements, rather than replaces, the typed 4-g aircraft design context.
    The primary stops are split only for sizing symmetry; one failed stop must
    not permit pack escape, hence independent secondary retention is required.
    """
    flight = inertial_force_n(case.mass_g, config.aircraft.design_load_factor_g, config.aircraft.gravity_m_s2)
    ejection = inertial_force_n(case.mass_g, BATTERY_LANDING_EJECTION_FACTOR_G, config.aircraft.gravity_m_s2)
    proof = ejection * STRUCTURAL_PROOF_FACTOR
    return {
        "usable_energy_wh": case.usable_energy_wh,
        "study_mass_g": case.mass_g,
        "study_envelope_mm": asdict(case.envelope),
        "flight_4g_inertial_load_n_per_principal_direction": flight,
        "landing_ejection_6g_assumption_n_per_principal_direction": ejection,
        "proof_load_n_per_principal_direction": proof,
        "two_primary_stops_nominal_share_n": proof / BATTERY_PRIMARY_LOAD_PATHS,
        "load_directions_to_prove": ["+X", "-X", "+Z (anti-ejection)", "-Z", "+Y", "-Y"],
    }


def motor_interface_cases(config: AircraftConfig) -> list[dict[str, Any]]:
    """Pusher reaction/load screen, not a prediction of selected-prop thrust."""
    results: list[dict[str, Any]] = []
    for electrical_w in MOTOR_ELECTRICAL_POWER_SCREEN_W:
        shaft_w = electrical_w * MOTOR_EFFICIENCY_SCREEN * ESC_EFFICIENCY_SCREEN
        torque = motor_shaft_torque_nm(shaft_w, MOTOR_PEAK_RPM_SCREEN)
        results.append({
            "electrical_power_screen_w": electrical_w,
            "shaft_power_screen_w": shaft_w,
            "rpm_screen": MOTOR_PEAK_RPM_SCREEN,
            "shaft_reaction_torque_nm": torque,
            "proof_torque_nm": torque * STRUCTURAL_PROOF_FACTOR,
            "dynamic_propulsive_thrust_screen_n": MOTOR_DYNAMIC_THRUST_SCREEN_N,
            "proof_axial_thrust_n": MOTOR_DYNAMIC_THRUST_SCREEN_N * STRUCTURAL_PROOF_FACTOR,
        })
    for mass_g in MOTOR_MASS_STUDY_G:
        force = inertial_force_n(mass_g, config.aircraft.design_load_factor_g, config.aircraft.gravity_m_s2)
        results.append({
            "motor_mass_study_g": mass_g,
            "mount_offset_study_mm": MOTOR_CG_OFFSET_FROM_MOUNT_MM,
            "4g_motor_inertial_load_n": force,
            "4g_mount_bending_moment_nm": force * MOTOR_CG_OFFSET_FROM_MOUNT_MM / 1000.0,
            "proof_bending_moment_nm": force * MOTOR_CG_OFFSET_FROM_MOUNT_MM / 1000.0 * STRUCTURAL_PROOF_FACTOR,
        })
    return results


def make_summary(config: AircraftConfig) -> dict[str, Any]:
    if not config.booms.is_defined or config.booms.lateral_offset_mm is None:
        raise ValueError("powertrain structural screen requires defined twin-boom geometry")
    battery_cases = [battery_retention_case(case, config) for case in structural_battery_study_cases()]
    motor_cases = motor_interface_cases(config)
    return {
        "schema": "lr1600-powertrain-structure-v1",
        "generated_utc": datetime.now(timezone.utc).isoformat(),
        "status": "preliminary structural interface requirements; no production design or hardware selection",
        "known_from_aircraft_config": {
            "target_mass_g": config.aircraft.target_mass_g,
            "design_load_factor_g": config.aircraft.design_load_factor_g,
            "gravity_m_s2": config.aircraft.gravity_m_s2,
            "tail_arm_mm": config.tail.tail_arm_mm,
            "boom_axis_y_mm_each": [-config.booms.lateral_offset_mm, config.booms.lateral_offset_mm],
            "boom_center_spacing_mm": 2.0 * config.booms.lateral_offset_mm,
            "boom_requirement_measured_EI_Nm2": 125.0,
            "boom_requirement_measured_GJ_Nm2": 105.0,
        },
        "design_assumptions": {
            "battery_landing_ejection_factor_g": BATTERY_LANDING_EJECTION_FACTOR_G,
            "structural_proof_factor": STRUCTURAL_PROOF_FACTOR,
            "battery_primary_load_paths": BATTERY_PRIMARY_LOAD_PATHS,
            "battery_nominal_pack_specific_energy_assumption_Wh_per_kg": 220.0,
            "battery_usable_energy_fraction_assumption": 0.80,
            "battery_retention_study_masses_g": list(BATTERY_RETENTION_STUDY_MASSES_G),
            "motor_electrical_power_screen_w": list(MOTOR_ELECTRICAL_POWER_SCREEN_W),
            "motor_and_esc_efficiency_for_torque_screen": [MOTOR_EFFICIENCY_SCREEN, ESC_EFFICIENCY_SCREEN],
            "motor_peak_rpm_screen": MOTOR_PEAK_RPM_SCREEN,
            "dynamic_propulsive_thrust_screen_n": MOTOR_DYNAMIC_THRUST_SCREEN_N,
            "motor_mass_study_g": list(MOTOR_MASS_STUDY_G),
            "motor_cg_offset_from_mount_mm": MOTOR_CG_OFFSET_FROM_MOUNT_MM,
        },
        "battery_retention": {
            "cases": battery_cases,
            "requirements": [
                "Use a full-area non-compressive cradle/support under the pack; inertia must react through tray hard-stops and straps, never through compressed cells.",
                "Provide indexed longitudinal positions over the packaging-study 60-mm travel, positive primary end-stops, and independent secondary anti-ejection retention.",
                "Primary hard-stops, rails and their airframe anchors must each be designed for the declared proof direction/load; a symmetric two-stop division is not redundancy evidence.",
                "Do not make the battery hatch, foam skin, hook-and-loop alone, wire harness or cell shrink-wrap a primary structural load path.",
                "Protect the connector/cable exit from chafe, isolate the pack from pusher-prop ingress and allow inspection/removal without battery compression.",
            ],
            "expected_failure_modes": [
                "rail or stop pull-out / plywood bearing-crushing at an insert",
                "latch opening, strap tear or anchor debond leading to pack ejection",
                "local pack abrasion, puncture or compression from an undersupported tray",
                "3-D printed retention creep/softening under battery or VTX thermal exposure",
            ],
            "proof_framework": {
                "article": "representative tray, rails, stops, secondary latch and its actual airframe attachment; use a dimensionally representative inert dummy, not a live Li-ion/LiPo pack",
                "loading": "apply the listed proof load separately in all six directions through a broad cradle/contact fixture; do not load a real cell at a point",
                "acceptance": ["no latch release or pack migration beyond indexed tolerance", "no permanent set, cracking, delamination, fastener/insert movement or rail slip", "repeat removal/reinstallation and verify connector clearance after proof"],
                "limit": "This screen does not establish crashworthiness. Flight/landing acceleration spectra and selected-pack vulnerability remain TBD.",
            },
        },
        "pusher_motor_interface": {
            "cases": motor_cases,
            "requirements": [
                "Transmit axial thrust, shaft reaction torque, motor inertial bending and off-axis installation loads into a structural cross-member tied to both booms/primary fuselage structure; do not react them through foam alone.",
                "Use an anti-rotation torque path with paired shear features/webs. A single 3-D printed tab, adhesive-only joint or unsupported thin plywood tongue is not an acceptable primary torque path.",
                "Provide a manufacturer-specific bolt-circle/shaft/adaptor interface only after motor selection; then check bolt bearing, net section, insert pull-out, adhesive peel and local carbon crushing using actual dimensions.",
                "Keep motor cooling and ESC airflow paths clear, retain all high-current wiring against vibration/chafe, and maintain verified propeller/boom/elevator clearance under deflection.",
            ],
            "expected_failure_modes": [
                "motor fastener bearing/pull-out or local crushing/splitting at insert",
                "cross-member torsion, boom-clamp slip or adhesive peel under shaft reaction torque",
                "mount bending/fatigue or resonance from motor mass and unbalance",
                "thermal creep/delamination of a printed or bonded local mount",
            ],
            "proof_framework": {
                "article": "representative motor-interface cross-member, boom/fuselage attachments, fasteners/inserts and cooling provisions",
                "loading": "separately apply axial load along prop axis, torque through a calibrated arm, and transverse motor-CG load at the selected offset. Use proof values only after selected hardware confirms peak torque/static thrust.",
                "acceptance": ["no permanent alignment change, fastener movement, cracking, delamination or clamp slip", "re-check prop-disk clearances and tail/boom relative alignment after proof"],
                "limit": "The present 10.05-N value is a dynamic climb requirement, not selected-prop static thrust. The selected launch method and propeller map can govern a larger axial load.",
            },
        },
        "tbd_before_release": [
            "selected battery chemistry, pack mass/dimensions, allowable support pressure and pack-specific retention instructions",
            "selected motor mass, bolt pattern, CG offset, propeller static thrust/torque map, balance and vibration data",
            "motor prop plane, axis Z, cross-member geometry, fuselage structural load path and boom attachment detail",
            "actual rail/stop material, adhesive/fastener allowables, local bearing/net-section coupons and representative proof results",
            "landing/crash acceleration spectrum, thermal environment and wiring/connector retention details",
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "aircraft.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "powertrain" / "structure_summary.json")
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(make_summary(load_aircraft_config(args.config)), indent=2) + "\n", encoding="utf-8")
    print(f"wrote {args.output.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
