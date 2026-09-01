"""Parametric reference geometry for the LR1600 master layout.

The wing remains a reference representation of the typed configuration, not a
second wing design.  Tail geometry is displayed only when its typed status is
``initial_design_assumption``.  Boom lines are reference axes for stability
integration, never an implied tube section or wing hardpoint.
"""

from __future__ import annotations

from dataclasses import dataclass
import cadquery as cq

from scripts.config import AircraftConfig


REFERENCE_THICKNESS_MM = 0.25
CONTROL_SURFACE_Z_OFFSET_MM = 0.5


@dataclass(frozen=True)
class MasterLayout:
    """Reference geometry and optional CG information in aircraft axes."""

    wing: cq.Workplane
    horizontal_tail: cq.Workplane | None
    elevator: cq.Workplane | None
    vertical_fins: cq.Workplane | None
    rudders: cq.Workplane | None
    # Packaging solids are simple typed installation envelopes, not selected
    # hardware or a fuselage skin.  Their stable identifiers make previews and
    # tests independent of an assumed avionics inventory.
    propeller_disks: tuple[cq.Workplane, ...]
    motor_envelope: cq.Workplane | None
    esc_envelope: cq.Workplane | None
    battery_envelope: cq.Workplane | None
    battery_travel_envelope: cq.Workplane | None
    avionics_envelopes: tuple[tuple[str, cq.Workplane], ...]
    # These are display-only axes from the wing AC to the tail AC.  They are
    # explicitly not boom tubes and do not select the still-TBD wing hardpoint.
    boom_axis_segments: tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...]
    mac_leading_edge_x_mm: float
    mac_mm: float
    cg_x_range_mm: tuple[float, float] | None
    first_flight_cg_x_mm: float | None
    known_mass_items: tuple[tuple[str, float, float, float], ...]


def _cg_range(config: AircraftConfig) -> tuple[float, float] | None:
    """Convert a configured initial MAC-fraction envelope to datum X values."""
    envelope = config.cg.initial_envelope
    if envelope.status != "initial_design_assumption":
        return None
    low_fraction = envelope.x_mac_fraction_min
    high_fraction = envelope.x_mac_fraction_max
    if low_fraction is None or high_fraction is None:
        return None
    mac_le_x = config.wing.mean_aerodynamic_chord_leading_edge_x_mm
    mac = config.wing.mean_aerodynamic_chord_mm
    return mac_le_x + low_fraction * mac, mac_le_x + high_fraction * mac


def _wing_reference(config: AircraftConfig) -> cq.Workplane:
    """Make a thin visual reference solid from the existing wing planform.

    The sole non-aircraft dimension is ``REFERENCE_THICKNESS_MM``; it permits
    reliable CadQuery tessellation and has no structural or aerodynamic meaning.
    Root leading edge is the aircraft datum (X=0, Y=0, Z=0).  No sweep is
    inferred because the typed wing model supplies none.
    """
    wing = config.wing
    half_span = wing.panel_span_mm
    root = wing.root_chord_mm
    tip = wing.tip_chord_mm
    # The existing wing generator centres its trapezoid: root LE is datum and
    # tip LE is half the root-to-tip chord difference aft of datum.
    tip_leading_edge_x = (root - tip) / 2.0
    right = cq.Workplane("XY").polyline([(0, 0), (root, 0), (tip_leading_edge_x + tip, half_span), (tip_leading_edge_x, half_span)]).close().extrude(REFERENCE_THICKNESS_MM)
    left = cq.Workplane("XY").polyline([(0, 0), (tip_leading_edge_x, -half_span), (tip_leading_edge_x + tip, -half_span), (root, 0)]).close().extrude(REFERENCE_THICKNESS_MM)
    # Rotate the flat panels about the longitudinal root chord to their known
    # dihedral.  This preserves the datum and the existing span/chord values.
    right = right.rotate((0, 0, 0), (1, 0, 0), wing.dihedral_deg_per_panel)
    left = left.rotate((0, 0, 0), (1, 0, 0), -wing.dihedral_deg_per_panel)
    return right.union(left)


