import copy
import hashlib
import json
from pathlib import Path

import pytest
import yaml

from scripts.analyze_material_measurements import (
    MeasurementError,
    analyze_measurements,
    build_summary,
    density_kg_m3,
    ei_from_central_load,
    gj_from_torque,
    load_measurement_summary,
)
from scripts.analyze_wing_structure import analyze
from scripts.config import load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]


def empty_document() -> dict:
    return yaml.safe_load((ROOT / "analysis/materials/measurements.example.yaml").read_text(encoding="utf-8"))


def measured_document() -> dict:
    data = empty_document()
    data["foam"]["foam_3mm"]["samples"] = [
        {"id": f"MAT-FOAM3-0{i}", "length_mm": 100, "width_mm": 100, "thickness_measurements_mm": [3, 3, 3], "mass_g": 1.2}
        for i in range(1, 4)
    ]
    data["carbon"]["spar_14x12"] = {
        "dimensional_stations": [
            {"station_mm": 0, "od_x_mm": 14, "od_y_mm": 14, "id_x_mm": 12, "id_y_mm": 12},
            {"station_mm": 600, "od_x_mm": 14, "od_y_mm": 14, "id_x_mm": 12, "id_y_mm": 12},
        ],
        "mass_specimen": {"length_mm": 800, "mass_g": 52},
        "bending_test": {"support_span_mm": 600, "points": [
            {"load_n": 5, "deflection_mm": 0.3701},
            {"load_n": 10, "deflection_mm": 0.7402},
            {"load_n": 15, "deflection_mm": 1.1103},
        ]},
    }
    data["beam_tests"] = [{"id": "PLY-BEND-B2-L-01", "material": "birch_2mm", "direction": "long", "support_span_mm": 200, "width_mm": 25, "thickness_measurements_mm": [2, 2, 2], "points": [{"load_n": 2, "deflection_mm": .2}, {"load_n": 4, "deflection_mm": .4}]}]
    data["adhesive_joints"] = [{"id": "GLUE-CB-01", "family": "carbon_birch2", "bond_area_mm2": 2500, "parts_mass_before_g": 10, "assembly_mass_after_g": 11, "first_slip_load_n": 10, "failure_load_n": 20, "failure_mode": "mixed", "mixed_failure_modes": ["plywood_delamination", "adhesive_interface"]}]
    data["dbox_tests"] = [{"id": "DBOX-C-01", "variant": "C", "length_mm": 300, "chord_mm": 250, "spar_fraction": .30, "closed_cell": True, "torque_points": [{"torque_nm": 1, "angle_deg": .753}, {"torque_nm": 2, "angle_deg": 1.506}], "mass_breakdown_g": {"foam": 20, "ribs": 10, "closure": 5, "reinforcement_dry": 6, "adhesive_resin": 3, "fixture_mass_g": 2, "complete_article_mass_g": 46}}]
    return data


def test_density_and_units_are_exact():
    assert density_kg_m3(100, 100, [3, 3, 3], 1.2) == pytest.approx(40.0)
    assert ei_from_central_load(600, 10, .7402) == pytest.approx(60.79, rel=2e-3)
    assert gj_from_torque(300, 2, 1.506) == pytest.approx(22.83, rel=2e-3)


def test_empty_document_explicitly_preserves_missing_state():
    result = analyze_measurements(empty_document())
    assert result["density_kg_m3"]["foam_3mm"]["state"] == "NOT_MEASURED"
    assert result["carbon_spar_14x12"]["bending"]["state"] == "NOT_MEASURED"
    assert result["dbox"]["state"] == "NOT_MEASURED"


def test_measurement_aggregates_ei_gj_and_retained_glue_mass():
    result = analyze_measurements(measured_document())
    assert result["density_kg_m3"]["foam_3mm"]["mean"] == pytest.approx(40)
    carbon = result["carbon_spar_14x12"]
    assert carbon["mass_per_m"]["value"] == pytest.approx(65)
    assert carbon["bending"]["valid_for_deflection_use"]
    assert result["adhesive_retained_mass"]["families"]["carbon_birch2"]["mean"] == pytest.approx(.04)
    assert result["dbox"][0]["actual_article_GJ_n_m2"] == pytest.approx(22.83, rel=2e-3)
    assert result["dbox"][0]["complete_article_mass_per_m"]["value"] == pytest.approx(44 / .3)
    assert result["dbox"][0]["fixture_mass_excluded_g"] == pytest.approx(2)


