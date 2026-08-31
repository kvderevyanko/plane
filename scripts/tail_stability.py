#!/usr/bin/env python3
"""Preliminary LR1600 tail, stability and pusher-boom integration study.

This module deliberately sizes a *requirement envelope*, not a flight-ready
empennage.  The only editable aircraft input is ``config/aircraft.yaml``.
Selected geometry is read from typed configuration; study constants below are
explicit assumptions and remain sensitivity inputs rather than aircraft facts.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from scripts.config import AircraftConfig, load_aircraft_config
from scripts.run_airfoil_analysis import RHO, required_cl


# These are study cases, not values inferred from the wing-only XFOIL data.
TAIL_ARMS_MM = (550.0, 650.0, 750.0)
HORIZONTAL_TAIL_VOLUME_STUDY = (0.45, 0.50, 0.55)
TAIL_EFFICIENCY_STUDY = (0.78, 0.85, 0.92)  # q_t/q_inf incl. installation loss
DOWNWASH_GRADIENT_STUDY = (0.35, 0.45, 0.55)  # d epsilon / d alpha [rad/rad]
FUSELAGE_NEUTRAL_POINT_SHIFT_STUDY = (-0.040, -0.020, 0.000)  # MAC; geometry TBD
# Tail chord is only 90 mm, so the actual low-Re finite-tail slope is an
# independent uncertainty from dynamic-pressure efficiency.
TAIL_LIFT_SLOPE_STUDY_PER_RAD = (3.4, 4.2, 4.9)
ELEVATOR_EFFECTIVENESS_STUDY = (0.40, 0.50, 0.60)
MIN_DESIGN_STATIC_MARGIN_MAC = 0.05
MIN_FIRST_FLIGHT_STATIC_MARGIN_MAC = 0.08
USABLE_ELEVATOR_TRAVEL_DEG = 20.0
MAX_TRIM_FRACTION_OF_USABLE_TRAVEL = 0.60
VERTICAL_TAIL_VOLUME_STUDY = (0.035, 0.043, 0.050, 0.060)
FIN_LIFT_SLOPE_STUDY_PER_RAD = (2.8, 3.15, 3.5)
TWIN_FIN_EFFICIENCY_STUDY = (0.65, 0.78, 0.90)
NON_TAIL_CN_BETA_STUDY_PER_RAD = (-0.080, -0.050, -0.020)
# Trade-only mass proxy: paired Ø20×18-mm tubes at the density bounds used by
# the structural screen.  It is not a mass-ledger item or tube selection.
BOOM_PAIR_MASS_PER_M_STUDY_G = (173.10, 196.98)
FLIGHT_SPEEDS_KM_H = (60.0, 70.0, 90.0)
CONSERVATIVE_STALL_KM_H = 37.55
PROPELLER_DIAMETERS_MM = (254.0, 304.8, 355.6, 381.0)


@dataclass(frozen=True)
class TailGeometry:
    """Preliminary planform in SI except geometry positions stated in metres."""

    arm_m: float
    horizontal_area_m2: float
    horizontal_span_m: float
    horizontal_root_chord_m: float
    horizontal_tip_chord_m: float
    elevator_chord_fraction: float
    vertical_fin_height_m: float
    vertical_root_chord_m: float
    vertical_tip_chord_m: float
    rudder_chord_fraction: float
    boom_y_m: float
    boom_z_m: float
    boom_radius_m: float
    clearance_m: float

    @property
    def horizontal_aspect_ratio(self) -> float:
        return self.horizontal_span_m**2 / self.horizontal_area_m2

    @property
    def horizontal_area_from_planform_m2(self) -> float:
        return self.horizontal_span_m * (self.horizontal_root_chord_m + self.horizontal_tip_chord_m) / 2.0

    @property
    def elevator_area_m2(self) -> float:
        return self.horizontal_area_m2 * self.elevator_chord_fraction

    @property
    def fin_area_each_m2(self) -> float:
        return self.vertical_fin_height_m * (self.vertical_root_chord_m + self.vertical_tip_chord_m) / 2.0

    @property
    def vertical_total_area_m2(self) -> float:
        return 2.0 * self.fin_area_each_m2

    @property
    def vertical_aspect_ratio_each(self) -> float:
        return self.vertical_fin_height_m**2 / self.fin_area_each_m2


@dataclass(frozen=True)
class StabilityCase:
    tail_lift_slope_per_rad: float
    tail_efficiency: float
    downwash_gradient: float
    fuselage_neutral_point_shift_mac: float
    neutral_point_mac: float


def _positive(value: float, name: str) -> float:
    if value <= 0:
        raise ValueError(f"{name} must be positive")
    return value


def trapezoid_area_m2(span_m: float, root_chord_m: float, tip_chord_m: float) -> float:
    """Planform area of one full-span trapezoidal surface."""
    return _positive(span_m, "span") * (_positive(root_chord_m, "root chord") + _positive(tip_chord_m, "tip chord")) / 2.0


def horizontal_tail_volume(horizontal_area_m2: float, tail_arm_m: float, wing_area_m2: float, mac_m: float) -> float:
    return _positive(horizontal_area_m2, "horizontal tail area") * _positive(tail_arm_m, "tail arm") / (_positive(wing_area_m2, "wing area") * _positive(mac_m, "MAC"))


def vertical_tail_volume(vertical_total_area_m2: float, tail_arm_m: float, wing_area_m2: float, wing_span_m: float) -> float:
    return _positive(vertical_total_area_m2, "vertical-tail area") * _positive(tail_arm_m, "tail arm") / (_positive(wing_area_m2, "wing area") * _positive(wing_span_m, "wing span"))


def finite_wing_lift_slope_per_rad(aspect_ratio: float, *, section_lift_slope_per_rad: float = 2.0 * math.pi, oswald_efficiency: float = 0.90) -> float:
    """First-order finite-wing lift-curve slope; no claim of CFD fidelity."""
    _positive(aspect_ratio, "aspect ratio")
    _positive(section_lift_slope_per_rad, "section lift slope")
    if not 0 < oswald_efficiency <= 1:
        raise ValueError("Oswald efficiency must be in (0, 1]")
    return section_lift_slope_per_rad / (1.0 + section_lift_slope_per_rad / (math.pi * oswald_efficiency * aspect_ratio))


def neutral_point_mac(*, wing_ac_mac: float, wing_lift_slope_per_rad: float, tail_lift_slope_per_rad: float,
                      tail_volume: float, tail_efficiency: float, downwash_gradient: float,
                      fuselage_neutral_point_shift_mac: float) -> float:
    """Stick-fixed, linear neutral point in MAC fractions.

    ``fuselage_neutral_point_shift_mac`` is an explicit uncertainty term: a
    negative value is destabilising.  It may not be silently set to zero until
    full fuselage/boom geometry has been analysed.
    """
    if not 0.0 <= wing_ac_mac <= 1.0 or not 0 <= downwash_gradient < 1.0:
        raise ValueError("wing AC must lie in MAC and downwash gradient in [0, 1)")
    if not 0 < tail_efficiency <= 1.0:
        raise ValueError("tail efficiency must be in (0, 1]")
    contribution = tail_efficiency * (tail_lift_slope_per_rad / _positive(wing_lift_slope_per_rad, "wing lift slope")) * (1.0 - downwash_gradient) * _positive(tail_volume, "tail volume")
    return wing_ac_mac + contribution + fuselage_neutral_point_shift_mac


def static_margin_mac(neutral_point: float, cg_mac: float) -> float:
    return neutral_point - cg_mac


def mac_fraction_to_x_mm(config: AircraftConfig, fraction: float) -> float:
    if not 0 <= fraction <= 1:
        raise ValueError("MAC fraction must be in [0, 1]")
    return config.wing.mean_aerodynamic_chord_leading_edge_x_mm + fraction * config.wing.mean_aerodynamic_chord_mm


def x_mm_to_mac_fraction(config: AircraftConfig, x_mm: float) -> float:
    return (x_mm - config.wing.mean_aerodynamic_chord_leading_edge_x_mm) / config.wing.mean_aerodynamic_chord_mm


def elevator_deflection_deg(*, wing_cm_ac: float, wing_cl: float, cg_mac: float, wing_ac_mac: float,
                             tail_volume: float, tail_efficiency: float, tail_lift_slope_per_rad: float,
                             elevator_effectiveness: float, tail_incidence_deg: float = 0.0) -> float:
    """Linear incremental trim deflection; positive is trailing-edge-down.

    This is measured from the tail's zero-lift reference.  The absolute servo
    neutral also needs tail-airfoil zero-lift angle, installed incidence and
    downwash angle, which are deliberately not invented at this stage.
    """
    if not 0 < tail_efficiency <= 1 or not 0 < elevator_effectiveness <= 1:
        raise ValueError("tail and elevator efficiencies must be in (0, 1]")
    tail_cl_required = (wing_cm_ac + wing_cl * (cg_mac - wing_ac_mac)) / (tail_efficiency * _positive(tail_volume, "tail volume"))
    tail_alpha_from_incidence = tail_lift_slope_per_rad * math.radians(tail_incidence_deg)
    return math.degrees((tail_cl_required - tail_alpha_from_incidence) / (_positive(tail_lift_slope_per_rad, "tail lift slope") * elevator_effectiveness))


def boom_axis_radial_distance_m(boom_y_m: float, boom_z_m: float) -> float:
    return math.hypot(boom_y_m, boom_z_m)


def prop_boom_has_clearance(*, propeller_diameter_m: float, boom_y_m: float, boom_z_m: float,
                            boom_radius_m: float, required_clearance_m: float) -> bool:
    needed = _positive(propeller_diameter_m, "propeller diameter") / 2.0 + _positive(boom_radius_m, "boom radius") + _positive(required_clearance_m, "clearance")
    return boom_axis_radial_distance_m(boom_y_m, boom_z_m) > needed


def required_boom_axis_spacing_m(*, propeller_diameter_m: float, boom_radius_m: float,
                                 required_clearance_m: float, boom_z_m: float = 0.0) -> float:
    """Minimum symmetric axis-to-axis spacing at the propeller plane.

    Uses the actual radial criterion.  A vertical boom offset reduces the
    required lateral spacing only when it genuinely supplies radial distance.
    """
    radial_need = _positive(propeller_diameter_m, "propeller diameter") / 2.0 + _positive(boom_radius_m, "boom radius") + _positive(required_clearance_m, "clearance")
    half_spacing = math.sqrt(max(0.0, radial_need**2 - boom_z_m**2))
    return 2.0 * half_spacing


def geometry_from_config(config: AircraftConfig) -> TailGeometry:
    """Build the selected preliminary geometry only from typed aircraft data."""
    if not config.tail.is_defined or not config.booms.is_defined:
        raise ValueError("tail stability requires defined preliminary tail and boom geometry")
    tail, booms = config.tail, config.booms
    if tail.horizontal is None or tail.vertical is None or tail.tail_arm_mm is None or booms.lateral_offset_mm is None or booms.axis_z_mm is None:
        raise ValueError("defined tail and booms must provide complete geometry")
    # Structural section remains TBD.  A 10 mm radius is consequently an
    # explicit clearance-study input, never a selection of a tube.
    boom_radius_m = 0.010 if booms.section_candidate.outer_diameter_mm is None else booms.section_candidate.outer_diameter_mm / 2000.0
    return TailGeometry(
        arm_m=tail.tail_arm_mm / 1000.0, horizontal_area_m2=tail.horizontal.area_m2,
        horizontal_span_m=tail.horizontal.span_mm / 1000.0,
        horizontal_root_chord_m=tail.horizontal.root_chord_mm / 1000.0,
        horizontal_tip_chord_m=tail.horizontal.tip_chord_mm / 1000.0,
        elevator_chord_fraction=tail.horizontal.elevator_chord_fraction,
        vertical_fin_height_m=tail.vertical.fin_height_mm / 1000.0,
        vertical_root_chord_m=tail.vertical.root_chord_mm / 1000.0,
        vertical_tip_chord_m=tail.vertical.tip_chord_mm / 1000.0,
        rudder_chord_fraction=tail.vertical.rudder_chord_fraction,
        boom_y_m=booms.lateral_offset_mm / 1000.0, boom_z_m=booms.axis_z_mm / 1000.0,
        # Matched to the structural preferred Ø20-mm study and its 30-mm
        # manufacturing/deflection clearance screen.  It remains a study
        # parameter while the tube and pusher plane are TBD.
        boom_radius_m=boom_radius_m, clearance_m=0.030,
    )


def stability_cases(config: AircraftConfig, geometry: TailGeometry) -> list[StabilityCase]:
    wing_ar = (config.wing.span_mm / 1000.0) ** 2 / config.wing.area_m2
    wing_slope = finite_wing_lift_slope_per_rad(wing_ar)
    volume = horizontal_tail_volume(geometry.horizontal_area_m2, geometry.arm_m, config.wing.area_m2, config.wing.mean_aerodynamic_chord_mm / 1000.0)
    return [
        StabilityCase(tail_slope, eta, downwash, fuselage, neutral_point_mac(
            wing_ac_mac=0.25, wing_lift_slope_per_rad=wing_slope,
            tail_lift_slope_per_rad=tail_slope, tail_volume=volume,
            tail_efficiency=eta, downwash_gradient=downwash,
            fuselage_neutral_point_shift_mac=fuselage,
        ))
        for tail_slope in TAIL_LIFT_SLOPE_STUDY_PER_RAD
        for eta in TAIL_EFFICIENCY_STUDY
        for downwash in DOWNWASH_GRADIENT_STUDY
        for fuselage in FUSELAGE_NEUTRAL_POINT_SHIFT_STUDY
    ]


def _range(values: Iterable[float]) -> dict[str, float]:
    values = list(values)
    return {"minimum": min(values), "maximum": max(values)}


def make_summary(config: AircraftConfig, geometry: TailGeometry | None = None) -> dict[str, Any]:
    geometry = geometry or geometry_from_config(config)
    if not config.cg.initial_envelope.is_defined or not config.cg.first_flight_recommendation.is_defined:
        raise ValueError("tail stability cannot report a numerical CG result while typed CG inputs are unresolved")
    envelope = config.cg.initial_envelope
    recommendation = config.cg.first_flight_recommendation
    if (envelope.x_mac_fraction_min is None or envelope.x_mac_fraction_max is None
            or recommendation.x_mac_fraction is None):
        raise ValueError("defined typed CG inputs must include numerical MAC fractions")
    wing_mac_m = config.wing.mean_aerodynamic_chord_mm / 1000.0
    wing_span_m = config.wing.span_mm / 1000.0
    wing_ar = wing_span_m**2 / config.wing.area_m2
    wing_slope = finite_wing_lift_slope_per_rad(wing_ar)
    tail_slope = 4.2  # central low-Re tail-slope study case, not an ideal 2π value
    volume_h = horizontal_tail_volume(geometry.horizontal_area_m2, geometry.arm_m, config.wing.area_m2, wing_mac_m)
    volume_v = vertical_tail_volume(geometry.vertical_total_area_m2, geometry.arm_m, config.wing.area_m2, wing_span_m)
    cases = stability_cases(config, geometry)
    nominal_np = neutral_point_mac(wing_ac_mac=.25, wing_lift_slope_per_rad=wing_slope, tail_lift_slope_per_rad=tail_slope,
                                   tail_volume=volume_h, tail_efficiency=.85, downwash_gradient=.45,
                                   fuselage_neutral_point_shift_mac=-.020)
    # Derive CG bounds before comparing them to the selected YAML design
    # assumption.  Aft is stability limited; forward is limited by the worst
    # low-speed linear trim requirement using only 60% of verified +/-20 deg.
    minimum_np = min(case.neutral_point_mac for case in cases)
    derived_aft_limit = minimum_np - MIN_DESIGN_STATIC_MARGIN_MAC
    trim_limit_deg = USABLE_ELEVATOR_TRAVEL_DEG * MAX_TRIM_FRACTION_OF_USABLE_TRAVEL
    def worst_low_speed_trim(cg_mac: float) -> float:
        speed = CONSERVATIVE_STALL_KM_H / 3.6
        wing_cl = required_cl(config.aircraft.target_mass_kg, speed, config.wing.area_m2, config.aircraft.gravity_m_s2)
        return max(abs(elevator_deflection_deg(wing_cm_ac=cm, wing_cl=wing_cl, cg_mac=cg_mac, wing_ac_mac=.25,
                                               tail_volume=volume_h, tail_efficiency=eta, tail_lift_slope_per_rad=a_t,
                                               elevator_effectiveness=tau))
                   for cm in (-.10, -.08, -.06) for eta in TAIL_EFFICIENCY_STUDY
                   for a_t in TAIL_LIFT_SLOPE_STUDY_PER_RAD for tau in ELEVATOR_EFFECTIVENESS_STUDY)
    feasible_forward = [candidate / 1000.0 for candidate in range(100, int(derived_aft_limit * 1000) + 1)
                        if worst_low_speed_trim(candidate / 1000.0) <= trim_limit_deg]
    if not feasible_forward:
        raise ValueError("no forward CG satisfies the stated low-speed trim-authority criterion")
    derived_forward_limit = min(feasible_forward)
    if envelope.x_mac_fraction_min < derived_forward_limit - .001 or envelope.x_mac_fraction_max > derived_aft_limit + .001:
        raise ValueError("typed design CG envelope exceeds the derived trim/static-margin limits")
    if static_margin_mac(minimum_np, recommendation.x_mac_fraction) < MIN_FIRST_FLIGHT_STATIC_MARGIN_MAC:
        raise ValueError("typed first-flight CG does not meet the derived conservative static-margin criterion")
    design_cg = {"forward_mac": envelope.x_mac_fraction_min, "nominal_mac": recommendation.x_mac_fraction,
                 "aft_mac": envelope.x_mac_fraction_max}
    # Representative linear wing Cm at useful pre-stall CL, from existing
    # clean Re~300k XFOIL polar (~-0.08); uncertainty is retained below.
    trim_cases = []
    for label, speed_km_h in (("conservative_stall", CONSERVATIVE_STALL_KM_H),) + tuple(("cruise", speed) for speed in FLIGHT_SPEEDS_KM_H) + (("climb_study", 60.0),):
        speed = speed_km_h / 3.6
        wing_cl = required_cl(config.aircraft.target_mass_kg, speed, config.wing.area_m2, config.aircraft.gravity_m_s2)
        deflections = [elevator_deflection_deg(wing_cm_ac=cm, wing_cl=wing_cl, cg_mac=cg, wing_ac_mac=.25,
                                                tail_volume=volume_h, tail_efficiency=eta, tail_lift_slope_per_rad=tail_slope,
                                                elevator_effectiveness=tau)
                       for cm in (-.10, -.08, -.06) for cg in (design_cg["forward_mac"], design_cg["nominal_mac"], design_cg["aft_mac"])
                       for eta in TAIL_EFFICIENCY_STUDY for tail_slope in TAIL_LIFT_SLOPE_STUDY_PER_RAD for tau in ELEVATOR_EFFECTIVENESS_STUDY]
        trim_cases.append({"condition": label, "speed_km_h": speed_km_h, "wing_cl": wing_cl,
                           "incremental_trim_elevator_deflection_deg_range": _range(deflections),
                           "note": "linear pre-stall incremental control screening about the tail zero-lift reference; absolute servo-neutral/incidence is TBD. Not an XFOIL post-stall prediction."})
    tail_arm_study = []
    for arm_mm in TAIL_ARMS_MM:
        for vh in HORIZONTAL_TAIL_VOLUME_STUDY:
            tail_arm_study.append({"tail_arm_mm": arm_mm, "horizontal_tail_volume": vh,
                                   "required_horizontal_area_m2": vh * config.wing.area_m2 * wing_mac_m / (arm_mm / 1000.0),
                                   "tail_ac_x_mm": mac_fraction_to_x_mm(config, .25) + arm_mm,
                                   "boom_pair_mass_design_estimate_g": [mass_per_m * arm_mm / 1000.0 for mass_per_m in BOOM_PAIR_MASS_PER_M_STUDY_G],
                                   "boom_pair_moment_about_wing_ac_kg_m": [mass_per_m / 1000.0 * (arm_mm / 1000.0) ** 2 / 2.0 for mass_per_m in BOOM_PAIR_MASS_PER_M_STUDY_G],
                                   "relative_boom_bending_lever_vs_650mm": (arm_mm / 650.0) ** 3})
    clearance = []
    for diameter_mm in PROPELLER_DIAMETERS_MM:
        diameter_m = diameter_mm / 1000.0
        clearance.append({"propeller_diameter_mm": diameter_mm,
                          "minimum_boom_axis_spacing_mm_at_z0": 1000.0 * required_boom_axis_spacing_m(propeller_diameter_m=diameter_m, boom_radius_m=geometry.boom_radius_m, required_clearance_m=geometry.clearance_m),
                          "baseline_boom_axis_radial_distance_mm": 1000.0 * boom_axis_radial_distance_m(geometry.boom_y_m, geometry.boom_z_m),
                          "baseline_clears_study_case": prop_boom_has_clearance(propeller_diameter_m=diameter_m, boom_y_m=geometry.boom_y_m, boom_z_m=geometry.boom_z_m, boom_radius_m=geometry.boom_radius_m, required_clearance_m=geometry.clearance_m)})
    # This is a mechanism-capability check, not a specified control travel.
    # It shows what a subsequently verified +/-20 deg travel would provide in
    # the same linear model; no claim is made past tail/elevator separation.
    recovery_moment = [eta * volume_h * tail_slope * tau * math.radians(USABLE_ELEVATOR_TRAVEL_DEG)
                       for eta in TAIL_EFFICIENCY_STUDY for tail_slope in TAIL_LIFT_SLOPE_STUDY_PER_RAD for tau in ELEVATOR_EFFECTIVENESS_STUDY]
    directional_cases = [
        {"vertical_tail_volume": vv, "fin_lift_slope_per_rad": a_v, "twin_fin_efficiency": eta_v,
         "non_tail_cn_beta_per_rad": non_tail,
         "net_cn_beta_proxy_per_rad": eta_v * a_v * vv + non_tail}
        for vv in VERTICAL_TAIL_VOLUME_STUDY for a_v in FIN_LIFT_SLOPE_STUDY_PER_RAD
        for eta_v in TWIN_FIN_EFFICIENCY_STUDY for non_tail in NON_TAIL_CN_BETA_STUDY_PER_RAD
    ]
    selected_directional = [case for case in directional_cases if abs(case["vertical_tail_volume"] - volume_v) < .001]
    return {
        "schema": "lr1600-tail-stability-v1",
        "status": "preliminary_design_assumption_not_release_to_manufacture",
        "datum": config.layout.coordinate_system.datum,
        "units": {"length": "mm unless named m", "area": "m2", "angles": "deg", "cg": "MAC fraction"},
        "known_inputs": {"wing_area_m2": config.wing.area_m2, "wing_span_mm": config.wing.span_mm,
                         "wing_mac_mm": config.wing.mean_aerodynamic_chord_mm,
                         "wing_mac_le_x_mm": config.wing.mean_aerodynamic_chord_leading_edge_x_mm,
                         "target_mass_g": config.aircraft.target_mass_g, "design_load_factor_g": config.aircraft.design_load_factor_g},
        "selected_preliminary_geometry": {**asdict(geometry), "horizontal_area_from_planform_m2": geometry.horizontal_area_from_planform_m2,
            "elevator_area_m2": geometry.elevator_area_m2, "fin_area_each_m2": geometry.fin_area_each_m2,
            "vertical_total_area_m2": geometry.vertical_total_area_m2, "horizontal_aspect_ratio": geometry.horizontal_aspect_ratio,
            "vertical_aspect_ratio_each": geometry.vertical_aspect_ratio_each,
            "tail_ac_x_mm": config.tail.aerodynamic_center_x_mm},
        "derived": {"horizontal_tail_volume": volume_h, "vertical_tail_volume_total_effective_area": volume_v,
            "wing_ac_x_mm_model_reference": mac_fraction_to_x_mm(config, .25), "wing_lift_slope_per_rad_model": wing_slope,
            "tail_lift_slope_per_rad_nominal": tail_slope, "neutral_point_mac_range": _range(item.neutral_point_mac for item in cases),
            "neutral_point_x_mm_range": _range(mac_fraction_to_x_mm(config, item.neutral_point_mac) for item in cases),
            "nominal_neutral_point_mac": nominal_np, "nominal_neutral_point_x_mm": mac_fraction_to_x_mm(config, nominal_np)},
        "stability_sensitivity": [asdict(case) for case in cases],
        "design_cg_envelope": {**design_cg, "derived_forward_trim_limit_mac": derived_forward_limit,
            "derived_aft_static_margin_limit_mac": derived_aft_limit,
            "minimum_static_margin_criterion_mac": MIN_DESIGN_STATIC_MARGIN_MAC,
            "forward_x_mm": mac_fraction_to_x_mm(config, design_cg["forward_mac"]),
            "nominal_x_mm": mac_fraction_to_x_mm(config, design_cg["nominal_mac"]), "aft_x_mm": mac_fraction_to_x_mm(config, design_cg["aft_mac"]),
            "static_margin_mac_range_across_sensitivity": {name: _range(static_margin_mac(case.neutral_point_mac, cg) for case in cases)
                for name, cg in design_cg.items()}},
        "first_flight_recommendation": {"cg_mac": recommendation.x_mac_fraction, "cg_x_mm": mac_fraction_to_x_mm(config, recommendation.x_mac_fraction),
            "minimum_static_margin_criterion_mac": MIN_FIRST_FLIGHT_STATIC_MARGIN_MAC,
            "static_margin_mac_nominal": static_margin_mac(nominal_np, recommendation.x_mac_fraction),
            "static_margin_mac_sensitivity_range": _range(static_margin_mac(case.neutral_point_mac, recommendation.x_mac_fraction) for case in cases),
            "status": "preliminary recommendation; requires measured mass properties and ground/flight verification"},
        "tail_arm_study": tail_arm_study,
        "elevator_trim_study": trim_cases,
        "elevator_authority_screening": {"conditional_elevator_travel_deg": USABLE_ELEVATOR_TRAVEL_DEG,
            "maximum_trim_fraction_of_usable_travel": MAX_TRIM_FRACTION_OF_USABLE_TRAVEL,
            "maximum_trim_deflection_deg": trim_limit_deg,
            "available_incremental_pitching_moment_coefficient_range": _range(recovery_moment),
            "interpretation": "If the selected linkage proves +/-20 deg usable linear travel, the full low-Re trim sweep remains within 60% of travel. Stall/recovery remains TBD until tail polar, linkage and flight-test evidence exist."},
        "twin_fin_screening": {"total_effective_area_m2": geometry.vertical_total_area_m2, "area_each_m2": geometry.fin_area_each_m2,
            "vertical_tail_volume": volume_v, "rudder_chord_fraction": geometry.rudder_chord_fraction,
            "net_cn_beta_proxy_minimum_criterion_per_rad": .025,
            "selected_geometry_cn_beta_proxy_range": _range(case["net_cn_beta_proxy_per_rad"] for case in selected_directional),
            "directional_sensitivity": directional_cases,
            "directional_stability_status": "Cn-beta is a conservative proxy sensitivity, not a complete aircraft derivative; boom/fuselage side area, fin interference and rudder hinge effectiveness still require geometry/test evidence."},
        "prop_boom_clearance_study": clearance,
        "assumptions": {"wing_ac_mac": .25, "section_lift_slope_per_rad": 2.0 * math.pi, "finite_surface_oswald_efficiency": .90,
            "tail_efficiency_study": list(TAIL_EFFICIENCY_STUDY), "tail_lift_slope_study_per_rad": list(TAIL_LIFT_SLOPE_STUDY_PER_RAD), "downwash_gradient_study": list(DOWNWASH_GRADIENT_STUDY),
            "fuselage_neutral_point_shift_study_mac": list(FUSELAGE_NEUTRAL_POINT_SHIFT_STUDY),
            "wing_cm_ac_study": [-.10, -.08, -.06], "elevator_effectiveness_study": list(ELEVATOR_EFFECTIVENESS_STUDY),
            "vertical_tail_volume_study": list(VERTICAL_TAIL_VOLUME_STUDY), "fin_lift_slope_study_per_rad": list(FIN_LIFT_SLOPE_STUDY_PER_RAD), "twin_fin_efficiency_study": list(TWIN_FIN_EFFICIENCY_STUDY), "non_tail_cn_beta_study_per_rad": list(NON_TAIL_CN_BETA_STUDY_PER_RAD),
            "prop_clearance_study_boom_radius_mm": geometry.boom_radius_m * 1000.0, "prop_clearance_study_required_clearance_mm": geometry.clearance_m * 1000.0},
        "tbd": ["actual fuselage/boom side and lifting contribution", "tail airfoil/Reynolds polar and measured incidence", "propwash/thrust-line power-on trim", "verified elevator and rudder hinge/control effectiveness", "boom outer diameter, deflection and dynamic clearance", "measured mass properties before first flight"],
    }


def write_plots(summary: dict[str, Any], output_dir: Path) -> None:
    plots = output_dir / "plots"; plots.mkdir(parents=True, exist_ok=True)
    arms = sorted(set(item["tail_arm_mm"] for item in summary["tail_arm_study"]))
    fig, axis = plt.subplots(figsize=(7, 4))
    for volume in HORIZONTAL_TAIL_VOLUME_STUDY:
        values = [next(item["required_horizontal_area_m2"] for item in summary["tail_arm_study"] if item["tail_arm_mm"] == arm and item["horizontal_tail_volume"] == volume) for arm in arms]
        axis.plot(arms, values, marker="o", label=f"Vh={volume:.2f}")
    axis.set(xlabel="Tail arm (mm)", ylabel="Required horizontal-tail area (m²)", title="Tail-volume trade study"); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "horizontal_tail_area_vs_arm.png", dpi=150); plt.close(fig)
    cases = summary["stability_sensitivity"]
    fig, axis = plt.subplots(figsize=(7, 4)); axis.scatter([c["tail_efficiency"] for c in cases], [c["neutral_point_mac"] for c in cases], c=[c["downwash_gradient"] for c in cases], cmap="viridis")
    axis.axhspan(.24, .34, color="tab:green", alpha=.15, label="Design CG envelope"); axis.set(xlabel="Tail efficiency", ylabel="Neutral point (MAC)", title="Neutral-point sensitivity"); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "neutral_point_sensitivity.png", dpi=150); plt.close(fig)
    clear = summary["prop_boom_clearance_study"]
    fig, axis = plt.subplots(figsize=(7, 4)); axis.plot([c["propeller_diameter_mm"] for c in clear], [c["minimum_boom_axis_spacing_mm_at_z0"] for c in clear], marker="o")
    axis.axhline(460, color="tab:green", linestyle="--", label="Baseline spacing: 460 mm"); axis.set(xlabel="Study propeller diameter (mm)", ylabel="Required boom axis spacing (mm)", title="Radial propeller/boom clearance, z=0"); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "boom_spacing_vs_prop_diameter.png", dpi=150); plt.close(fig)
    trim = [item for item in summary["elevator_trim_study"] if item["condition"] != "climb_study"]
    fig, axis = plt.subplots(figsize=(7, 4)); speeds = [item["speed_km_h"] for item in trim]
    lows = [item["incremental_trim_elevator_deflection_deg_range"]["minimum"] for item in trim]; highs = [item["incremental_trim_elevator_deflection_deg_range"]["maximum"] for item in trim]
    axis.fill_between(speeds, lows, highs, alpha=.25, label="Sensitivity envelope")
    axis.plot(speeds, lows, marker="o", color="tab:blue"); axis.plot(speeds, highs, marker="o", color="tab:blue")
    axis.axhline(0, color="black", linewidth=.8); axis.set(xlabel="Airspeed (km/h)", ylabel="Incremental elevator deflection (deg)", title="Linear trim-control sensitivity"); axis.grid(True, alpha=.3); axis.legend(); fig.tight_layout(); fig.savefig(plots / "elevator_trim_vs_airspeed.png", dpi=150); plt.close(fig)


def main() -> int:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=ROOT / "analysis" / "tail"); parser.add_argument("--no-plots", action="store_true")
    args = parser.parse_args(); summary = make_summary(load_aircraft_config())
    args.output.mkdir(parents=True, exist_ok=True); (args.output / "summary.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    if not args.no_plots: write_plots(summary, args.output)
    print(f"LR1600 tail stability study: {args.output / 'summary.json'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
