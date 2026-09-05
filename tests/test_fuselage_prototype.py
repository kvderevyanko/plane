from pathlib import Path
from dataclasses import replace

import pytest

from cad.fuselage.model import (assembly_mass_properties, battery_removal_sweep,
                                dry_assembly_errors, gear_leg_specimens,
                                joint_validation_report, longeron_support_report,
                                laser_parts, longeron_paths, mass_estimate,
                                mating_interfaces, part_instances, part_station_trace,
                                profile_solid, structural_assembly, validate_geometry)
from cad.fuselage.model import (active_skeleton_assembly, active_skeleton_instances,
                                active_skeleton_part_ids, longeron_support_contract,
                                skeleton_assembly_report, skeleton_collision_report,
                                skeleton_features, skeleton_joint_report,
                                skeleton_joints, joint_definitions,
                                joint_geometry_ownership_report,
                                skeleton_profile_validity_report, part_frame,
                                validate_skeleton_v4, active_skeleton_placement_registry,
                                joint_receiver_void_solid, _web_boundary_ligament_mm)
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
    # v4.3.1 extends the terminal contour locally by 6 mm.  The X=365
    # material tongue therefore retains a measured 6.5-mm end bridge.
    assert parts["FUS-KEEL-L"].outline_mm[1][0] == pytest.approx(851)
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
    assert len([name for name in assembly if name.startswith("FUS-FMR-")]) == 8
    assert {"FUS-GEAR-DOUBLER-L#1", "FUS-GEAR-CLOSURE-L#1", "FUS-NOSE-INDEX-BLOCK#1", "FUS-MOTOR-CROSSMEMBER#1"} <= set(assembly)
    sweep = battery_removal_sweep(config).val().BoundingBox()
    assert sweep.xlen >= 210 and sweep.ylen >= 75 and sweep.zlen >= 160
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


def test_profile_identity_quantity_and_finite_geometry_centroid():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    parts = {part.id: part for part in laser_parts(config)}
    instances = part_instances(config)
    assert len(instances) == sum(part.quantity for part in parts.values() if part.status != "TOOLING" and part.id in {i.part_id for i in instances})
    for instance in instances:
        part = parts[instance.part_id]
        assert structural_assembly(config)[instance.instance_id].val().Volume() == pytest.approx(profile_solid(part, instance.plane, instance.origin_mm).val().Volume())
    props = assembly_mass_properties(config)
    assert props["mass_g"] == pytest.approx(mass_estimate(config)["cad_structural_total_g"])
    assert all(abs(value) < 1e5 for value in props["centroid_mm"])
    assert all(mate.width_mm > 0 for mate in mating_interfaces(config))


def test_legacy_v3_joint_metadata_is_not_the_v43_material_joint_gate():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    # v3's ``mating_interfaces()/joint_validation_report()`` calls a web
    # perimeter a tab in metadata.  v4.3 replaces that superseded contract
    # with JointDefinition-derived retained BRep tongues and receiver voids;
    # asserting the old metadata rows would conceal the very fake-joint
    # regression that v4.3 fixes.  Keep unrelated legacy assembly checks here.
    assert dry_assembly_errors(config) == []
    supports = longeron_support_report(config)
    assert len(supports) == 4
    assert all(row["section_mm"] == (5.0, 3.0) and row["largest_unsupported_gap_mm"] == 0 for row in supports.values())
    variants = gear_leg_specimens()
    assert {float(key) + value["total_shim_mm"] for key, value in variants.items()} == {4.0}


def test_v4_active_skeleton_has_30_world_coordinate_joints_and_no_orphan_features():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    joints = skeleton_joints(config)
    assert len(joints) == 30  # 16 keel + 14 side; -285 is before the side webs.
    features = {feature.id: feature for feature in skeleton_features(config)}
    used = [item for joint in joints for item in (joint.tab, joint.slot)]
    assert len(used) == len(set(used))
    assert all(item in features for item in used)
    assert all(row["alignment"] and row["ligament_mm"] > 0 for row in skeleton_joint_report(config))


def test_v43_joint_definitions_own_one_real_web_tongue_and_one_former_receiver():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    definitions = joint_definitions(config)
    ownership = joint_geometry_ownership_report(config)
    assert len(definitions) == len(ownership) == 30
    assert all(row["definition_count"] == 1 and row["material_owner_count"] == 1 and row["receiver_count"] == 1
               and row["former_operation_present"] and row["web_material_retained"]
               for row in ownership)
    # The local datums are transforms of one placed world datum, not raw
    # profile station constants duplicated in the profile builder.
    for definition in definitions:
        assert part_frame(config, definition.former_instance).local_to_world(definition.former_local_mm) == pytest.approx(definition.center_mm)
        assert part_frame(config, definition.web_instance).local_to_world(definition.web_local_mm) == pytest.approx(definition.center_mm)


def test_v43_active_former_web_profiles_are_manufacturable_and_pose_gate_is_plywood_only():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    assert all(row["valid"] for row in skeleton_profile_validity_report(config))
    rows = skeleton_assembly_report(config)
    assert all(row["result"] == "PASS" for row in rows)
    assert {row["step"][:2] for row in rows} >= {"S3", "S4"}
    # v4.2 gates all 12 plywood instances only; carbon saddle work is the
    # explicitly deferred next pass.
    assert all("LONGERON" not in moving for row in rows for moving in row["moving_instances"])
    assert skeleton_collision_report(config) == []


