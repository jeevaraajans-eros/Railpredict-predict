import requests
import time

base_url = 'http://localhost:8001'

def reset():
    requests.post(f'{base_url}/simulation/control', json={'action': 'RESET'})
    print("RESET")

def start():
    requests.post(f'{base_url}/simulation/control', json={'action': 'START', 'speed_multiplier': 10})
    print("START")

def get_eta():
    r = requests.get(f'{base_url}/trains/12004')
    train = r.json()['train']
    etas = (train.get('latest_eta') or {}).get('station_wise_etas', [])
    print(f"--- ETAs at {time.time()} ---")
    print(f"Current station: {train['current_station']}")
    if not etas:
        print("  No ETAs yet")
    for eta in etas:
        print(f"  {eta['station']}: ETA {eta['predicted_travel_time_min']}m (Accumulated delay: {eta['accumulated_delay_min']}m, Risk: {eta['delay_risk']}, Arr: {eta['predicted_arrival']})")
    
def inject_congestion():
    event = {
        'train_id': '12004',
        'event_type': 'congestion',
        'severity': 0.8  # e.g., 80% congestion
    }
    r = requests.post(f'{base_url}/simulation/event', json=event)
    print(f"INJECT CONGESTION: {r.status_code}")

def clear_disruption():
    event = {
        'train_id': '12004',
        'event_type': 'clear disruption',
        'severity': 0.0
    }
    r = requests.post(f'{base_url}/simulation/event', json=event)
    print(f"CLEAR DISRUPTION: {r.status_code}")

reset()
time.sleep(2)
start()
time.sleep(2)
get_eta()
inject_congestion()
time.sleep(2)
get_eta()
clear_disruption()
time.sleep(2)
get_eta()
