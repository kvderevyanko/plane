from dataclasses import replace
from pathlib import Path

import pytest

from cad.master_layout.model import master_layout_from_config
from scripts.config import MassBudgetConfig, load_aircraft_config
from scripts.hardware import load_hardware_config


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "aircraft.yaml"
HARDWARE = ROOT / "config" / "hardware.yaml"


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


def test_master_layout_packaging_envelopes_track_only_typed_configuration():
    config = load_aircraft_config(CONFIG)
    layout = master_layout_from_config(config)

    assert len(layout.propeller_disks) == 2
    min_disk, max_disk = (disk.val().BoundingBox() for disk in layout.propeller_disks)
    assert min_disk.xlen == pytest.approx(.25)
    assert max_disk.xlen == pytest.approx(.25)
    assert (min_disk.ylen, min_disk.zlen) == pytest.approx((config.propulsion.propeller.diameter_min_mm,) * 2)
    assert (max_disk.ylen, max_disk.zlen) == pytest.approx((config.propulsion.propeller.diameter_max_mm,) * 2)
    assert (min_disk.xmin + min_disk.xmax) / 2.0 == pytest.approx(config.propulsion.propeller_plane_x_mm)

    motor = layout.motor_envelope.val().BoundingBox()
    assert motor.xlen == pytest.approx(config.propulsion.motor.envelope_length_mm)
    assert motor.ylen == pytest.approx(config.propulsion.motor.envelope_diameter_mm)
    assert (motor.xmin + motor.xmax) / 2.0 == pytest.approx(config.propulsion.motor_cg_x_mm)

    esc = layout.esc_envelope.val().BoundingBox()
    assert (esc.xlen, esc.ylen, esc.zlen) == pytest.approx((
        config.propulsion.esc.length_mm, config.propulsion.esc.width_mm, config.propulsion.esc.height_mm,
    ))
    assert ((esc.xmin + esc.xmax) / 2.0, (esc.ymin + esc.ymax) / 2.0, (esc.zmin + esc.zmax) / 2.0) == pytest.approx((
        config.propulsion.esc.x_mm, config.propulsion.esc.y_mm, config.propulsion.esc.z_mm,
    ))

    battery = layout.battery_envelope.val().BoundingBox()
    battery_travel = layout.battery_travel_envelope.val().BoundingBox()
    assert battery.xlen == pytest.approx(config.battery.package_length_mm)
    assert battery.ylen == pytest.approx(config.battery.package_width_mm)
    assert battery.zlen == pytest.approx(config.battery.package_height_mm)
    assert battery_travel.xlen == pytest.approx(
        config.battery.package_length_mm + config.battery.x_adjustment_max_mm - config.battery.x_adjustment_min_mm,
    )

    assert tuple(component_id for component_id, _ in layout.avionics_envelopes) == tuple(
        component.id for component in config.avionics.components
    )
    for component, (_, envelope) in zip(config.avionics.components, layout.avionics_envelopes, strict=True):
        box = envelope.val().BoundingBox()
        assert (box.xmin + box.xmax) / 2.0 == pytest.approx(component.x_mm)
        assert (box.ymin + box.ymax) / 2.0 == pytest.approx(component.y_mm)
        assert (box.zmin + box.zmax) / 2.0 == pytest.approx(component.z_mm)
        assert (box.xlen, box.ylen, box.zlen) == pytest.approx(
            (component.length_mm, component.width_mm, component.height_mm),
        )


def test_master_layout_avionics_position_changes_only_with_typed_source(tmp_path: Path):
    changed = tmp_path / "aircraft.yaml"
    changed.write_text(CONFIG.read_text(encoding="utf-8").replace("      x_mm: 170.0", "      x_mm: 175.0", 1), encoding="utf-8")

    layout = master_layout_from_config(load_aircraft_config(changed))
    flight_controller = dict(layout.avionics_envelopes)["flight_controller"].val().BoundingBox()

    assert (flight_controller.xmin + flight_controller.xmax) / 2.0 == pytest.approx(175.0)


def test_full_battery_travel_envelope_has_positive_x_clearance_to_typed_avionics():
    layout = master_layout_from_config(load_aircraft_config(CONFIG))
    battery = layout.battery_travel_envelope.val().BoundingBox()
    for component_id, envelope in layout.avionics_envelopes:
        box = envelope.val().BoundingBox()
        overlaps = (
            max(battery.xmin, box.xmin) < min(battery.xmax, box.xmax)
            and max(battery.ymin, box.ymin) < min(battery.ymax, box.ymax)
            and max(battery.zmin, box.zmin) < min(battery.zmax, box.zmax)
        )
        assert not overlaps, component_id


