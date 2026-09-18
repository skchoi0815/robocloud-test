from agent_brain import invoke_agent_with_retry, needs_human_confirmation, build_mission_prompt, FakeBedrockError

def test_retry_on_throttling():
    calls = {'n': 0}
    def flaky():
        calls['n'] += 1
        if calls['n'] < 3:
            raise FakeBedrockError('ThrottlingException')
        return "AEGIS: HIGH THREAT, recommend turret-04"
    r = invoke_agent_with_retry(flaky, max_retries=3)
    assert r['status'] == 'SUCCESS'
    assert 'turret-04' in r['output']
    assert calls['n'] == 3

def test_no_retry_on_other_error():
    def bad():
        raise FakeBedrockError('ValidationException')
    r = invoke_agent_with_retry(bad, max_retries=3)
    assert r['status'] == 'ERROR'
    assert 'Escalating to human' in r['output']

def test_human_in_loop():
    assert needs_human_confirmation('assign_turret_to_track') is True
    assert needs_human_confirmation('get_active_tracks') is False

def test_prompt_format():
    p = build_mission_prompt({'type':'HIGH_THREAT','track_id':'trk-d9e8','confidence':0.98,'region':'sector_gamma'})
    assert 'trk-d9e8' in p
    assert 'sector_gamma' in p
