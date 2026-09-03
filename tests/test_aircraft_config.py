from dataclasses import asdict
import json
import math
from pathlib import Path

import pytest

from scripts.config import ConfigurationError, load_aircraft_config
from scripts.generate_wing import (
    chord_at,
    generate,
    washout_at,
    wing_parameters_from_config,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "aircraft.yaml"
SNAPSHOT_FLOAT_ABS_TOLERANCE = 1e-12


def assert_complete_snapshot_matches_model(actual: object, expected: object) -> None:
    """Compare every JSON snapshot value with the typed generator model.

    ``parameters.json`` is deliberately checked as a complete, flat serialized
    dataclass rather than as a hand-picked subset.  The very small absolute
    tolerance only covers JSON's representation of Python floats; all values
    currently originate directly from the typed model.
    """
    assert isinstance(actual, dict)
    assert isinstance(expected, dict)
    assert set(actual) == set(expected)
    for key, expected_value in expected.items():
        actual_value = actual[key]
        if isinstance(expected_value, float):
            assert isinstance(actual_value, (int, float))
            assert math.isclose(
                actual_value,
                expected_value,
                rel_tol=0.0,
                abs_tol=SNAPSHOT_FLOAT_ABS_TOLERANCE,
            ), key
        else:
            assert actual_value == expected_value, key


def test_repository_aircraft_yaml_loads_and_has_expected_planform():
    config = load_aircraft_config(CONFIG_PATH)

    assert config.project.units == "mm"
    assert config.wing.span_mm == 1600
    assert config.wing.root_chord_mm == 250
    assert config.wing.tip_chord_mm == 200
    assert config.wing.area_m2 == pytest.approx(0.36)
    assert config.wing.mean_aerodynamic_chord_mm == pytest.approx(225.925926)
    assert config.layout.coordinate_system.datum == "wing_root_leading_edge"
    assert config.layout.coordinate_system.x_positive == "aft"
    assert config.layout.coordinate_system.y_positive == "right"
    assert config.layout.coordinate_system.z_positive == "up"
    assert config.cg.initial_envelope.status == "initial_design_assumption"
    assert config.cg.initial_envelope.x_mac_fraction_min == pytest.approx(.24)
    assert config.cg.initial_envelope.x_mac_fraction_max == pytest.approx(.28)
    assert config.cg.first_flight_recommendation.status == "preliminary_recommendation"
    assert config.cg.first_flight_recommendation.x_mac_fraction == pytest.approx(.25)
    assert config.tail.horizontal.area_m2 == pytest.approx(.063)
    assert config.tail.vertical.total_area_m2 == pytest.approx(.0531691)
    assert config.booms.lateral_offset_mm == pytest.approx(230)
    assert config.propulsion.is_defined
    assert config.propulsion.nominal_series_count == 6
    assert config.propulsion.propeller.diameter_min_mm == pytest.approx(330.2)
    assert config.propulsion.propeller.diameter_max_mm == pytest.approx(355.6)
    assert config.propulsion.esc.x_mm == pytest.approx(285.0)
    assert config.electrical.hotel_load_nominal_w == pytest.approx(16.0)
    assert config.battery.chemistry_direction == "li_ion_preliminary"
    assert config.aircraft.target_mass_g == pytest.approx(2600.0)
    assert config.battery.mass_min_g == pytest.approx(490.0)
    assert config.battery.mass_max_g == pytest.approx(520.0)
    assert (config.battery.package_length_mm, config.battery.package_width_mm, config.battery.package_height_mm) == pytest.approx((155.0, 75.0, 28.0))
    assert config.battery.nominal_x_mm == pytest.approx(-370.0)
    assert config.fuselage_integration.is_defined
    assert (config.fuselage_integration.outer_x_min_mm, config.fuselage_integration.outer_x_max_mm) == pytest.approx((-500.0, 410.0))
    assert tuple(servo.id for servo in config.fuselage_integration.forward_servos) == (
        "elevator_servo", "rudder_servo_left", "rudder_servo_right",
    )
    assert {component.id for component in config.avionics.components} >= {"flight_controller", "gnss_compass", "vtx"}
    assert config.wing.mean_aerodynamic_chord_leading_edge_x_mm == pytest.approx(12.037037)
    assert {component.id for component in config.mass_budget.components} >= {"wing_assembly", "tail_boom_left", "tail_boom_right"}


def test_yaml_values_map_directly_to_wing_generator(tmp_path: Path):
    parameters = generate(CONFIG_PATH, tmp_path / "generated")

    assert parameters.span_mm == 1600
    assert parameters.root_chord_mm == 250
    assert parameters.tip_chord_mm == 200
    assert (tmp_path / "generated" / "rib_manifest.csv").exists()
    assert not (tmp_path / "generated" / "wing_parameters.json").exists()
    assert not (ROOT / "design" / "wing_parameters.json").exists()


def test_generated_parameters_snapshot_is_complete_typed_yaml_model(tmp_path: Path):
    """The full generated snapshot is serialized only from the YAML model."""
    config = load_aircraft_config(CONFIG_PATH)
    output = tmp_path / "generated"
    generated_model = generate(CONFIG_PATH, output)

    snapshot = json.loads((output / "parameters.json").read_text(encoding="utf-8"))
    expected_model = asdict(wing_parameters_from_config(config))

    # This also confirms generate() used the same common-loader model.
    assert_complete_snapshot_matches_model(asdict(generated_model), expected_model)
    assert_complete_snapshot_matches_model(snapshot, expected_model)


def test_corrupted_snapshot_is_ignored_and_regenerated_from_yaml(tmp_path: Path):
    """A stale or edited snapshot cannot affect a subsequent generation."""
    output = tmp_path / "generated"
    expected_model = wing_parameters_from_config(load_aircraft_config(CONFIG_PATH))
    generate(CONFIG_PATH, output)

    snapshot_path = output / "parameters.json"
    corrupted_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    corrupted_snapshot.update({
        "span_mm": 9999.0,
        "root_chord_mm": 999.0,
        "tip_chord_mm": 111.0,
        "tip_washout_deg": 9.0,
    })
    snapshot_path.write_text(json.dumps(corrupted_snapshot, indent=2) + "\n", encoding="utf-8")

    regenerated_model = generate(CONFIG_PATH, output)
    restored_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))

    assert_complete_snapshot_matches_model(asdict(regenerated_model), asdict(expected_model))
    assert_complete_snapshot_matches_model(restored_snapshot, asdict(expected_model))

    # Check geometry-bearing quantities from the actual regenerated model, not
    # merely the replacement snapshot: YAML values win over the corrupt data.
    assert chord_at(0.0, regenerated_model) == expected_model.root_chord_mm
    assert chord_at(regenerated_model.panel_span_mm, regenerated_model) == expected_model.tip_chord_mm
    assert washout_at(regenerated_model.panel_span_mm, regenerated_model) == expected_model.tip_washout_deg
    assert chord_at(0.0, regenerated_model) != corrupted_snapshot["root_chord_mm"]
    assert chord_at(regenerated_model.panel_span_mm, regenerated_model) != corrupted_snapshot["tip_chord_mm"]
    assert washout_at(regenerated_model.panel_span_mm, regenerated_model) != corrupted_snapshot["tip_washout_deg"]