@pytest.mark.parametrize("mutate", [
    lambda data: data["foam"]["foam_3mm"]["samples"].append({"id": "BAD", "length_mm": 100, "width_mm": 100, "thickness_measurements_mm": [3, 3, 3], "mass_g": -1}),
    lambda data: data["carbon"].update({"spar_14x12": {"dimensional_stations": [{"station_mm": 0, "od_x_mm": 12, "od_y_mm": 12, "id_x_mm": 13, "id_y_mm": 11}], "mass_specimen": None, "bending_test": None}}),
])
def test_invalid_physical_inputs_are_rejected(mutate):
    data = empty_document(); mutate(data)
    with pytest.raises(MeasurementError):
        analyze_measurements(data)


def test_measured_ei_is_opt_in_and_never_changes_strength_allowables():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    summary = analyze_measurements(measured_document())
    baseline, _ = analyze(config, measurements=summary)
    opted, _ = analyze(config, measurements=summary, use_measured_stiffness=True, dbox_variant="C")
    assert baseline["main_spar"]["measured_stiffness"]["state"] == "NOT_USED"
    assert opted["main_spar"]["measured_stiffness"]["strength_allowables"] == "NOT_REPLACED"
    assert opted["main_spar"]["material_envelopes"] == baseline["main_spar"]["material_envelopes"]
    assert opted["mass_budget"]["measured_inputs_used"]["foam_3mm"]["state"] == "MEASURED"
    assert opted["mass_budget"]["measured_inputs_used"]["dbox_complete_article"]["state"] == "MEASURED"


def test_density_needs_three_samples_and_carbon_e_needs_dimensional_gate():
    data = measured_document()
    data["foam"]["foam_3mm"]["samples"] = data["foam"]["foam_3mm"]["samples"][:1]
    summary = analyze_measurements(data)
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    result, _ = analyze(config, measurements=summary)
    assert "foam_3mm" not in result["mass_budget"]["measured_inputs_used"]
    data = measured_document()
    data["carbon"]["spar_14x12"]["dimensional_stations"][0]["od_x_mm"] = 14.5
    assert not analyze_measurements(data)["carbon_spar_14x12"]["bending"]["valid_for_deflection_use"]


def test_density_scatter_always_propagates_to_mass_range():
    data = measured_document()
    data["foam"]["foam_3mm"]["samples"][1]["mass_g"] = 1.5
    summary = analyze_measurements(data)
    result, _ = analyze(load_aircraft_config(ROOT / "config/aircraft.yaml"), measurements=summary)
    assert result["mass_budget"]["items_g"]["foam_3mm_skins_top_and_bottom"][0] < result["mass_budget"]["items_g"]["foam_3mm_skins_top_and_bottom"][1]


def test_adhesive_mass_projection_requires_all_families_and_explicit_areas():
    result = analyze_measurements(measured_document())
    assert result["wing_adhesive_mass_projection"]["state"] == "NOT_MEASURED"
    assert result["adhesive_retained_mass"]["glue_gate"]["state"] == "NOT_MEASURED"


def test_measurement_workflow_reads_typed_yaml_not_generated_snapshot():
    source = (ROOT / "scripts/analyze_material_measurements.py").read_text(encoding="utf-8")
    assert "generated/parameters.json" not in source
    result = analyze_measurements(empty_document())
    assert result["provenance"]["aircraft_typed_loader"]["wing"]["span_mm"] == 1600


def test_socket_requires_125_percent_proof_and_explicit_failure_observations():
    data = measured_document()
    data["socket_tests"] = [{"id": "SOCKET-01", "moment_steps_nm": [5, 10, 15.982], "residual_displacement_mm": 0, "slip": False, "crush": False, "hoop_split": False, "delamination": False, "plate_crack": False}]
    result = analyze_measurements(data)
    assert not result["socket"][0]["pass"]
    data["socket_tests"][0]["moment_steps_nm"].append(20.0)
    assert analyze_measurements(data)["socket"][0]["pass"]
    data["socket_tests"][0]["slip"] = True
    failed = analyze_measurements(data)["socket"][0]
    assert not failed["pass"]
    assert failed["failure_observations"]["slip"] is True


