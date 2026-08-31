"""Parametric, reference-only geometry for the LR1600 master layout.

The model deliberately contains no fuselage, propulsion, battery, boom, tail,
or avionics geometry.  Those items need engineering inputs that are not yet in
the source configuration.  The wing planform is a reference representation of
the typed configuration, not a second wing design.
"""

from __future__ import annotations

from dataclasses import dataclass
import cadquery as cq

from scripts.config import AircraftConfig


REFERENCE_THICKNESS_MM = 0.25


@dataclass(frozen=True)
class MasterLayout:
    """Known reference geometry and optional CG information in aircraft axes."""

    wing: cq.Workplane
    mac_leading_edge_x_mm: float
    mac_mm: float
    cg_x_range_mm: tuple[float, float] | None
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


def master_layout_from_config(config: AircraftConfig) -> MasterLayout:
    """Return a master layout built exclusively from typed source parameters."""
    known_mass_items = tuple(
        (component.id, component.x_mm, component.y_mm, component.z_mm)
        for component in config.mass_budget.components
        if component.is_resolved
    )
    return MasterLayout(
        wing=_wing_reference(config),
        mac_leading_edge_x_mm=config.wing.mean_aerodynamic_chord_leading_edge_x_mm,
        mac_mm=config.wing.mean_aerodynamic_chord_mm,
        cg_x_range_mm=_cg_range(config),
        # Config validation guarantees non-null numeric coordinates for every
        # `known` item. These are display markers, not inferred component CAD.
        known_mass_items=known_mass_items,
    )
