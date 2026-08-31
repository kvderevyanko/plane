from dataclasses import replace
from pathlib import Path

import pytest

from cad.master_layout.model import master_layout_from_config
from scripts.config import MassBudgetConfig, load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "aircraft.yaml"


def test_master_layout_uses_typed_mac_and_does_not_invent_current_tbd_geometry():
    config = load_aircraft_config(CONFIG)
    layout = master_layout_from_config(config)

    assert layout.mac_mm == config.wing.mean_aerodynamic_chord_mm
    assert layout.mac_leading_edge_x_mm == config.wing.mean_aerodynamic_chord_leading_edge_x_mm
    assert layout.cg_x_range_mm is None
    assert layout.known_mass_items == ()


def test_master_layout_exposes_only_explicitly_known_mass_item_points():
    config = load_aircraft_config(CONFIG)
    known_wing = replace(
        config.mass_budget.components[0], status="known", mass_g=500.0,
        x_mm=100.0, y_mm=0.0, z_mm=10.0,
    )
    configured = replace(config, mass_budget=MassBudgetConfig((known_wing, *config.mass_budget.components[1:])))

    layout = master_layout_from_config(configured)

    assert layout.known_mass_items == (("wing_assembly", 100.0, 0.0, 10.0),)


def test_master_layout_mac_tracks_changed_source_config(tmp_path: Path):
    changed = tmp_path / "aircraft.yaml"
    changed.write_text(CONFIG.read_text(encoding="utf-8").replace("root_chord: 250", "root_chord: 260"), encoding="utf-8")

    changed_config = load_aircraft_config(changed)
    layout = master_layout_from_config(changed_config)

    assert layout.mac_mm == pytest.approx(changed_config.wing.mean_aerodynamic_chord_mm)
    assert layout.mac_mm != load_aircraft_config(CONFIG).wing.mean_aerodynamic_chord_mm
