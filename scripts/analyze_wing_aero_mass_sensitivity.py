#!/usr/bin/env python3
"""Reproduce the LR1600 2400/2600-g aero sensitivity from existing polars.

This is a mass-load sensitivity only.  It reads the canonical 2400-g typed
YAML and the committed XFOIL polar artefacts; it neither writes a second YAML
nor changes wing geometry, profile, or control-surface assumptions.
"""

from __future__ import annotations

import argparse
import csv
import json
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

try:
    from config import DEFAULT_CONFIG_PATH, load_aircraft_config
    from propulsion_sizing import (
        OSWALD_E,
        dynamic_pressure,
        load_clean_cases,
        wing_drag_n,
    )
    from run_airfoil_analysis import (
        RHO,
        engineering_ncrit5_estimates,
        metrics_for_rows,
        required_cl,
        reynolds_number,
        solve_wing_stall,
    )
except ImportError:  # pragma: no cover - module invocation
    from scripts.config import DEFAULT_CONFIG_PATH, load_aircraft_config
    from scripts.propulsion_sizing import (
        OSWALD_E,
        dynamic_pressure,
        load_clean_cases,
        wing_drag_n,
    )
    from scripts.run_airfoil_analysis import (
        RHO,
        engineering_ncrit5_estimates,
        metrics_for_rows,
        required_cl,
        reynolds_number,
        solve_wing_stall,
    )


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_AERO_ROOT = ROOT / "analysis" / "aero"
DEFAULT_OUTPUT = DEFAULT_AERO_ROOT / "mass_sensitivity_2400_2600.json"
REFERENCE_MASS_G = 2400.0
SENSITIVITY_MASS_G = 2600.0
SPEEDS_KM_H = (50.0, 60.0, 70.0, 80.0, 90.0)
STALL_SCENARIOS = {
    "clean": ("clean", 0.90, 1.0),
    "nominal_realistic": ("realistic_model", 0.85, 1.0),
    "conservative_realistic": ("realistic_model", 0.75, 0.90),
}


def load_polar_cases(aero_root: Path) -> list[dict[str, Any]]:
    """Load direct parsed polar points declared by the existing summary."""
    summary_path = aero_root / "summary.json"
    summary = json.loads(summary_path.read_text(encoding="utf-8"))
    cases: list[dict[str, Any]] = []
    for item in summary["two_d_cases"]:
        # ``summary.json`` points to the parsed CSV rather than XFOIL's
        # whitespace polar; ``parse_polar`` is intentionally for the latter.
        path = ROOT / item["parsed_csv"]
        with path.open(newline="", encoding="utf-8") as source:
            rows = [{key: float(value) if key != "source" else value for key, value in row.items()}
                    for row in csv.DictReader(source)]
        cases.append({
            "reynolds": item["reynolds"],
            "scenario": item["scenario"],
            "rows": rows,
            "metrics": metrics_for_rows(rows, -6.0, 18.0, 0.25),
        })
    if not cases:
        raise ValueError("existing aero summary declares no parsed polars")
    return cases


