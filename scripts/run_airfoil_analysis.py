#!/usr/bin/env python3
"""Reproducible XFOIL analysis for the LR1600 Clark Y wing.

``config/aircraft.yaml`` is the only aircraft-input source.  This program
does not read CAD outputs or generated snapshots as inputs.  XFOIL results are
viscous, two-dimensional estimates; its non-converged post-stall region is
preserved as missing data rather than fabricated by interpolation.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import tempfile
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

try:  # Supports both `python scripts/run_airfoil_analysis.py` and pytest imports.
    from config import DEFAULT_CONFIG_PATH, AircraftConfig, load_aircraft_config
except ImportError:
    from scripts.config import DEFAULT_CONFIG_PATH, AircraftConfig, load_aircraft_config

ROOT = Path(__file__).resolve().parents[1]
AIRFOIL = ROOT / "data/airfoils/clarky.dat"
DEFAULT_XFOIL = ROOT / ".tools/apps/xfoil/usr/bin/xfoil"
RHO = 1.225  # kg/m³, ISA sea level
MU = 1.789e-5  # Pa s, ISA sea level
RE_CASES = (120000, 150000, 200000, 214862, 300000, 430000, 480000)
NCRIT_CASES = {"clean": 9.0, "realistic_model": 5.0}
ALPHA_START, ALPHA_END, ALPHA_STEP = -6.0, 18.0, 0.25
RAW_ARTIFACT_NAME = re.compile(r"clarky_re\d+_(?:clean|realistic_model)(?:_reverse)?\.(?:in|log|polar)$")


def cleanup_raw_side_artifacts(output: Path) -> None:
    """Remove stale XFOIL side files; retain only documented raw artifacts."""
    raw = output / "raw"
    if not raw.exists():
        return
    for path in raw.iterdir():
        if path.is_file() and path.name != "clarky.xfoil.dat" and not RAW_ARTIFACT_NAME.fullmatch(path.name):
            path.unlink()


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_airfoil_coordinates(path: Path = AIRFOIL) -> list[tuple[float, float]]:
    """Read UIUC DAT coordinates, skipping its optional point-count line."""
    coordinates: list[tuple[float, float]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if len(fields) != 2:
            continue
        try:
            x, z = map(float, fields)
        except ValueError:
            continue
        # UIUC's ``61 61`` line is metadata, not a normalized coordinate.
        if 0.0 <= x <= 1.0 and -0.5 <= z <= 0.5:
            coordinates.append((x, z))
    if len(coordinates) < 20 or min(x for x, _ in coordinates) > 1e-9:
        raise ValueError(f"{path} is not a plausible normalized airfoil DAT")
    return coordinates


def materialize_xfoil_coordinates(output: Path) -> Path:
    """Create an XFOIL-safe derivative without UIUC's ``61 61`` metadata.

    The downloaded source DAT remains immutable.  This small generated file is
    necessary because XFOIL 6.99 treats that UIUC count line as a coordinate.
    """
    target = output / "raw" / "clarky.xfoil.dat"
    target.parent.mkdir(parents=True, exist_ok=True)
    coordinates = load_airfoil_coordinates(AIRFOIL)
    # UIUC lists both surfaces LE→TE; XFOIL needs upper TE→LE then lower LE→TE.
    le_repeat = next(index for index, point in enumerate(coordinates[1:], 1) if abs(point[0]) < 1e-12 and abs(point[1]) < 1e-12)
    xfoil_order = list(reversed(coordinates[:le_repeat])) + coordinates[le_repeat:]
    target.write_text("Clark Y generated XFOIL input; source clarky.dat unchanged\n" + "\n".join(
        f"{x:.7f} {z:.7f}" for x, z in xfoil_order
    ) + "\n", encoding="utf-8")
    return target


def reynolds_number(speed_m_s: float, chord_m: float, rho: float = RHO, mu: float = MU) -> float:
    if speed_m_s <= 0 or chord_m <= 0 or rho <= 0 or mu <= 0:
        raise ValueError("speed, chord, density, and viscosity must be positive")
    return rho * speed_m_s * chord_m / mu


def required_cl(mass_kg: float, speed_m_s: float, area_m2: float, gravity: float) -> float:
    if min(mass_kg, speed_m_s, area_m2, gravity) <= 0:
        raise ValueError("mass, speed, area, and gravity must be positive")
    return mass_kg * gravity / (0.5 * RHO * speed_m_s**2 * area_m2)


def stall_speed_m_s(mass_kg: float, area_m2: float, clmax_wing: float, gravity: float) -> float:
    if min(mass_kg, area_m2, clmax_wing, gravity) <= 0:
        raise ValueError("mass, area, CLmax, and gravity must be positive")
    return math.sqrt(2 * mass_kg * gravity / (RHO * area_m2 * clmax_wing))


def xfoil_banner(binary: Path) -> str:
    result = subprocess.run([str(binary)], input="QUIT\n", text=True, capture_output=True, check=False, timeout=20)
    match = re.search(r"XFOIL Version[^\n]*", result.stdout)
    return match.group(0).strip() if match else "XFOIL banner unavailable"


def xfoil_input(airfoil: Path, polar: Path, reynolds: int, ncrit: float, alpha_start: float = ALPHA_START, alpha_end: float = ALPHA_END, alpha_step: float = ALPHA_STEP) -> str:
    return "\n".join((
        f"LOAD {airfoil}", "PANE", "OPER", f"VISC {reynolds}", "VPAR", f"N {ncrit:g}", "", "ITER 200",
        "PACC", polar.name, "", f"ASEQ {alpha_start:g} {alpha_end:g} {alpha_step:g}", "PACC", "", "QUIT", "",
    ))


def parse_polar(path: Path) -> list[dict[str, float]]:
    rows: list[dict[str, float]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        values = line.split()
        if len(values) < 7:
            continue
        try:
            alpha, cl, cd, cdp, cm, xtr_top, xtr_bottom = map(float, values[:7])
        except ValueError:
            continue
        rows.append(dict(alpha_deg=alpha, cl=cl, cd=cd, cdp=cdp, cm=cm, xtr_top=xtr_top, xtr_bottom=xtr_bottom))
    return rows


def run_case(binary: Path, out: Path, xfoil_airfoil: Path, reynolds: int, scenario: str, ncrit: float, reuse_raw: bool = False, sweep: str = "forward") -> dict[str, Any]:
    stem = f"clarky_re{reynolds}_{scenario}" + ("" if sweep == "forward" else f"_{sweep}")
    raw, log, command = out / "raw" / f"{stem}.polar", out / "raw" / f"{stem}.log", out / "raw" / f"{stem}.in"
    parsed = out / "parsed" / f"{stem}.csv"
    raw.parent.mkdir(parents=True, exist_ok=True); parsed.parent.mkdir(parents=True, exist_ok=True)
    # Avoid XFOIL's interactive "use old polar parameters" prompt on reruns.
    if reuse_raw and raw.exists():
        result = subprocess.CompletedProcess([], 0, "", "")
    else:
        raw.unlink(missing_ok=True)
        alpha_start, alpha_end, alpha_step = (ALPHA_START, ALPHA_END, ALPHA_STEP) if sweep == "forward" else (ALPHA_END, ALPHA_START, -ALPHA_STEP)
        command.write_text(xfoil_input(xfoil_airfoil, raw, reynolds, ncrit, alpha_start, alpha_end, alpha_step), encoding="utf-8")
        # XFOIL 6.99 truncates PACC paths to a short Fortran filename field
        # and may emit auxiliary files.  Isolate those in a temp dir; retain
        # only the named PACC polar, recorded input and log in the repository.
        with tempfile.TemporaryDirectory(prefix="lr1600-xfoil-") as temp:
            result = subprocess.run([str(binary)], input=command.read_text(encoding="utf-8"), text=True,
                                    capture_output=True, cwd=temp, check=False, timeout=180)
            produced = Path(temp) / raw.name
            if produced.exists(): shutil.copy2(produced, raw)
        log.write_text(result.stdout + "\n--- STDERR ---\n" + result.stderr, encoding="utf-8")
    if not raw.exists():
        raw.write_text("# XFOIL did not create a polar file\n", encoding="utf-8")
    rows = parse_polar(raw)
    with parsed.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["alpha_deg", "cl", "cd", "cdp", "cm", "xtr_top", "xtr_bottom", "source"], lineterminator="\n")
        writer.writeheader(); writer.writerows([{**row, "source": sweep} for row in rows])
    requested = np.arange(ALPHA_START, ALPHA_END + ALPHA_STEP / 2, ALPHA_STEP)
    present = {round(row["alpha_deg"], 3) for row in rows}
    missing = [round(float(alpha), 3) for alpha in requested if round(float(alpha), 3) not in present]
    warnings = []
    if result.returncode:
        warnings.append(f"XFOIL exit code {result.returncode}")
    if missing:
        warnings.append(f"{len(missing)} requested alpha points absent; no values inferred")
    if not rows:
        warnings.append("no converged polar points")
    metrics: dict[str, Any] = {"points": len(rows), "missing_alpha_deg": missing, "last_converged_alpha_deg": max((r["alpha_deg"] for r in rows), default=None), "warnings": warnings}
    if rows:
        best_ld = max(rows, key=lambda r: r["cl"] / r["cd"] if r["cd"] > 0 else -math.inf)
        cdmin = min(rows, key=lambda r: r["cd"])
        clmax = max(rows, key=lambda r: r["cl"])
        metrics.update({
            "clmax_2d_converged": clmax["cl"], "clmax_alpha_deg": clmax["alpha_deg"],
            "clmax_is_lower_bound": clmax["alpha_deg"] >= metrics["last_converged_alpha_deg"],
            "cdmin": cdmin["cd"], "cdmin_alpha_deg": cdmin["alpha_deg"],
            "best_ld": best_ld["cl"] / best_ld["cd"], "best_ld_cl": best_ld["cl"], "best_ld_alpha_deg": best_ld["alpha_deg"],
            "best_ld_cm": best_ld["cm"],
        })
        reliable = reliable_pre_peak_rows(rows)
        if reliable:
            peak = reliable[-1]
            metrics.update({"reliable_pre_peak_clmax": peak["cl"], "reliable_pre_peak_alpha_deg": peak["alpha_deg"],
                            "post_peak_points_excluded_from_stall": len(rows) - len(reliable)})
    return {"reynolds": reynolds, "scenario": scenario, "ncrit": ncrit, "sweep": sweep, "raw_polar": str(raw.relative_to(ROOT)),
            "input": str(command.relative_to(ROOT)), "log": str(log.relative_to(ROOT)), "parsed_csv": str(parsed.relative_to(ROOT)), "metrics": metrics, "rows": rows}


def merge_direct_sweeps(forward: dict[str, Any], reverse: dict[str, Any], out: Path) -> dict[str, Any]:
    """Merge actual PACC rows only; forward wins duplicates, reverse fills gaps."""
    rows: dict[float, dict[str, Any]] = {}
    for source_case in (reverse, forward):
        for row in source_case["rows"]:
            rows[round(row["alpha_deg"], 3)] = {**row, "source": source_case["sweep"]}
    combined = [rows[key] for key in sorted(rows)]
    stem = f"clarky_re{forward['reynolds']}_{forward['scenario']}_combined"
    parsed = out / "parsed" / f"{stem}.csv"
    parsed.parent.mkdir(parents=True, exist_ok=True)
    with parsed.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["alpha_deg", "cl", "cd", "cdp", "cm", "xtr_top", "xtr_bottom", "source"], lineterminator="\n")
        writer.writeheader(); writer.writerows(combined)
    merged = dict(forward)
    parsed_reference = str(parsed.relative_to(ROOT)) if parsed.is_relative_to(ROOT) else str(parsed)
    merged.update({"sweep": "combined_direct", "rows": combined, "parsed_csv": parsed_reference,
                   "source_raw_polars": [forward["raw_polar"], reverse["raw_polar"]],
                   "source_inputs": [forward["input"], reverse["input"]], "source_logs": [forward["log"], reverse["log"]]})
    # Metrics below are for the combined direct evidence; forward-only metrics
    # remain explicitly available for audit rather than being silently reused.
    merged["forward_metrics"] = forward["metrics"]
    merged["metrics"] = metrics_for_rows(combined, ALPHA_START, ALPHA_END, ALPHA_STEP)
    merged["metrics"].update(combined_direct_points=len(combined), reverse_only_points=sum(1 for row in combined if row["source"] == "reverse"))
    return merged


def reliable_pre_peak_rows(rows: list[dict[str, float]]) -> list[dict[str, float]]:
    """Return only the initial attached-flow branch through its first CL peak.

    XFOIL's post-peak continuation can be numerically plausible-looking but is
    not a defensible section-stall model.  Repeated alpha records are reduced
    to their last solved value, and every record after the first observed
    maximum is excluded from the 3D/stall calculation.
    """
    unique = {row["alpha_deg"]: row for row in rows}
    ordered = [unique[key] for key in sorted(unique)]
    if not ordered:
        return []
    peak_index = max(range(len(ordered)), key=lambda index: ordered[index]["cl"])
    return ordered[:peak_index + 1]


def metrics_for_rows(rows: list[dict[str, float]], alpha_start: float, alpha_end: float, alpha_step: float) -> dict[str, Any]:
    """Recompute all reported metrics from exactly the supplied direct rows."""
    requested = np.arange(alpha_start, alpha_end + alpha_step / 2, alpha_step)
    present = {round(row["alpha_deg"], 3) for row in rows}
    metrics: dict[str, Any] = {"points": len(rows), "missing_alpha_deg": [round(float(a), 3) for a in requested if round(float(a), 3) not in present],
                               "last_converged_alpha_deg": max((r["alpha_deg"] for r in rows), default=None), "warnings": []}
    if rows:
        clmax, cdmin = max(rows, key=lambda r: r["cl"]), min(rows, key=lambda r: r["cd"])
        best = max(rows, key=lambda r: r["cl"] / r["cd"] if r["cd"] > 0 else -math.inf)
        reliable = reliable_pre_peak_rows(rows)
        metrics.update({"clmax_2d_converged":clmax["cl"], "clmax_alpha_deg":clmax["alpha_deg"], "clmax_is_lower_bound":clmax["alpha_deg"] >= metrics["last_converged_alpha_deg"],
                        "cdmin":cdmin["cd"], "cdmin_alpha_deg":cdmin["alpha_deg"], "best_ld":best["cl"]/best["cd"], "best_ld_cl":best["cl"], "best_ld_alpha_deg":best["alpha_deg"], "best_ld_cm":best["cm"],
                        "reliable_pre_peak_clmax":reliable[-1]["cl"] if reliable else None, "reliable_pre_peak_alpha_deg":reliable[-1]["alpha_deg"] if reliable else None,
                        "post_peak_points_excluded_from_stall":len(rows)-len(reliable)})
    return metrics


def _curve_at_alpha(rows: list[dict[str, float]], alpha: float) -> tuple[float, float] | None:
    rows = reliable_pre_peak_rows(rows)
    for a, b in zip(rows, rows[1:]):
        if a["alpha_deg"] <= alpha <= b["alpha_deg"] and b["alpha_deg"] - a["alpha_deg"] <= 0.26:
            ratio = (alpha - a["alpha_deg"]) / (b["alpha_deg"] - a["alpha_deg"])
            return (a["cl"] + ratio * (b["cl"] - a["cl"]), a["cd"] + ratio * (b["cd"] - a["cd"]))
    return None


def section_polar_at_reynolds(cases: list[dict[str, Any]], local_re: float, alpha: float) -> tuple[float, float] | None:
    """Interpolate only between bracketing, reliable pre-peak polar branches."""
    ordered = sorted(cases, key=lambda case: case["reynolds"])
    lower = [case for case in ordered if case["reynolds"] <= local_re]
    upper = [case for case in ordered if case["reynolds"] >= local_re]
    lo, hi = (lower[-1] if lower else None), (upper[0] if upper else None)
    if lo is None or hi is None:
        candidate = lo or hi
        if candidate is None or abs(candidate["reynolds"] - local_re) / local_re > .20: return None
        return _curve_at_alpha(candidate["rows"], alpha)
    lo_value, hi_value = _curve_at_alpha(lo["rows"], alpha), _curve_at_alpha(hi["rows"], alpha)
    if lo_value is None or hi_value is None: return None
    if lo["reynolds"] == hi["reynolds"]: return lo_value
    fraction = math.log(local_re / lo["reynolds"]) / math.log(hi["reynolds"] / lo["reynolds"])
    return tuple(a + fraction * (b - a) for a, b in zip(lo_value, hi_value))


def wing_curve_at_speed(config: AircraftConfig, cases: list[dict[str, Any]], scenario: str, oswald_e: float, speed_m_s: float) -> list[dict[str, float]]:
    """Conservative lifting-line-style estimate, deliberately with no flaperon credit.

    A station only contributes if a same-scenario polar can support its local
    Re (nearest analysed Re within 20%) and requested effective angle.  The
    model stops at the first unsupported angle; it never extrapolates a polar.
    """
    """Compute area-weighted finite-wing points at a stated true airspeed."""
    wing = config.wing
    available = [c for c in cases if c["scenario"] == scenario and c["rows"]]
    samples = []
    # 1° is adequate for the deliberately approximate 3D lifting-line sweep;
    # the raw 2D polar retains its requested 0.25° resolution.
    for alpha in np.arange(-2.0, 18.01, 1.0):
        # A simple fixed-point induced angle iteration at 40 semi-span stations.
        clwing = 0.0
        for _ in range(6):
            induced = math.degrees(clwing / (math.pi * (wing.span_mm / 1000)**2 / wing.area_m2 * oswald_e))
            weighted_cl, weighted_cd, area_weights, unsupported = [], [], [], False
            for fraction in (np.arange(40) + .5) / 40:
                chord_mm = wing.root_chord_mm + (wing.tip_chord_mm - wing.root_chord_mm) * fraction
                twist = wing.washout_deg * fraction
                local_re = reynolds_number(speed_m_s, chord_mm / 1000)
                value = section_polar_at_reynolds(available, local_re, float(alpha + twist - induced))
                if value is None:
                    unsupported = True; break
                area_weights.append(chord_mm); weighted_cl.append(value[0] * chord_mm); weighted_cd.append(value[1] * chord_mm)
            if unsupported: break
            candidate = float(sum(weighted_cl) / sum(area_weights))
            if abs(candidate - clwing) < 1e-4: break
            clwing = .6 * clwing + .4 * candidate
        if not unsupported:
            samples.append({"alpha_deg": float(alpha), "cl": clwing, "profile_cd_area_weighted": float(sum(weighted_cd) / sum(area_weights))})
    return samples


def solve_wing_stall(config: AircraftConfig, cases: list[dict[str, Any]], scenario: str, oswald_e: float, margin: float, mass_kg: float,
                     curve_cache: dict[float, list[dict[str, float]]] | None = None) -> dict[str, Any]:
    """Find the first supported 1g condition using only pre-peak section data."""
    wing, aircraft = config.wing, config.aircraft
    previous: tuple[float, float, dict[str, Any]] | None = None
    curve_cache = curve_cache if curve_cache is not None else {}
    def curve(speed: float) -> list[dict[str, float]]:
        key = round(speed, 6)
        if key not in curve_cache:
            curve_cache[key] = wing_curve_at_speed(config, cases, scenario, oswald_e, speed)
        return curve_cache[key]
    for speed in np.arange(7.5, 16.01, .5):
        samples = curve(float(speed))
        if not samples:
            continue
        if max(sample["alpha_deg"] for sample in samples) < 8.0:
            return {"unsupported": True, "reason": "Reliable pre-peak polar coverage ends below 8° effective wing alpha; insufficient to establish CLmax without interpolation."}
        positive_alphas = [sample["alpha_deg"] for sample in samples if sample["alpha_deg"] >= 0]
        if any(b - a > 1.01 for a, b in zip(positive_alphas, positive_alphas[1:])):
            return {"unsupported": True, "reason": "Direct polar coverage has an internal pre-peak alpha gap; no interpolation was used to bridge it."}
        maximum = max(samples, key=lambda sample: sample["cl"])
        usable = maximum["cl"] * margin
        residual = usable - required_cl(mass_kg, float(speed), wing.area_m2, aircraft.gravity_m_s2)
        if previous and previous[1] < 0 and max(sample["alpha_deg"] for sample in samples) < previous[2]["alpha_deg"] - 1.0:
            return {"unsupported": True, "reason": "Reliable pre-peak polar coverage collapses before a 1g stall root; no post-peak or gap interpolation was used."}
        current = (float(speed), residual, maximum)
        if previous and previous[1] < 0 <= residual:
            lo, hi = previous[0], float(speed)
            # Bisection solves V with its own local Re, rather than assuming 70 km/h.
            for _ in range(10):
                mid = (lo + hi) / 2
                mid_samples = curve(mid)
                if not mid_samples: lo = mid; continue
                mid_max = max(mid_samples, key=lambda sample: sample["cl"])
                mid_residual = mid_max["cl"] * margin - required_cl(mass_kg, mid, wing.area_m2, aircraft.gravity_m_s2)
                if mid_residual >= 0: hi = mid
                else: lo = mid
            speed = hi; final_samples = curve(speed); final_max = max(final_samples, key=lambda sample: sample["cl"])
            return {"speed_m_s":speed, "speed_km_h":speed*3.6, "clmax_wing_at_stall":final_max["cl"]*margin,
                    "alpha_deg":final_max["alpha_deg"], "stations_per_semispan":40, "area_weighting":"local chord × equal dy",
                    "reynolds_root":reynolds_number(speed, wing.root_chord_mm/1000), "reynolds_tip":reynolds_number(speed, wing.tip_chord_mm/1000),
                    "curve":final_samples}
        previous = current
    return {"unsupported": True, "reason":"No self-consistent supported stall root in 6–16 m/s."}


def engineering_ncrit5_estimates(config: AircraftConfig, cases: list[dict[str, Any]], clean_clmax: float) -> dict[str, Any]:
    """Documented sensitivity estimates, not direct XFOIL wing-solver outputs.

    The Ncrit factor is the direct pre-peak CL ratio at Re=200k (a mandatory,
    representative case); all quantities and formulas are retained in summary.
    """
    clean = next(case for case in cases if case["scenario"] == "clean" and case["reynolds"] == 200000)
    realistic = next(case for case in cases if case["scenario"] == "realistic_model" and case["reynolds"] == 200000)
    ncrit_factor = realistic["metrics"]["reliable_pre_peak_clmax"] / clean["metrics"]["reliable_pre_peak_clmax"]
    ar = (config.wing.span_mm / 1000) ** 2 / config.wing.area_m2
    f = lambda e: 1 / (1 + 6.3 / (math.pi * e * ar))
    definitions = {"nominal": {"e": .85, "margin": 1.0}, "conservative": {"e": .75, "margin": .90}}
    output: dict[str, Any] = {"classification":"engineering sensitivity estimate; not direct XFOIL wing-solver output", "raw_rule":"Ncrit factor = reliable pre-peak CLmax(Ncrit=5)/CLmax(Ncrit=9) at Re=200000", "ncrit_factor":ncrit_factor, "aspect_ratio":ar, "f_formula":"1/[1 + 6.3/(pi*e*AR)]", "clean_solver_clmax":clean_clmax, "scenarios":{}}
    for name, spec in definitions.items():
        cl = clean_clmax * ncrit_factor * f(spec["e"]) / f(.90) * spec["margin"]
        output["scenarios"][name] = {"oswald_e":spec["e"], "margin":spec["margin"], "clmax_wing":cl,
            "vs_km_h":{f"{mass_g:.0f}_g":stall_speed_m_s(mass_g/1000, config.wing.area_m2, cl, config.aircraft.gravity_m_s2)*3.6 for mass_g in (2200,2400,2600,2800)}}
    return output


def make_plots(cases: list[dict[str, Any]], out: Path) -> None:
    plots = out / "plots"; plots.mkdir(parents=True, exist_ok=True)
    for case in cases:
        rows = case["rows"]
        if not rows: continue
        x = np.array([r["alpha_deg"] for r in rows]); cl = np.array([r["cl"] for r in rows]); cd = np.array([r["cd"] for r in rows]); cm = np.array([r["cm"] for r in rows])
        fig, axes = plt.subplots(2, 2, figsize=(10, 7)); fig.suptitle(f"Clark Y — Re {case['reynolds']:,}, {case['scenario']} (Ncrit {case['ncrit']:g})")
        axes[0,0].plot(x,cl); axes[0,0].set(xlabel="α (deg)", ylabel="CL")
        axes[0,1].plot(cl,cd); axes[0,1].set(xlabel="CL", ylabel="CD")
        axes[1,0].plot(cl,cl/cd); axes[1,0].set(xlabel="CL", ylabel="L/D")
        axes[1,1].plot(x,cm); axes[1,1].set(xlabel="α (deg)", ylabel="Cm")
        for axis in axes.flat: axis.grid(True, alpha=.3)
        fig.tight_layout(); fig.savefig(plots / f"clarky_re{case['reynolds']}_{case['scenario']}.png", dpi=150); plt.close(fig)
    for scenario in NCRIT_CASES:
        fig, axis = plt.subplots(figsize=(8,5))
        for case in cases:
            if case["scenario"] == scenario and case["rows"]:
                axis.plot([r["alpha_deg"] for r in case["rows"]], [r["cl"] for r in case["rows"]], label=f"Re {case['reynolds']:,}")
        axis.set(title=f"Clark Y CL comparison — {scenario}", xlabel="α (deg)", ylabel="CL"); axis.grid(True, alpha=.3); axis.legend(ncol=2)
        fig.tight_layout(); fig.savefig(plots / f"comparison_cl_alpha_{scenario}.png", dpi=150); plt.close(fig)


def summary(config: AircraftConfig, cases: list[dict[str, Any]], xfoil: Path) -> dict[str, Any]:
    wing, aircraft = config.wing, config.aircraft
    re_speeds = {f"{v}_km_h": reynolds_number(v/3.6, wing.mean_aerodynamic_chord_mm/1000) for v in (35,50,70,100)}
    scenario_settings = {"clean": ("clean", .90, 1.0), "nominal_realistic": ("realistic_model", .85, 1.0), "conservative_realistic": ("realistic_model", .75, .90)}
    stall = {}
    for name, (polar_scenario, e, margin) in scenario_settings.items():
        cache: dict[float, list[dict[str, float]]] = {}
        stall[name] = {f"{mass_g:.0f}_g": solve_wing_stall(config, cases, polar_scenario, e, margin, mass_g / 1000, cache)
                       for mass_g in (aircraft.target_mass_g-200, aircraft.target_mass_g, aircraft.target_mass_g+200, aircraft.target_mass_g+400)}
    cruise = [{"speed_km_h": v, "cl_required": required_cl(aircraft.target_mass_kg, v/3.6, wing.area_m2, aircraft.gravity_m_s2)} for v in (50,60,70,80,90,100)]
    wind = [{"airspeed_km_h": v, "headwind_m_s": w, "groundspeed_km_h": v-w*3.6} for v in (60,70,80,90) for w in (0,5,8,10,12)]
    return {"schema": "lr1600-airfoil-analysis-v1", "generated_utc": datetime.now(timezone.utc).isoformat(),
            "aircraft_typed_yaml_snapshot": asdict(config), "atmosphere": {"model":"ISA sea level baseline", "rho_kg_m3":RHO,"mu_pa_s":MU},
            "airfoil": {"path":str(AIRFOIL.relative_to(ROOT)), "sha256":sha256(AIRFOIL), "coordinates":len(load_airfoil_coordinates())},
            "tool": {"binary":str(xfoil.relative_to(ROOT)) if xfoil.is_relative_to(ROOT) else str(xfoil), "banner":xfoil_banner(xfoil)},
            "xfoil_inputs":{"alpha_deg":{"start":ALPHA_START,"end":ALPHA_END,"step":ALPHA_STEP},"reynolds_cases":list(RE_CASES),"ncrit":NCRIT_CASES},
            "reynolds_mac":re_speeds, "two_d_cases":[{k:v for k,v in c.items() if k != "rows"} for c in cases],
            "stall_solutions_1g":stall, "engineering_ncrit5_estimates":engineering_ncrit5_estimates(config, cases, stall["clean"]["2400_g"]["clmax_wing_at_stall"]), "cruise_required_cl":cruise, "headwind_groundspeed_km_h":wind,
            "wing_method_limitations":"Self-consistent V/Re solution; 40 stations per semispan, chord-area weighting, finite-AR induced angle. Only each raw polar's reliable pre-peak branch is available to the solver; no flaperon credit or post-peak extrapolation."}


def main() -> None:
    parser = argparse.ArgumentParser(); parser.add_argument("--output", type=Path, default=ROOT / "analysis/aero"); parser.add_argument("--xfoil", type=Path); parser.add_argument("--reuse-raw", action="store_true", help="reparse existing raw PACC polars without launching XFOIL")
    args = parser.parse_args(); config = load_aircraft_config(DEFAULT_CONFIG_PATH)
    xfoil = args.xfoil or Path(os.environ.get("XFOIL_BIN", DEFAULT_XFOIL))
    if not xfoil.is_file() or not os.access(xfoil, os.X_OK): raise SystemExit(f"XFOIL executable unavailable: {xfoil}")
    load_airfoil_coordinates(AIRFOIL)
    cleanup_raw_side_artifacts(args.output)
    xfoil_airfoil = materialize_xfoil_coordinates(args.output)
    forward_cases = [run_case(xfoil, args.output, xfoil_airfoil, reynolds, scenario, ncrit, args.reuse_raw) for scenario, ncrit in NCRIT_CASES.items() for reynolds in RE_CASES]
    # Reverse sweep is complementary direct XFOIL evidence for Ncrit=5 gaps.
    reverse_cases = [run_case(xfoil, args.output, xfoil_airfoil, reynolds, "realistic_model", NCRIT_CASES["realistic_model"], args.reuse_raw, "reverse") for reynolds in RE_CASES]
    reverse_by_re = {case["reynolds"]: case for case in reverse_cases}
    cases = [merge_direct_sweeps(case, reverse_by_re[case["reynolds"]], args.output) if case["scenario"] == "realistic_model" else case for case in forward_cases]
    make_plots(cases, args.output)
    result = summary(config, cases, xfoil)
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "summary.json").write_text(json.dumps(result, indent=2, allow_nan=False) + "\n", encoding="utf-8")
    with (args.output / "engineering_ncrit5_estimates.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["scenario", "oswald_e", "margin", "clmax_wing", "mass", "vs_km_h"], lineterminator="\n"); writer.writeheader()
        for name, estimate in result["engineering_ncrit5_estimates"]["scenarios"].items():
            for mass, vs in estimate["vs_km_h"].items(): writer.writerow({"scenario":name, "oswald_e":estimate["oswald_e"], "margin":estimate["margin"], "clmax_wing":estimate["clmax_wing"], "mass":mass, "vs_km_h":vs})
    with (args.output / "summary_cases.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=["scenario","ncrit","reynolds","points","clmax_2d_converged","clmax_alpha_deg","cdmin","best_ld","best_ld_cl","last_converged_alpha_deg","warnings"], lineterminator="\n"); writer.writeheader()
        for case in cases:
            metrics = case["metrics"]; writer.writerow({"scenario":case["scenario"],"ncrit":case["ncrit"],"reynolds":case["reynolds"], **{key: metrics.get(key) for key in writer.fieldnames if key not in {"scenario","ncrit","reynolds"}}, "warnings":"; ".join(metrics["warnings"])})

if __name__ == "__main__": main()
