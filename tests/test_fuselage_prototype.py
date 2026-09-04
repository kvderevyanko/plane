from pathlib import Path

import pytest

from cad.fuselage.model import (battery_removal_sweep, laser_parts, longeron_paths,
                                mass_estimate, part_station_trace, structural_assembly,
                                validate_geometry)
from scripts.config import load_aircraft_config

ROOT = Path(__file__).resolve().parents[1]


def test_prototype_uses_typed_5x3_carbon_and_extended_forward_rail():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    p = config.fuselage_prototype
    assert (p.longeron_width_mm, p.longeron_height_mm) == pytest.approx((5, 3))
    assert (p.battery_rail_x_min_mm, p.battery_rail_x_max_mm) == pytest.approx((-387.5, -332.5))


def test_primary_lower_load_path_reaches_forward_pack_stop():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    lower = [path for path in longeron_paths(config) if "LOWER" in path[0]]
    assert all(start[0] <= -475 and end[0] >= 365 for _, start, end in lower)
    parts = {part.id: part for part in laser_parts(config)}
    assert parts["FUS-KEEL-L"].outline_mm[1][0] == pytest.approx(840)
    assert parts["FUS-HATCH-RAIL-L"].classification == "PRIMARY STRUCTURE"


def test_boom_placeholder_and_fixed_nose_index_are_not_steering_parts():
    parts = {part.id: part for part in laser_parts(load_aircraft_config(ROOT / "config" / "aircraft.yaml"))}
    assert parts["FUS-BOOM-SADDLE-F-L"].status == "NOT RELEASED"
    assert "no steering freedom" in parts["FUS-NOSE-INDEX-BLOCK"].reason.lower()
    assert parts["FUS-GEAR-SHIM-4P0"].quantity == 2


def test_station_trace_locks_critical_interfaces_to_aircraft_datums():
    trace = part_station_trace()
    assert trace["FUS-MOTOR-PLATE"] == pytest.approx((410, 0, 50))
    assert trace["FUS-BOOM-SADDLE-F-L"][1] == pytest.approx(-230)
    assert trace["FUS-BOOM-SADDLE-A-R"][0] - trace["FUS-BOOM-SADDLE-F-R"][0] == pytest.approx(80)


def test_assembly_contains_real_load_bays_and_service_sweep():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    assembly = structural_assembly(config)
    assert len([name for name in assembly if name.startswith("FUS-FORMER")]) == 8
    assert {"FUS-WING-TRANSFER-FRAME", "FUS-GEAR-BOX", "FUS-NOSE-KEY-SOCKET", "FUS-MOTOR-CROSSMEMBER"} <= set(assembly)
    sweep = battery_removal_sweep(config).val().BoundingBox()
    assert (sweep.xlen, sweep.ylen, sweep.zlen) == pytest.approx((210, 75, 160))
    assert validate_geometry(config) == []


def test_battery_retention_has_positive_stops_and_two_independent_strap_anchors():
    parts = {part.id: part for part in laser_parts(load_aircraft_config(ROOT / "config" / "aircraft.yaml"))}
    assert parts["FUS-BAT-FWD-STOP"].thickness_mm == 3
    assert parts["FUS-BAT-AFT-STOP"].thickness_mm == 3
    assert parts["FUS-BAT-STRAP-ANCHOR-F"].quantity == 2
    rail_indexes = [hole[0] for hole in parts["FUS-BAT-RAIL-L"].holes_mm]
    assert [b - a for a, b in zip(rail_indexes, rail_indexes[1:])] == pytest.approx([11] * 5)
    slot = parts["FUS-BAT-FINE-CLAMP-L"].slots_mm[0]
    assert (slot[0], slot[2]) == pytest.approx((40, 55))


def test_cad_mass_is_explicit_dry_geometry_plus_allowances_not_ledger_mass():
    estimate = mass_estimate(load_aircraft_config(ROOT / "config" / "aircraft.yaml"))
    assert estimate["birch_dry_g"] > 0
    assert estimate["carbon_dry_g"] > 0
    assert estimate["cad_structural_total_g"] == pytest.approx(
        estimate["birch_dry_g"] + estimate["carbon_dry_g"] + estimate["adhesive_allowance_g"] + estimate["fastener_allowance_g"]
    )