def test_dbox_gate_requires_both_linearity_and_actual_gj_threshold():
    data = measured_document()
    data["dbox_tests"][0]["torque_points"] = [{"torque_nm": 1, "angle_deg": 3}, {"torque_nm": 2, "angle_deg": 6}]
    result = analyze_measurements(data)
    assert not result["dbox"][0]["gate"]["GJ_pass"]
    assert not result["dbox"][0]["valid_for_dbox_gate"]


def test_rejects_metre_values_in_mm_density_fields_and_invalid_glue_mode():
    data = empty_document()
    data["foam"]["foam_3mm"]["samples"] = [{"id": "BAD-UNITS", "length_mm": .1, "width_mm": .1, "thickness_measurements_mm": [.003, .003, .003], "mass_g": 1}]
    with pytest.raises(MeasurementError, match="metre"):
        analyze_measurements(data)
    data = measured_document()
    data["adhesive_joints"][0]["failure_mode"] = "uncontrolled"
    with pytest.raises(MeasurementError, match="failure_mode"):
        analyze_measurements(data)


def test_glue_gate_rejects_no_load_no_failure_and_impossible_family_mode():
    data = empty_document()
    data["adhesive_joints"] = [{"id": f"GLUE-FF-{index}", "family": "foam_foam", "bond_area_mm2": 625, "parts_mass_before_g": 1, "assembly_mass_after_g": 1.1, "failure_mode": "no_failure"} for index in range(3)]
    with pytest.raises(MeasurementError, match="maximum_applied"):
        analyze_measurements(data)
    data = measured_document()
    data["adhesive_joints"][0]["failure_mode"] = "cohesive_foam"
    data["adhesive_joints"][0].pop("mixed_failure_modes")
    with pytest.raises(MeasurementError, match="impossible"):
        analyze_measurements(data)


def test_glue_gate_fails_three_coupon_carbon_mixed_adhesive_interface_regression():
    data = empty_document()
    joints = []
    for family, mode in (("foam_foam", "cohesive_foam"), ("foam_birch2", "cohesive_foam"), ("birch2_birch2", "plywood_delamination")):
        joints.extend({"id": f"{family}-{index}", "family": family, "bond_area_mm2": 625, "parts_mass_before_g": 1, "assembly_mass_after_g": 1.1, "failure_load_n": 10, "failure_mode": mode} for index in range(3))
    joints.extend({"id": f"carbon-{index}", "family": "carbon_birch2", "bond_area_mm2": 625, "parts_mass_before_g": 1, "assembly_mass_after_g": 1.1, "failure_load_n": 10, "failure_mode": "mixed", "mixed_failure_modes": ["plywood_delamination", "adhesive_interface"]} for index in range(3))
    data["adhesive_joints"] = joints
    glue = analyze_measurements(data)["adhesive_retained_mass"]
    assert glue["families"]["carbon_birch2"]["coupon_evidence"][0]["mixed_failure_modes"] == ["plywood_delamination", "adhesive_interface"]
    assert glue["glue_gate"]["state"] == "DERIVED"
    assert not glue["glue_gate"]["pass"]
    assert glue["glue_gate"]["unacceptable_failure_modes"]["carbon_birch2"] == ["adhesive_interface"]


def test_summary_trust_boundary_rejects_hand_edit_and_stale_raw(tmp_path: Path):
    raw_path = tmp_path / "measurements.yaml"
    raw_path.write_text(yaml.safe_dump(empty_document()), encoding="utf-8")
    digest = hashlib.sha256(raw_path.read_bytes()).hexdigest()
    summary = build_summary(yaml.safe_load(raw_path.read_text(encoding="utf-8")), ROOT / "config/aircraft.yaml", raw_path, digest)
    summary_path = tmp_path / "summary.json"
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    assert load_measurement_summary(summary_path, config_path=ROOT / "config/aircraft.yaml")["schema"] == "lr1600-material-results-v2"
    summary["density_kg_m3"]["foam_3mm"] = {"state": "DERIVED", "n": 3, "mean": 1, "min": 1, "max": 1, "stddev": 0}
    summary_path.write_text(json.dumps(summary), encoding="utf-8")
    with pytest.raises(MeasurementError, match="edited"):
        load_measurement_summary(summary_path, config_path=ROOT / "config/aircraft.yaml")
