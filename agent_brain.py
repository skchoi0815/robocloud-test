import time
import random

class FakeBedrockError(Exception):
    def __init__(self, code):
        self.response = {'Error': {'Code': code}}
        super().__init__(code)

def invoke_agent_with_retry(invoke_fn, max_retries=3):
    for attempt in range(max_retries):
        try:
            return {'status': 'SUCCESS', 'output': invoke_fn()}
        except Exception as e:
            code = getattr(e, 'response', {}).get('Error', {}).get('Code', '')
            if code == 'ThrottlingException' and attempt < max_retries - 1:
                backoff = (2 ** attempt) + random.random() * 0.1
                time.sleep(backoff * 0.01)
                continue
            return {'status': 'ERROR', 'error': str(e), 'error_code': code,
                    'output': f"AEGIS: Escalating to human. Error: {code}"}
    return {'status': 'ERROR', 'output': 'AEGIS: Max retries exceeded.'}

def needs_human_confirmation(action: str) -> bool:
    PHYSICAL = {'assign_turret_to_track', 'track_and_illuminate', 'illuminate'}
    return action in PHYSICAL

def build_mission_prompt(threat: dict) -> str:
    return (f"NEW THREAT ALERT:\n- Type: {threat.get('type')}\n"
            f"- Track ID: {threat.get('track_id')}\n"
            f"- Confidence: {threat.get('confidence')}\n"
            f"- Region: {threat.get('region')}\nAssess and recommend.")
