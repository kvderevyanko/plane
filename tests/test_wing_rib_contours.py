"""Regression checks for the laser-cut manufacturing rib contours."""

import math
from pathlib import Path

import pytest

from scripts.config import load_aircraft_config
from scripts.generate_wing import (
    airfoil_at_chord,
    chord_at,
    generate,
    rib_contour,
    rib_stations,
    signed_area,
    washout_at,
    wing_parameters_from_config,
)


ROOT = Path(__file__).resolve().parents[1]
CONFIG = ROOT / "config" / "aircraft.yaml"


def _cross(a: tuple[float, float], b: tuple[float, float]) -> float:
    return a[0] * b[1] - a[1] * b[0]


def _proper_intersection(a, b, c, d) -> bool:
    """Whether two non-adjacent contour segments cross away from endpoints."""
    r = (b[0] - a[0], b[1] - a[1])
    s = (d[0] - c[0], d[1] - c[1])
    denominator = _cross(r, s)
    if abs(denominator) < 1e-10:
        return False
    q_minus_p = (c[0] - a[0], c[1] - a[1])
    t = _cross(q_minus_p, s) / denominator
    u = _cross(q_minus_p, r) / denominator
    return 1e-8 < t < 1.0 - 1e-8 and 1e-8 < u < 1.0 - 1e-8


def _has_self_intersection(contour: list[tuple[float, float]]) -> bool:
    count = len(contour)
    for i in range(count):
        for j in range(i + 1, count):
            # Neighbours (including the implicit final-to-first edge) share a
            # vertex by design and are not crossings.
            if j in (i, (i + 1) % count, (i - 1) % count):
                continue
            if _proper_intersection(contour[i], contour[(i + 1) % count],
                                    contour[j], contour[(j + 1) % count]):
                return True
    return False


@pytest.fixture(scope="module")
def parameters():
    return wing_parameters_from_config(load_aircraft_config(CONFIG))


def test_all_rib_manufacturing_contours_are_closed_simple_and_within_te_boundary(parameters):
    for station in rib_stations(parameters):
        contour = rib_contour(station, parameters)
        theoretical = airfoil_at_chord(
            chord_at(station, parameters), washout_at(station, parameters), parameters,
        )

        assert len(contour) >= 3
        assert abs(signed_area(contour)) > 1.0
        assert not _has_self_intersection(contour)
        # The theoretical profile's aft-most x is the admissible TE boundary.
        assert max(x for x, _ in contour) <= max(x for x, _ in theoretical) + 1e-9


@pytest.mark.parametrize("station", [0.0, 800.0], ids=["R00-root", "R08-tip"])
def test_sharp_te_has_one_closure_point_not_a_hairpin(parameters, station):
    contour = rib_contour(station, parameters)
    trailing_edge = contour[0]

    # The two inset skins are trimmed to their intersection.  Thus their sole
    # aft-most point is the explicit closure point, rather than a short return
    # segment plus a second offset endpoint (the old parasitic tail).
    assert trailing_edge[0] == pytest.approx(max(x for x, _ in contour))
    assert sum(math.isclose(point[0], trailing_edge[0], abs_tol=1e-7)
               for point in contour) == 1
    assert contour[1][0] < trailing_edge[0] - 1.0
    assert contour[-1][0] < trailing_edge[0] - 1.0


def test_rib_exports_keep_closed_polyline_spar_hole_and_typed_parameters(tmp_path, parameters):
    output = tmp_path / "generated"
    generate(CONFIG, output)

    for filename in ("rib_00_root.dxf", "rib_08_tip.dxf"):
        document = (output / filename).read_text(encoding="ascii")
        assert "LWPOLYLINE\n8\nCUT\n" in document
        assert "70\n1\n" in document
        # Ø14.50: 14-mm OD plus the configured 0.25-mm radial clearance.
        assert "CIRCLE\n8\nCUT\n" in document
        assert "40\n7.25000\n" in document

    manifest = (output / "rib_manifest.csv").read_text(encoding="utf-8")
    assert "R00,0.000,250.000,-0.0000" in manifest
    assert "R08,800.000,200.000,-1.5000" in manifest
    assert parameters.spar_fraction == pytest.approx(0.30)
    assert parameters.skin_thickness_mm == pytest.approx(3.0)
