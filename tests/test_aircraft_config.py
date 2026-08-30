from pathlib import Path

import pytest

from scripts.config import ConfigurationError, load_aircraft_config
from scripts.generate_wing import chord_at, generate, wing_parameters_from_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG_PATH = ROOT / "config" / "aircraft.yaml"


def test_repository_aircraft_yaml_loads_and_has_expected_planform():
    config = load_aircraft_config(CONFIG_PATH)

    assert config.project.units == "mm"
    assert config.wing.span_mm == 1600
    assert config.wing.root_chord_mm == 250
    assert config.wing.tip_chord_mm == 200
    assert config.wing.area_m2 == pytest.approx(0.36)
    assert config.wing.mean_aerodynamic_chord_mm == pytest.approx(225.925926)


def test_yaml_values_map_directly_to_wing_generator(tmp_path: Path):
    parameters = generate(CONFIG_PATH, tmp_path / "generated")

    assert parameters.span_mm == 1600
    assert parameters.root_chord_mm == 250
    assert parameters.tip_chord_mm == 200
    assert (tmp_path / "generated" / "rib_manifest.csv").exists()
    assert not (tmp_path / "generated" / "wing_parameters.json").exists()
    assert not (ROOT / "design" / "wing_parameters.json").exists()


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
