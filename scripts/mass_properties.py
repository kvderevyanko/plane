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
    """Known-mass subtotal and the unresolved work that prevents final CG."""

    total_mass_g: float
    x_cg_mm: float | None
    y_cg_mm: float | None
    z_cg_mm: float | None
    included_component_ids: tuple[str, ...]
    unresolved_components: tuple[MassComponentConfig, ...]

    @property
    def is_final_aircraft_cg(self) -> bool:
        """True only when every configured component is resolved and nonzero total exists."""
        return not self.unresolved_components and self.total_mass_g > 0.0


def _finite(value: float | None, field: str, component_id: str) -> float:
    if value is None or isinstance(value, bool) or not isinstance(value, (int, float)):
        raise MassPropertiesError(f"{component_id}.{field} must be a finite number")
    value = float(value)
    if not math.isfinite(value):
        raise MassPropertiesError(f"{component_id}.{field} must be finite")
    return value


def _validate_component(component: MassComponentConfig) -> None:
    if component.status not in {"known", "tbd"}:
        raise MassPropertiesError(f"{component.id}.status must be known or tbd")
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
    """Calculate mass and CG from only complete, ``known`` point-mass items.

    ``Xcg = Σ(m_i X_i) / Σm_i`` (and identically for Y/Z).  Every ``tbd``
    component is returned in ``unresolved_components``.  Therefore callers
    must inspect :attr:`MassProperties.is_final_aircraft_cg` before presenting
    a result as an aircraft-level CG.
    """
    total_mass_g = 0.0
    x_moment = y_moment = z_moment = 0.0
    included: list[str] = []
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
        total_mass_g += mass
        x_moment += mass * x_mm
        y_moment += mass * y_mm
        z_moment += mass * z_mm
        included.append(component.id)

    if total_mass_g == 0.0:
        return MassProperties(0.0, None, None, None, tuple(included), tuple(unresolved))
    return MassProperties(
        total_mass_g,
        x_moment / total_mass_g,
        y_moment / total_mass_g,
        z_moment / total_mass_g,
        tuple(included),
        tuple(unresolved),
    )
