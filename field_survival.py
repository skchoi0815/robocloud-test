# Ch24 - Submarine 31도 살아남은 로직

def battery_soc(voltage: float) -> float:
    if voltage > 13.0:
        soc = 90 + (voltage - 13.0) * 20
    elif voltage > 12.8:
        soc = 70 + (voltage - 12.8) * 100
    elif voltage > 12.0:
        soc = 20 + (voltage - 12.0) * 62.5
    elif voltage > 10.5:
        soc = (voltage - 10.5) * 13.3
    else:
        soc = 0
    return min(100, max(0, soc))

def adaptive_power_mode(soc: float, solar_watts: float) -> str:
    if soc > 80 and solar_watts > 10:
        return 'full'
    if soc > 50 or solar_watts > 5:
        return 'normal'
    if soc > 20 or solar_watts > 0:
        return 'economy'
    return 'survival'

def check_enclosure(temp: float, humidity: float):
    alerts = []
    if temp > 60:
        alerts.append({'level': 'CRITICAL', 'action': 'enable_cooling'})
    if humidity > 85:
        alerts.append({'level': 'CRITICAL', 'action': 'enable_dehumidifier'})
    return {'status': 'DEGRADED' if alerts else 'OPERATIONAL', 'alerts': alerts}
