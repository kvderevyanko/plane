#!/usr/bin/env python3
"""Preliminary structural requirement model for the LR1600 twin tail booms.

This is a bounded cantilever screening model, deliberately not a tube SKU
selector.  It uses the selected preliminary tail geometry as an integration
input and retains carbon properties, attachment compliance, and loads without
validated manoeuvre/yaw spectra as explicit assumptions.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import AircraftConfig, load_aircraft_config


RHO_KG_M3 = 1.225
MAX_SCREEN_SPEED_M_S = 25.0  # existing propulsion study's 90 km/h case
HORIZONTAL_TAIL_CL_SCREEN = 1.20
VERTICAL_TAIL_FORCE_COEFFICIENT_SCREEN = 1.00
ASYMMETRIC_YAW_FACTOR = 1.50
EMPENNAGE_MASS_ESTIMATE_KG = 0.150
FIN_LOAD_ECCENTRICITY_M = 0.090
HANDLING_LOAD_PER_BOOM_N = 20.0
CARBON_DENSITY_RANGE_KG_M3 = (1450.0, 1650.0)
CARBON_E_MIN_PA = 70e9
CARBON_G_MIN_PA = 25e9
CARBON_COMPRESSION_ALLOWABLE_SCREEN_PA = 300e6
MAX_DIFFERENTIAL_PITCH_DEG = 0.25
MAX_COMMON_PITCH_LIMIT_DEG = 2.0
MAX_COMMON_PITCH_CRUISE_DEG = 0.5
MAX_TORSIONAL_TWIST_DEG = 0.5
REQUIRED_MEASURED_EI_NM2 = 125.0
REQUIRED_MEASURED_GJ_NM2 = 105.0
MANUFACTURING_CLEARANCE_M = 0.030
BOOM_Z_AT_PROP_PLANE_M = 0.0


@dataclass(frozen=True)
class TubeCandidate:
    name: str
    outer_diameter_mm: float
    inner_diameter_mm: float


CANDIDATES = (
    TubeCandidate("16 x 14 mm", 16.0, 14.0),
    TubeCandidate("18 x 16 mm", 18.0, 16.0),
    TubeCandidate("20 x 18 mm", 20.0, 18.0),
)


def tube_properties(outer_diameter_m: float, inner_diameter_m: float) -> dict[str, float]:
    """Return SI area, bending and torsion section properties of a circular tube."""
    if outer_diameter_m <= 0 or inner_diameter_m < 0 or inner_diameter_m >= outer_diameter_m:
        raise ValueError("tube diameters require OD > ID >= 0")
    area = math.pi / 4.0 * (outer_diameter_m**2 - inner_diameter_m**2)
    second_moment = math.pi / 64.0 * (outer_diameter_m**4 - inner_diameter_m**4)
    polar_moment = 2.0 * second_moment
    return {
        "area_m2": area,
        "second_moment_m4": second_moment,
        "polar_moment_m4": polar_moment,
        "section_modulus_m3": second_moment / (outer_diameter_m / 2.0),
    }


def dynamic_pressure(speed_m_s: float, rho_kg_m3: float = RHO_KG_M3) -> float:
    if speed_m_s <= 0 or rho_kg_m3 <= 0:
        raise ValueError("speed and density must be positive")
    return 0.5 * rho_kg_m3 * speed_m_s**2


def cantilever_point_response(load_n: float, length_m: float, youngs_modulus_pa: float, second_moment_m4: float) -> dict[str, float]:
    """Root moment and free-end deflection of one fixed-free boom."""
    if min(load_n, length_m, youngs_modulus_pa, second_moment_m4) <= 0:
        raise ValueError("load, length, modulus and second moment must be positive")
    return {
        "root_moment_nm": load_n * length_m,
        "tip_deflection_m": load_n * length_m**3 / (3.0 * youngs_modulus_pa * second_moment_m4),
        "tip_slope_rad": load_n * length_m**2 / (2.0 * youngs_modulus_pa * second_moment_m4),
    }


def euler_buckling_load_n(length_m: float, youngs_modulus_pa: float, second_moment_m4: float, effective_length_factor: float = 2.0) -> float:
    """First-order Euler axial screen; K=2 represents a fixed-free member."""
    if min(length_m, youngs_modulus_pa, second_moment_m4, effective_length_factor) <= 0:
        raise ValueError("buckling inputs must be positive")
    return math.pi**2 * youngs_modulus_pa * second_moment_m4 / (effective_length_factor * length_m) ** 2


def required_boom_center_spacing_mm(prop_diameter_mm: float, boom_outer_diameter_mm: float, clearance_mm: float, boom_axis_z_offset_mm: float = 0.0) -> float:
    """Minimum boom centre spacing from true radial prop-disk clearance.

    For each boom, sqrt((spacing/2)^2 + z^2) must exceed prop radius + boom
    radius + clearance.  A boom sufficiently above/below the disk needs no
    lateral spacing from this constraint alone.
    """
    if prop_diameter_mm <= 0 or boom_outer_diameter_mm <= 0 or clearance_mm < 0:
        raise ValueError("prop and boom diameters must be positive; clearance must not be negative")
    required_radius = prop_diameter_mm / 2.0 + boom_outer_diameter_mm / 2.0 + clearance_mm
    radial_square = required_radius**2 - boom_axis_z_offset_mm**2
    return 2.0 * math.sqrt(max(0.0, radial_square))


def _selected_geometry(config: AircraftConfig) -> dict[str, float]:
    """Read the selected preliminary integration geometry, never a copy of it."""
    if not config.tail.is_defined or not config.booms.is_defined or config.tail.horizontal is None or config.tail.vertical is None:
        raise ValueError("tail and boom initial_design_assumption geometry is required for boom sizing")
    return {
        "tail_arm_m": config.tail.tail_arm_mm / 1000.0,
        "boom_half_spacing_m": config.booms.lateral_offset_mm / 1000.0,
        "boom_z_m": config.booms.axis_z_mm / 1000.0,
        "horizontal_tail_area_m2": config.tail.horizontal.area_m2,
        "vertical_tail_total_area_m2": config.tail.vertical.total_area_m2,
    }


def _loads(config: AircraftConfig, geometry: dict[str, float]) -> dict[str, float]:
    q = dynamic_pressure(MAX_SCREEN_SPEED_M_S)
    horizontal_aero = q * geometry["horizontal_tail_area_m2"] * HORIZONTAL_TAIL_CL_SCREEN
    horizontal_aero_lower = q * geometry["horizontal_tail_area_m2"] * .80
    planform_scaled_4g = (geometry["horizontal_tail_area_m2"] / config.wing.area_m2) * (config.aircraft.target_mass_kg * config.aircraft.gravity_m_s2 * config.aircraft.design_load_factor_g)
    empennage_inertia = EMPENNAGE_MASS_ESTIMATE_KG * config.aircraft.gravity_m_s2 * config.aircraft.design_load_factor_g
    vertical_per_boom = (horizontal_aero + empennage_inertia) / 2.0
    lateral_per_boom = q * geometry["vertical_tail_total_area_m2"] * VERTICAL_TAIL_FORCE_COEFFICIENT_SCREEN * ASYMMETRIC_YAW_FACTOR / 2.0
    torsion = lateral_per_boom * FIN_LOAD_ECCENTRICITY_M
    return {
        "dynamic_pressure_pa": q,
        "horizontal_tail_planform_scaled_4g_study_n_total": planform_scaled_4g,
        "horizontal_tail_aerodynamic_load_study_n_total_at_CL0_8": horizontal_aero_lower,
        "horizontal_tail_aerodynamic_load_n_total": horizontal_aero,
        "empennage_4g_inertial_load_n_total": empennage_inertia,
        "combined_vertical_load_n_per_boom": vertical_per_boom,
        "asymmetric_fin_side_load_n_per_boom": lateral_per_boom,
        "fin_eccentricity_torsion_nm_per_boom": torsion,
        "handling_or_landing_point_load_n_per_boom": HANDLING_LOAD_PER_BOOM_N,
    }


def candidate_analysis(candidate: TubeCandidate, loads: dict[str, float], tail_arm_m: float, boom_half_spacing_m: float) -> dict[str, Any]:
    props = tube_properties(candidate.outer_diameter_mm / 1000.0, candidate.inner_diameter_mm / 1000.0)
    vertical = cantilever_point_response(loads["combined_vertical_load_n_per_boom"], tail_arm_m, CARBON_E_MIN_PA, props["second_moment_m4"])
    handling = cantilever_point_response(loads["handling_or_landing_point_load_n_per_boom"], tail_arm_m, CARBON_E_MIN_PA, props["second_moment_m4"])
    governing = max(vertical["root_moment_nm"], handling["root_moment_nm"])
    stress = governing / props["section_modulus_m3"]
    torsion_twist_rad = loads["fin_eccentricity_torsion_nm_per_boom"] * tail_arm_m / (CARBON_G_MIN_PA * props["polar_moment_m4"])
    common_pitch = math.degrees(vertical["tip_slope_rad"])
    # 10% EI mismatch changes one boom's longitudinal end slope, so this is
    # pitch/incidence differential. Translation difference across ±Y is a
    # separate tail-roll/dihedral distortion and must not be called incidence.
    differential_pitch = common_pitch / 9.0
    tail_roll_from_translation = math.degrees((vertical["tip_deflection_m"] / .90 - vertical["tip_deflection_m"]) / (2.0 * boom_half_spacing_m))
    normal_cruise_pitch = common_pitch / 4.0
    mass_per_m = tuple(props["area_m2"] * density * 1000.0 for density in CARBON_DENSITY_RANGE_KG_M3)
    pair_mass = tuple(value * 2.0 * tail_arm_m for value in mass_per_m)
    return {
        "geometry": {"outer_diameter_mm": candidate.outer_diameter_mm, "inner_diameter_mm": candidate.inner_diameter_mm, "wall_mm": (candidate.outer_diameter_mm - candidate.inner_diameter_mm) / 2.0},
        "section": {"area_mm2": props["area_m2"] * 1e6, "I_mm4": props["second_moment_m4"] * 1e12, "J_mm4": props["polar_moment_m4"] * 1e12, "Z_mm3": props["section_modulus_m3"] * 1e9},
        "stiffness": {"EI_nm2_at_E70GPa": CARBON_E_MIN_PA * props["second_moment_m4"], "GJ_nm2_at_G25GPa": CARBON_G_MIN_PA * props["polar_moment_m4"]},
        "loads": {"governing_root_bending_moment_nm": governing, "bending_stress_mpa_at_assumed_E": stress / 1e6, "screening_compression_sf_vs_assumed_300MPa": CARBON_COMPRESSION_ALLOWABLE_SCREEN_PA / stress, "vertical_tip_deflection_mm": vertical["tip_deflection_m"] * 1000.0, "handling_tip_deflection_mm": handling["tip_deflection_m"] * 1000.0, "common_tail_pitch_deg_limit_screen": common_pitch, "common_tail_pitch_deg_normal_1g_proxy": normal_cruise_pitch, "differential_tail_pitch_deg_for_10pct_EI_mismatch": differential_pitch, "tail_roll_from_translation_deg_for_10pct_EI_mismatch": tail_roll_from_translation, "torsion_twist_deg": math.degrees(torsion_twist_rad), "euler_buckling_n_fixed_free": euler_buckling_load_n(tail_arm_m, CARBON_E_MIN_PA, props["second_moment_m4"])},
        "mass_estimate": {"density_assumption_kg_m3": list(CARBON_DENSITY_RANGE_KG_M3), "mass_per_m_g": list(mass_per_m), "two_booms_at_selected_arm_g": list(pair_mass), "status": "design_estimate, not ledger known mass"},
        "assessment": {
            "meets_minimum_EI_125_Nm2": CARBON_E_MIN_PA * props["second_moment_m4"] >= REQUIRED_MEASURED_EI_NM2,
            "meets_minimum_GJ_105_Nm2": CARBON_G_MIN_PA * props["polar_moment_m4"] >= REQUIRED_MEASURED_GJ_NM2,
            "meets_differential_pitch_0_25deg": differential_pitch <= MAX_DIFFERENTIAL_PITCH_DEG,
            "meets_common_pitch_limit_2deg": common_pitch <= MAX_COMMON_PITCH_LIMIT_DEG,
            "meets_common_pitch_normal_0_5deg": normal_cruise_pitch <= MAX_COMMON_PITCH_CRUISE_DEG,
            "meets_torsional_twist_0_5deg": math.degrees(torsion_twist_rad) <= MAX_TORSIONAL_TWIST_DEG,
        },
    }


def make_summary(config: AircraftConfig) -> dict[str, Any]:
    geometry = _selected_geometry(config)
    loads = _loads(config, geometry)
    candidate_results = {candidate.name: candidate_analysis(candidate, loads, geometry["tail_arm_m"], geometry["boom_half_spacing_m"]) for candidate in CANDIDATES}
    selected_spacing_mm = 2.0 * geometry["boom_half_spacing_m"] * 1000.0
    prop_clearance = [{
        "diameter_in": inch,
        "diameter_mm": inch * 25.4,
        "required_boom_center_spacing_mm_at_z0": required_boom_center_spacing_mm(inch * 25.4, 20.0, MANUFACTURING_CLEARANCE_M * 1000.0),
        "clears_selected_spacing_at_z0": selected_spacing_mm > required_boom_center_spacing_mm(inch * 25.4, 20.0, MANUFACTURING_CLEARANCE_M * 1000.0),
    } for inch in (10.0, 12.0, 14.0, 15.0)]
    return {
        "status": "preliminary_design_assumption; not release-to-manufacture and not a tube selection",
        "source_of_truth": "config/aircraft.yaml, loaded through scripts.config; it supplies target mass, 4g context and selected preliminary tail/boom geometry",
        "known_from_config": {"target_mass_g": config.aircraft.target_mass_g, "design_load_factor_g": config.aircraft.design_load_factor_g, "gravity_m_s2": config.aircraft.gravity_m_s2},
        "selected_integration_geometry": {"tail_arm_mm": geometry["tail_arm_m"] * 1000.0, "boom_lateral_position_mm": [-geometry["boom_half_spacing_m"] * 1000.0, geometry["boom_half_spacing_m"] * 1000.0], "boom_center_spacing_mm": 2 * geometry["boom_half_spacing_m"] * 1000.0, "boom_z_mm": geometry["boom_z_m"] * 1000.0, "horizontal_tail_area_m2": geometry["horizontal_tail_area_m2"], "vertical_tail_total_area_m2": geometry["vertical_tail_total_area_m2"]},
        "design_assumptions": {
            "carbon_property_envelope": {"E_assumed_GPa": CARBON_E_MIN_PA / 1e9, "G_assumed_GPa": CARBON_G_MIN_PA / 1e9, "compression_allowable_screen_MPa": CARBON_COMPRESSION_ALLOWABLE_SCREEN_PA / 1e6, "qualification": "conditional analysis values, not conservative generic tube properties; candidate needs measured/datasheet EI, GJ and coupon/proof evidence"},
            "tail_load_cases": {"max_speed_km_h": MAX_SCREEN_SPEED_M_S * 3.6, "horizontal_tail_CL_screen": HORIZONTAL_TAIL_CL_SCREEN, "empennage_mass_design_estimate_kg": EMPENNAGE_MASS_ESTIMATE_KG, "vertical_fin_force_coefficient_screen": VERTICAL_TAIL_FORCE_COEFFICIENT_SCREEN, "asymmetric_yaw_factor": ASYMMETRIC_YAW_FACTOR, "handling_load_N_per_boom": HANDLING_LOAD_PER_BOOM_N, "fin_load_eccentricity_mm": FIN_LOAD_ECCENTRICITY_M * 1000.0},
            "alignment_model": "10% EI mismatch, individual fixed-free cantilevers and no shared-stabilizer/mount-compliance credit; common pitch, differential pitch, tail roll and torsion are reported separately",
        },
        "load_results": loads,
        "candidate_sections": candidate_results,
        "candidate_requirement_envelope": {
            "minimum_screened_section": "20 x 18 mm circular carbon tube (1 mm nominal wall), conditional on measured/datasheet EI and GJ",
            "preferred_stiffness_margin_section": "larger or torsionally stiffer section if measured GJ/mount compliance is below the stated screen",
            "required_each_boom": {"measured_EI_Nm2_min": REQUIRED_MEASURED_EI_NM2, "measured_GJ_Nm2_min": REQUIRED_MEASURED_GJ_NM2, "common_pitch_limit_deg": MAX_COMMON_PITCH_LIMIT_DEG, "common_pitch_normal_1g_deg": MAX_COMMON_PITCH_CRUISE_DEG, "differential_pitch_limit_deg": MAX_DIFFERENTIAL_PITCH_DEG, "torsional_twist_limit_deg": MAX_TORSIONAL_TWIST_DEG, "straightness_requirement": "TBD by alignment fixture; measure over the typed unsupported length"},
            "expected_primary_failure_mode": "wing hardpoint/bond or local tube crushing/splitting before global tube bending; prove load transfer with representative mounted article",
        },
        "propeller_radial_clearance_screen": {"formula": "sqrt((spacing/2)^2 + z_offset^2) > prop_radius + boom_radius + manufacturing/deflection clearance", "boom_OD_mm_for_screen": 20.0, "clearance_mm": MANUFACTURING_CLEARANCE_M * 1000.0, "selected_spacing_mm": selected_spacing_mm, "cases": prop_clearance, "conclusion": f"{selected_spacing_mm:.1f} mm center spacing clears 10–14 inch study disks at z=0 with the 20 mm OD / 30 mm clearance screen. 15 inch requires >461 mm at z=0, so it is not a no-penalty fit; actual boom Z, local prop plane and dynamic deflection must be integrated before selection."},
        "wing_attachment_interface_requirements": {
            "preliminary_locations": "one hardpoint on each wing panel near y = +/-230 mm; coordinate X must be tied to the local main spar/D-box load path, not foam or skin alone. Exact x and fastener pattern remain TBD with the pusher/fuselage integration.",
            "load_transfer": "each boom mount must transfer the published vertical, lateral and torsional loads through paired birch-2 ribs straddling the mount, birch-2 longitudinal plates, main spar and closed D-box; 3-mm birch only as a local bearing/crushing doubler after fastener calculation/coupon.",
            "attachment_length_and_rotation": "use two separated longitudinal load stations (target >=60 mm fore/aft separation) or an equivalently substantiated clamp/sleeve; provide positive anti-rotation and a replaceable boom-to-hardpoint interface. Do not use a single foam-supported bolt.",
            "alignment": "fixture both boom axes and horizontal-tail incidence within +/-0.15 deg during bond; verify proof-load common pitch <=2 deg, normal 1g pitch <=0.5 deg, differential pitch <=0.25 deg and torsional twist <=0.5 deg. Mount compliance is uncredited in this screen.",
            "production_status": "no production DXF, bolt size or adhesive allowable is released by this study",
        },
        "tbd": [
            "manufacturer datasheet, fibre architecture, actual E/G/strength, ovality and mass per metre of any carbon tube",
            "complete fuselage/motor/propeller plane and actual boom Z offset, clearance and dynamic deflection",
            "validated tail aerodynamic/control loads, gust/yaw/landing spectrum and empirical empennage mass",
            "wing hardpoint X coordinate, fastener/clamp geometry, bond area, local bearing/net-section coupons and proof fixture",
            "complete aircraft mass ledger and measured final CG",
        ],
    }


def render_plot(summary: dict[str, Any], path: Path) -> None:
    results = summary["candidate_sections"]
    labels = list(results)
    figure, axes = plt.subplots(1, 2, figsize=(9, 3.8), dpi=150)
    axes[0].bar(labels, [results[key]["loads"]["vertical_tip_deflection_mm"] for key in labels], color="#4477aa")
    axes[0].axhline(12.5, color="#aa4444", linestyle="--", linewidth=1, label="screening target")
    axes[0].set(ylabel="Vertical tip deflection (mm)", title="Boom deflection at E = 70 GPa")
    axes[0].tick_params(axis="x", rotation=20); axes[0].legend(); axes[0].grid(axis="y", alpha=.25)
    axes[1].plot([row["diameter_in"] for row in summary["propeller_radial_clearance_screen"]["cases"]], [row["required_boom_center_spacing_mm_at_z0"] for row in summary["propeller_radial_clearance_screen"]["cases"]], marker="o", color="#228833")
    axes[1].axhline(460, color="#aa4444", linestyle="--", linewidth=1, label="selected 460 mm")
    axes[1].set(xlabel="Propeller study diameter (in)", ylabel="Required CL spacing (mm)", title="Radial clearance at prop plane, z = 0")
    axes[1].grid(alpha=.25); axes[1].legend()
    figure.tight_layout(); figure.savefig(path); plt.close(figure)


def write_outputs(summary: dict[str, Any], output_root: Path = ROOT / "analysis" / "booms") -> None:
    output_root.mkdir(parents=True, exist_ok=True)
    (output_root / "summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    render_plot(summary, output_root / "deflection_and_clearance.png")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=ROOT / "config" / "aircraft.yaml")
    parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "booms")
    args = parser.parse_args()
    summary = make_summary(load_aircraft_config(args.config))
    write_outputs(summary, args.output)
    print(f"wrote {args.output / 'summary.json'}")


if __name__ == "__main__":
    main()
