"""Typed commercial-hardware manifest for the LR1600 preliminary baseline.

``config/aircraft.yaml`` remains the source for aircraft geometry and design
requirements.  This module deliberately keeps implementation-specific SKU,
datasheet and installation values in ``config/hardware.yaml`` so their mass
and dimensions have exactly one editable source.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

import yaml

from scripts.config import ConfigurationError, MassComponentConfig


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_HARDWARE_PATH = ROOT / "config" / "hardware.yaml"


def _mapping(value: Any, name: str) -> dict[str, Any]:
    if not isinstance(value, dict):
        raise ConfigurationError(f"{name} must be a mapping")
    return value


def _number(value: Any, name: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ConfigurationError(f"{name} must be a number")
    return float(value)


def _positive(value: Any, name: str) -> float:
    value = _number(value, name)
    if value <= 0:
        raise ConfigurationError(f"{name} must be positive")
    return value


@dataclass(frozen=True)
class HardwareComponent:
    id: str
    category: str
    status: Literal["selected_preliminary", "fallback", "design_estimate", "tbd"]
    manufacturer: str | None
    model: str | None
    source_url: str | None
    source_retrieved_date: str | None
    mass_g: float | None
    mass_status: Literal["datasheet", "design_estimate", "tbd"]
    length_mm: float | None
    width_mm: float | None
    height_mm: float | None
    x_mm: float | None
    y_mm: float | None
    z_mm: float | None
    notes: str
    limits: dict[str, Any]

    @property
    def has_installation_envelope(self) -> bool:
        return all(value is not None for value in (
            self.length_mm, self.width_mm, self.height_mm, self.x_mm, self.y_mm, self.z_mm,
        ))

    def as_mass_component(self) -> MassComponentConfig | None:
        if self.mass_g is None or any(value is None for value in (self.x_mm, self.y_mm, self.z_mm)):
            return None
        # Hardware mass is never promoted to measured/known merely because a
        # datasheet exists.  It remains a preliminary configuration estimate.
        return MassComponentConfig(self.id, self.model or self.id, "design_estimate", self.mass_g,
                                   self.x_mm, self.y_mm, self.z_mm, "center", None)


@dataclass(frozen=True)
class BatteryInstallation:
    topology: str
    nominal_energy_wh_typical: float
    usable_energy_wh_study: float
    usable_fraction: float
    x_nominal_mm: float
    x_min_mm: float
    x_max_mm: float
    removal_axis: Literal["+z", "-z", "+x", "-x"]
    hatch_length_mm: float
    hatch_width_mm: float
    hatch_height_mm: float
    clearance_mm: float


@dataclass(frozen=True)
class HardwareConfig:
    schema: str
    status: str
    components: tuple[HardwareComponent, ...]
    battery_installation: BatteryInstallation
    high_current_route: tuple[tuple[float, float, float], ...]
    antenna_keepouts: tuple[HardwareComponent, ...]

    def component(self, component_id: str) -> HardwareComponent:
        try:
            return next(item for item in self.components if item.id == component_id)
        except StopIteration as error:
            raise ConfigurationError(f"hardware manifest has no component {component_id!r}") from error

    @property
    def selected_components(self) -> tuple[HardwareComponent, ...]:
        return tuple(item for item in self.components if item.status == "selected_preliminary")


def _component(raw: Any, name: str) -> HardwareComponent:
    value = _mapping(raw, name)
    required = {"id", "category", "status", "manufacturer", "model", "source_url", "source_retrieved_date", "mass_g", "mass_status", "dimensions_mm", "position_mm", "notes", "limits"}
    missing, unknown = required - set(value), set(value) - required
    if missing or unknown:
        raise ConfigurationError(f"{name} keys mismatch; missing={sorted(missing)}, unknown={sorted(unknown)}")
    status = value["status"]
    if status not in {"selected_preliminary", "fallback", "design_estimate", "tbd"}:
        raise ConfigurationError(f"{name}.status is invalid")
    mass_status = value["mass_status"]
    if mass_status not in {"datasheet", "design_estimate", "tbd"}:
        raise ConfigurationError(f"{name}.mass_status is invalid")
    dimensions = _mapping(value["dimensions_mm"], f"{name}.dimensions_mm")
    position = _mapping(value["position_mm"], f"{name}.position_mm")
    if set(dimensions) != {"length", "width", "height"} or set(position) != {"x", "y", "z"}:
        raise ConfigurationError(f"{name} dimensions_mm/position_mm have unknown keys")
    mass = value["mass_g"]
    if mass is not None:
        mass = _positive(mass, f"{name}.mass_g")
    dims = tuple(None if dimensions[key] is None else _positive(dimensions[key], f"{name}.dimensions_mm.{key}") for key in ("length", "width", "height"))
    pos = tuple(None if position[key] is None else _number(position[key], f"{name}.position_mm.{key}") for key in ("x", "y", "z"))
    is_selected = status == "selected_preliminary"
    if is_selected and (not all(isinstance(value[key], str) and value[key] for key in ("manufacturer", "model", "source_url", "source_retrieved_date")) or mass is None or any(item is None for item in (*dims, *pos))):
        raise ConfigurationError(f"{name}: selected preliminary component needs source, mass, dimensions and position")
    if not isinstance(value["notes"], str) or not isinstance(value["limits"], dict):
        raise ConfigurationError(f"{name}.notes/limits are invalid")
    return HardwareComponent(value["id"], value["category"], status, value["manufacturer"], value["model"],
                             value["source_url"], value["source_retrieved_date"], mass, mass_status,
                             *dims, *pos, value["notes"], value["limits"])


def load_hardware_config(path: Path = DEFAULT_HARDWARE_PATH) -> HardwareConfig:
    try:
        document = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), str(path))
    except OSError as error:
        raise ConfigurationError(f"Unable to read hardware manifest {path}: {error}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid hardware manifest {path}: {error}") from error
    required = {"schema", "status", "components", "battery_installation", "high_current_route_mm", "antenna_keepouts"}
    if set(document) != required:
        raise ConfigurationError("hardware manifest top-level keys mismatch")
    components_raw = document["components"]
    if not isinstance(components_raw, list) or not components_raw:
        raise ConfigurationError("hardware manifest components must be a non-empty list")
    components = tuple(_component(item, f"hardware.components[{index}]") for index, item in enumerate(components_raw))
    ids = [item.id for item in components]
    if len(ids) != len(set(ids)):
        raise ConfigurationError("hardware manifest component ids must be unique")
    installation = _mapping(document["battery_installation"], "battery_installation")
    install_keys = {"topology", "nominal_energy_wh_typical", "usable_energy_wh_study", "usable_fraction", "x_nominal_mm", "x_min_mm", "x_max_mm", "removal_axis", "hatch_opening_mm", "clearance_mm"}
    if set(installation) != install_keys:
        raise ConfigurationError("battery_installation keys mismatch")
    hatch = _mapping(installation["hatch_opening_mm"], "battery_installation.hatch_opening_mm")
    if set(hatch) != {"length", "width", "height"}:
        raise ConfigurationError("battery_installation.hatch_opening_mm keys mismatch")
    x_min, x_nominal, x_max = (_number(installation[key], f"battery_installation.{key}") for key in ("x_min_mm", "x_nominal_mm", "x_max_mm"))
    if not x_min <= x_nominal <= x_max:
        raise ConfigurationError("battery installation nominal X must lie within travel")
    if installation["removal_axis"] not in {"+z", "-z", "+x", "-x"}:
        raise ConfigurationError("battery installation removal axis is invalid")
    battery = BatteryInstallation(installation["topology"], _positive(installation["nominal_energy_wh_typical"], "battery nominal energy"),
                                  _positive(installation["usable_energy_wh_study"], "battery usable energy"),
                                  _positive(installation["usable_fraction"], "battery usable fraction"), x_nominal, x_min, x_max,
                                  installation["removal_axis"], *(_positive(hatch[key], f"hatch.{key}") for key in ("length", "width", "height")),
                                  _positive(installation["clearance_mm"], "battery clearance"))
    route_raw = document["high_current_route_mm"]
    if not isinstance(route_raw, list) or len(route_raw) < 2:
        raise ConfigurationError("high_current_route_mm needs two or more points")
    route = tuple(tuple(_number(value, "high_current_route_mm coordinate") for value in point) for point in route_raw)
    if any(len(point) != 3 for point in route):
        raise ConfigurationError("each high-current route point must be XYZ")
    keepouts = tuple(_component(item, f"antenna_keepouts[{index}]") for index, item in enumerate(document["antenna_keepouts"]))
    return HardwareConfig(document["schema"], document["status"], components, battery, route, keepouts)
