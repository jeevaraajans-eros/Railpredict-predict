import requests
import time

base_url = 'http://localhost:8001'

def reset():
    requests.post(f'{base_url}/simulation/control', json={'action': 'RESET'})
    print("--- RESET ---")

def start():
    requests.post(f'{base_url}/simulation/control', json={'action': 'START', 'speed_multiplier': 10})
    print("--- START ---")

def get_eta():
    r = requests.get(f'{base_url}/trains/12004')
    train = r.json()['train']
    etas = (train.get('latest_eta') or {}).get('station_wise_etas', [])
    print(f"Current station: {train['current_station']}")
    if not etas:
        print("  No ETAs yet")
    for eta in etas:
        print(f"  {eta['station']}: ETA {eta['predicted_travel_time_min']}m (Total Accumulated delay: {eta['accumulated_delay_min']}m, Risk: {eta['delay_risk']})")
    
def inject_congestion(severity=0.8):
    event = {
        'train_id': '12004',
        'event_type': 'congestion',
        'severity': severity
    }
    requests.post(f'{base_url}/simulation/event', json=event)
    print(f"--- INJECT CONGESTION ({severity*100}%) ---")

def clear_disruption():
    event = {
        'train_id': '12004',
        'event_type': 'clear disruption',
        'severity': 0.0
    }
    requests.post(f'{base_url}/simulation/event', json=event)
    print(f"--- CLEAR DISRUPTION ---")

print("SCENARIO A: RECOVERY")
reset()
time.sleep(2)
start()
time.sleep(2)
get_eta()
# Train starts with 10 mins delay. Wait for a few seconds to let it recover natively in the first section (NDLS-GZB).
time.sleep(3)
get_eta()

print("\nSCENARIO B: ACCUMULATION")
reset()
time.sleep(2)
start()
time.sleep(2)
inject_congestion(0.5)
time.sleep(2)
get_eta()

print("\nSCENARIO C: COMBINED")
reset()
time.sleep(2)
start()
time.sleep(2)
get_eta() # Recovering slightly
inject_congestion(0.8) # Now getting congested
time.sleep(2)
get_eta()
clear_disruption()
time.sleep(2)
get_eta() # Recovering again
