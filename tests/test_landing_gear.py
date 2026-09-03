import pytest
from scripts.landing_gear import summary

def test_full_rough_clearance_accounts_for_every_declared_deduction():
    data=summary(); p=data['prop_clearance_mm']; d=p['deductions']
    assert p['full_rough'] == pytest.approx(p['static']-sum(d.values()))
    assert data['passes_goal']
    assert data['masses_g']['ski_module_replacing_wheels'] == 238.0

def test_one_main_case_governs_the_main_hardpoint():
    loads=summary()['loads_n']
    assert loads['one_main_governing'] > loads['taxi_main'] > loads['rough_main'] > loads['normal_main']
