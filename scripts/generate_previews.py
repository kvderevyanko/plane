#!/usr/bin/env python3
"""Generate disposable visual previews of the current CAD build artifacts.

This module is deliberately downstream-only: it reads CadQuery source geometry
and already-generated 2-D drawings, then writes files below ``generated/``.
It never reads a preview as an input and it never supplies aircraft parameters
to a generator.
"""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

import cadquery as cq
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from cad.common.calibration_coupon import make_solid
from cad.master_layout.model import MasterLayout, master_layout_from_config
from scripts.config import DEFAULT_CONFIG_PATH, load_aircraft_config
from scripts.hardware import DEFAULT_HARDWARE_PATH, load_hardware_config

if TYPE_CHECKING:
    from scripts.config import AircraftConfig


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SOURCE = ROOT / "generated"
DEFAULT_OUTPUT = DEFAULT_SOURCE / "previews"
VIEW_FILES = {
    "iso": "calibration_coupon_iso.png",
    "top": "calibration_coupon_top.png",
    "side": "calibration_coupon_side.png",
}
MASTER_LAYOUT_VIEW_FILES = {
    "master_layout_iso": "master_layout_iso.png",
    "master_layout_top": "master_layout_top.png",
    "master_layout_side": "master_layout_side.png",
}
DETAIL_FILES = {
    "Wing plan (SVG)": "panel_plan.svg",
    "Root rib (SVG)": "rib_00_root.svg",
    "Tip rib (SVG)": "rib_08_tip.svg",
}
TEST_DETAIL_FILES = {
    "Material & Structural Test Coupons — density template": "test_MAT-DENS-100.svg",
    "Material & Structural Test Coupons — spar EI cradle": "test_SPAR-EI-CRADLE-14.svg",
    "Material & Structural Test Coupons — D-box root rib": "test_DBOX-A-RIB-X000.svg",
    "Material & Structural Test Coupons — guarded socket fixture": "test_SOCKET-GUARDED-FIXTURE.svg",
}


def _mesh_faces(model: cq.Workplane) -> list[list[tuple[float, float, float]]]:
    vertices, triangles = model.val().tessellate(0.1)
    points = [vertex.toTuple() for vertex in vertices]
    return [[points[index] for index in triangle] for triangle in triangles]


def _render_view(model: cq.Workplane, destination: Path, *, elevation: float, azimuth: float) -> None:
    faces = _mesh_faces(model)
    figure = plt.figure(figsize=(8, 5), dpi=150)
    axis = figure.add_subplot(111, projection="3d")
    axis.add_collection3d(Poly3DCollection(faces, facecolor="#9cc9e8", edgecolor="#1e4d70", linewidth=0.25))

    xs = [point[0] for face in faces for point in face]
    ys = [point[1] for face in faces for point in face]
    zs = [point[2] for face in faces for point in face]
    span = max(max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs), 1.0)
    for setter, values in ((axis.set_xlim, xs), (axis.set_ylim, ys), (axis.set_zlim, zs)):
        centre = (min(values) + max(values)) / 2.0
        setter(centre - span / 2.0, centre + span / 2.0)
    axis.set_box_aspect((1.0, 1.0, 0.25))
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_axis_off()
    figure.tight_layout(pad=0)
    figure.savefig(destination, transparent=False, bbox_inches="tight", pad_inches=0.02)
    plt.close(figure)


