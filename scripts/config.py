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
    first_flight_recommendation: "FirstFlightCGConfig"


@dataclass(frozen=True)
class FirstFlightCGConfig:
    """Preliminary marker, never a substitute for measured all-up CG."""

    status: Literal["tbd", "preliminary_recommendation"]
    x_mac_fraction: float | None
    basis: str | None

    @property
    def is_defined(self) -> bool:
        return self.status == "preliminary_recommendation"


@dataclass(frozen=True)
class HorizontalTailConfig:
    span_mm: float
    root_chord_mm: float
    tip_chord_mm: float
    elevator_chord_fraction: float

    @property
    def area_m2(self) -> float:
        return self.span_mm * (self.root_chord_mm + self.tip_chord_mm) / 2_000_000.0


@dataclass(frozen=True)
class VerticalTailConfig:
    fin_height_mm: float
    root_chord_mm: float
    tip_chord_mm: float
    rudder_chord_fraction: float

    @property
    def area_each_m2(self) -> float:
        return self.fin_height_mm * (self.root_chord_mm + self.tip_chord_mm) / 2_000_000.0

    @property
    def total_area_m2(self) -> float:
        return 2.0 * self.area_each_m2


@dataclass(frozen=True)
class TailConfig:
    status: Literal["tbd", "initial_design_assumption"]
    tail_arm_mm: float | None
    horizontal: HorizontalTailConfig | None
    vertical: VerticalTailConfig | None
    wing_aerodynamic_center_x_mm: float

    @property
    def is_defined(self) -> bool:
        return self.status == "initial_design_assumption"

    @property
    def aerodynamic_center_x_mm(self) -> float | None:
        """Derived from the typed wing AC plus the stored tail arm.

        It is deliberately not a second YAML datum: a wing-source sensitivity
        must move this reference automatically rather than invalidate config.
        """
        return None if self.tail_arm_mm is None else self.wing_aerodynamic_center_x_mm + self.tail_arm_mm


@dataclass(frozen=True)
class BoomSectionCandidateConfig:
    status: Literal["tbd", "design_estimate"]
    outer_diameter_mm: float | None
    inner_diameter_mm: float | None


@dataclass(frozen=True)
class BoomsConfig:
    status: Literal["tbd", "initial_design_assumption"]
    lateral_offset_mm: float | None
    axis_z_mm: float | None
    tail_attachment_x_mm: float | None
    section_candidate: BoomSectionCandidateConfig

    @property
    def is_defined(self) -> bool:
        return self.status == "initial_design_assumption"


@dataclass(frozen=True)
class PropellerEnvelopeConfig:
    diameter_min_mm: float
    diameter_max_mm: float
    pitch_min_mm: float
    pitch_max_mm: float
    cruise_rpm_min: float
    cruise_rpm_max: float


@dataclass(frozen=True)
class MotorEnvelopeConfig:
    kv_min_rpm_per_v: float
    kv_max_rpm_per_v: float
    continuous_electrical_power_w: float
    peak_electrical_power_w: float
    continuous_current_a: float
    peak_current_a: float
    mass_min_g: float
    mass_max_g: float
    envelope_length_mm: float
    envelope_diameter_mm: float


@dataclass(frozen=True)
class EscEnvelopeConfig:
    length_mm: float
    width_mm: float
    height_mm: float
    x_mm: float
    y_mm: float
    z_mm: float


@dataclass(frozen=True)
class PropulsionConfig:
    status: Literal["tbd", "initial_design_assumption"]
    nominal_series_count: int | None
    propeller: PropellerEnvelopeConfig | None
    motor: MotorEnvelopeConfig | None
    esc: EscEnvelopeConfig | None
    propeller_plane_x_mm: float | None
    motor_cg_x_mm: float | None
    motor_axis_z_mm: float | None

    @property
    def is_defined(self) -> bool:
        return self.status == "initial_design_assumption"


@dataclass(frozen=True)
class ElectricalConfig:
    status: Literal["tbd", "initial_design_assumption"]
    propulsion_bus_nominal_voltage_v: float | None
    propulsion_bus_loaded_min_voltage_v: float | None
    avionics_logic_rail_v: float | None
    servo_rail_v: float | None
    hotel_load_low_w: float | None
    hotel_load_nominal_w: float | None
    hotel_load_high_w: float | None

    @property
    def is_defined(self) -> bool:
        return self.status == "initial_design_assumption"


