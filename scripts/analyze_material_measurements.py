#!/usr/bin/env python3
"""Validate raw LR1600 home-test observations and derive material metrics.

This program deliberately separates an observation from an engineering
allowable.  It only derives density, mass-per-length, EI/E from linear elastic
test data, retained adhesive mass and D-box GJ.  Missing observations stay
``NOT_MEASURED``; no value is inferred from aircraft.yaml or the structural
envelopes.  All aircraft configuration access is through the typed loader so a
result has traceable geometry provenance without duplicating the YAML model.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from dataclasses import asdict
from pathlib import Path
from statistics import mean, pstdev
from typing import Any

import yaml

try:
    from config import DEFAULT_CONFIG_PATH, load_aircraft_config
except ImportError:  # pragma: no cover
    from scripts.config import DEFAULT_CONFIG_PATH, load_aircraft_config

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_INPUT = ROOT / "analysis" / "materials" / "measurements.yaml"
DEFAULT_OUTPUT = ROOT / "analysis" / "materials" / "results" / "summary.json"
SCHEMA = "lr1600-material-measurements-v1"
RESULT_SCHEMA = "lr1600-material-results-v2"
ANALYZER_VERSION = 2
NOT_MEASURED = {"state": "NOT_MEASURED"}


class MeasurementError(ValueError):
    """Input has an invalid unit, impossible value or unknown schema field."""


def _positive(value: Any, field: str, *, zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or (value < 0 if zero else value <= 0):
        comparator = "non-negative" if zero else "positive"
        raise MeasurementError(f"{field} must be a finite {comparator} number in documented SI/mm/g units")
    return float(value)


def _mapping(value: Any, field: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise MeasurementError(f"{field} must be a mapping")
    return value


def _only(mapping: dict[str, Any], allowed: set[str], field: str) -> None:
    unknown = set(mapping) - allowed
    if unknown:
        raise MeasurementError(f"{field} has unknown fields: {sorted(unknown)}")


def _sequence(value: Any, field: str) -> list[Any]:
    if not isinstance(value, list):
        raise MeasurementError(f"{field} must be a list")
    return value


def _stat(values: list[float], unit: str) -> dict[str, Any]:
    if not values:
        return dict(NOT_MEASURED)
    return {"state": "DERIVED", "unit": unit, "n": len(values), "mean": mean(values), "min": min(values), "max": max(values), "stddev": pstdev(values) if len(values) > 1 else 0.0}


def _canonical_digest(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")).hexdigest()


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def density_kg_m3(length_mm: float, width_mm: float, thicknesses_mm: list[float], mass_g: float) -> float:
    """Return density from measured dimensions; mm³/g convert exactly to kg/m³."""
    thickness = mean(thicknesses_mm)
    return mass_g * 1_000_000.0 / (length_mm * width_mm * thickness)


def rectangular_second_moment_m4(width_mm: float, thickness_mm: float) -> float:
    return (width_mm / 1000.0) * (thickness_mm / 1000.0) ** 3 / 12.0


def ei_from_central_load(support_span_mm: float, load_n: float, deflection_mm: float) -> float:
    """Simply-supported central-load EI in N m²."""
    return load_n * (support_span_mm / 1000.0) ** 3 / (48.0 * (deflection_mm / 1000.0))


def gj_from_torque(length_mm: float, torque_nm: float, angle_deg: float) -> float:
    """Prismatic torsion-test GJ in N m²."""
    return torque_nm * (length_mm / 1000.0) / math.radians(angle_deg)


def _linear_fit_through_origin(points: list[tuple[float, float]]) -> dict[str, float]:
    """Fit load = slope * deflection, returning r² against the origin fit."""
    if len(points) < 2:
        raise MeasurementError("A stiffness test needs at least two non-zero load/deflection points")
    denominator = sum(deflection * deflection for _, deflection in points)
    if denominator <= 0:
        raise MeasurementError("deflection data cannot all be zero")
    slope = sum(load * deflection for load, deflection in points) / denominator
    total = sum(load * load for load, _ in points)
    residual = sum((load - slope * deflection) ** 2 for load, deflection in points)
    return {"slope_n_per_m": slope, "r_squared": 1.0 - residual / total if total else 0.0}


def _sample_density(samples: Any, field: str) -> dict[str, Any]:
    densities: list[float] = []
    for index, raw in enumerate(_sequence(samples, field)):
        sample = _mapping(raw, f"{field}[{index}]")
        _only(sample, {"id", "length_mm", "width_mm", "thickness_measurements_mm", "mass_g", "photo"}, f"{field}[{index}]")
        if not isinstance(sample.get("id"), str) or not sample["id"]:
            raise MeasurementError(f"{field}[{index}].id must be non-empty")
        length = _positive(sample.get("length_mm"), f"{field}[{index}].length_mm")
        width = _positive(sample.get("width_mm"), f"{field}[{index}].width_mm")
        if length < 10 or width < 10:
            raise MeasurementError(f"{field}[{index}] dimensions look like metre values entered in mm fields")
        thicknesses = [_positive(value, f"{field}[{index}].thickness_measurements_mm") for value in _sequence(sample.get("thickness_measurements_mm"), f"{field}[{index}].thickness_measurements_mm")]
        if len(thicknesses) < 3:
            raise MeasurementError(f"{field}[{index}] needs at least three thickness measurements")
        if min(thicknesses) < .1 or max(thicknesses) > 20:
            raise MeasurementError(f"{field}[{index}] thickness is physically implausible for this coupon workflow")
        density = density_kg_m3(length, width, thicknesses, _positive(sample.get("mass_g"), f"{field}[{index}].mass_g"))
        if not 5 <= density <= 2500:
            raise MeasurementError(f"{field}[{index}] density is physically implausible; check mm/g units")
        densities.append(density)
    return _stat(densities, "kg/m3")


def _beam_result(test: dict[str, Any], field: str) -> dict[str, Any]:
    _only(test, {"id", "material", "direction", "support_span_mm", "width_mm", "thickness_measurements_mm", "points", "photo"}, field)
    span = _positive(test.get("support_span_mm"), f"{field}.support_span_mm")
    width = _positive(test.get("width_mm"), f"{field}.width_mm")
    thicknesses = [_positive(value, f"{field}.thickness_measurements_mm") for value in _sequence(test.get("thickness_measurements_mm"), f"{field}.thickness_measurements_mm")]
    if len(thicknesses) < 3:
        raise MeasurementError(f"{field} needs at least three thickness measurements")
    points: list[tuple[float, float]] = []
    for index, raw in enumerate(_sequence(test.get("points"), f"{field}.points")):
        point = _mapping(raw, f"{field}.points[{index}]")
        _only(point, {"load_n", "deflection_mm"}, f"{field}.points[{index}]")
        points.append((_positive(point.get("load_n"), f"{field}.points[{index}].load_n"), _positive(point.get("deflection_mm"), f"{field}.points[{index}].deflection_mm")))
    fit = _linear_fit_through_origin([(load, deflection / 1000.0) for load, deflection in points])
    ei = fit["slope_n_per_m"] * (span / 1000.0) ** 3 / 48.0
    inertia = rectangular_second_moment_m4(width, mean(thicknesses))
    return {"state": "DERIVED", "id": test.get("id", field), "material": test.get("material"), "direction": test.get("direction"), "EI_n_m2": ei, "effective_E_gpa": ei / inertia / 1e9, "linearity_r_squared": fit["r_squared"], "valid_for_stiffness_use": fit["r_squared"] >= .995, "note": "Effective stiffness only; this home test does not establish a strength allowable."}


def _carbon_result(carbon: dict[str, Any]) -> dict[str, Any]:
    _only(carbon, {"dimensional_stations", "mass_specimen", "bending_test"}, "carbon.spar_14x12")
    stations = _sequence(carbon.get("dimensional_stations"), "carbon.spar_14x12.dimensional_stations")
    ods: list[float] = []; ids: list[float] = []
    for index, raw in enumerate(stations):
        station = _mapping(raw, f"carbon.spar_14x12.dimensional_stations[{index}]")
        _only(station, {"station_mm", "od_x_mm", "od_y_mm", "id_x_mm", "id_y_mm"}, f"carbon.spar_14x12.dimensional_stations[{index}]")
        _positive(station.get("station_mm"), f"carbon station {index}.station_mm", zero=True)
        odx, ody = _positive(station.get("od_x_mm"), f"carbon station {index}.od_x_mm"), _positive(station.get("od_y_mm"), f"carbon station {index}.od_y_mm")
        idx, idy = _positive(station.get("id_x_mm"), f"carbon station {index}.id_x_mm"), _positive(station.get("id_y_mm"), f"carbon station {index}.id_y_mm")
        if max(idx, idy) >= min(odx, ody):
            raise MeasurementError(f"carbon station {index}: ID must be less than OD in both axes")
        ods.extend((odx, ody)); ids.extend((idx, idy))
    walls = [(min(float(s["od_x_mm"]), float(s["od_y_mm"])) - max(float(s["id_x_mm"]), float(s["id_y_mm"]))) / 2 for s in stations]
    ovalities = [abs(float(s["od_x_mm"]) - float(s["od_y_mm"])) for s in stations]
    geometry = {"stations": stations, "od_mm": _stat(ods, "mm"), "id_mm": _stat(ids, "mm"), "ovality_mm": _stat(ovalities, "mm"), "minimum_wall_mm": _stat(walls, "mm")}
    geometry_gate: dict[str, Any] = dict(NOT_MEASURED)
    if stations:
        od_ok = min(ods) >= 13.90 and max(ods) <= 14.10
        id_ok = min(ids) >= 11.85 and max(ids) <= 12.10
        wall_ok = min(walls) >= .90
        ovality_ok = max(ovalities) <= .20
        geometry_gate = {"state": "DERIVED", "pass": od_ok and id_ok and wall_ok and ovality_ok, "od_range_pass": od_ok, "id_range_pass": id_ok, "minimum_wall_pass": wall_ok, "max_ovality_pass": ovality_ok, "limits_mm": {"od": [13.90, 14.10], "id": [11.85, 12.10], "wall_min": .90, "ovality_max": .20}}
    mass_data = carbon.get("mass_specimen")
    mass_per_m: dict[str, Any] = dict(NOT_MEASURED)
    if mass_data is not None:
        mass = _mapping(mass_data, "carbon.spar_14x12.mass_specimen")
        _only(mass, {"length_mm", "mass_g"}, "carbon.spar_14x12.mass_specimen")
        mass_per_m = {"state": "DERIVED", "unit": "g/m", "value": _positive(mass.get("mass_g"), "carbon mass_g") * 1000 / _positive(mass.get("length_mm"), "carbon length_mm")}
    bending = carbon.get("bending_test")
    bending_result: dict[str, Any] = dict(NOT_MEASURED)
    if bending is not None:
        test = _mapping(bending, "carbon.spar_14x12.bending_test")
        _only(test, {"support_span_mm", "points"}, "carbon.spar_14x12.bending_test")
        span = _positive(test.get("support_span_mm"), "carbon bending support_span_mm")
        points = []
        for index, raw in enumerate(_sequence(test.get("points"), "carbon bending points")):
            point = _mapping(raw, f"carbon bending points[{index}]"); _only(point, {"load_n", "deflection_mm"}, f"carbon bending points[{index}]")
            points.append((_positive(point.get("load_n"), "carbon bending load_n"), _positive(point.get("deflection_mm"), "carbon bending deflection_mm") / 1000.0))
        fit = _linear_fit_through_origin(points)
        ei = fit["slope_n_per_m"] * (span / 1000) ** 3 / 48.0
        if geometry["od_mm"]["state"] == "DERIVED" and geometry["id_mm"]["state"] == "DERIVED":
            od, inner = geometry["od_mm"]["mean"] / 1000, geometry["id_mm"]["mean"] / 1000
            inertia = math.pi / 64 * (od**4 - inner**4)
            effective_e = ei / inertia / 1e9
        else:
            effective_e = None
        bending_result = {"state": "DERIVED", "EI_n_m2": ei, "effective_E_gpa": effective_e, "linearity_r_squared": fit["r_squared"], "valid_for_deflection_use": bool(effective_e is not None and fit["r_squared"] >= .995 and geometry_gate.get("pass") is True), "note": "Non-destructive effective E may update deflection only after dimensional gate passes. It never replaces tensile/compression/shear strength envelopes."}
    return {"geometry": geometry, "geometry_gate": geometry_gate, "mass_per_m": mass_per_m, "bending": bending_result}


def _adhesive_result(joints: Any) -> dict[str, Any]:
    families = ("foam_foam", "foam_birch2", "birch2_birch2", "carbon_birch2")
    values: dict[str, list[float]] = {family: [] for family in families}
    first_slip: dict[str, list[float]] = {family: [] for family in families}
    failure_load: dict[str, list[float]] = {family: [] for family in families}
    maximum_applied: dict[str, list[float]] = {family: [] for family in families}
    modes: dict[str, list[str]] = {family: [] for family in families}
    evidence: dict[str, list[dict[str, Any]]] = {family: [] for family in families}
    family_modes = {
        "foam_foam": {"cohesive_foam", "adhesive_interface", "mixed", "no_failure"},
        "foam_birch2": {"cohesive_foam", "adhesive_interface", "mixed", "no_failure"},
        "birch2_birch2": {"plywood_delamination", "adhesive_interface", "mixed", "no_failure"},
        "carbon_birch2": {"plywood_delamination", "adhesive_interface", "carbon_interface", "mixed", "no_failure"},
    }
    for index, raw in enumerate(_sequence(joints, "adhesive_joints")):
        joint = _mapping(raw, f"adhesive_joints[{index}]")
        _only(joint, {"id", "family", "bond_area_mm2", "parts_mass_before_g", "assembly_mass_after_g", "first_slip_load_n", "failure_load_n", "maximum_applied_load_n", "failure_mode", "mixed_failure_modes", "photo"}, f"adhesive_joints[{index}]")
        family = joint.get("family")
        if family not in families:
            raise MeasurementError(f"adhesive_joints[{index}].family is unsupported")
        before, after = _positive(joint.get("parts_mass_before_g"), "adhesive parts_mass_before_g", zero=True), _positive(joint.get("assembly_mass_after_g"), "adhesive assembly_mass_after_g")
        if after < before:
            raise MeasurementError("assembly_mass_after_g cannot be less than parts_mass_before_g")
        area_cm2 = _positive(joint.get("bond_area_mm2"), "adhesive bond_area_mm2") / 100
        values[family].append((after - before) / area_cm2)
        per_joint_loads: dict[str, float] = {}
        for key, target in (("first_slip_load_n", first_slip), ("failure_load_n", failure_load), ("maximum_applied_load_n", maximum_applied)):
            if joint.get(key) is not None:
                per_joint_loads[key] = _positive(joint[key], f"adhesive {key}")
                target[family].append(per_joint_loads[key])
        mode = joint.get("failure_mode")
        if mode not in family_modes[family]:
            raise MeasurementError(f"adhesive failure_mode {mode!r} is impossible for {family}")
        if mode == "no_failure" and "maximum_applied_load_n" not in per_joint_loads:
            raise MeasurementError("adhesive no_failure needs positive maximum_applied_load_n")
        if mode != "no_failure" and not ({"first_slip_load_n", "failure_load_n"} & set(per_joint_loads)):
            raise MeasurementError("adhesive failure observation needs positive first_slip_load_n and/or failure_load_n")
        mixed_detail = joint.get("mixed_failure_modes")
        if mode == "mixed":
            if not isinstance(mixed_detail, list) or len(mixed_detail) < 2 or any(value not in family_modes[family] - {"mixed", "no_failure"} for value in mixed_detail):
                raise MeasurementError("mixed adhesive failure needs two or more family-valid mixed_failure_modes")
        elif mixed_detail is not None:
            raise MeasurementError("mixed_failure_modes is allowed only when failure_mode is mixed")
        modes[family].append(mode)
        evidence[family].append({"id": joint.get("id"), "failure_mode": mode, "mixed_failure_modes": mixed_detail or [], "first_slip_load_n": per_joint_loads.get("first_slip_load_n"), "failure_load_n": per_joint_loads.get("failure_load_n"), "maximum_applied_load_n": per_joint_loads.get("maximum_applied_load_n")})
    output: dict[str, Any] = {}
    for family in families:
        retained = _stat(values[family], "g/cm2")
        output[family] = retained | {"first_slip_load_n": _stat(first_slip[family], "N"), "failure_load_n": _stat(failure_load[family], "N"), "maximum_applied_load_n": _stat(maximum_applied[family], "N"), "failure_modes": modes[family], "coupon_evidence": evidence[family]}
    unacceptable = {"adhesive_interface", "carbon_interface"}
    enough = all(output[family].get("n", 0) >= 3 for family in families)
    bad = {family: sorted({mode for coupon in output[family]["coupon_evidence"] for mode in [coupon["failure_mode"], *coupon["mixed_failure_modes"]] if mode in unacceptable}) for family in families}
    if not enough:
        gate = {"state": "NOT_MEASURED", "reason": "Each of four adhesive families needs at least three coupons."}
    elif any(bad.values()):
        gate = {"state": "DERIVED", "pass": False, "unacceptable_failure_modes": bad}
    else:
        gate = {"state": "DERIVED", "pass": True, "unacceptable_failure_modes": bad, "note": "Home-test evidence only; this is not a numerical joint strength allowable."}
    return {"families": output, "glue_gate": gate}


def _adhesive_projection(adhesive: dict[str, Any], model: Any) -> dict[str, Any]:
    families = ("foam_foam", "foam_birch2", "birch2_birch2", "carbon_birch2")
    coefficients = adhesive["families"]
    if model is None:
        return {"state": "NOT_MEASURED", "reason": "No complete wing bond-area model supplied; coupon g/cm2 is not projected into wing mass."}
    data = _mapping(model, "wing_bond_area_model")
    _only(data, {"source", "areas_cm2"}, "wing_bond_area_model")
    if not isinstance(data.get("source"), str) or not data["source"]:
        raise MeasurementError("wing_bond_area_model.source must identify the reproducible geometry/bond-area source")
    areas = _mapping(data.get("areas_cm2"), "wing_bond_area_model.areas_cm2")
    if set(areas) != set(families):
        raise MeasurementError("wing bond-area model must contain all four adhesive families")
    if adhesive["glue_gate"].get("pass") is not True or any(coefficients[family].get("state") != "DERIVED" or coefficients[family].get("n", 0) < 3 for family in families):
        return {"state": "NOT_MEASURED", "reason": "Every adhesive family needs at least three retained-mass coupon observations before projection."}
    low = sum(float(coefficients[family]["min"]) * _positive(areas[family], f"bond area {family}") for family in families)
    high = sum(float(coefficients[family]["max"]) * _positive(areas[family], f"bond area {family}") for family in families)
    return {"state": "DERIVED", "unit": "g", "range_g": [low, high], "bond_area_source": data["source"], "areas_cm2": areas}


def _dbox_result(tests: Any, config: Any) -> list[dict[str, Any]] | dict[str, str]:
    output: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(tests, "dbox_tests")):
        test = _mapping(raw, f"dbox_tests[{index}]")
        _only(test, {"id", "variant", "length_mm", "chord_mm", "spar_fraction", "closed_cell", "torque_points", "mass_breakdown_g", "photo"}, f"dbox_tests[{index}]")
        if test.get("variant") not in {"A", "B", "C"}:
            raise MeasurementError("dbox variant must be A, B or C")
        if test.get("closed_cell") is not True:
            raise MeasurementError("dbox test must explicitly confirm a closed cell")
        if abs(_positive(test.get("chord_mm"), "dbox chord_mm") - config.wing.root_chord_mm) > .5 or abs(_positive(test.get("spar_fraction"), "dbox spar_fraction") - config.spar.chord_position) > .005:
            raise MeasurementError("dbox article geometry does not match typed root chord / spar fraction")
        length = _positive(test.get("length_mm"), "dbox length_mm")
        points: list[tuple[float, float]] = []
        for point_index, point_raw in enumerate(_sequence(test.get("torque_points"), "dbox torque_points")):
            point = _mapping(point_raw, f"dbox torque_points[{point_index}]"); _only(point, {"torque_nm", "angle_deg"}, "dbox torque point")
            points.append((_positive(point.get("torque_nm"), "dbox torque_nm"), _positive(point.get("angle_deg"), "dbox angle_deg")))
        fit = _linear_fit_through_origin([(torque, math.radians(angle)) for torque, angle in points])
        gj = fit["slope_n_per_m"] * (length / 1000.0)
        mass = _mapping(test.get("mass_breakdown_g"), "dbox mass_breakdown_g")
        required_mass = {"foam", "ribs", "closure", "reinforcement_dry", "adhesive_resin", "fixture_mass_g", "complete_article_mass_g"}
        _only(mass, required_mass, "dbox mass_breakdown_g")
        if set(mass) != required_mass:
            raise MeasurementError("dbox mass_breakdown_g must include every constituent and complete")
        for key, value in mass.items():
            _positive(value, f"dbox mass_breakdown_g.{key}", zero=True)
        components = sum(float(mass[key]) for key in required_mass - {"complete_article_mass_g"})
        if abs(float(mass["complete_article_mass_g"]) - components) > max(.2, .05 * float(mass["complete_article_mass_g"])):
            raise MeasurementError("dbox complete mass does not reconcile with constituent masses")
        flight_representative_mass = float(mass["complete_article_mass_g"]) - float(mass["fixture_mass_g"])
        if flight_representative_mass <= 0:
            raise MeasurementError("D-box flight-representative mass must remain positive after fixture exclusion")
        complete_mass_per_m = flight_representative_mass / (length / 1000.0)
        linear = fit["r_squared"] >= .995
        gj_pass = gj >= 22.8
        output.append({"state": "DERIVED", "id": test.get("id"), "variant": test.get("variant"), "actual_article_GJ_n_m2": gj, "linearity_r_squared": fit["r_squared"], "GJ_threshold_n_m2": 22.8, "valid_for_dbox_gate": linear and gj_pass, "gate": {"linearity_pass": linear, "GJ_pass": gj_pass, "pass": linear and gj_pass}, "mass_breakdown_g": mass, "complete_article_mass_per_m": {"state": "DERIVED", "unit": "g/m", "value": complete_mass_per_m, "basis": "closed root article, excluding explicitly recorded test-only fixture mass"}, "fixture_mass_excluded_g": float(mass["fixture_mass_g"]), "note": "Actual article GJ is independent of effective material G; it may only confirm the D-box torsion gate."})
    return output or dict(NOT_MEASURED)


def _joiner_result(joiner: dict[str, Any], carbon: dict[str, Any]) -> dict[str, Any]:
    _only(joiner, {"solid_rod", "fit_pairs"}, "joiner")
    rod = _mapping(joiner.get("solid_rod"), "joiner.solid_rod")
    _only(rod, {"diameter_measurements_mm", "mass_specimen"}, "joiner.solid_rod")
    diameters = [_positive(value, "joiner rod diameter") for value in _sequence(rod.get("diameter_measurements_mm"), "joiner.solid_rod.diameter_measurements_mm")]
    rod_geometry = _stat(diameters, "mm")
    rod_mass: dict[str, Any] = dict(NOT_MEASURED)
    if rod.get("mass_specimen") is not None:
        specimen = _mapping(rod["mass_specimen"], "joiner rod mass_specimen")
        _only(specimen, {"length_mm", "mass_g"}, "joiner rod mass_specimen")
        rod_mass = {"state": "DERIVED", "unit": "g/m", "value": _positive(specimen.get("mass_g"), "joiner rod mass_g") * 1000 / _positive(specimen.get("length_mm"), "joiner rod length_mm")}
    rod_gate = dict(NOT_MEASURED)
    if diameters:
        rod_gate = {"state": "DERIVED", "pass": min(diameters) >= 11.50 and max(diameters) <= 11.70, "limits_mm": [11.50, 11.70]}
    pairs: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(joiner.get("fit_pairs"), "joiner.fit_pairs")):
        pair = _mapping(raw, f"joiner.fit_pairs[{index}]")
        _only(pair, {"id", "tube_station_mm", "tube_id_mm", "rod_od_mm"}, f"joiner.fit_pairs[{index}]")
        tube_id = _positive(pair.get("tube_id_mm"), "joiner pair tube_id_mm")
        rod_od = _positive(pair.get("rod_od_mm"), "joiner pair rod_od_mm")
        clearance = (tube_id - rod_od) / 2
        if clearance < 0:
            raise MeasurementError("joiner pair has impossible negative radial clearance")
        pairs.append({"id": pair.get("id"), "tube_station_mm": _positive(pair.get("tube_station_mm"), "joiner pair tube_station_mm", zero=True), "tube_id_mm": tube_id, "rod_od_mm": rod_od, "radial_clearance_mm": clearance, "pass": .075 <= clearance <= .175})
    tube_gate = carbon["geometry_gate"]
    dimension_gate = {"state": "DERIVED", "pass": bool(rod_gate.get("pass") and tube_gate.get("pass") and pairs and all(pair["pass"] for pair in pairs)), "rod_gate": rod_gate, "tube_gate": tube_gate, "fit_pairs": pairs or dict(NOT_MEASURED), "required_radial_clearance_mm": [.075, .175]}
    return {"solid_rod": {"diameter_mm": rod_geometry, "mass_per_m": rod_mass, "geometry_gate": rod_gate}, "fit": dimension_gate}


def _socket_result(tests: Any, required_moment_nm: float) -> list[dict[str, Any]] | dict[str, str]:
    output: list[dict[str, Any]] = []
    for index, raw in enumerate(_sequence(tests, "socket_tests")):
        test = _mapping(raw, f"socket_tests[{index}]")
        _only(test, {"id", "moment_steps_nm", "residual_displacement_mm", "slip", "crush", "hoop_split", "delamination", "plate_crack", "photo"}, f"socket_tests[{index}]")
        steps = [_positive(value, "socket moment step") for value in _sequence(test.get("moment_steps_nm"), "socket moment_steps_nm")]
        if not steps:
            raise MeasurementError("socket test needs moment steps")
        failures = {name: test.get(name) for name in ("slip", "crush", "hoop_split", "delamination", "plate_crack")}
        if any(not isinstance(value, bool) for value in failures.values()):
            raise MeasurementError("socket failure observations must be explicit booleans")
        residual = _positive(test.get("residual_displacement_mm"), "socket residual_displacement_mm", zero=True)
        proof_reached = max(steps) >= required_moment_nm
        passed = proof_reached and residual <= .10 and not any(failures.values())
        output.append({"state": "DERIVED", "id": test.get("id"), "required_proof_moment_nm": required_moment_nm, "maximum_applied_moment_nm": max(steps), "residual_displacement_mm": residual, "failure_observations": failures, "pass": passed, "note": "1.25 x current design/limit root moment is the structural closeout proof, not a strength allowable."})
    return output or dict(NOT_MEASURED)


def _validate_metadata(metadata: Any) -> dict[str, Any]:
    data = _mapping(metadata, "metadata")
    _only(data, {"format_version", "data_variant", "operator", "scale_resolution_g", "caliper_resolution_mm", "ambient_temperature_c"}, "metadata")
    if data.get("format_version") != 1:
        raise MeasurementError("metadata.format_version must be 1")
    if data.get("data_variant") != "home-test-v1":
        raise MeasurementError("metadata.data_variant must be home-test-v1")
    for key in ("scale_resolution_g", "caliper_resolution_mm"):
        if data.get(key) is not None:
            _positive(data[key], f"metadata.{key}")
    if data.get("ambient_temperature_c") is not None:
        _positive(data["ambient_temperature_c"], "metadata.ambient_temperature_c", zero=True)
    if data.get("operator") is not None and not isinstance(data["operator"], str):
        raise MeasurementError("metadata.operator must be a string")
    return data


def _validate_supplementary_records(document: dict[str, Any], foam: dict[str, Any], plywood: dict[str, Any], lwpla: dict[str, Any]) -> dict[str, Any]:
    """Strictly acknowledge non-derived observations so they are never discarded."""
    counts: dict[str, int] = {}
    for name, entry in foam.items():
        item = _mapping(entry, f"foam.{name}"); _only(item, {"samples", "indentation_tests"}, f"foam.{name}")
        tests = _sequence(item.get("indentation_tests"), f"foam.{name}.indentation_tests")
        for raw in tests:
            test = _mapping(raw, "foam indentation test"); _only(test, {"id", "indenter_area_mm2", "steps", "recovery_mm", "photo"}, "foam indentation test")
            _positive(test.get("indenter_area_mm2"), "foam indenter area")
            _positive(test.get("recovery_mm"), "foam recovery", zero=True)
            for point in _sequence(test.get("steps"), "foam indentation steps"):
                row = _mapping(point, "foam indentation step"); _only(row, {"load_n", "indentation_mm"}, "foam indentation step")
                _positive(row.get("load_n"), "foam indentation load"); _positive(row.get("indentation_mm"), "foam indentation", zero=True)
        counts[f"{name}_indentation"] = len(tests)
    for name, entry in plywood.items():
        item = _mapping(entry, f"plywood.{name}"); _only(item, {"samples", "visual_observations"}, f"plywood.{name}")
        observations = _sequence(item.get("visual_observations"), f"plywood.{name}.visual_observations")
        for record in observations:
            if not isinstance(record, str):
                raise MeasurementError("plywood visual observation must be text")
        counts[f"{name}_visual"] = len(observations)
    bearing = _sequence(document.get("bearing_tests"), "bearing_tests")
    for record in bearing:
        item = _mapping(record, "bearing test"); _only(item, {"id", "material", "hole_diameter_mm", "first_ovality_load_n", "failure_load_n", "failure_mode", "photo"}, "bearing test")
        _positive(item.get("hole_diameter_mm"), "bearing hole diameter")
        for key in ("first_ovality_load_n", "failure_load_n"):
            if item.get(key) is not None:
                _positive(item[key], f"bearing {key}")
    counts["bearing"] = len(bearing)
    if lwpla.get("bending_test") is not None:
        _beam_result(_mapping(lwpla["bending_test"], "lwpla.bending_test"), "lwpla.bending_test")
    creep = _sequence(lwpla.get("creep_tests"), "lwpla.creep_tests")
    for record in creep:
        item = _mapping(record, "lwpla creep test"); _only(item, {"id", "temperature_c", "load_n", "deflections_mm", "photo"}, "lwpla creep test")
        _positive(item.get("temperature_c"), "lwpla creep temperature", zero=True); _positive(item.get("load_n"), "lwpla creep load")
        for value in _sequence(item.get("deflections_mm"), "lwpla creep deflections"):
            _positive(value, "lwpla creep deflection", zero=True)
    counts["lwpla_creep"] = len(creep)
    return {"state": "MEASURED" if any(counts.values()) else "NOT_MEASURED", "record_counts": counts}


def analyze_measurements(document: dict[str, Any], config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Any]:
    _only(document, {"schema", "metadata", "foam", "plywood", "beam_tests", "bearing_tests", "carbon", "joiner", "lwpla", "adhesive_joints", "wing_bond_area_model", "dbox_tests", "socket_tests"}, "measurement document")
    if document.get("schema") != SCHEMA:
        raise MeasurementError(f"schema must be {SCHEMA}")
    metadata = _validate_metadata(document.get("metadata"))
    config = load_aircraft_config(config_path)
    foam = _mapping(document.get("foam"), "foam"); plywood = _mapping(document.get("plywood"), "plywood")
    _only(foam, {"foam_3mm", "foam_5mm"}, "foam"); _only(plywood, {"poplar_2mm", "birch_2mm", "birch_3mm"}, "plywood")
    density = {name: _sample_density(_mapping(foam[name], f"foam.{name}").get("samples"), f"foam.{name}.samples") for name in foam}
    density.update({name: _sample_density(_mapping(plywood[name], f"plywood.{name}").get("samples"), f"plywood.{name}.samples") for name in plywood})
    beams = []
    for index, raw in enumerate(_sequence(document.get("beam_tests"), "beam_tests")):
        beams.append(_beam_result(_mapping(raw, f"beam_tests[{index}]"), f"beam_tests[{index}]"))
    carbon = _carbon_result(_mapping(document.get("carbon"), "carbon").get("spar_14x12"))
    joiner = _joiner_result(_mapping(document.get("joiner"), "joiner"), carbon)
    lwpla = _mapping(document.get("lwpla"), "lwpla")
    _only(lwpla, {"samples", "bending_test", "creep_tests"}, "lwpla")
    lwpla_density = _sample_density(lwpla.get("samples"), "lwpla.samples")
    required_socket_moment = config.aircraft.target_mass_kg * config.aircraft.gravity_m_s2 * config.aircraft.design_load_factor_g / 2 * 4 * (config.wing.panel_span_mm / 1000) / (3 * math.pi) * 1.25
    adhesive = _adhesive_result(document.get("adhesive_joints"))
    return {"schema": RESULT_SCHEMA, "analyzer_version": ANALYZER_VERSION, "provenance": {"aircraft_config": str(config_path), "aircraft_typed_loader": asdict(config), "input_state": "MEASURED observations only", "config_sha256": _file_digest(config_path)}, "metadata": metadata, "density_kg_m3": density | {"lwpla": lwpla_density}, "plywood_beam_tests": beams or dict(NOT_MEASURED), "carbon_spar_14x12": carbon, "joiner": joiner, "adhesive_retained_mass": adhesive, "wing_adhesive_mass_projection": _adhesive_projection(adhesive, document.get("wing_bond_area_model")), "dbox": _dbox_result(document.get("dbox_tests"), config), "socket": _socket_result(document.get("socket_tests"), required_socket_moment), "supplementary_records": _validate_supplementary_records(document, foam, plywood, lwpla), "unresolved": "NOT_MEASURED means no observation was supplied; strength allowables remain independent assumptions or datasheet values."}


def build_summary(document: dict[str, Any], config_path: Path, input_path: Path, input_sha256: str) -> dict[str, Any]:
    result = analyze_measurements(document, config_path)
    result["provenance"]["input_path"] = str(input_path.resolve())
    result["provenance"]["input_sha256"] = input_sha256
    result["derived_sha256"] = _canonical_digest(result)
    return result


def load_measurement_summary(path: Path, *, config_path: Path = DEFAULT_CONFIG_PATH, raw_input: Path | None = None) -> dict[str, Any]:
    """Reject edited/stale summaries by regenerating their derived payload from raw YAML."""
    stored = json.loads(path.read_text(encoding="utf-8"))
    if stored.get("schema") != RESULT_SCHEMA or stored.get("analyzer_version") != ANALYZER_VERSION:
        raise MeasurementError("not a current lr1600 material results file")
    provenance = _mapping(stored.get("provenance"), "results provenance")
    source = raw_input or Path(provenance.get("input_path", ""))
    if not source.is_file():
        raise MeasurementError("raw measurement YAML required to validate results trust boundary")
    raw_bytes = source.read_bytes()
    if provenance.get("input_sha256") != hashlib.sha256(raw_bytes).hexdigest():
        raise MeasurementError("measurement results are stale: raw YAML digest differs")
    if provenance.get("config_sha256") != _file_digest(config_path):
        raise MeasurementError("measurement results are stale: typed aircraft YAML changed")
    stored_without_digest = dict(stored)
    stored_digest = stored_without_digest.pop("derived_sha256", None)
    if stored_digest != _canonical_digest(stored_without_digest):
        raise MeasurementError("measurement results were edited")
    rebuilt = build_summary(_mapping(yaml.safe_load(raw_bytes), "measurement document"), config_path, source, hashlib.sha256(raw_bytes).hexdigest())
    if stored.get("derived_sha256") != rebuilt["derived_sha256"]:
        raise MeasurementError("measurement results were edited or do not match raw YAML")
    return rebuilt


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    args = parser.parse_args()
    if not args.input.is_file():
        raise SystemExit(f"Measurement input is absent: {args.input}. Copy analysis/materials/measurements.example.yaml first.")
    raw_bytes = args.input.read_bytes()
    raw = yaml.safe_load(raw_bytes)
    result = build_summary(_mapping(raw, "measurement document"), args.config, args.input, hashlib.sha256(raw_bytes).hexdigest())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Material measurement summary written to {args.output}")


if __name__ == "__main__":
    main()
