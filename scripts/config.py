"""Typed, validated access to the LR1600 engineering configuration.

``config/aircraft.yaml`` is the sole editable source of aircraft parameters.
Consumers must use this module rather than parsing a private copy of values.
All dimensional values exposed by these dataclasses are millimetres unless the
field name states another unit.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

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
class AircraftConfig:
    project: ProjectConfig
    wing: WingConfig
    spar: SparConfig
    materials: MaterialsConfig
    aircraft: AircraftMassConfig


def load_aircraft_config(path: Path = DEFAULT_CONFIG_PATH) -> AircraftConfig:
    """Load and strictly validate the sole editable aircraft configuration."""
    try:
        document = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), str(path))
    except OSError as error:
        raise ConfigurationError(f"Unable to read configuration {path}: {error}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML in {path}: {error}") from error

    top_level = {"project", "wing", "spar", "materials", "aircraft"}
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
    return AircraftConfig(ProjectConfig(project["name"], project["units"]), wing_config, spar_config, materials_config, aircraft_config)
