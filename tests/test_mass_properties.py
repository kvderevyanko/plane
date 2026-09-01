from dataclasses import replace

import pytest

from scripts.config import MassComponentConfig, load_aircraft_config
from scripts.mass_properties import MassPropertiesError, calculate_mass_properties


def known(component_id: str, mass_g: float, x_mm: float, y_mm: float, z_mm: float) -> MassComponentConfig:
    return MassComponentConfig(component_id, component_id, "known", mass_g, x_mm, y_mm, z_mm, "center", None)


def test_calculates_total_mass_and_three_axis_cg_for_known_items():
    result = calculate_mass_properties((
        known("a", 100.0, 10.0, -20.0, 5.0),
        known("b", 300.0, 30.0, 20.0, -5.0),
    ))

    assert result.total_mass_g == pytest.approx(400.0)
    assert result.x_cg_mm == pytest.approx(25.0)
    assert result.y_cg_mm == pytest.approx(10.0)
    assert result.z_cg_mm == pytest.approx(-2.5)
    assert result.is_final_aircraft_cg


def test_symmetric_pair_has_zero_y_cg():
    result = calculate_mass_properties((
        known("left", 50.0, 100.0, -120.0, 15.0),
        known("right", 50.0, 100.0, 120.0, 15.0),
    ))

    assert result.y_cg_mm == pytest.approx(0.0, abs=1e-12)


def test_tbd_items_are_reported_and_block_final_aircraft_cg():
    incomplete = replace(known("battery", 0.0, 0.0, 0.0, 0.0), status="tbd", mass_g=None, x_mm=None, y_mm=None, z_mm=None)
    result = calculate_mass_properties((known("wing", 200.0, 100.0, 0.0, 0.0), incomplete))

    assert result.total_mass_g == pytest.approx(200.0)
    assert result.x_cg_mm == pytest.approx(100.0)
    assert [item.id for item in result.unresolved_components] == ["battery"]
    assert not result.is_final_aircraft_cg


def test_design_estimates_produce_an_explicitly_nonfinal_estimated_configuration_cg():
    estimated = MassComponentConfig("battery", "Battery", "design_estimate", 600.0, 10.0, 0.0, 0.0, "center", None)
    result = calculate_mass_properties((known("wing", 1800.0, 90.0, 0.0, 0.0), estimated))

    assert result.total_mass_g == pytest.approx(1800.0)
    assert result.estimated_total_mass_g == pytest.approx(2400.0)
    assert result.estimated_x_cg_mm == pytest.approx(70.0)
    assert [item.id for item in result.design_estimate_components] == ["battery"]
    assert result.has_estimated_configuration_cg
    assert not result.is_final_aircraft_cg


def test_empty_known_subtotal_has_no_cg_and_keeps_tbd_items():
    component = MassComponentConfig("motor", "Motor", "tbd", None, None, None, None, "center", None)
    result = calculate_mass_properties((component,))

    assert result.total_mass_g == 0.0
    assert result.x_cg_mm is result.y_cg_mm is result.z_cg_mm is None
    assert [item.id for item in result.unresolved_components] == ["motor"]
    assert not result.is_final_aircraft_cg


@pytest.mark.parametrize("component", [
    known("negative", -1.0, 0.0, 0.0, 0.0),
    known("nan", 1.0, float("nan"), 0.0, 0.0),
    MassComponentConfig("incomplete", "Incomplete", "known", 1.0, None, 0.0, 0.0, "center", None),
])
def test_rejects_invalid_mass_items(component: MassComponentConfig):
    with pytest.raises(MassPropertiesError):
        calculate_mass_properties((component,))


def test_repository_tbd_ledger_is_not_silently_treated_as_aircraft_cg():
    config = load_aircraft_config()
    result = calculate_mass_properties(config.mass_budget.components)

    assert result.total_mass_g == 0.0
    assert len(result.unresolved_components) == len(config.mass_budget.components)
    assert not result.is_final_aircraft_cg