def test_v43_actual_solids_prove_material_tab_occupancy_attachment_and_bounded_receivers():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    rows = skeleton_joint_report(config)
    assert len(rows) == 30
    assert all(row["material_owner"] == row["web"] and row["receiver"] == row["former"] for row in rows)
    assert all(row["tab_volume_mm3"] > .01 and row["receiver_void_volume_mm3"] > .01 for row in rows)
    assert all(row["occupied_volume_mm3"] > .01 and row["occupancy_fraction"] > 0 for row in rows)
    assert all(row["tab_connected_to_parent"] and row["receiver_bounded"] and row["locating_face_count"] >= 3
               for row in rows)
    assert all(row["tab_root_width_mm"] >= 20 and row["minimum_residual_ligament_mm"] >= row["required_residual_ligament_mm"] for row in rows)


def test_v431_terminal_ligament_is_post_boolean_boundary_measurement_and_repair_is_real():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    rows = {row["joint_id"]: row for row in skeleton_joint_report(config)}
    for joint_id in ("SKEL-365-KEEL-L", "SKEL-365-KEEL-R"):
        row = rows[joint_id]
        assert row["terminal_boundary_ligament_mm"] == pytest.approx(6.5)
        assert row["terminal_boundary_witness_mm"] is not None
    # The same post-boolean edge algorithm catches the side-web leading root,
    # which was 1.5 mm before its local contour extension.
    for joint_id in ("SKEL--170-SIDE-L", "SKEL--170-SIDE-R"):
        assert rows[joint_id]["web_boundary_ligament_mm"] == pytest.approx(7.5)


def test_v431_post_boolean_boundary_regression_detects_the_old_half_mm_terminal_bridge():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    definition = next(joint for joint in joint_definitions(config) if joint.id == "SKEL-365-KEEL-L")
    part = next(part for part in laser_parts(config) if part.id == "FUS-KEEL-L")
    # Recreate only the rejected v4.3 terminal contour while retaining the
    # same generated joint reliefs.  The BRep-edge metric must see 0.5 mm;
    # this guards against a return to nominal/bounding-box report values.
    rejected = replace(part, outline_mm=((0.,0.),(845.,0.),(845.,52.),(0.,52.)))
    origin, plane = active_skeleton_placement_registry(config)["FUS-KEEL-L#1"]
    legacy_web = profile_solid(rejected, plane, origin).val()
    legacy_tab = legacy_web.intersect(joint_receiver_void_solid(config, definition).val())
    assert _web_boundary_ligament_mm(legacy_web, legacy_tab)[0] == pytest.approx(.5)


def test_v431_port_feature_midplanes_and_contacts_are_geometry_derived():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    rows = skeleton_joint_report(config)
    port = [row for row in rows if "SIDE-L" in row["joint_id"]]
    assert len(port) == 7
    assert all(row["occupancy_fraction"] == pytest.approx(1.0) for row in port)
    assert all(row["alignment_error_mm"] <= .01 and row["minimum_lateral_gap_mm"] <= .01 for row in port)
    assert all(row["locating_face_count"] >= 3 and row["minimum_locating_contact_area_mm2"] > 0 for row in rows)
    assert all(row["web_boundary_ligament_mm"] > 0 and row["receiver_boundary_ligament_mm"] > 0
               and row["web_boundary_witness_mm"] and row["receiver_boundary_witness_mm"] for row in rows)


def test_v431_active_placement_has_one_registry_and_legacy_view_derives_from_it():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    registry = active_skeleton_placement_registry(config)
    legacy = {instance.instance_id: (instance.origin_mm, instance.plane) for instance in part_instances(config)}
    assert set(registry) <= set(legacy)
    assert all(legacy[instance_id] == placement for instance_id, placement in registry.items())
    assert all(part_frame(config, instance_id).origin_mm == placement[0]
               for instance_id, placement in registry.items())


def test_v43_active_profiles_have_no_unintended_disconnected_solids():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    parts = {part.id: part for part in laser_parts(config)}
    for instance in active_skeleton_instances(config):
        solid = profile_solid(parts[instance.part_id], instance.plane, instance.origin_mm).val()
        assert len(solid.Solids()) == 1, instance.part_id


def test_v4_method_a_represents_actual_5y_by_3z_stock_and_isolated_collision_gate():
    config = load_aircraft_config(ROOT / "config" / "aircraft.yaml")
    active = active_skeleton_assembly(config)
    assert len(active_skeleton_part_ids(config)) == 12
    assert len(active_skeleton_instances(config)) == 12
    for name in ("FUS-LONGERON-LOWER-L", "FUS-LONGERON-LOWER-R", "FUS-LONGERON-UPPER-L", "FUS-LONGERON-UPPER-R"):
        box = active[name].val().BoundingBox()
        assert (box.ylen, box.zlen) == pytest.approx((5, 3))
    assert all(row["result"] == "PASS" for row in skeleton_assembly_report(config))
    assert not [row for row in skeleton_collision_report(config) if row["contact_id"] == "UNEXPLAINED"]
    supports = longeron_support_contract(config)
    assert all(row["largest_unsupported_gap_mm"] == 0 and row["insertion_compatible"] for row in supports.values())
    assert validate_skeleton_v4(config) == []
