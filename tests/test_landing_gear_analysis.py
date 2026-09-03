from pathlib import Path

import pytest

from scripts.config import load_aircraft_config
from scripts.landing_gear_analysis import make_summary


ROOT = Path(__file__).resolve().parents[1]


def test_rough_clearance_keeps_roll_rut_and_wear_deductions():
    summary = make_summary(load_aircraft_config(ROOT / "config" / "aircraft.yaml"))
    clearance = summary["clearance_mm"]
    assert clearance["full_rough"] == pytest.approx(
        clearance["one_main_roll"] - clearance["rut_or_stone_deduction"] - clearance["wear_build_deduction"]
    )
    assert clearance["full_rough"] >= clearance["goal"]


def test_2600g_one_main_proof_is_the_governing_vertical_screen():
    summary = make_summary(load_aircraft_config(ROOT / "config" / "aircraft.yaml"))
    loads = summary["loads_n"]
    assert summary["mass_case_g"] == 2600
    assert loads["one_main_3_5g_proof"] == pytest.approx(120.48, rel=3e-3)
    assert loads["one_main_3_5g_proof"] > loads["taxi_2_5g_one_main_proof"]


def test_calculation_carries_fixed_nose_architecture_contract():
    summary = make_summary(load_aircraft_config(ROOT / "config" / "aircraft.yaml"))
    architecture = summary["nose_architecture"]
    assert architecture == {
        "heading": "fixed_longitudinal",
        "anti_rotation": "positive_mechanical_index",
        "compliance": "replaceable_sprung_strut_fork",
        "seasonal_axle_interface": "wheel_or_pitch_pivot_ski",
        "yaw_freedom": "locked",
    }