def _render_master_layout_view(layout: MasterLayout, destination: Path, *, elevation: float, azimuth: float) -> None:
    """Render reference geometry plus coordinate/MAC/optional-CG annotations."""
    figure = plt.figure(figsize=(9, 5.5), dpi=150)
    axis = figure.add_subplot(111, projection="3d")
    models = (
        (layout.wing, "#b9d8ee", "#1e4d70"),
        (layout.horizontal_tail, "#e5c07b", "#7b5e00"),
        (layout.elevator, "#e07a16", "#8b3b00"),
        (layout.vertical_fins, "#e5c07b", "#7b5e00"),
        (layout.rudders, "#e07a16", "#8b3b00"),
        (layout.battery_travel_envelope, "#f6d55c", "#8f6d00"),
        (layout.battery_envelope, "#ed553b", "#8b2e20"),
        (layout.motor_envelope, "#8ecae6", "#1d5f73"),
        (layout.esc_envelope, "#83c5be", "#276b68"),
    )
    faces_by_model = []
    for model, fill, edge in models:
        if model is None:
            continue
        model_faces = _mesh_faces(model)
        faces_by_model.extend(model_faces)
        axis.add_collection3d(Poly3DCollection(model_faces, facecolor=fill, edgecolor=edge, linewidth=0.25))

    for disk in layout.propeller_disks:
        disk_faces = _mesh_faces(disk)
        faces_by_model.extend(disk_faces)
        axis.add_collection3d(Poly3DCollection(disk_faces, facecolor="#a7c957", edgecolor="#386641", linewidth=0.25, alpha=.30))
    for component_id, envelope in layout.avionics_envelopes:
        component_faces = _mesh_faces(envelope)
        faces_by_model.extend(component_faces)
        axis.add_collection3d(Poly3DCollection(component_faces, facecolor="#bdb2ff", edgecolor="#5a4b9a", linewidth=0.25, alpha=.72))
        box = envelope.val().BoundingBox()
        axis.text((box.xmin + box.xmax) / 2.0, (box.ymin + box.ymax) / 2.0, box.zmax + 5.0, component_id, color="#41356d", fontsize=6)

    for component_id, envelope in layout.selected_hardware_envelopes:
        component_faces = _mesh_faces(envelope)
        faces_by_model.extend(component_faces)
        axis.add_collection3d(Poly3DCollection(component_faces, facecolor="#70c1b3", edgecolor="#176b5d", linewidth=.35, alpha=.78))
        box = envelope.val().BoundingBox()
        axis.text((box.xmin + box.xmax) / 2.0, (box.ymin + box.ymax) / 2.0, box.zmax + 5.0, component_id, color="#145447", fontsize=6)
    if layout.selected_propeller_disk is not None:
        prop_faces = _mesh_faces(layout.selected_propeller_disk)
        faces_by_model.extend(prop_faces)
        axis.add_collection3d(Poly3DCollection(prop_faces, facecolor="#4d908e", edgecolor="#1f5d5b", linewidth=.4, alpha=.42))
    for keepout_id, envelope in layout.antenna_keepout_envelopes:
        keepout_faces = _mesh_faces(envelope)
        faces_by_model.extend(keepout_faces)
        axis.add_collection3d(Poly3DCollection(keepout_faces, facecolor="#f9c74f", edgecolor="#a15c00", linewidth=.25, alpha=.10))
        box = envelope.val().BoundingBox()
        axis.text((box.xmin + box.xmax) / 2.0, (box.ymin + box.ymax) / 2.0, box.zmax + 5.0, keepout_id, color="#8d5200", fontsize=6)

    xs = [point[0] for face in faces_by_model for point in face]
    ys = [point[1] for face in faces_by_model for point in face]
    zs = [point[2] for face in faces_by_model for point in face]
    axis.plot([0, 180], [0, 0], [0, 0], color="#d22", linewidth=2)
    axis.plot([0, 0], [0, 180], [0, 0], color="#287b2d", linewidth=2)
    axis.plot([0, 0], [0, 0], [0, 100], color="#2456b5", linewidth=2)
    axis.scatter([0], [0], [0], color="#111", s=20)

    mac_x0, mac_x1 = layout.mac_leading_edge_x_mm, layout.mac_leading_edge_x_mm + layout.mac_mm
    axis.plot([mac_x0, mac_x1], [0, 0], [4, 4], color="#6a3d9a", linewidth=3)
    if layout.cg_x_range_mm is not None:
        low, high = layout.cg_x_range_mm
        axis.plot([low, high], [0, 0], [8, 8], color="#e07a16", linewidth=6, alpha=0.75)
    if layout.first_flight_cg_x_mm is not None:
        axis.scatter([layout.first_flight_cg_x_mm], [0], [12], color="#5b2c83", marker="D", s=32, depthshade=False)
    for start, end in layout.boom_axis_segments:
        axis.plot([start[0], end[0]], [start[1], end[1]], [start[2], end[2]], color="#536878", linestyle="--", linewidth=1.5)
    if layout.high_current_route:
        route_x, route_y, route_z = zip(*layout.high_current_route, strict=True)
        axis.plot(route_x, route_y, route_z, color="#c1121f", linestyle="-.", linewidth=2.0)
    for component_id, x_mm, y_mm, z_mm in layout.known_mass_items:
        axis.scatter([x_mm], [y_mm], [z_mm], color="#b3261e", s=28, depthshade=False)
        axis.text(x_mm, y_mm, z_mm + 8, component_id, color="#7f1712", fontsize=7)

    all_zs = zs + [0, 100]
    x_margin, y_margin, z_margin = 100.0, 80.0, 20.0
    axis.set_xlim(min(xs) - x_margin, max(xs) + x_margin)
    axis.set_ylim(min(ys) - y_margin, max(ys) + y_margin)
    axis.set_zlim(min(all_zs) - z_margin, max(all_zs) + z_margin)
    axis.set_box_aspect((max(xs) - min(xs) + 2 * x_margin,
                         max(ys) - min(ys) + 2 * y_margin,
                         max(all_zs) - min(all_zs) + 2 * z_margin))
    axis.view_init(elev=elevation, azim=azimuth)
    axis.set_axis_off()
    cg_note = "CG band: not defined (TBD)" if layout.cg_x_range_mm is None else "CG band: initial design assumption"
    tail_note = "Tail/boom axes: preliminary design assumption" if layout.horizontal_tail is not None else "Tail/boom axes: TBD"
    first_flight_note = "First-flight marker: preliminary only" if layout.first_flight_cg_x_mm is not None else "First-flight marker: TBD"
    packaging_note = "Typed packaging envelopes: preliminary design assumptions" if (layout.motor_envelope or layout.esc_envelope or layout.battery_envelope or layout.avionics_envelopes) else "Packaging envelopes: TBD"
    hardware_note = "Commercial hardware: selected preliminary envelopes; bench/installation validation required" if layout.selected_hardware_envelopes else "Commercial hardware envelopes: not loaded"
    battery_note = "Battery removal/hatch clearance: NOT validated (CG/mass-moment closure blocked)"
    figure.text(0.02, 0.02, f"Datum: root leading edge | +X aft (red), +Y right (green), +Z up (blue)\nMAC: {layout.mac_mm:.3f} mm | {cg_note}\n{tail_note} | {first_flight_note}\n{packaging_note}\n{hardware_note}\n{battery_note}", fontsize=8)
    figure.tight_layout(pad=0)
    figure.savefig(destination, transparent=False, bbox_inches="tight", pad_inches=0.02)
    plt.close(figure)