def test_changed_temporary_yaml_changes_generator_geometry(tmp_path: Path):
    changed_config = tmp_path / "aircraft.yaml"
    changed_config.write_text(
        CONFIG_PATH.read_text(encoding="utf-8").replace("root_chord: 250", "root_chord: 260"),
        encoding="utf-8",
    )

    baseline = wing_parameters_from_config(load_aircraft_config(CONFIG_PATH))
    altered = generate(changed_config, tmp_path / "altered")
    assert chord_at(0, baseline) == 250
    assert chord_at(0, altered) == 260


def test_config_rejects_missing_required_generator_parameter(tmp_path: Path):
    invalid_config = tmp_path / "aircraft.yaml"
    invalid_config.write_text(
        CONFIG_PATH.read_text(encoding="utf-8").replace("  rib_pitch_mm: 100\n", ""),
        encoding="utf-8",
    )
    with pytest.raises(ConfigurationError, match="rib_pitch_mm"):
        load_aircraft_config(invalid_config)


@pytest.mark.parametrize(("old", "new", "message"), [
    (
        "    mass_unit: g\n",
        "    mass_unit: g\n    invented_axis: forward\n",
        "unknown keys",
    ),
    (
        "      pair_id: tail_booms\n",
        "      pair_id: tail_booms\n      invented_mass_field: 123\n",
        "unknown keys",
    ),
    (
        "      mass_g: null\n",
        "      mass_g: -1\n",
        "must not be negative",
    ),
])
def test_config_rejects_unknown_and_invalid_master_layout_mass_fields(
    tmp_path: Path, old: str, new: str, message: str,
):
    invalid_config = tmp_path / "aircraft.yaml"
    invalid_config.write_text(CONFIG_PATH.read_text(encoding="utf-8").replace(old, new, 1), encoding="utf-8")

    with pytest.raises(ConfigurationError, match=message):
        load_aircraft_config(invalid_config)
