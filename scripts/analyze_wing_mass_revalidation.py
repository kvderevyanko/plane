#!/usr/bin/env python3
"""Compare the canonical LR1600 2400-g wing case with a 2600-g sensitivity.

This is deliberately a load-case override, not a second aircraft configuration.
The typed YAML remains the source of truth at 2400 g; geometry and construction
are reused from :mod:`analyze_wing_structure` without alteration.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import replace
from pathlib import Path
from typing import Any

try:
    from analyze_wing_structure import (
        CARBON_ENVELOPES,
        aeroelastic_twist,
        analyze,
        dbox_gj,
        load_cruise_aero_cm,
    )
    from config import DEFAULT_CONFIG_PATH, load_aircraft_config
except ImportError:  # pragma: no cover - module invocation
    from scripts.analyze_wing_structure import (
        CARBON_ENVELOPES,
        aeroelastic_twist,
        analyze,
        dbox_gj,
        load_cruise_aero_cm,
    )
    from scripts.config import DEFAULT_CONFIG_PATH, load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "analysis" / "wing_mass_revalidation"
REFERENCE_MASS_G = 2400.0
SENSITIVITY_MASS_G = 2600.0
SPAR_DEFLECTION_STOP_MM = 40.0
DBOX_TWIST_GATES_DEG = {100: 2.0, 120: 3.0}
TORQUE_ARM_M = 0.250


def config_at_mass(config: Any, mass_g: float) -> Any:
    """Return an in-memory typed load case, leaving the loaded YAML untouched."""
    return replace(config, aircraft=replace(config.aircraft, target_mass_g=mass_g))


def _at_station(load: dict[str, list[float]], station_m: float) -> dict[str, float]:
    y = load["y_m"]
    if not 0.0 <= station_m <= y[-1]:
        raise ValueError("station must be within one panel")
    interval = next(index for index in range(len(y) - 1) if y[index] <= station_m <= y[index + 1])
    fraction = (station_m - y[interval]) / (y[interval + 1] - y[interval])
    return {
        "y_mm": station_m * 1000.0,
        "section_shear_n": load["shear_n"][interval] + fraction * (load["shear_n"][interval + 1] - load["shear_n"][interval]),
        "section_bending_moment_nm": load["moment_nm"][interval] + fraction * (load["moment_nm"][interval + 1] - load["moment_nm"][interval]),
    }


def _case(config: Any, mass_g: float, aero_polar: Path) -> dict[str, Any]:
    case_config = config_at_mass(config, mass_g)
    result, working = analyze(case_config, aero_polar_path=aero_polar)
    spar = result["main_spar"]
    conservative = next(item for item in spar["material_envelopes"] if item["name"] == "conservative")
    nominal = next(item for item in spar["material_envelopes"] if item["name"] == "nominal")
    joiner = result["joiner"]
    load_case = result["load_case"]
    root_moment = spar["root_bending_moment_nm"]
    return {
        "mass_g": mass_g,
        "source": "typed config with in-memory target_mass override; YAML unchanged",
        "design_load_factor_g": load_case["design_load_factor_g"],
        "total_design_lift_n": load_case["design_total_lift_n"],
        "per_panel_lift_n": load_case["per_panel_lift_n"],
        "root_shear_n": spar["root_shear_n"],
        "root_bending_moment_nm": root_moment,
        "main_spar": {
            "root_bending_stress_mpa": conservative["root_bending_stress_mpa"],
            "root_shear_screening_mpa": conservative["root_shear_screening_mpa"],
            "conservative": {key: conservative[key] for key in ("tension_sf", "compression_sf", "shear_sf", "tip_deflection_mm")},
            "nominal": {key: nominal[key] for key in ("tension_sf", "compression_sf", "shear_sf", "tip_deflection_mm")},
            "all_material_envelopes": spar["material_envelopes"],
        },
        "joiner": {
            "bending_stress_mpa": joiner["bending_stress_mpa"],
            "material_envelopes": joiner["material_envelopes"],
            "centre_50mm_screening_deflection_mm": next(item for item in joiner["material_envelopes"] if item["name"] == "conservative")["centre_50mm_screening_deflection_mm"],
            "contact_couple_force_n": joiner["contact_couple_force_n"],
            "socket_screening": joiner["socket_screening"],
        },
        "sensitivity_cases": load_case["sensitivity_cases"],
        "boom_station_y230mm_background_wing_load": _at_station(working["load"], .230),
        "proof_schedule_100_percent": result["proof_test"]["loads_per_console"],
    }


def _dbox(config: Any, mass_g: float, aero_polar: Path) -> dict[str, Any]:
    case_config = config_at_mass(config, mass_g)
    cm_abs = load_cruise_aero_cm(aero_polar)
    root_gj_at_g300 = dbox_gj(case_config.wing.root_chord_mm / 1000.0, 300e6)
    twists = {str(speed): math.degrees(aeroelastic_twist(case_config, speed, 300e6, cm_abs)) for speed in (70, 90, 100, 120)}
    # The current proxy is linear in effective G/GJ.  State the derived gate
    # explicitly rather than rounding the existing 22.8-Nm2 gate downward.
    required_gj = max(root_gj_at_g300 * twists[str(speed)] / gate for speed, gate in DBOX_TWIST_GATES_DEG.items())
    return {
        "cm_abs": cm_abs,
        "effective_G_mpa": 300.0,
        "root_gj_nm2_at_G300": root_gj_at_g300,
        "twist_deg": twists,
        "required_root_equivalent_gj_nm2": required_gj,
        "practical_qualification_gate_gj_nm2": math.ceil(required_gj * 10.0) / 10.0,
        "model": "existing worst cruise |Cm| plus 1-g elliptic lift offset model; only the 1-g lift term scales with mass",
    }


def build_summary(config_path: Path = DEFAULT_CONFIG_PATH, aero_polar: Path = ROOT / "analysis" / "aero" / "parsed" / "clarky_re300000_realistic_model_combined.csv") -> dict[str, Any]:
    config = load_aircraft_config(config_path)
    if config.aircraft.target_mass_g != REFERENCE_MASS_G:
        raise ValueError("This sensitivity is anchored to the canonical 2400-g YAML reference case")
    reference = _case(config, REFERENCE_MASS_G, aero_polar)
    sensitivity = _case(config, SENSITIVITY_MASS_G, aero_polar)
    dbox = {str(int(mass)): _dbox(config, mass, aero_polar) for mass in (REFERENCE_MASS_G, SENSITIVITY_MASS_G)}
    reference_ei = CARBON_ENVELOPES[0].youngs_modulus_gpa * 1e9 * (result := analyze(config, aero_polar_path=aero_polar)[1])["spar"]["second_moment_m4"]
    required_ei = reference_ei * sensitivity["main_spar"]["conservative"]["tip_deflection_mm"] / SPAR_DEFLECTION_STOP_MM
    proof_torque = 1.25 * sensitivity["root_bending_moment_nm"]
    proof_arm_force = proof_torque / TORQUE_ARM_M
    return {
        "schema": "lr1600-wing-mass-revalidation-v1",
        "status": "PRELIMINARY_CONDITIONAL",
        "scope": {
            "canonical_reference_config": str(config_path.relative_to(ROOT)),
            "canonical_target_mass_g": config.aircraft.target_mass_g,
            "sensitivity_mass_g": SENSITIVITY_MASS_G,
            "geometry_and_structural_concept": "unchanged; only an in-memory mass override is used",
            "design_load_factor_g": config.aircraft.design_load_factor_g,
            "design_case_interpretation": "current design/limit case only; no ultimate claim and no 125% full-wing proof",
        },
        "mass_ratio_2600_over_2400": SENSITIVITY_MASS_G / REFERENCE_MASS_G,
        "cases": {"2400g_reference": reference, "2600g_sensitivity": sensitivity},
        "dbox": dbox,
        "qualification_requirements_for_2600g": {
            "spar_measured_EI_min_nm2": required_ei,
            "spar_equivalent_effective_E_min_gpa_for_existing_14x12": required_ei / result["spar"]["second_moment_m4"] / 1e9,
            "spar_deflection_stop_mm": SPAR_DEFLECTION_STOP_MM,
            "note_on_EI": "Measured EI qualifies deflection only; it does not replace carbon strength allowables.",
            "dbox_root_equivalent_GJ_min_nm2": dbox["2600"]["practical_qualification_gate_gj_nm2"],
            "dbox_twist_limits_deg": {str(speed): value for speed, value in DBOX_TWIST_GATES_DEG.items()},
            "representative_joiner_socket_proof_torque_nm": proof_torque,
            "representative_joiner_socket_proof_force_per_existing_250mm_arm_n": proof_arm_force,
            "representative_joiner_socket_proof_mass_equivalent_per_arm_kg": proof_arm_force / config.aircraft.gravity_m_s2,
            "socket_acceptance": "Existing acceptance unchanged: no slip, crushing, hoop splitting, delamination or plate crack; residual displacement <=0.10 mm.",
        },
        "qualification_status": {
            "state": "UNQUALIFIED_PENDING_2600G_SPECIFIC_EVIDENCE",
            "canonical_2400g_gate_is_not_transferable": True,
            "reason": "A canonical 2400-g material/fixture PASS at E>=70 GPa, socket 19.977 N m, or D-box GJ>=22.8 N m2 does not qualify the 2600-g sensitivity case. The 2600-g requirements in this artifact must be explicitly met and recorded.",
        },
        "boom_interface": {
            "mass_dependent_background": "Wing section shear and bending at y=230 mm are reported from the 4-g elliptic wing-load model and scale 2600/2400.",
            "not_automatically_scaled": "Published boom/tail aerodynamic, yaw, handling and landing loads retain their existing physical assumptions; they are not multiplied solely by aircraft MTOW.",
            "status": "No new mass-induced boom limiting case is demonstrated by this sensitivity. The hardpoint remains not release-ready: X coordinate, clamp/fastener geometry, bond area, bearing/net-section proof and representative mounted test are TBD.",
        },
        "limitations": [
            "Carbon strength values and socket local allowables remain provisional screening envelopes, not measured allowables.",
            "D-box GJ must be established by a linear representative article; the aeroelastic calculation is not flutter or coupled aeroelastic substantiation.",
            "The 2600-g case is preliminary and does not alter config/aircraft.yaml or permit a geometry/construction change.",
        ],
    }


def write_outputs(summary: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    rows = []
    for key, case in summary["cases"].items():
        rows.append({
            "case": key, "mass_g": case["mass_g"], "total_design_lift_n": case["total_design_lift_n"],
            "per_panel_lift_n": case["per_panel_lift_n"], "root_shear_n": case["root_shear_n"],
            "root_bending_moment_nm": case["root_bending_moment_nm"],
            "spar_root_stress_mpa": case["main_spar"]["root_bending_stress_mpa"],
            "spar_tip_deflection_E70_mm": case["main_spar"]["conservative"]["tip_deflection_mm"],
            "spar_tip_deflection_E110_mm": case["main_spar"]["nominal"]["tip_deflection_mm"],
            "joiner_stress_mpa": case["joiner"]["bending_stress_mpa"],
            "boom_y230_shear_n": case["boom_station_y230mm_background_wing_load"]["section_shear_n"],
            "boom_y230_moment_nm": case["boom_station_y230mm_background_wing_load"]["section_bending_moment_nm"],
            "dbox_twist_100kmh_deg_G300": summary["dbox"][str(int(case["mass_g"]))]["twist_deg"]["100"],
            "dbox_twist_120kmh_deg_G300": summary["dbox"][str(int(case["mass_g"]))]["twist_deg"]["120"],
        })
    with (output / "comparison.csv").open("w", newline="", encoding="utf-8") as destination:
        writer = csv.DictWriter(destination, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--aero-polar", type=Path, default=ROOT / "analysis" / "aero" / "parsed" / "clarky_re300000_realistic_model_combined.csv")
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    summary = build_summary(args.config, args.aero_polar)
    write_outputs(summary, args.output)
    print(f"Wing 2400/2600-g structural sensitivity written to {args.output}")


if __name__ == "__main__":
    main()
