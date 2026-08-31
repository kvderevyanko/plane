from dataclasses import replace
from pathlib import Path

import pytest

from cad.master_layout.model import master_layout_from_config
from scripts.config import MassBudgetConfig, load_aircraft_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "aircraft.yaml"


def test_master_layout_uses_typed_mac_and_selected_preliminary_tail_geometry():
    config = load_aircraft_config(CONFIG)
    layout = master_layout_from_config(config)

    assert layout.mac_mm == config.wing.mean_aerodynamic_chord_mm
    assert layout.mac_leading_edge_x_mm == config.wing.mean_aerodynamic_chord_leading_edge_x_mm
    assert layout.cg_x_range_mm == pytest.approx((
        config.wing.mean_aerodynamic_chord_leading_edge_x_mm + .24 * config.wing.mean_aerodynamic_chord_mm,
        config.wing.mean_aerodynamic_chord_leading_edge_x_mm + .28 * config.wing.mean_aerodynamic_chord_mm,
    ))
    assert layout.first_flight_cg_x_mm == pytest.approx(
        config.wing.mean_aerodynamic_chord_leading_edge_x_mm + .25 * config.wing.mean_aerodynamic_chord_mm,
    )
    assert layout.horizontal_tail is not None
    assert layout.elevator is not None
    assert layout.vertical_fins is not None
    assert layout.rudders is not None
    assert len(layout.boom_axis_segments) == 2
    assert layout.known_mass_items == ()


def test_master_layout_tail_geometry_tracks_typed_config_and_twin_boom_symmetry():
    config = load_aircraft_config(CONFIG)
    layout = master_layout_from_config(config)

    tail_box = layout.horizontal_tail.val().BoundingBox()
    elevator_box = layout.elevator.val().BoundingBox()
    fin_box = layout.vertical_fins.val().BoundingBox()
    assert tail_box.xlen == pytest.approx(config.tail.horizontal.root_chord_mm)
    assert tail_box.ylen == pytest.approx(config.tail.horizontal.span_mm)
    assert elevator_box.xlen == pytest.approx(
        config.tail.horizontal.root_chord_mm * config.tail.horizontal.elevator_chord_fraction,
    )
    assert fin_box.zlen == pytest.approx(config.tail.vertical.fin_height_mm)
    assert [segment[0][1] for segment in layout.boom_axis_segments] == pytest.approx([
        -config.booms.lateral_offset_mm,
        config.booms.lateral_offset_mm,
    ])
    assert all(segment[1][0] == pytest.approx(config.tail.aerodynamic_center_x_mm) for segment in layout.boom_axis_segments)


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
    # The tail AC and boom tail reference are derived from typed wing AC plus
    # the invariant selected tail arm, so no second YAML X coordinate changes.
    changed.write_text(CONFIG.read_text(encoding="utf-8").replace("root_chord: 250", "root_chord: 260"), encoding="utf-8")

    changed_config = load_aircraft_config(changed)
    layout = master_layout_from_config(changed_config)

    assert layout.mac_mm == pytest.approx(changed_config.wing.mean_aerodynamic_chord_mm)
    assert layout.mac_mm != load_aircraft_config(CONFIG).wing.mean_aerodynamic_chord_mm
