import pytest
from scripts.landing_gear import summary

def test_full_rough_clearance_accounts_for_every_declared_deduction():
    data=summary(); p=data['prop_clearance_mm']; d=p['deductions']
    assert p['full_rough'] == pytest.approx(p['static']-sum(d.values()))
    assert data['passes_goal']
    assert data['masses_g']['wheel_gear'] == 196.0
    assert data['masses_g']['ski_module_replacing_wheels'] == 232.0

def test_nose_interface_is_fixed_compliant_and_has_no_steering_parts():
    architecture = summary()['nose_architecture']
    assert architecture['heading'] == 'fixed_longitudinal'
    assert architecture['anti_rotation'] == 'positive_mechanical_index'
    assert architecture['compliance'] == 'replaceable_sprung_strut_fork'
    assert architecture['seasonal_axle_interface'] == 'wheel_or_pitch_pivot_ski'
    assert architecture['yaw_freedom'] == 'locked'
    assert set(architecture['excluded_items']) == {
        'steering_linkage', 'steering_servo_connection', 'servo_saver',
        'steering_arm', 'steering_cable', 'yaw_stops',
    }

def test_one_main_case_governs_the_main_hardpoint():
    loads=summary()['loads_n']
    assert loads['one_main_governing'] > loads['taxi_main'] > loads['rough_main'] > loads['normal_main']
