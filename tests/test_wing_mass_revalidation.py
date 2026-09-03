import json
from pathlib import Path

import pytest

from scripts.analyze_wing_mass_revalidation import build_summary, write_outputs
from scripts.config import load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]


def test_2600g_mass_sensitivity_preserves_reference_yaml_and_scales_loads():
    config = load_aircraft_config(ROOT / "config/aircraft.yaml")
    assert config.aircraft.target_mass_g == 2600
    summary = build_summary()
    reference = summary["cases"]["2400g_reference"]
    sensitivity = summary["cases"]["2600g_sensitivity"]
    ratio = 2600 / 2400
    assert summary["mass_ratio_2600_over_2400"] == pytest.approx(ratio)
    for field in ("total_design_lift_n", "per_panel_lift_n", "root_shear_n", "root_bending_moment_nm"):
        assert sensitivity[field] / reference[field] == pytest.approx(ratio, rel=2e-5)
    assert sensitivity["main_spar"]["root_bending_stress_mpa"] == pytest.approx(139.6, rel=.01)


def test_2600g_qualification_gates_preserve_existing_concept_without_strength_substitution():
    summary = build_summary()
    gates = summary["qualification_requirements_for_2600g"]
    assert gates["spar_measured_EI_min_nm2"] == pytest.approx(63.12, rel=.01)
    assert gates["spar_equivalent_effective_E_min_gpa_for_existing_14x12"] == pytest.approx(72.73, rel=.01)
    assert gates["dbox_root_equivalent_GJ_min_nm2"] == pytest.approx(22.9)
    assert gates["representative_joiner_socket_proof_torque_nm"] == pytest.approx(21.64, rel=.01)
    assert gates["representative_joiner_socket_proof_force_per_existing_250mm_arm_n"] == pytest.approx(86.6, rel=.01)
    assert "deflection only" in gates["note_on_EI"]
    status = summary["qualification_status"]
    assert status["state"] == "UNQUALIFIED_PENDING_2600G_SPECIFIC_EVIDENCE"
    assert status["canonical_2400g_gate_is_not_transferable"] is True


def test_outputs_are_internal_consistent(tmp_path: Path):
    summary = build_summary()
    write_outputs(summary, tmp_path)
    saved = json.loads((tmp_path / "summary.json").read_text(encoding="utf-8"))
    lines = (tmp_path / "comparison.csv").read_text(encoding="utf-8").splitlines()
    assert saved["scope"]["canonical_target_mass_g"] == 2600
    assert len(lines) == 3
    assert "spar_tip_deflection_E70_mm" in lines[0]