@dataclass(frozen=True)
class BatteryConfig:
    status: Literal["tbd", "initial_design_assumption"]
    chemistry_direction: Literal["tbd", "li_ion_preliminary", "lipo_preliminary"]
    usable_energy_preferred_min_wh: float | None
    usable_energy_preferred_max_wh: float | None
    mass_min_g: float | None
    mass_max_g: float | None
    package_length_mm: float | None
    package_width_mm: float | None
    package_height_mm: float | None
    nominal_x_mm: float | None
    x_adjustment_min_mm: float | None
    x_adjustment_max_mm: float | None
    y_mm: float | None
    z_mm: float | None
    tray_status: Literal["tbd", "preliminary_design_assumption"]

    @property
    def is_defined(self) -> bool:
        return self.status == "initial_design_assumption"


@dataclass(frozen=True)
class AvionicsComponentEnvelopeConfig:
    id: str
    length_mm: float
    width_mm: float
    height_mm: float
    x_mm: float
    y_mm: float
    z_mm: float


@dataclass(frozen=True)
class AvionicsConfig:
    status: Literal["tbd", "initial_design_assumption"]
    components: tuple[AvionicsComponentEnvelopeConfig, ...]

    @property
    def is_defined(self) -> bool:
        return self.status == "initial_design_assumption"


@dataclass(frozen=True)
class MassComponentConfig:
    """One point-mass ledger entry in the common aircraft coordinate system."""

    id: str
    name: str
    status: Literal["known", "design_estimate", "tbd"]
    mass_g: float | None
    x_mm: float | None
    y_mm: float | None
    z_mm: float | None
    side: Literal["left", "right", "center"]
    pair_id: str | None

    @property
    def is_resolved(self) -> bool:
        return self.status == "known"

    @property
    def is_design_estimate(self) -> bool:
        return self.status == "design_estimate"


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
    tail: TailConfig
    booms: BoomsConfig
    propulsion: PropulsionConfig
    electrical: ElectricalConfig
    battery: BatteryConfig
    avionics: AvionicsConfig
    mass_budget: MassBudgetConfig