def generate_master_layout_previews(config: "AircraftConfig", output: Path) -> dict[str, Path]:
    """Write the three disposable views of the reference-only master layout."""
    hardware = load_hardware_config(DEFAULT_HARDWARE_PATH) if DEFAULT_HARDWARE_PATH.is_file() else None
    layout = master_layout_from_config(config, hardware)
    for name, elevation, azimuth in (("master_layout_iso", 25, -55), ("master_layout_top", 90, -90), ("master_layout_side", 0, -90)):
        _render_master_layout_view(layout, output / MASTER_LAYOUT_VIEW_FILES[name], elevation=elevation, azimuth=azimuth)
    return {name: output / filename for name, filename in MASTER_LAYOUT_VIEW_FILES.items()}


def _write_index(destination: Path) -> Path:
    cards = [
        ("Master layout — isometric", MASTER_LAYOUT_VIEW_FILES["master_layout_iso"]),
        ("Master layout — top", MASTER_LAYOUT_VIEW_FILES["master_layout_top"]),
        ("Master layout — side", MASTER_LAYOUT_VIEW_FILES["master_layout_side"]),
        ("Calibration coupon — isometric", VIEW_FILES["iso"]),
        ("Calibration coupon — top", VIEW_FILES["top"]),
        ("Calibration coupon — side", VIEW_FILES["side"]),
        *DETAIL_FILES.items(),
    ]
    test_cards = list(TEST_DETAIL_FILES.items())
    items = "\n".join(
        f'    <figure><a href="{filename}"><img src="{filename}" alt="{title}"></a><figcaption>{title}</figcaption></figure>'
        for title, filename in cards
    )
    index = destination / "index.html"
    test_items = "\n".join(
        f'    <figure><a href="{filename}"><img src="{filename}" alt="{title}"></a><figcaption>{title}</figcaption></figure>'
        for title, filename in test_cards
    )
    index.write_text(
        """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>LR1600 generated CAD previews</title>
<style>body{font-family:system-ui,sans-serif;margin:2rem;background:#f7f9fb;color:#16212b}main{max-width:1200px;margin:auto}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:1.25rem}figure{margin:0;background:white;border:1px solid #d9e1e8;border-radius:.5rem;padding:.75rem;box-shadow:0 1px 2px #0001}img{display:block;width:100%;height:220px;object-fit:contain;background:#fff}figcaption{margin-top:.6rem;font-weight:600}p{max-width:70ch}</style>
</head><body><main><h1>LR1600 generated CAD previews</h1><p>Disposable build artifacts for visual inspection only. Aircraft geometry and parameters remain defined by source files and <code>config/aircraft.yaml</code>.</p><section class="grid">
"""
        + items
        + "\n</section><h2>Material &amp; Structural Test Coupons</h2><p>TEST-ONLY, nominal, no-kerf geometry. These are not flight or production parts.</p><section class=\"grid\">\n"
        + test_items + "\n</section></main></body></html>\n",
        encoding="utf-8",
    )
    return index