def _strict_stall_cases(config: Any, cases: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Run the existing stall solver at each mass, preserving its no-gap rule."""
    result: dict[str, dict[str, Any]] = {}
    for name, (polar_scenario, oswald_e, margin) in STALL_SCENARIOS.items():
        cache: dict[float, list[dict[str, float]]] = {}
        result[name] = {
            f"{int(mass_g)}g": solve_wing_stall(
                config, cases, polar_scenario, oswald_e, margin, mass_g / 1000.0, cache,
            )
            for mass_g in (REFERENCE_MASS_G, SENSITIVITY_MASS_G)
        }
    return result


def _drag_point(config: Any, clean_cases: list[dict[str, Any]], mass_g: float, speed_km_h: float) -> dict[str, float]:
    """Use existing wing_drag_n; split its documented finite-wing induced term."""
    speed_m_s = speed_km_h / 3.6
    mass_kg = mass_g / 1000.0
    cl = required_cl(mass_kg, speed_m_s, config.wing.area_m2, config.aircraft.gravity_m_s2)
    ar = (config.wing.span_mm / 1000.0) ** 2 / config.wing.area_m2
    induced_cd = cl**2 / (math.pi * OSWALD_E * ar)
    q_s = dynamic_pressure(speed_m_s) * config.wing.area_m2
    induced_drag = q_s * induced_cd
    total_drag = wing_drag_n(config, clean_cases, mass_kg, speed_m_s, OSWALD_E)
    profile_drag = total_drag - induced_drag
    return {
        "speed_km_h": speed_km_h,
        "required_cl": cl,
        "reynolds_mac": reynolds_number(speed_m_s, config.wing.mean_aerodynamic_chord_mm / 1000.0),
        "profile_drag_n": profile_drag,
        "induced_drag_n": induced_drag,
        "total_wing_drag_n": total_drag,
        "wing_ld": mass_kg * config.aircraft.gravity_m_s2 / total_drag,
    }


def _best_ld_range(config: Any, clean_cases: list[dict[str, Any]], mass_g: float) -> dict[str, float]:
    """Find the supported integer-km/h wing-only L/D plateau, not a new optimum."""
    points = []
    for speed_km_h in range(40, 101):
        try:
            points.append(_drag_point(config, clean_cases, mass_g, float(speed_km_h)))
        except ValueError:
            continue
    if not points:
        raise ValueError("no supported clean-polar points for L/D sensitivity")
    best = max(points, key=lambda point: point["wing_ld"])
    floor = best["wing_ld"] * 0.99
    near_best = [point for point in points if point["wing_ld"] >= floor]
    return {
        "best_sampled_speed_km_h": best["speed_km_h"],
        "best_sampled_wing_ld": best["wing_ld"],
        "within_99_percent_speed_low_km_h": near_best[0]["speed_km_h"],
        "within_99_percent_speed_high_km_h": near_best[-1]["speed_km_h"],
        "method": "1-km/h sampled finite-wing clean-polar sensitivity; not a flight-speed prescription",
    }


@lru_cache(maxsize=None)
def build_summary(config_path: Path = DEFAULT_CONFIG_PATH, aero_root: Path = DEFAULT_AERO_ROOT) -> dict[str, Any]:
    config = load_aircraft_config(config_path)
    # This historical 2400/2600 comparison intentionally remains available
    # after the aircraft-level integration case moved to 2600 g.  It does not
    # alter the wing geometry or structural concept.
    cases = load_polar_cases(aero_root)
    clean_cases = load_clean_cases(aero_root)
    strict_stall = _strict_stall_cases(config, cases)
    clean_2400 = strict_stall["clean"]["2400g"]
    if clean_2400.get("unsupported"):
        raise ValueError("existing clean polar coverage cannot solve the 2400-g stall reference")
    estimates = engineering_ncrit5_estimates(config, cases, clean_2400["clmax_wing_at_stall"])
    cases_by_mass = {}
    for mass_g in (REFERENCE_MASS_G, SENSITIVITY_MASS_G):
        key = f"{int(mass_g)}g"
        cases_by_mass[key] = {
            "mass_g": mass_g,
            "wing_loading_g_dm2": mass_g / (config.wing.area_m2 * 100.0),
            "points": [_drag_point(config, clean_cases, mass_g, speed) for speed in SPEEDS_KM_H],
            "best_wing_ld": _best_ld_range(config, clean_cases, mass_g),
            "strict_clean_stall": strict_stall["clean"][key],
            "nominal_realistic_stall_engineering_sensitivity": estimates["scenarios"]["nominal"]["vs_km_h"][key.replace("g", "_g")],
            "conservative_realistic_stall_engineering_sensitivity": estimates["scenarios"]["conservative"]["vs_km_h"][key.replace("g", "_g")],
        }
    ratio = math.sqrt(SENSITIVITY_MASS_G / REFERENCE_MASS_G)
    return {
        "schema": "lr1600-wing-aero-mass-sensitivity-v1",
        "scope": {
            "canonical_config": str(config_path.relative_to(ROOT)),
            "canonical_target_mass_g": config.aircraft.target_mass_g,
            "sensitivity_mass_g": SENSITIVITY_MASS_G,
            "geometry": "unchanged; span/chords/airfoil/washout/dihedral and controls are read from canonical YAML",
            "atmosphere": {"model": "ISA sea level", "rho_kg_m3": RHO},
        },
        "source_artifacts": {
            "aero_summary": str((aero_root / "summary.json").relative_to(ROOT)),
            "method": "existing XFOIL direct polar data; existing 40-station finite-wing model and clean-polar wing_drag_n",
            "limitations": "Wing-only drag excludes fuselage, tail, pusher/propeller, gaps and full-aircraft CdA. Ncrit=5 direct polar gaps prevent strict realistic-model stall roots; nominal/conservative stalls remain documented engineering sensitivities.",
        },
        "mass_ratio_2600_over_2400": SENSITIVITY_MASS_G / REFERENCE_MASS_G,
        "speed_ratio_sqrt_weight": ratio,
        "cases": cases_by_mass,
        "approach_implication": {
            "result": "No approved approach-speed multiplier exists in the current project. Preserve any future verified Vapp/Vstall policy; all stall-referenced speeds rise by sqrt(2600/2400).",
            "speed_ratio": ratio,
            "conservative_stall_increase_km_h": cases_by_mass["2600g"]["conservative_realistic_stall_engineering_sensitivity"] - cases_by_mass["2400g"]["conservative_realistic_stall_engineering_sensitivity"],
        },
        "practical_cruise_implication": "The clean wing-only 99%-of-best-L/D plateau shifts approximately with sqrt(W), from 56–64 to 59–67 km/h in this model. This is a small shift; it does not establish a new optimum or full-aircraft cruise speed.",
    }


def write_outputs(summary: dict[str, Any], output: Path) -> None:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    csv_path = output.with_suffix(".csv")
    rows = []
    for case_name, case in summary["cases"].items():
        for point in case["points"]:
            rows.append({
                "case": case_name,
                "mass_g": case["mass_g"],
                "wing_loading_g_dm2": case["wing_loading_g_dm2"],
                **point,
                "clean_stall_km_h": case["strict_clean_stall"].get("speed_km_h"),
                "nominal_stall_km_h": case["nominal_realistic_stall_engineering_sensitivity"],
                "conservative_stall_km_h": case["conservative_realistic_stall_engineering_sensitivity"],
            })
    with csv_path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]), lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG_PATH)
    parser.add_argument("--aero-root", type=Path, default=DEFAULT_AERO_ROOT)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    write_outputs(build_summary(args.config, args.aero_root), args.output)
    print(f"Wing aero 2400/2600-g sensitivity written to {args.output}")


if __name__ == "__main__":
    main()