def load_aircraft_config(path: Path = DEFAULT_CONFIG_PATH) -> AircraftConfig:
    """Load and strictly validate the sole editable aircraft configuration."""
    try:
        document = _mapping(yaml.safe_load(path.read_text(encoding="utf-8")), str(path))
    except OSError as error:
        raise ConfigurationError(f"Unable to read configuration {path}: {error}") from error
    except yaml.YAMLError as error:
        raise ConfigurationError(f"Invalid YAML in {path}: {error}") from error

    top_level = {"project", "wing", "spar", "materials", "aircraft", "layout", "cg", "tail", "booms", "propulsion", "electrical", "battery", "avionics", "mass_budget"}
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

    cg = _section(document, "cg", {"initial_envelope", "first_flight_recommendation"})
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
    first_flight = _section(cg, "first_flight_recommendation", {"status", "x_mac_fraction", "basis"})
    if first_flight["status"] not in {"tbd", "preliminary_recommendation"}:
        raise ConfigurationError("cg.first_flight_recommendation.status must be 'tbd' or 'preliminary_recommendation'")
    first_flight_fraction = _nullable_number(first_flight["x_mac_fraction"], "cg.first_flight_recommendation.x_mac_fraction")
    first_flight_basis = first_flight["basis"]
    if first_flight_basis is not None:
        first_flight_basis = _non_empty_string(first_flight_basis, "cg.first_flight_recommendation.basis")
    if first_flight["status"] == "tbd":
        if first_flight_fraction is not None or first_flight_basis is not None:
            raise ConfigurationError("tbd cg.first_flight_recommendation must use null fraction and basis")
    elif first_flight_fraction is None or first_flight_basis is None or not 0.0 <= first_flight_fraction <= 1.0:
        raise ConfigurationError("defined cg.first_flight_recommendation needs a fraction in [0, 1] and a basis")
    if envelope["status"] == "tbd" and first_flight["status"] != "tbd":
        raise ConfigurationError("cg.first_flight_recommendation needs a defined initial_envelope")
    if envelope["status"] != "tbd" and first_flight["status"] != "tbd" and not fraction_min <= first_flight_fraction <= fraction_max:
        raise ConfigurationError("cg.first_flight_recommendation must lie inside cg.initial_envelope")
    cg_config = CGConfig(
        CGEnvelopeConfig(envelope["status"], fraction_min, fraction_max, basis),
        FirstFlightCGConfig(first_flight["status"], first_flight_fraction, first_flight_basis),
    )

    tail = _section(document, "tail", {"status", "tail_arm_mm", "horizontal", "vertical"})
    if tail["status"] not in {"tbd", "initial_design_assumption"}:
        raise ConfigurationError("tail.status must be 'tbd' or 'initial_design_assumption'")
    tail_arm = _nullable_number(tail["tail_arm_mm"], "tail.tail_arm_mm")
    horizontal_raw, vertical_raw = tail["horizontal"], tail["vertical"]
    if tail["status"] == "tbd":
        if any(value is not None for value in (tail_arm, horizontal_raw, vertical_raw)):
            raise ConfigurationError("tbd tail must use null geometry")
        wing_ac_x = wing_config.mean_aerodynamic_chord_leading_edge_x_mm + .25 * wing_config.mean_aerodynamic_chord_mm
        tail_config = TailConfig("tbd", None, None, None, wing_ac_x)
    else:
        if tail_arm is None:
            raise ConfigurationError("defined tail needs tail_arm_mm")
        horizontal = _mapping(horizontal_raw, "tail.horizontal")
        horizontal_keys = {"span_mm", "root_chord_mm", "tip_chord_mm", "elevator_chord_fraction"}
        if set(horizontal) != horizontal_keys:
            raise ConfigurationError("tail.horizontal has missing or unknown keys")
        vertical = _mapping(vertical_raw, "tail.vertical")
        vertical_keys = {"fin_height_mm", "root_chord_mm", "tip_chord_mm", "rudder_chord_fraction"}
        if set(vertical) != vertical_keys:
            raise ConfigurationError("tail.vertical has missing or unknown keys")
        horizontal_config = HorizontalTailConfig(
            _positive(horizontal["span_mm"], "tail.horizontal.span_mm"), _positive(horizontal["root_chord_mm"], "tail.horizontal.root_chord_mm"),
            _positive(horizontal["tip_chord_mm"], "tail.horizontal.tip_chord_mm"), _bounded(horizontal["elevator_chord_fraction"], "tail.horizontal.elevator_chord_fraction", .05, .80),
        )
        vertical_config = VerticalTailConfig(
            _positive(vertical["fin_height_mm"], "tail.vertical.fin_height_mm"), _positive(vertical["root_chord_mm"], "tail.vertical.root_chord_mm"),
            _positive(vertical["tip_chord_mm"], "tail.vertical.tip_chord_mm"), _bounded(vertical["rudder_chord_fraction"], "tail.vertical.rudder_chord_fraction", .05, .80),
        )
        wing_ac_x = wing_config.mean_aerodynamic_chord_leading_edge_x_mm + .25 * wing_config.mean_aerodynamic_chord_mm
        if tail_arm <= 0:
            raise ConfigurationError("defined tail must lie aft of the wing aerodynamic-center reference")
        tail_config = TailConfig("initial_design_assumption", tail_arm, horizontal_config, vertical_config, wing_ac_x)

    booms = _section(document, "booms", {"status", "lateral_offset_mm", "axis_z_mm", "section_candidate"})
    if booms["status"] not in {"tbd", "initial_design_assumption"}:
        raise ConfigurationError("booms.status must be 'tbd' or 'initial_design_assumption'")
    boom_y = _nullable_number(booms["lateral_offset_mm"], "booms.lateral_offset_mm")
    boom_z = _nullable_number(booms["axis_z_mm"], "booms.axis_z_mm")
    section = _mapping(booms["section_candidate"], "booms.section_candidate")
    if set(section) != {"status", "outer_diameter_mm", "inner_diameter_mm"}:
        raise ConfigurationError("booms.section_candidate has missing or unknown keys")
    if section["status"] not in {"tbd", "design_estimate"}:
        raise ConfigurationError("booms.section_candidate.status must be 'tbd' or 'design_estimate'")
    outer = _nullable_number(section["outer_diameter_mm"], "booms.section_candidate.outer_diameter_mm")
    inner = _nullable_number(section["inner_diameter_mm"], "booms.section_candidate.inner_diameter_mm")
    if section["status"] == "tbd":
        if outer is not None or inner is not None:
            raise ConfigurationError("tbd booms.section_candidate must use null dimensions")
    elif outer is None or inner is None or outer <= inner or inner <= 0:
        raise ConfigurationError("design_estimate booms.section_candidate needs positive OD > ID")
    section_config = BoomSectionCandidateConfig(section["status"], outer, inner)
    if booms["status"] == "tbd":
        if any(value is not None for value in (boom_y, boom_z)):
            raise ConfigurationError("tbd booms must use null reference axes")
        booms_config = BoomsConfig("tbd", None, None, None, section_config)
    else:
        if boom_y is None or boom_z is None or boom_y <= 0:
            raise ConfigurationError("defined booms need positive lateral offset and complete axes")
        booms_config = BoomsConfig("initial_design_assumption", boom_y, boom_z, tail_config.aerodynamic_center_x_mm, section_config)

    propulsion = _section(document, "propulsion", {"status", "nominal_series_count", "propeller", "motor", "esc", "propeller_plane_x_mm", "motor_cg_x_mm", "motor_axis_z_mm"})
    if propulsion["status"] not in {"tbd", "initial_design_assumption"}:
        raise ConfigurationError("propulsion.status must be 'tbd' or 'initial_design_assumption'")
    series_count = propulsion["nominal_series_count"]
    propeller_raw, motor_raw, esc_raw = propulsion["propeller"], propulsion["motor"], propulsion["esc"]
    installation = tuple(_nullable_number(propulsion[key], f"propulsion.{key}") for key in ("propeller_plane_x_mm", "motor_cg_x_mm", "motor_axis_z_mm"))
    if propulsion["status"] == "tbd":
        if series_count is not None or propeller_raw is not None or motor_raw is not None or esc_raw is not None or any(value is not None for value in installation):
            raise ConfigurationError("tbd propulsion must use null architecture and envelopes")
        propulsion_config = PropulsionConfig("tbd", None, None, None, None, None, None, None)
    else:
        if isinstance(series_count, bool) or not isinstance(series_count, int) or series_count not in {3, 4, 6}:
            raise ConfigurationError("defined propulsion.nominal_series_count must be 3, 4, or 6")
        propeller = _mapping(propeller_raw, "propulsion.propeller")
        propeller_keys = {"diameter_min_mm", "diameter_max_mm", "pitch_min_mm", "pitch_max_mm", "cruise_rpm_min", "cruise_rpm_max"}
        if set(propeller) != propeller_keys:
            raise ConfigurationError("propulsion.propeller has missing or unknown keys")
        propeller_config = PropellerEnvelopeConfig(*(_positive(propeller[key], f"propulsion.propeller.{key}") for key in (
            "diameter_min_mm", "diameter_max_mm", "pitch_min_mm", "pitch_max_mm", "cruise_rpm_min", "cruise_rpm_max",
        )))
        if propeller_config.diameter_min_mm > propeller_config.diameter_max_mm or propeller_config.pitch_min_mm > propeller_config.pitch_max_mm or propeller_config.cruise_rpm_min > propeller_config.cruise_rpm_max:
            raise ConfigurationError("propulsion.propeller range minimum must not exceed maximum")
        motor = _mapping(motor_raw, "propulsion.motor")
        motor_keys = {"kv_min_rpm_per_v", "kv_max_rpm_per_v", "continuous_electrical_power_w", "peak_electrical_power_w", "continuous_current_a", "peak_current_a", "mass_min_g", "mass_max_g", "envelope_length_mm", "envelope_diameter_mm"}
        if set(motor) != motor_keys:
            raise ConfigurationError("propulsion.motor has missing or unknown keys")
        motor_config = MotorEnvelopeConfig(*(_positive(motor[key], f"propulsion.motor.{key}") for key in (
            "kv_min_rpm_per_v", "kv_max_rpm_per_v", "continuous_electrical_power_w", "peak_electrical_power_w", "continuous_current_a", "peak_current_a", "mass_min_g", "mass_max_g", "envelope_length_mm", "envelope_diameter_mm",
        )))
        if motor_config.kv_min_rpm_per_v > motor_config.kv_max_rpm_per_v or motor_config.continuous_electrical_power_w > motor_config.peak_electrical_power_w or motor_config.continuous_current_a > motor_config.peak_current_a or motor_config.mass_min_g > motor_config.mass_max_g:
            raise ConfigurationError("propulsion.motor range/continuous values are inconsistent")
        esc = _mapping(esc_raw, "propulsion.esc")
        esc_keys = {"length_mm", "width_mm", "height_mm", "x_mm", "y_mm", "z_mm"}
        if set(esc) != esc_keys:
            raise ConfigurationError("propulsion.esc has missing or unknown keys")
        esc_dimensions = tuple(_positive(esc[key], f"propulsion.esc.{key}") for key in ("length_mm", "width_mm", "height_mm"))
        esc_location = tuple(_number(esc[key], f"propulsion.esc.{key}") for key in ("x_mm", "y_mm", "z_mm"))
        esc_config = EscEnvelopeConfig(*esc_dimensions, *esc_location)
        if any(value is None for value in installation):
            raise ConfigurationError("defined propulsion needs propeller plane, motor CG, and motor-axis Z")
        propeller_x, motor_x, motor_z = installation
        propulsion_config = PropulsionConfig("initial_design_assumption", series_count, propeller_config, motor_config, esc_config, propeller_x, motor_x, motor_z)

    electrical = _section(document, "electrical", {"status", "propulsion_bus_nominal_voltage_v", "propulsion_bus_loaded_min_voltage_v", "avionics_logic_rail_v", "servo_rail_v", "hotel_load_low_w", "hotel_load_nominal_w", "hotel_load_high_w"})
    if electrical["status"] not in {"tbd", "initial_design_assumption"}:
        raise ConfigurationError("electrical.status must be 'tbd' or 'initial_design_assumption'")
    electrical_values = tuple(_nullable_number(electrical[key], f"electrical.{key}") for key in (
        "propulsion_bus_nominal_voltage_v", "propulsion_bus_loaded_min_voltage_v", "avionics_logic_rail_v", "servo_rail_v", "hotel_load_low_w", "hotel_load_nominal_w", "hotel_load_high_w",
    ))
    if electrical["status"] == "tbd":
        if any(value is not None for value in electrical_values):
            raise ConfigurationError("tbd electrical must use null values")
        electrical_config = ElectricalConfig("tbd", *(None for _ in electrical_values))
    else:
        if any(value is None or value <= 0 for value in electrical_values):
            raise ConfigurationError("defined electrical values must be positive")
        bus_nominal, bus_loaded, logic_rail, servo_rail, hotel_low, hotel_nominal, hotel_high = electrical_values
        if bus_loaded > bus_nominal or hotel_low > hotel_nominal or hotel_nominal > hotel_high:
            raise ConfigurationError("electrical voltage/load bounds are inconsistent")
        electrical_config = ElectricalConfig("initial_design_assumption", *electrical_values)

    battery = _section(document, "battery", {"status", "chemistry_direction", "usable_energy_preferred_min_wh", "usable_energy_preferred_max_wh", "mass_min_g", "mass_max_g", "package_length_mm", "package_width_mm", "package_height_mm", "nominal_x_mm", "x_adjustment_min_mm", "x_adjustment_max_mm", "y_mm", "z_mm", "tray_status"})
    if battery["status"] not in {"tbd", "initial_design_assumption"}:
        raise ConfigurationError("battery.status must be 'tbd' or 'initial_design_assumption'")
    chemistry = battery["chemistry_direction"]
    tray_status = battery["tray_status"]
    if chemistry not in {"tbd", "li_ion_preliminary", "lipo_preliminary"}:
        raise ConfigurationError("battery.chemistry_direction is invalid")
    if tray_status not in {"tbd", "preliminary_design_assumption"}:
        raise ConfigurationError("battery.tray_status is invalid")
    battery_values = tuple(_nullable_number(battery[key], f"battery.{key}") for key in (
        "usable_energy_preferred_min_wh", "usable_energy_preferred_max_wh", "mass_min_g", "mass_max_g", "package_length_mm", "package_width_mm", "package_height_mm", "nominal_x_mm", "x_adjustment_min_mm", "x_adjustment_max_mm", "y_mm", "z_mm",
    ))
    if battery["status"] == "tbd":
        if chemistry != "tbd" or tray_status != "tbd" or any(value is not None for value in battery_values):
            raise ConfigurationError("tbd battery must use tbd/null values")
        battery_config = BatteryConfig("tbd", "tbd", *(None for _ in battery_values), "tbd")
    else:
        if chemistry == "tbd" or tray_status != "preliminary_design_assumption" or any(value is None for value in battery_values):
            raise ConfigurationError("defined battery needs chemistry, tray status, and all envelope values")
        energy_min, energy_max, mass_min, mass_max, length, width, height, nominal_x, x_min, x_max, y_mm, z_mm = battery_values
        if min(energy_min, mass_min, length, width, height) <= 0 or energy_min > energy_max or mass_min > mass_max or x_min >= x_max:
            raise ConfigurationError("battery envelope/range values are inconsistent")
        battery_config = BatteryConfig("initial_design_assumption", chemistry, *battery_values, tray_status)

    avionics = _section(document, "avionics", {"status", "components"})
    if avionics["status"] not in {"tbd", "initial_design_assumption"}:
        raise ConfigurationError("avionics.status must be 'tbd' or 'initial_design_assumption'")
    components_raw = avionics["components"]
    if avionics["status"] == "tbd":
        if components_raw is not None:
            raise ConfigurationError("tbd avionics must use null components")
        avionics_config = AvionicsConfig("tbd", ())
    else:
        if not isinstance(components_raw, list) or not components_raw:
            raise ConfigurationError("defined avionics.components must be a non-empty list")
        component_ids: set[str] = set()
        avionics_components: list[AvionicsComponentEnvelopeConfig] = []
        component_keys = {"id", "length_mm", "width_mm", "height_mm", "x_mm", "y_mm", "z_mm"}
        for index, item_raw in enumerate(components_raw):
            item = _mapping(item_raw, f"avionics.components[{index}]")
            if set(item) != component_keys:
                raise ConfigurationError("avionics component has missing or unknown keys")
            component_id = _non_empty_string(item["id"], f"avionics.components[{index}].id")
            if component_id in component_ids:
                raise ConfigurationError(f"duplicate avionics component id: {component_id}")
            component_ids.add(component_id)
            dimensions = tuple(_positive(item[key], f"avionics.components[{index}].{key}") for key in ("length_mm", "width_mm", "height_mm"))
            location = tuple(_number(item[key], f"avionics.components[{index}].{key}") for key in ("x_mm", "y_mm", "z_mm"))
            avionics_components.append(AvionicsComponentEnvelopeConfig(component_id, *dimensions, *location))
        avionics_config = AvionicsConfig("initial_design_assumption", tuple(avionics_components))

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
        if status not in {"known", "design_estimate", "tbd"}:
            raise ConfigurationError(f"mass_budget.components[{index}].status must be 'known', 'design_estimate', or 'tbd'")
        mass_g = _nullable_number(item["mass_g"], f"mass_budget.components[{index}].mass_g")
        if mass_g is not None and mass_g < 0:
            raise ConfigurationError(f"mass_budget.components[{index}].mass_g must not be negative")
        coordinates = tuple(_nullable_number(item[key], f"mass_budget.components[{index}].{key}") for key in ("x_mm", "y_mm", "z_mm"))
        if status in {"known", "design_estimate"} and (mass_g is None or any(value is None for value in coordinates)):
            raise ConfigurationError(f"resolved mass_budget.components[{index}] needs mass_g and all coordinates")
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
        materials_config, aircraft_config, layout_config, cg_config, tail_config, booms_config,
        propulsion_config, electrical_config, battery_config, avionics_config, mass_budget_config,
    )