def _horizontal_tail_reference(config: AircraftConfig) -> tuple[cq.Workplane, cq.Workplane] | tuple[None, None]:
    """Return horizontal-tail and elevator display solids from typed tail data.

    The configured tail AC is the quarter-chord point of its mean aerodynamic
    chord; this is the same declared reference used for the typed tail arm.
    The thin solids are visual outlines only, not thickness or structure.
    """
    tail = config.tail
    if not tail.is_defined or tail.horizontal is None:
        return None, None
    horizontal = tail.horizontal
    taper = horizontal.tip_chord_mm / horizontal.root_chord_mm
    mac = (2.0 / 3.0) * horizontal.root_chord_mm * (1 + taper + taper * taper) / (1 + taper)
    mac_le_x = (horizontal.root_chord_mm - mac) / 2.0
    leading_x = tail.aerodynamic_center_x_mm - (mac_le_x + 0.25 * mac)
    half_span = horizontal.span_mm / 2.0
    tip_leading_x = leading_x + (horizontal.root_chord_mm - horizontal.tip_chord_mm) / 2.0
    trailing_x = leading_x + horizontal.root_chord_mm
    tip_trailing_x = tip_leading_x + horizontal.tip_chord_mm
    stabilizer = (
        cq.Workplane("XY")
        .polyline([(tip_leading_x, -half_span), (tip_trailing_x, -half_span), (trailing_x, 0), (tip_trailing_x, half_span), (tip_leading_x, half_span), (leading_x, 0)])
        .close()
        .extrude(REFERENCE_THICKNESS_MM)
    )
    elevator = (
        cq.Workplane("XY")
        .polyline([
            (tip_trailing_x - horizontal.tip_chord_mm * horizontal.elevator_chord_fraction, -half_span),
            (tip_trailing_x, -half_span), (trailing_x, 0), (tip_trailing_x, half_span),
            (tip_trailing_x - horizontal.tip_chord_mm * horizontal.elevator_chord_fraction, half_span),
            (trailing_x - horizontal.root_chord_mm * horizontal.elevator_chord_fraction, 0),
        ])
        .close()
        .extrude(REFERENCE_THICKNESS_MM)
        .translate((0, 0, CONTROL_SURFACE_Z_OFFSET_MM))
    )
    return stabilizer, elevator


def _vertical_tail_reference(config: AircraftConfig) -> tuple[cq.Workplane, cq.Workplane] | tuple[None, None]:
    """Return twin-fin and rudder display solids from typed tail/boom data."""
    tail, booms = config.tail, config.booms
    if not tail.is_defined or tail.vertical is None or not booms.is_defined:
        return None, None
    vertical = tail.vertical
    # Root and tip quarter-chord points are aligned with the declared tail AC;
    # this defines the reference-planform sweep without adding another X datum.
    root_le_x = tail.aerodynamic_center_x_mm - 0.25 * vertical.root_chord_mm
    tip_le_x = tail.aerodynamic_center_x_mm - 0.25 * vertical.tip_chord_mm
    root_te_x = root_le_x + vertical.root_chord_mm
    tip_te_x = tip_le_x + vertical.tip_chord_mm
    z0, z1 = booms.axis_z_mm, booms.axis_z_mm + vertical.fin_height_mm

    def fin_at(y_mm: float) -> cq.Workplane:
        return (
            cq.Workplane("XZ")
            .polyline([(root_le_x, z0), (root_te_x, z0), (tip_te_x, z1), (tip_le_x, z1)])
            .close()
            .extrude(REFERENCE_THICKNESS_MM)
            .translate((0, y_mm, 0))
        )

    def rudder_at(y_mm: float) -> cq.Workplane:
        root_hinge_x = root_te_x - vertical.root_chord_mm * vertical.rudder_chord_fraction
        tip_hinge_x = tip_te_x - vertical.tip_chord_mm * vertical.rudder_chord_fraction
        return (
            cq.Workplane("XZ")
            .polyline([(root_hinge_x, z0), (root_te_x, z0), (tip_te_x, z1), (tip_hinge_x, z1)])
            .close()
            .extrude(REFERENCE_THICKNESS_MM)
            .translate((0, y_mm, CONTROL_SURFACE_Z_OFFSET_MM))
        )

    fins = fin_at(-booms.lateral_offset_mm).union(fin_at(booms.lateral_offset_mm))
    rudders = rudder_at(-booms.lateral_offset_mm).union(rudder_at(booms.lateral_offset_mm))
    return fins, rudders


def _boom_axis_segments(config: AircraftConfig) -> tuple[tuple[tuple[float, float, float], tuple[float, float, float]], ...]:
    """Return preliminary axis segments, not physical boom geometry."""
    if not config.tail.is_defined or not config.booms.is_defined:
        return ()
    wing_ac_x = config.wing.mean_aerodynamic_chord_leading_edge_x_mm + 0.25 * config.wing.mean_aerodynamic_chord_mm
    tail_x = config.tail.aerodynamic_center_x_mm
    z = config.booms.axis_z_mm
    return tuple(
        ((wing_ac_x, y, z), (tail_x, y, z))
        for y in (-config.booms.lateral_offset_mm, config.booms.lateral_offset_mm)
    )


def _first_flight_cg_x(config: AircraftConfig) -> float | None:
    recommendation = config.cg.first_flight_recommendation
    if not recommendation.is_defined or recommendation.x_mac_fraction is None:
        return None
    return config.wing.mean_aerodynamic_chord_leading_edge_x_mm + recommendation.x_mac_fraction * config.wing.mean_aerodynamic_chord_mm


def _centered_box(*, length_mm: float, width_mm: float, height_mm: float,
                  x_mm: float, y_mm: float, z_mm: float) -> cq.Workplane:
    """Return a display-only bounding box centred at a typed aircraft point."""
    return cq.Workplane("XY").box(length_mm, width_mm, height_mm).translate((x_mm, y_mm, z_mm))


