from scripts.check_agent_profiles import validate_agent_profiles


def test_specialist_agent_profiles_follow_cost_policy():
    assert validate_agent_profiles() == []