def test_selected_nonbattery_hardware_layout_comes_only_from_manifest():
    hardware = load_hardware_config(HARDWARE)
    layout = master_layout_from_config(load_aircraft_config(CONFIG), hardware)

    displayed = dict(layout.selected_hardware_envelopes)
    expected = {
        component.id for component in hardware.selected_components
        if component.id not in {"flight_battery", "propulsion_propeller"} and component.has_installation_envelope
    }
    assert set(displayed) == expected
    assert "flight_battery" not in displayed
    for component_id, envelope in displayed.items():
        component = hardware.component(component_id)
        box = envelope.val().BoundingBox()
        assert (box.xlen, box.ylen, box.zlen) == pytest.approx((
            component.length_mm, component.width_mm, component.height_mm,
        ))
        assert ((box.xmin + box.xmax) / 2, (box.ymin + box.ymax) / 2, (box.zmin + box.zmax) / 2) == pytest.approx((
            component.x_mm, component.y_mm, component.z_mm,
        ))

    prop = hardware.component("propulsion_propeller")
    prop_box = layout.selected_propeller_disk.val().BoundingBox()
    assert (prop_box.ylen, prop_box.zlen) == pytest.approx((prop.length_mm, prop.height_mm))
    assert (prop_box.xmin + prop_box.xmax) / 2 == pytest.approx(prop.x_mm)
    assert layout.high_current_route == hardware.high_current_route
    assert tuple(item_id for item_id, _ in layout.antenna_keepout_envelopes) == tuple(item.id for item in hardware.antenna_keepouts)


def test_hardware_manifest_does_not_false_claim_battery_removal_closure():
    layout = master_layout_from_config(load_aircraft_config(CONFIG), load_hardware_config(HARDWARE))

    # The manifest includes a candidate pack and hatch dimensions, but CG/mass
    # moments have not closed.  The CAD reference must not imply a clearance-
    # passed removal path or replace the current typed aircraft battery study.
    assert layout.battery_removal_validated is False
    assert "flight_battery" not in dict(layout.selected_hardware_envelopes)
    assert layout.battery_envelope is not None
    assert layout.battery_travel_envelope is not None


def test_ground_operations_reference_tracks_typed_rough_field_screen():
    config = load_aircraft_config(CONFIG)
    layout = master_layout_from_config(config)
    ground = config.ground_operations

    assert len(layout.main_wheels) == 2
    assert layout.nose_wheel is not None
    assert layout.ground_reference is not None
    assert tuple(name for name, _ in layout.propeller_tip_clearance_cases_mm) == (
        "static", "compressed", "tail_low", "full_rough",
    )
    assert tuple(value for _, value in layout.propeller_tip_clearance_cases_mm) == pytest.approx((
        ground.static_propeller_axis_height_mm - ground.propeller_diameter_mm / 2.0,
        ground.compressed_tip_clearance_mm, ground.rotation_tip_clearance_mm,
        ground.rough_tip_clearance_mm,
    ))
    assert layout.propeller_tip_clearance_dynamic_mm == pytest.approx(ground.rough_tip_clearance_mm)
    assert layout.propeller_tip_clearance_dynamic_mm >= ground.dynamic_tip_clearance_goal_mm
    assert [(point[0], point[1]) for point in layout.landing_gear_hardpoints] == pytest.approx([
        (ground.main_wheel_x_mm, -ground.main_track_mm / 2.0),
        (ground.main_wheel_x_mm, ground.main_track_mm / 2.0),
    ])


def test_forward_tail_linkage_routes_follow_typed_reference_stations():
    config = load_aircraft_config(CONFIG)
    layout = master_layout_from_config(config)

    assert len(layout.linkage_route_segments) == 3
    assert all(start[0] == pytest.approx(config.linkage_reference.servo_x_mm)
               for start, _ in layout.linkage_route_segments)
    assert all(end[0] == pytest.approx(config.tail.aerodynamic_center_x_mm)
               for _, end in layout.linkage_route_segments)
    assert [end[1] for _, end in layout.linkage_route_segments] == pytest.approx([
        0.0, -config.booms.lateral_offset_mm, config.booms.lateral_offset_mm,
    ])