def _propeller_disk_references(config: AircraftConfig) -> tuple[cq.Workplane, ...]:
    """Return min/max typed pusher disk envelopes in the configured prop plane."""
    propulsion = config.propulsion
    if not propulsion.is_defined or propulsion.propeller is None or propulsion.propeller_plane_x_mm is None or propulsion.motor_axis_z_mm is None:
        return ()
    # YZ is normal to the aircraft +X propulsion axis, so this is an actual
    # radial disk at the typed pusher plane. Thickness is only tessellation.
    return tuple(
        cq.Workplane("YZ").circle(diameter_mm / 2.0).extrude(REFERENCE_THICKNESS_MM)
        .translate((propulsion.propeller_plane_x_mm - REFERENCE_THICKNESS_MM / 2.0, 0.0, propulsion.motor_axis_z_mm))
        for diameter_mm in (propulsion.propeller.diameter_min_mm, propulsion.propeller.diameter_max_mm)
    )


def _motor_envelope(config: AircraftConfig) -> cq.Workplane | None:
    propulsion = config.propulsion
    if not propulsion.is_defined or propulsion.motor is None or propulsion.motor_cg_x_mm is None or propulsion.motor_axis_z_mm is None:
        return None
    return _centered_box(
        length_mm=propulsion.motor.envelope_length_mm,
        width_mm=propulsion.motor.envelope_diameter_mm,
        height_mm=propulsion.motor.envelope_diameter_mm,
        x_mm=propulsion.motor_cg_x_mm,
        y_mm=0.0,
        z_mm=propulsion.motor_axis_z_mm,
    )


def _esc_envelope(config: AircraftConfig) -> cq.Workplane | None:
    """Return only the typed ESC installation bounding box."""
    propulsion = config.propulsion
    if not propulsion.is_defined or propulsion.esc is None:
        return None
    esc = propulsion.esc
    return _centered_box(
        length_mm=esc.length_mm, width_mm=esc.width_mm, height_mm=esc.height_mm,
        x_mm=esc.x_mm, y_mm=esc.y_mm, z_mm=esc.z_mm,
    )


def _battery_envelopes(config: AircraftConfig) -> tuple[cq.Workplane | None, cq.Workplane | None]:
    """Return the typed pack volume and its full typed X travel swept volume."""
    battery = config.battery
    if not battery.is_defined:
        return None, None
    assert battery.package_length_mm is not None
    assert battery.package_width_mm is not None
    assert battery.package_height_mm is not None
    assert battery.x_adjustment_min_mm is not None
    assert battery.x_adjustment_max_mm is not None
    assert battery.y_mm is not None and battery.z_mm is not None
    assert battery.nominal_x_mm is not None
    centre_x = battery.nominal_x_mm
    pack = _centered_box(
        length_mm=battery.package_length_mm, width_mm=battery.package_width_mm,
        height_mm=battery.package_height_mm, x_mm=centre_x, y_mm=battery.y_mm, z_mm=battery.z_mm,
    )
    travel = _centered_box(
        length_mm=battery.package_length_mm + battery.x_adjustment_max_mm - battery.x_adjustment_min_mm,
        width_mm=battery.package_width_mm, height_mm=battery.package_height_mm,
        x_mm=centre_x, y_mm=battery.y_mm, z_mm=battery.z_mm,
    )
    return pack, travel


def _avionics_envelopes(config: AircraftConfig) -> tuple[tuple[str, cq.Workplane], ...]:
    """Build only the explicitly typed avionics/package bounding boxes."""
    if not config.avionics.is_defined:
        return ()
    return tuple(
        (component.id, _centered_box(
            length_mm=component.length_mm, width_mm=component.width_mm, height_mm=component.height_mm,
            x_mm=component.x_mm, y_mm=component.y_mm, z_mm=component.z_mm,
        ))
        for component in config.avionics.components
    )


def master_layout_from_config(config: AircraftConfig) -> MasterLayout:
    """Return a master layout built exclusively from typed source parameters."""
    known_mass_items = tuple(
        (component.id, component.x_mm, component.y_mm, component.z_mm)
        for component in config.mass_budget.components
        if component.is_resolved
    )
    horizontal_tail, elevator = _horizontal_tail_reference(config)
    vertical_fins, rudders = _vertical_tail_reference(config)
    battery_envelope, battery_travel_envelope = _battery_envelopes(config)
    return MasterLayout(
        wing=_wing_reference(config),
        horizontal_tail=horizontal_tail,
        elevator=elevator,
        vertical_fins=vertical_fins,
        rudders=rudders,
        propeller_disks=_propeller_disk_references(config),
        motor_envelope=_motor_envelope(config),
        esc_envelope=_esc_envelope(config),
        battery_envelope=battery_envelope,
        battery_travel_envelope=battery_travel_envelope,
        avionics_envelopes=_avionics_envelopes(config),
        boom_axis_segments=_boom_axis_segments(config),
        mac_leading_edge_x_mm=config.wing.mean_aerodynamic_chord_leading_edge_x_mm,
        mac_mm=config.wing.mean_aerodynamic_chord_mm,
        cg_x_range_mm=_cg_range(config),
        first_flight_cg_x_mm=_first_flight_cg_x(config),
        # Config validation guarantees non-null numeric coordinates for every
        # `known` item. These are display markers, not inferred component CAD.
        known_mass_items=known_mass_items,
    )
