"""Typed, validated access to the LR1600 engineering configuration.

``config/aircraft.yaml`` is the sole editable source of aircraft parameters.
Consumers must use this module rather than parsing a private copy of values.
All dimensional values exposed by these dataclasses are millimetres unless the
field name states another unit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_CONFIG_PATH = ROOT / "config" / "aircraft.yaml"


class ConfigurationError(ValueError):
    """The aircraft configuration is missing, malformed, or unsafe to use."""


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{name} must be a mapping")
    return value


def _section(document: dict[str, Any], name: str, keys: set[str]) -> dict[str, Any]:
    if name not in document:
        raise ConfigurationError(f"Missing required section: {name}")
    section = _mapping(document[name], name)
    missing, unknown = keys - set(section), set(section) - keys
    if missing:
        raise ConfigurationError(f"{name} is missing required keys: {sorted(missing)}")
    if unknown:
        raise ConfigurationError(f"{name} has unknown keys: {sorted(unknown)}")
    return section


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{name} must be a number")
    return float(value)


def _positive(value: Any, name: str) -> float:
    value = _number(value, name)
    if value <= 0:
        raise ConfigurationError(f"{name} must be positive")
    return value


def _bounded(value: Any, name: str, low: float, high: float) -> float:
    value = _number(value, name)
    if not low <= value <= high:
        raise ConfigurationError(f"{name} must be between {low} and {high}")
    return value


def _nullable_number(value: Any, name: str) -> float | None:
    if value is None:
        return None
    return _number(value, name)


def _non_empty_string(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ConfigurationError(f"{name} must be a non-empty string")
    return value


@dataclass(frozen=True)
class ProjectConfig:
    name: str
    units: str


@dataclass(frozen=True)
class WingConfig:
    span_mm: float
    root_chord_mm: float
    tip_chord_mm: float
    airfoil: str
    washout_deg: float
    dihedral_deg_per_panel: float
    twist_axis_fraction: float
    rib_pitch_mm: float
    aileron_span_mm: float
    aileron_chord_mm: float
    aileron_inboard_offset_mm: float

    @property
    def panel_span_mm(self) -> float:
        return self.span_mm / 2.0

    @property
    def area_m2(self) -> float:
        return (self.span_mm / 1000.0) * (self.root_chord_mm + self.tip_chord_mm) / 2000.0

    @property
    def taper_ratio(self) -> float:
        return self.tip_chord_mm / self.root_chord_mm

    @property
    def mean_aerodynamic_chord_mm(self) -> float:
        taper = self.taper_ratio
        return (2.0 / 3.0) * self.root_chord_mm * (1 + taper + taper * taper) / (1 + taper)

    @property
    def mean_aerodynamic_chord_leading_edge_x_mm(self) -> float:
        """MAC leading-edge X in the root-LE datum of the current planform.

        The generated wing planform centres each tapered panel on the root
        chord.  At the MAC station its local chord equals the existing MAC, so
        the leading-edge location derives from that one canonical value.
        """
        return (self.root_chord_mm - self.mean_aerodynamic_chord_mm) / 2.0


@dataclass(frozen=True)
class SparConfig:
    type: str
    outer_diameter_mm: float
    inner_diameter_mm: float
    chord_position: float
    hole_clearance_mm: float


@dataclass(frozen=True)
class MaterialsConfig:
    skin_foam_mm: float
    rib_foam_mm: float
    root_rib_plywood_mm: float
    plywood_structural_mm: tuple[float, ...]


@dataclass(frozen=True)
class AircraftMassConfig:
    target_mass_g: float
    design_load_factor_g: float
    gravity_m_s2: float

    @property
    def target_mass_kg(self) -> float:
        return self.target_mass_g / 1000.0


@dataclass(frozen=True)
class CoordinateSystemConfig:
    datum: Literal["wing_root_leading_edge"]
    x_positive: Literal["aft"]
    y_positive: Literal["right"]
    z_positive: Literal["up"]
    length_unit: Literal["mm"]
    mass_unit: Literal["g"]


@dataclass(frozen=True)
class LayoutConfig:
    coordinate_system: CoordinateSystemConfig


@dataclass(frozen=True)
class CGEnvelopeConfig:
    status: Literal["tbd", "initial_design_assumption"]
    x_mac_fraction_min: float | None
    x_mac_fraction_max: float | None
    basis: str | None

    @property
    def is_defined(self) -> bool:
        return self.status == "initial_design_assumption"


@dataclass(frozen=True)
class CGConfig:
    initial_envelope: CGEnvelopeConfig


@dataclass(frozen=True)
class MassComponentConfig:
    """One point-mass ledger entry in the common aircraft coordinate system."""

    id: str
    name: str
    status: Literal["known", "tbd"]
    mass_g: float | None
    x_mm: float | None
    y_mm: float | None
    z_mm: float | None
    side: Literal["left", "right", "center"]
    pair_id: str | None

    @property
    def is_resolved(self) -> bool:
        return self.status == "known"


@dataclass(frozen=True)
class MassBudgetConfig:
    components: tuple[MassComponentConfig, ...]


@dataclass(frozen=True)
class AircraftConfig:
    project: ProjectConfig
    wing: WingConfig
    spar: SparConfig
    materials: MaterialsConfig
    aircraft: AircraftMassConfig
    layout: LayoutConfig
    cg: CGConfig
    mass_budget: MassBudgetConfig


def load_aircraft_config(path: Path = DEFAULT_CONFIG_PATH) -> AircraftConfig:
    """Load and strictly validate the sole editable aircraft configuration."""
    try:
        document = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), str(path))
    except OSError as error:
        raise ConfigurationError(f"Unable to read configuration {path}: {error}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML in {path}: {error}") from error

    top_level = {"project", "wing", "spar", "materials", "aircraft", "layout", "cg", "mass_budget"}
    missing, unknown = top_level - set(document), set(document) - top_level
    if missing:
        raise ConfigurationError(f"Configuration is missing required sections: {sorted(missing)}")
    if unknown:
        raise ConfigurationError(f"Configuration has unknown sections: {sorted(unknown)}")

    project = _section(document, "project", {"name", "units"})
    if not isinstance(project["name"], str) or not project["name"].strip():
        raise ConfigurationError("project.name must be a non-empty string")
    if project["units"] != "mm":
        raise ConfigurationError("project.units must be mm")

    wing = _section(document, "wing", {
        "span", "root_chord", "tip_chord", "airfoil", "washout_deg", "dihedral_deg",
        "twist_axis_fraction", "rib_pitch_mm", "aileron_span_mm", "aileron_chord_mm",
        "aileron_inboard_offset_mm",
    })
    if wing["airfoil"] != "clark_y":
        raise ConfigurationError("wing.airfoil must name a supported airfoil (currently: clark_y)")
    wing_config = WingConfig(
        span_mm=_positive(wing["span"], "wing.span"),
        root_chord_mm=_positive(wing["root_chord"], "wing.root_chord"),
        tip_chord_mm=_positive(wing["tip_chord"], "wing.tip_chord"),
        airfoil=wing["airfoil"],
        washout_deg=_bounded(wing["washout_deg"], "wing.washout_deg", -10.0, 10.0),
        dihedral_deg_per_panel=_bounded(wing["dihedral_deg"], "wing.dihedral_deg", -10.0, 15.0),
        twist_axis_fraction=_bounded(wing["twist_axis_fraction"], "wing.twist_axis_fraction", 0.0, 1.0),
        rib_pitch_mm=_positive(wing["rib_pitch_mm"], "wing.rib_pitch_mm"),
        aileron_span_mm=_positive(wing["aileron_span_mm"], "wing.aileron_span_mm"),
        aileron_chord_mm=_positive(wing["aileron_chord_mm"], "wing.aileron_chord_mm"),
        aileron_inboard_offset_mm=_positive(wing["aileron_inboard_offset_mm"], "wing.aileron_inboard_offset_mm"),
    )
    if not wing_config.aileron_inboard_offset_mm + wing_config.aileron_span_mm <= wing_config.panel_span_mm:
        raise ConfigurationError("Aileron must lie within one wing panel")
    if wing_config.aileron_chord_mm >= wing_config.tip_chord_mm:
        raise ConfigurationError("wing.aileron_chord_mm must be less than the tip chord")
    bays = wing_config.panel_span_mm / wing_config.rib_pitch_mm
    if abs(bays - round(bays)) > 1e-9:
        raise ConfigurationError("wing.rib_pitch_mm must divide the panel span exactly")

    spar = _section(document, "spar", {"type", "outer_diameter", "inner_diameter", "chord_position", "hole_clearance_mm"})
    if spar["type"] != "carbon_tube":
        raise ConfigurationError("spar.type must be carbon_tube")
    spar_config = SparConfig(
        type=spar["type"],
        outer_diameter_mm=_positive(spar["outer_diameter"], "spar.outer_diameter"),
        inner_diameter_mm=_positive(spar["inner_diameter"], "spar.inner_diameter"),
        chord_position=_bounded(spar["chord_position"], "spar.chord_position", 0.01, 0.99),
        hole_clearance_mm=_bounded(spar["hole_clearance_mm"], "spar.hole_clearance_mm", 0.0, 2.0),
    )
    if spar_config.outer_diameter_mm <= spar_config.inner_diameter_mm:
        raise ConfigurationError("spar.outer_diameter must exceed spar.inner_diameter")

    materials = _section(document, "materials", {"skin_foam_mm", "rib_foam_mm", "root_rib_plywood_mm", "plywood_structural_mm"})
    plywood = materials["plywood_structural_mm"]
    if not isinstance(plywood, list) or not plywood:
        raise ConfigurationError("materials.plywood_structural_mm must be a non-empty list")
    plywood_mm = tuple(_positive(value, "materials.plywood_structural_mm item") for value in plywood)
    root_rib_plywood_mm = _positive(materials["root_rib_plywood_mm"], "materials.root_rib_plywood_mm")
    if root_rib_plywood_mm not in plywood_mm:
        raise ConfigurationError("materials.root_rib_plywood_mm must be listed in plywood_structural_mm")
    materials_config = MaterialsConfig(
        skin_foam_mm=_positive(materials["skin_foam_mm"], "materials.skin_foam_mm"),
        rib_foam_mm=_positive(materials["rib_foam_mm"], "materials.rib_foam_mm"),
        root_rib_plywood_mm=root_rib_plywood_mm,
        plywood_structural_mm=plywood_mm,
    )

    aircraft = _section(document, "aircraft", {"target_mass_g", "design_load_factor_g", "gravity_m_s2"})
    aircraft_config = AircraftMassConfig(
        target_mass_g=_positive(aircraft["target_mass_g"], "aircraft.target_mass_g"),
        design_load_factor_g=_bounded(aircraft["design_load_factor_g"], "aircraft.design_load_factor_g", 0.1, 20.0),
        gravity_m_s2=_bounded(aircraft["gravity_m_s2"], "aircraft.gravity_m_s2", 9.0, 10.0),
    )
    layout = _section(document, "layout", {"coordinate_system"})
    coordinate_system = _section(layout, "coordinate_system", {
        "datum", "x_positive", "y_positive", "z_positive", "length_unit", "mass_unit",
    })
    expected_coordinates = {
        "datum": "wing_root_leading_edge", "x_positive": "aft", "y_positive": "right",
        "z_positive": "up", "length_unit": "mm", "mass_unit": "g",
    }
    for key, expected in expected_coordinates.items():
        if coordinate_system[key] != expected:
            raise ConfigurationError(f"layout.coordinate_system.{key} must be {expected!r}")
    layout_config = LayoutConfig(CoordinateSystemConfig(**coordinate_system))

    cg = _section(document, "cg", {"initial_envelope"})
    envelope = _section(cg, "initial_envelope", {
        "status", "x_mac_fraction_min", "x_mac_fraction_max", "basis",
    })
    if envelope["status"] not in {"tbd", "initial_design_assumption"}:
        raise ConfigurationError("cg.initial_envelope.status must be 'tbd' or 'initial_design_assumption'")
    fraction_min = _nullable_number(envelope["x_mac_fraction_min"], "cg.initial_envelope.x_mac_fraction_min")
    fraction_max = _nullable_number(envelope["x_mac_fraction_max"], "cg.initial_envelope.x_mac_fraction_max")
    basis = envelope["basis"]
    if basis is not None:
        basis = _non_empty_string(basis, "cg.initial_envelope.basis")
    if envelope["status"] == "tbd":
        if any(value is not None for value in (fraction_min, fraction_max, basis)):
            raise ConfigurationError("tbd cg.initial_envelope must use null fractions and basis")
    else:
        if fraction_min is None or fraction_max is None or basis is None:
            raise ConfigurationError("defined cg.initial_envelope needs both fractions and a basis")
        if not 0.0 <= fraction_min < fraction_max <= 1.0:
            raise ConfigurationError("cg.initial_envelope fractions must satisfy 0 <= min < max <= 1")
    cg_config = CGConfig(CGEnvelopeConfig(envelope["status"], fraction_min, fraction_max, basis))

    mass_budget = _section(document, "mass_budget", {"components"})
    components_raw = mass_budget["components"]
    if not isinstance(components_raw, list):
        raise ConfigurationError("mass_budget.components must be a list")
    component_keys = {"id", "name", "status", "mass_g", "x_mm", "y_mm", "z_mm", "side", "pair_id"}
    components: list[MassComponentConfig] = []
    ids: set[str] = set()
    pair_sides: dict[str, set[str]] = {}
    for index, raw in enumerate(components_raw):
        item = _mapping(raw, f"mass_budget.components[{index}]")
        missing, unknown = component_keys - set(item), set(item) - component_keys
        if missing:
            raise ConfigurationError(f"mass_budget.components[{index}] is missing required keys: {sorted(missing)}")
        if unknown:
            raise ConfigurationError(f"mass_budget.components[{index}] has unknown keys: {sorted(unknown)}")
        component_id = _non_empty_string(item["id"], f"mass_budget.components[{index}].id")
        if component_id in ids:
            raise ConfigurationError(f"Duplicate mass component id: {component_id}")
        ids.add(component_id)
        name = _non_empty_string(item["name"], f"mass_budget.components[{index}].name")
        status = item["status"]
        if status not in {"known", "tbd"}:
            raise ConfigurationError(f"mass_budget.components[{index}].status must be 'known' or 'tbd'")
        mass_g = _nullable_number(item["mass_g"], f"mass_budget.components[{index}].mass_g")
        if mass_g is not None and mass_g < 0:
            raise ConfigurationError(f"mass_budget.components[{index}].mass_g must not be negative")
        coordinates = tuple(_nullable_number(item[key], f"mass_budget.components[{index}].{key}") for key in ("x_mm", "y_mm", "z_mm"))
        if status == "known" and (mass_g is None or any(value is None for value in coordinates)):
            raise ConfigurationError(f"known mass_budget.components[{index}] needs mass_g and all coordinates")
        side = item["side"]
        if side not in {"left", "right", "center"}:
            raise ConfigurationError(f"mass_budget.components[{index}].side must be left, right, or center")
        pair_id = item["pair_id"]
        if pair_id is not None:
            pair_id = _non_empty_string(pair_id, f"mass_budget.components[{index}].pair_id")
            if side == "center":
                raise ConfigurationError(f"mass_budget.components[{index}].pair_id requires left or right side")
            sides = pair_sides.setdefault(pair_id, set())
            if side in sides:
                raise ConfigurationError(f"mass component pair {pair_id!r} has more than one {side} item")
            sides.add(side)
        elif side != "center":
            raise ConfigurationError(f"mass_budget.components[{index}] left/right side needs pair_id")
        components.append(MassComponentConfig(component_id, name, status, mass_g, *coordinates, side, pair_id))
    for pair_id, sides in pair_sides.items():
        if sides != {"left", "right"}:
            raise ConfigurationError(f"mass component pair {pair_id!r} must include one left and one right item")
    mass_budget_config = MassBudgetConfig(tuple(components))

    return AircraftConfig(
        ProjectConfig(project["name"], project["units"]), wing_config, spar_config,
        materials_config, aircraft_config, layout_config, cg_config, mass_budget_config,
    )
