#!/usr/bin/env python3
"""Reproducible preliminary structural sizing for the LR1600 wing.

This is deliberately a *concept-validation* calculation, not a release drawing
or a material allowables database.  Aircraft dimensions, mass, gravity and the
candidate spar are read only through :func:`scripts.config.load_aircraft_config`.
Material values below are explicitly labelled envelopes until coupons and vendor
data replace them.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

try:
    from config import DEFAULT_CONFIG_PATH, AircraftConfig, load_aircraft_config
except ImportError:  # pragma: no cover - supports module and script invocation
    from scripts.config import DEFAULT_CONFIG_PATH, AircraftConfig, load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUTPUT = ROOT / "analysis" / "structures"
SCHEMA = "lr1600-wing-structure-v1"


@dataclass(frozen=True)
class CarbonEnvelope:
    name: str
    youngs_modulus_gpa: float
    tensile_strength_mpa: float
    compressive_strength_mpa: float
    shear_strength_mpa: float
    density_kg_m3: float


# These are not claims about a particular supplier tube.  They bracket common
# non-aerospace hobby/commercial pultrusions until a data sheet and coupons exist.
CARBON_ENVELOPES = (
    CarbonEnvelope("conservative", 70.0, 350.0, 300.0, 35.0, 1550.0),
    CarbonEnvelope("nominal", 110.0, 600.0, 500.0, 60.0, 1600.0),
    CarbonEnvelope("high_quality", 140.0, 900.0, 750.0, 90.0, 1650.0),
)


def tube_properties(outer_diameter_m: float, inner_diameter_m: float) -> dict[str, float]:
    """Area, second moment and section modulus of a circular annulus in SI."""
    if not 0 <= inner_diameter_m < outer_diameter_m:
        raise ValueError("tube diameters must be positive and OD must exceed ID")
    area = math.pi / 4.0 * (outer_diameter_m**2 - inner_diameter_m**2)
    second_moment = math.pi / 64.0 * (outer_diameter_m**4 - inner_diameter_m**4)
    return {
        "area_m2": area,
        "second_moment_m4": second_moment,
        "section_modulus_m3": second_moment / (outer_diameter_m / 2.0),
    }


def solid_rod_properties(diameter_m: float) -> dict[str, float]:
    return tube_properties(diameter_m, 0.0)


def trapezoid_integral(values: list[float], spacing: float) -> float:
    return sum((left + right) * spacing / 2.0 for left, right in zip(values, values[1:]))


def reverse_integral(values: list[float], spacing: float) -> list[float]:
    """Integral from station y to the tip for equally spaced data."""
    result = [0.0] * len(values)
    for index in range(len(values) - 2, -1, -1):
        result[index] = result[index + 1] + (values[index] + values[index + 1]) * spacing / 2.0
    return result


def elliptic_load(panel_span_m: float, panel_lift_n: float, stations: int = 801) -> dict[str, list[float]]:
    """Elliptic distributed lift, then V and M for one root-supported panel."""
    y = [panel_span_m * index / (stations - 1) for index in range(stations)]
    q = [panel_lift_n * 4.0 / (math.pi * panel_span_m) * math.sqrt(max(0.0, 1.0 - (value / panel_span_m) ** 2)) for value in y]
    dy = y[1] - y[0]
    shear = reverse_integral(q, dy)
    # M(y) = integral_y^tip q(s) * (s-y) ds.  Integrating shear backward is
    # numerically stable and guarantees M(tip)=0.
    moment = reverse_integral(shear, dy)
    return {"y_m": y, "q_n_m": q, "shear_n": shear, "moment_nm": moment}


def cantilever_deflection(moment_nm: list[float], spacing_m: float, youngs_modulus_pa: float, second_moment_m4: float) -> list[float]:
    curvature = [moment / (youngs_modulus_pa * second_moment_m4) for moment in moment_nm]
    slope = [0.0] * len(moment_nm)
    deflection = [0.0] * len(moment_nm)
    for index in range(1, len(moment_nm)):
        slope[index] = slope[index - 1] + (curvature[index - 1] + curvature[index]) * spacing_m / 2.0
        deflection[index] = deflection[index - 1] + (slope[index - 1] + slope[index]) * spacing_m / 2.0
    return deflection


def rectangular_tube_properties(width_m: float, height_m: float, wall_m: float) -> dict[str, float]:
    inner_width, inner_height = width_m - 2 * wall_m, height_m - 2 * wall_m
    if min(inner_width, inner_height, wall_m) <= 0:
        raise ValueError("invalid rectangular tube")
    area = width_m * height_m - inner_width * inner_height
    second_moment = (width_m * height_m**3 - inner_width * inner_height**3) / 12.0
    return {"area_m2": area, "second_moment_m4": second_moment, "section_modulus_m3": second_moment / (height_m / 2)}


def caps_web_properties() -> dict[str, float]:
    """Two 8 x 1 mm caps, centrelines 24 mm apart; 0.5 mm x 24 mm web."""
    cap_width, cap_thickness, separation = .008, .001, .024
    cap_area = cap_width * cap_thickness
    cap_i_each = cap_width * cap_thickness**3 / 12 + cap_area * (separation / 2) ** 2
    web_i = .0005 * separation**3 / 12
    area = 2 * cap_area + .0005 * separation
    second_moment = 2 * cap_i_each + web_i
    return {"area_m2": area, "second_moment_m4": second_moment, "section_modulus_m3": second_moment / (separation / 2)}


def dbox_gj(chord_m: float, effective_shear_modulus_pa: float) -> float:
    """Thin-wall triangular one-cell screening estimate for LE--30%-chord D-box.

    The triangular cell is intentionally a rough geometric proxy.  Its output is a
    screening stiffness only; the effective shear modulus is what coupons must
    establish for a foam-only or reinforced skin lay-up.
    """
    width, depth, skin = .30 * chord_m, .11 * chord_m, .003
    area = .5 * width * depth
    perimeter = width + 2.0 * math.hypot(width / 2.0, depth)
    return 4.0 * area**2 * effective_shear_modulus_pa * skin / perimeter


def load_cruise_aero_cm(path: Path = ROOT / "analysis" / "aero" / "parsed" / "clarky_re300000_realistic_model_combined.csv") -> float:
    """Worst observed |CM| at the existing 70--100-km/h cruise CL bracket."""
    with path.open(newline="", encoding="utf-8") as source:
        rows = list(csv.DictReader(source))
    selected = [abs(float(row["cm"])) for row in rows if .13 <= float(row["cl"]) <= .30]
    if not selected:
        raise ValueError(f"No Re300k cruise-CL CM rows in {path}")
    return max(selected)


def aeroelastic_twist(config: AircraftConfig, speed_kmh: float, effective_shear_modulus_pa: float, cm_abs: float) -> float:
    """Tip twist from worst cruise CM plus c/4-to-spar lift transfer; not flutter."""
    rho = 1.225
    speed = speed_kmh / 3.6
    dynamic_pressure = .5 * rho * speed**2
    panel = config.wing.panel_span_mm / 1000.0
    stations = 801
    dy = panel / (stations - 1)
    chord = [((config.wing.root_chord_mm + (config.wing.tip_chord_mm - config.wing.root_chord_mm) * index / (stations - 1)) / 1000.0) for index in range(stations)]
    one_g = elliptic_load(panel, config.aircraft.target_mass_kg * config.aircraft.gravity_m_s2 / 2.0, stations)["q_n_m"]
    # Sum magnitudes deliberately: sign/elastic-axis uncertainty must not be
    # credited before a coupled aeroelastic model and D-box coupon exist.
    torque_per_span = [dynamic_pressure * cm_abs * value**2 + lift * (.30 - .25) * value for value, lift in zip(chord, one_g)]
    torque = reverse_integral(torque_per_span, dy)
    twist_gradient = [value / dbox_gj(c, effective_shear_modulus_pa) for value, c in zip(torque, chord)]
    return trapezoid_integral(twist_gradient, dy)


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader(); writer.writerows(rows)


def render_plot(path: Path, x: list[float], series: dict[str, list[float]], ylabel: str, title: str) -> None:
    figure, axis = plt.subplots(figsize=(7, 4), dpi=150)
    for label, values in series.items(): axis.plot(x, values, label=label, linewidth=1.6)
    axis.set(xlabel="Semi-span y (mm)", ylabel=ylabel, title=title)
    axis.grid(True, alpha=.3)
    if len(series) > 1: axis.legend()
    figure.tight_layout(); figure.savefig(path); plt.close(figure)


def mass_budget(config: AircraftConfig, carbon_density: float) -> dict[str, Any]:
    """Ranges retain unknown measured foam/printed densities as uncertainties."""
    panel = config.wing.panel_span_mm / 1000
    root_chord, tip_chord = config.wing.root_chord_mm / 1000, config.wing.tip_chord_mm / 1000
    panel_area = panel * (root_chord + tip_chord) / 2
    tube = tube_properties(config.spar.outer_diameter_mm / 1000, config.spar.inner_diameter_mm / 1000)
    joiner = solid_rod_properties(.0115)
    # Net rib plan area uses 70% of a 12%-thick profile bounding rectangle;
    # it is a stated planning estimate, to be replaced by generated net areas.
    typical_rib_area = .70 * ((root_chord + tip_chord) / 2) * .12 * ((root_chord + tip_chord) / 2)
    foam_rib_volume = typical_rib_area * .005 * 7
    birch_rib_volume = typical_rib_area * .002 * 4
    poplar_structural_volume = .000025  # hatch rails/formers, both panels
    dbox_birch_web_volume = 2 * panel * .025 * .002  # continuous spar closure, both panels
    birch_plates_volume = .000028       # root sockets and boom plates, both panels
    adhesive_mass = (35.0, 80.0)
    def interval(volume: float, densities: tuple[float, float]) -> tuple[float, float]: return tuple(round(volume * density * 1000, 1) for density in densities)
    full = {
        "foam_3mm_skins_top_and_bottom": interval(4 * panel_area * .003, (30, 80)),
        "foam_5mm_ordinary_ribs": interval(2 * foam_rib_volume, (30, 80)),
        "poplar_2mm_secondary_hatch_formers": interval(poplar_structural_volume, (420, 500)),
        "birch_2mm_root_boom_and_dbox_closure": interval(birch_rib_volume * 2 + birch_plates_volume + dbox_birch_web_volume, (600, 750)),
        "birch_3mm_local_only": (0.0, 18.0),
        "dbox_bias_laminate_and_resin": (35.0, 75.0),
        "carbon_main_spars": (round(2 * tube["area_m2"] * panel * carbon_density * 1000, 1),) * 2,
        "carbon_joiner_11_5mm_x_600mm": (round(joiner["area_m2"] * .600 * carbon_density * 1000, 1),) * 2,
        "lw_pla": (0.0, 0.0),
        "adhesive": adhesive_mass,
        "servo_mounts_wiring": (18.0, 38.0),
        "placeholder_servos_two": (40.0, 80.0),
    }
    low, high = (sum(value[0] for value in full.values()), sum(value[1] for value in full.values()))
    return {"per_console_excluding_joiner_g": [round((low - full["carbon_joiner_11_5mm_x_600mm"][0]) / 2, 1), round((high - full["carbon_joiner_11_5mm_x_600mm"][1]) / 2, 1)], "joiner_g": list(full["carbon_joiner_11_5mm_x_600mm"]), "full_wing_assembly_g": [round(low, 1), round(high, 1)], "percent_target_mass": [round(low / config.aircraft.target_mass_g * 100, 1), round(high / config.aircraft.target_mass_g * 100, 1)], "items_g": full, "note": "Planning range: foam density and printed density must be physically measured; no material density is inferred from aircraft.yaml."}


def proof_schedule(load: dict[str, list[float]], gravity_m_s2: float) -> list[dict[str, float]]:
    """Five equal-span bays, each loaded at its centre by a spreader pad."""
    y, q = load["y_m"], load["q_n_m"]
    stations_per_bay = (len(y) - 1) // 5
    zones = []
    for index in range(5):
        first, last = index * stations_per_bay, (index + 1) * stations_per_bay
        force = trapezoid_integral(q[first:last + 1], y[1] - y[0])
        zones.append({"centre_y_mm": (y[first] + y[last]) * 500, "load_at_100_percent_n": force, "hanging_mass_at_100_percent_kg": force / gravity_m_s2})
    return zones


def analyze(config: AircraftConfig, *, aero_polar_path: Path = ROOT / "analysis" / "aero" / "parsed" / "clarky_re300000_realistic_model_combined.csv") -> dict[str, Any]:
    panel_span = config.wing.panel_span_mm / 1000.0
    design_lift = config.aircraft.target_mass_kg * config.aircraft.gravity_m_s2 * config.aircraft.design_load_factor_g
    load = elliptic_load(panel_span, design_lift / 2.0)
    dy = load["y_m"][1] - load["y_m"][0]
    spar = tube_properties(config.spar.outer_diameter_mm / 1000, config.spar.inner_diameter_mm / 1000)
    root_moment, root_shear = load["moment_nm"][0], load["shear_n"][0]
    stress_mpa = root_moment / spar["section_modulus_m3"] / 1e6
    shear_mpa = 2.0 * root_shear / spar["area_m2"] / 1e6  # intentionally conservative screening factor
    envelopes = []
    deflections: dict[str, list[float]] = {}
    for envelope in CARBON_ENVELOPES:
        deflection = cantilever_deflection(load["moment_nm"], dy, envelope.youngs_modulus_gpa * 1e9, spar["second_moment_m4"])
        deflections[envelope.name] = deflection
        envelopes.append({"name": envelope.name, "youngs_modulus_gpa": envelope.youngs_modulus_gpa, "root_bending_stress_mpa": stress_mpa, "root_shear_screening_mpa": shear_mpa, "tension_sf": envelope.tensile_strength_mpa / stress_mpa, "compression_sf": envelope.compressive_strength_mpa / stress_mpa, "shear_sf": envelope.shear_strength_mpa / shear_mpa, "tip_deflection_mm": deflection[-1] * 1000})
    joiner = solid_rod_properties(.0115)
    joiner_stress = root_moment / joiner["section_modulus_m3"] / 1e6
    contact_force = root_moment / .0115
    contact_length_m, minimum_tube_wall_m = .050, .00090
    bearing_stress = contact_force / (.0115 * contact_length_m) / 1e6
    hoop_screening = contact_force / (2 * minimum_tube_wall_m * contact_length_m) / 1e6
    birch_bearing = contact_force / (2 * .002 * contact_length_m) / 1e6
    birch_net_tension = contact_force / (2 * .002 * .030) / 1e6
    bondline_shear = contact_force / (2 * .050 * .050) / 1e6
    joiner_centre_span_m = .050
    joiner_deflection = {
        envelope.name: root_moment * joiner_centre_span_m**2 / (8 * envelope.youngs_modulus_gpa * 1e9 * joiner["second_moment_m4"]) * 1000
        for envelope in CARBON_ENVELOPES
    }
    joiner_envelopes = [{"name": envelope.name, "bending_sf_tension": envelope.tensile_strength_mpa / joiner_stress, "bending_sf_compression": envelope.compressive_strength_mpa / joiner_stress, "centre_50mm_screening_deflection_mm": joiner_deflection[envelope.name]} for envelope in CARBON_ENVELOPES]
    alternatives = []
    for name, properties, comment in (
        ("round_14x12", spar, "Current candidate; simple ribs and purchase, but deflection must be proof-tested."),
        ("rectangular_16x8x1", rectangular_tube_properties(.016, .008, .001), "Less bending I in this orientation; no advantage unless a vendor section is materially better."),
        ("carbon_caps_8x1_web_0_5", caps_web_properties(), "Highest stiffness/mass potential, but needs reliable web bonds, rib integration and damage-tolerant manufacture."),
    ):
        alternatives.append({"name": name, "area_mm2": properties["area_m2"] * 1e6, "I_mm4": properties["second_moment_m4"] * 1e12, "Z_mm3": properties["section_modulus_m3"] * 1e9, "root_stress_nominal_mpa": root_moment / properties["section_modulus_m3"] / 1e6, "comment": comment})
    cm_abs = load_cruise_aero_cm(aero_polar_path)
    twist = {str(speed): {"foam_only_conservative_deg": math.degrees(aeroelastic_twist(config, speed, 8e6, cm_abs)), "reinforced_dbox_conservative_deg": math.degrees(aeroelastic_twist(config, speed, 100e6, cm_abs)), "reinforced_dbox_nominal_deg": math.degrees(aeroelastic_twist(config, speed, 250e6, cm_abs)), "reinforced_dbox_minimum_g300_deg": math.degrees(aeroelastic_twist(config, speed, 300e6, cm_abs))} for speed in (70, 90, 100, 120)}
    return {
        "schema": SCHEMA,
        "calculation_status": "preliminary concept validation; not a production release",
        "configuration_from_typed_loader": {"path": str(DEFAULT_CONFIG_PATH.relative_to(ROOT)), "value": asdict(config)},
        "load_case": {"design_load_factor_g": config.aircraft.design_load_factor_g, "classification": "YAML does not define limit versus ultimate; treated here as the current design/limit case, not an ultimate rating.", "design_total_lift_n": design_lift, "per_panel_lift_n": design_lift / 2, "distribution": "elliptic, normalized separately on each semi-span", "sensitivity_cases": {"vertical_gust_screening": "1.25 x design lift sensitivity only; not a regulatory gust calculation", "vertical_gust_root_v_n": root_shear * 1.25, "vertical_gust_root_m_nm": root_moment * 1.25, "asymmetric_70_30_total_lift_split": "70/30 of total design lift: loaded/unloaded panel reactions, preserving total lift", "asymmetric_loaded_root_v_n": root_shear * 1.4, "asymmetric_loaded_root_m_nm": root_moment * 1.4, "asymmetric_unloaded_root_v_n": root_shear * .6, "asymmetric_unloaded_root_m_nm": root_moment * .6}},
        "main_spar": {"dimensions_mm": [config.spar.outer_diameter_mm, config.spar.inner_diameter_mm], "area_mm2": spar["area_m2"] * 1e6, "second_moment_mm4": spar["second_moment_m4"] * 1e12, "section_modulus_mm3": spar["section_modulus_m3"] * 1e9, "root_bending_moment_nm": root_moment, "root_shear_n": root_shear, "material_envelopes": envelopes, "purchasing_requirements": "OD 14.00 ±0.10 mm; measured ID at least 11.85 mm after ovality check; E >=70 GPa, compressive allowable >=300 MPa, tensile >=350 MPa, shear allowable >=35 MPa; continuous predominantly 0-degree fibres (pultruded or documented wound laminate), straightness <=1 mm/800 mm. Supplier data plus coupon/proof test required."},
        "joiner": {"recommendation": "precision solid carbon rod, nominal 11.5 mm, total 600 mm, 275 mm insertion per console with 50 mm controlled centre/support zone; do not specify nominal 12 mm without measured fit.", "properties": {key: value * (1e6 if key == "area_m2" else 1e12 if key == "second_moment_m4" else 1e9) for key, value in joiner.items()}, "root_moment_nm": root_moment, "bending_stress_mpa": joiner_stress, "material_envelopes": joiner_envelopes, "contact_couple_force_n": contact_force, "socket_screening": {"model": "50-mm prepared contact at each moment-couple support; external hoop sleeve and two 2-mm birch plates are mandatory", "minimum_tube_wall_mm": minimum_tube_wall_m * 1000, "carbon_contact_bearing_mpa": bearing_stress, "carbon_hoop_splitting_mpa": hoop_screening, "birch_plate_bearing_mpa": birch_bearing, "birch_plate_net_tension_mpa_with_30mm_ligament": birch_net_tension, "bondline_shear_mpa_over_two_50x50mm_plates": bondline_shear, "provisional_allowables_mpa": {"carbon_radial_bearing": 15.0, "carbon_hoop_with_external_sleeve": 25.0, "birch_bearing": 15.0, "birch_net_tension": 20.0}, "screening_sf": {"carbon_radial_bearing": 15.0 / bearing_stress, "carbon_hoop_with_external_sleeve": 25.0 / hoop_screening, "birch_bearing": 15.0 / birch_bearing, "birch_net_tension": 20.0 / birch_net_tension}, "status": "Provisional assumed-allowable screen only: no final socket SF until representative tube/liner/birch/bond coupons and proof test pass."}, "fit_requirement": "Measure every tube ID, OD, wall and rod OD. Select rod actual OD 11.50--11.70 mm, tube minimum ID >=11.85 mm, tube maximum ID <=12.10 mm and tube minimum wall >=0.90 mm, giving 0.075--0.175 mm radial clearance. A loose, unmeasured slip fit is prohibited.", "load_path": "Use a 50-mm long prepared internal G10/CF wear liner at each contact plus a 50-mm external ±45-degree carbon hoop sleeve. Each support is backed by two 2-mm birch longitudinal plates with >=30-mm net ligament and >=50-mm bonded length. The joiner end at y=275 mm is bracketed by ribs at y=250 and 300 mm. Do not rely on foam or an unbonded tube wall alone."},
        "spar_alternatives": alternatives,
        "dbox_twist_screening": {"cm_abs": cm_abs, "source": str(aero_polar_path.relative_to(ROOT)), "cruise_cl_bracket": [0.13, 0.30], "moment_model": "worst observed Re300k cruise |CM| plus 1-g elliptic lift transferred from c/4 to 30%-chord spar; magnitudes are summed conservatively", "root_gj_nm2_at_effective_g_250mpa": dbox_gj(config.wing.root_chord_mm / 1000, 250e6), "minimum_screening_requirement": "effective D-box G >= 300 MPa by coupon, equivalent root GJ >= 22.8 N m2; target tip twist <=2 deg at 100 km/h and <=3 deg at 120 km/h", "speed_cases_deg": twist, "conclusion": "Foam-only D-box is not acceptable as a validated torsion structure. Continuous closed LE-to-spar cell, 2-mm birch closure web and documented ±45-degree carbon/glass reinforcement are required; values remain coupon-dependent."},
        "mass_budget": mass_budget(config, 1600),
        "proof_test": {"distribution": "five equal-span load zones; use a broad pad/spreader at each centre, not point contact on foam", "loads_per_console": proof_schedule(load, config.aircraft.gravity_m_s2), "steps_percent": [25, 50, 75, 100], "dwell_s": 60, "release_condition": "125% is prohibited pending explicit limit/ultimate classification and safety review."},
        "recommendation": {"main_spar": "Keep 14x12 only provisionally: it has conservative strength screening SF >2.2 in bending, but 4-g tip deflection is a design driver and must pass proof test. Caps+web is a later mass/stiffness option, not an automatic change.", "root_ribs_per_console": [{"station_mm": 0, "material": "birch 2 mm"}, {"station_mm": 50, "material": "birch 2 mm"}, {"station_mm": 250, "material": "birch 2 mm"}, {"station_mm": 300, "material": "birch 2 mm"}], "ordinary_ribs": "5-mm foam at 100-mm nominal pitch; birch 2-mm locally at servo/boom mounts, no LW-PLA primary path. LW-PLA is suitable for tip rib, alignment and servo geometry only after mass/creep coupon.", "root_structure": "Four 2-mm birch ribs plus paired 2-mm birch longitudinal shear plates/root socket doublers. Use 3-mm birch only for a small boom/fastener doubler if bearing/net-section coupon or bolt sizing requires it.", "boom_attachment": "Two or more birch-2 ribs straddling each final boom station; clamp load through birch plates into spar and D-box closure, with anti-rotation fore/aft spacing. Foam is shape-only. Birch 3-mm only as local bolted crushing plate.", "servo": "Add a rear spar/false spar across two foam bays; use poplar 2-mm hatch rails only as secondary formers, birch 2-mm at servo screw/load transfer, and LW-PLA only non-primary locating geometry."},
    }, {"load": load, "deflections": deflections, "spar": spar}


def emit(result: dict[str, Any], working: dict[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "safety_factor_vs_envelope.png").unlink(missing_ok=True)
    (output / "summary.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    load = working["load"]
    section_modulus = working["spar"]["section_modulus_m3"]
    rows = [{"y_mm": y * 1000, "lift_n_per_m": q, "shear_n": shear, "moment_nm": moment, "spar_bending_stress_mpa": moment / section_modulus / 1e6} for y, q, shear, moment in zip(load["y_m"], load["q_n_m"], load["shear_n"], load["moment_nm"])]
    write_csv(output / "distributed_load.csv", rows)
    y_mm = [value * 1000 for value in load["y_m"]]
    render_plot(output / "load_vs_span.png", y_mm, {"lift q": load["q_n_m"]}, "Lift (N/m)", "Elliptic design lift per console")
    render_plot(output / "shear_vs_span.png", y_mm, {"V": load["shear_n"]}, "Shear (N)", "Shear force")
    render_plot(output / "moment_vs_span.png", y_mm, {"M": load["moment_nm"]}, "Bending moment (N m)", "Bending moment")
    render_plot(output / "deflection_vs_span.png", y_mm, {name: [value * 1000 for value in values] for name, values in working["deflections"].items()}, "Deflection (mm)", "14x12 spar, design load")
    stress = [row["spar_bending_stress_mpa"] for row in rows]
    render_plot(output / "safety_factor_vs_span.png", y_mm, {"conservative compression": [300.0 / max(value, .01) for value in stress], "nominal compression": [500.0 / max(value, .01) for value in stress], "high-quality compression": [750.0 / max(value, .01) for value in stress]}, "Compression safety factor", "14x12 spar safety factor along span")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--aero-polar", type=Path, default=ROOT / "analysis" / "aero" / "parsed" / "clarky_re300000_realistic_model_combined.csv")
    args = parser.parse_args()
    config = load_aircraft_config(args.config)
    result, working = analyze(config, aero_polar_path=args.aero_polar)
    result["calculation_provenance"] = {"config_path": str(args.config.resolve()), "aero_polar_path": str(args.aero_polar.resolve()), "output_path": str(args.output.resolve())}
    emit(result, working, args.output)
    print(f"Structural concept analysis written to {args.output}")


if __name__ == "__main__":
    main()