def generate_previews(source: Path = DEFAULT_SOURCE, output: Path = DEFAULT_OUTPUT,
                      config_path: Path = DEFAULT_CONFIG_PATH) -> dict[str, Path]:
    """Render coupon views and copy current 2-D inspection drawings to a gallery."""
    output.mkdir(parents=True, exist_ok=True)
    for stale in [*VIEW_FILES.values(), *MASTER_LAYOUT_VIEW_FILES.values(), *DETAIL_FILES.values(), *TEST_DETAIL_FILES.values(), "index.html"]:
        (output / stale).unlink(missing_ok=True)

    master_layout_paths = generate_master_layout_previews(load_aircraft_config(config_path), output)
    model = make_solid()
    _render_view(model, output / VIEW_FILES["iso"], elevation=25, azimuth=-55)
    _render_view(model, output / VIEW_FILES["top"], elevation=90, azimuth=-90)
    _render_view(model, output / VIEW_FILES["side"], elevation=0, azimuth=-90)
    for filename in DETAIL_FILES.values():
        origin = source / filename
        if not origin.is_file():
            raise FileNotFoundError(f"Missing current generated drawing: {origin}")
        shutil.copyfile(origin, output / filename)
    for preview_name in TEST_DETAIL_FILES.values():
        origin = source / "test_coupons" / preview_name.removeprefix("test_")
        if not origin.is_file():
            raise FileNotFoundError(f"Missing current generated test drawing: {origin}")
        shutil.copyfile(origin, output / preview_name)
    index = _write_index(output)
    paths = {name: output / filename for name, filename in VIEW_FILES.items()}
    paths.update(master_layout_paths)
    paths.update({filename: output / filename for filename in DETAIL_FILES.values()})
    paths.update({filename: output / filename for filename in TEST_DETAIL_FILES.values()})
    paths["index"] = index
    if not all(path.is_file() and path.stat().st_size > 0 for path in paths.values()):
        raise RuntimeError("Preview generation produced an empty artifact")
    return paths


if __name__ == "__main__":
    paths = generate_previews()
    print(f"Generated {len(paths)} CAD previews in {DEFAULT_OUTPUT}")
