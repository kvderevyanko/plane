"""Aircraft mass-property calculations in the single LR1600 coordinate system.

The functions deliberately calculate a subtotal only from resolved point-mass
items.  They retain every unresolved item in the returned result, so callers
cannot silently mistake a partial subtotal for the aircraft's final CG.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable

from scripts.config import MassComponentConfig


class MassPropertiesError(ValueError):
    """A mass item is malformed or cannot be used in a physical calculation."""


@dataclass(frozen=True)
class MassProperties:
    """Known subtotal plus an explicitly distinct preliminary estimate."""

    total_mass_g: float
    x_cg_mm: float | None
    y_cg_mm: float | None
    z_cg_mm: float | None
    included_component_ids: tuple[str, ...]
    estimated_total_mass_g: float | None
    estimated_x_cg_mm: float | None
    estimated_y_cg_mm: float | None
    estimated_z_cg_mm: float | None
    design_estimate_components: tuple[MassComponentConfig, ...]
    unresolved_components: tuple[MassComponentConfig, ...]

    @property
    def is_final_aircraft_cg(self) -> bool:
        """True only when every configured component is measured/known."""
        return not self.unresolved_components and not self.design_estimate_components and self.total_mass_g > 0.0

    @property
    def has_estimated_configuration_cg(self) -> bool:
        """True only for a complete ledger containing design estimates."""
        return not self.unresolved_components and bool(self.design_estimate_components) and self.estimated_total_mass_g is not None


def _finite(value: float | None, field: str, component_id: str) -> float:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MassPropertiesError(f"{component_id}.{field} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise MassPropertiesError(f"{component_id}.{field} must be finite")
    return value


def _validate_component(component: MassComponentConfig) -> None:
    if component.status not in {"known", "design_estimate", "tbd"}:
        raise MassPropertiesError(f"{component.id}.status must be known, design_estimate, or tbd")
    if component.status == "tbd":
        # Values collected before the item is fully located remain explicitly
        # unresolved, but any supplied value still needs to be physically sane.
        if component.mass_g is not None:
            mass = _finite(component.mass_g, "mass_g", component.id)
            if mass < 0.0:
                raise MassPropertiesError(f"{component.id}.mass_g must not be negative")
        for field in ("x_mm", "y_mm", "z_mm"):
            value = getattr(component, field)
            if value is not None:
                _finite(value, field, component.id)
        return

    mass = _finite(component.mass_g, "mass_g", component.id)
    if mass < 0.0:
        raise MassPropertiesError(f"{component.id}.mass_g must not be negative")
    for field in ("x_mm", "y_mm", "z_mm"):
        _finite(getattr(component, field), field, component.id)


def calculate_mass_properties(components: Iterable[MassComponentConfig]) -> MassProperties:
    """Calculate known subtotal and a separate all-item estimated CG when valid.

    ``known`` values form the measurement-backed subtotal. ``design_estimate``
    values are accumulated only into a separate result which is emitted only
    if no ``tbd`` values remain; that result must never be labelled final.
    """
    total_mass_g = 0.0
    x_moment = y_moment = z_moment = 0.0
    included: list[str] = []
    estimated_mass_g = 0.0
    estimated_x_moment = estimated_y_moment = estimated_z_moment = 0.0
    design_estimates: list[MassComponentConfig] = []
    unresolved: list[MassComponentConfig] = []
    seen_ids: set[str] = set()

    for component in components:
        if not isinstance(component, MassComponentConfig):
            raise MassPropertiesError("components must contain MassComponentConfig instances")
        if component.id in seen_ids:
            raise MassPropertiesError(f"Duplicate mass component id: {component.id}")
        seen_ids.add(component.id)
        _validate_component(component)
        if component.status == "tbd":
            unresolved.append(component)
            continue

        mass = float(component.mass_g)
        x_mm, y_mm, z_mm = float(component.x_mm), float(component.y_mm), float(component.z_mm)
        if component.status == "known":
            total_mass_g += mass
            x_moment += mass * x_mm
            y_moment += mass * y_mm
            z_moment += mass * z_mm
            included.append(component.id)
        else:
            estimated_mass_g += mass
            estimated_x_moment += mass * x_mm
            estimated_y_moment += mass * y_mm
            estimated_z_moment += mass * z_mm
            design_estimates.append(component)

    all_item_mass_g = total_mass_g + estimated_mass_g
    estimate_is_complete = not unresolved and bool(design_estimates) and all_item_mass_g > 0.0
    estimated_result = (
        all_item_mass_g if estimate_is_complete else None,
        (x_moment + estimated_x_moment) / all_item_mass_g if estimate_is_complete else None,
        (y_moment + estimated_y_moment) / all_item_mass_g if estimate_is_complete else None,
        (z_moment + estimated_z_moment) / all_item_mass_g if estimate_is_complete else None,
    )

    if total_mass_g == 0.0:
        return MassProperties(0.0, None, None, None, tuple(included), *estimated_result, tuple(design_estimates), tuple(unresolved))
    return MassProperties(
        total_mass_g,
        x_moment / total_mass_g,
        y_moment / total_mass_g,
        z_moment / total_mass_g,
        tuple(included),
        *estimated_result,
        tuple(design_estimates),
        tuple(unresolved),
    )
