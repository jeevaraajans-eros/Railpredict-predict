from datetime import datetime

STATION_COORDS = {
  'NDLS': [28.6139, 77.2090],
  'GZB': [28.6692, 77.4538],
  'ALJN': [27.8815, 78.0746],
  'CNB': [26.4499, 80.3319]
}

common_route = [
    {
        'section_id': 'NDLS-GZB',
        'destination_station': 'GZB',
        'distance_km': 25.0,
        'scheduled_section_time_min': 30,
        'dwell_time_min': 5,
        'historical_section_avg_time': 32
    },
    {
        'section_id': 'GZB-ALJN',
        'destination_station': 'ALJN',
        'distance_km': 100.0,
        'scheduled_section_time_min': 80,
        'dwell_time_min': 5,
        'historical_section_avg_time': 85
    },
    {
        'section_id': 'ALJN-CNB',
        'destination_station': 'CNB',
        'distance_km': 300.0,
        'scheduled_section_time_min': 210,
        'dwell_time_min': 10,
        'historical_section_avg_time': 225
    }
]

ROUTE_DATA = {
    "12004": common_route,
    "12952": common_route,
    "12802": common_route
}

def get_initial_simulation_state():
    return {
        'is_running': False,
        'current_time': datetime(2025, 1, 1, 12, 0, 0),
        'speed_multiplier': 1, 
    }

def get_initial_trains():
    return {
        "12004": {
            "train_id": "12004", 
            "type": "Shatabdi Exp", 
            "current_delay_min": 10, 
            "current_station": "NDLS",
            "current_section_id": "NDLS-GZB",
            "distance_covered_in_section_km": 0.0,
            "status": "EN_ROUTE",
            "latest_eta": None
        },
        "12952": {
            "train_id": "12952", 
            "type": "Rajdhani Exp", 
            "current_delay_min": 0, 
            "current_station": "GZB",
            "current_section_id": "GZB-ALJN",
            "distance_covered_in_section_km": 15.0,
            "status": "EN_ROUTE",
            "latest_eta": None
        },
        "12802": {
            "train_id": "12802", 
            "type": "Purushottam Exp", 
            "current_delay_min": 45, 
            "current_station": "ALJN",
            "current_section_id": "ALJN-CNB",
            "distance_covered_in_section_km": 50.0,
            "status": "EN_ROUTE",
            "latest_eta": None
        }
    }

def get_initial_network():
    return {
        'congestion_level': 0.1,
        'weather_condition': 'Clear',
        'operational_event': 'Normal',
        'average_speed_kmph': 80.0
    }

# Memory reference bindings maintained exactly
SIMULATION_STATE = get_initial_simulation_state()
EVENT_TIMELINE = [{"time": "12:00:00", "event": "Train 12004 Dispatched onto Corridor", "type": "INFO"}]
ACTIVE_TRAINS = get_initial_trains()
GLOBAL_NETWORK_CONDITIONS = get_initial_network()

def reset_simulation():
    global SIMULATION_STATE, EVENT_TIMELINE, ACTIVE_TRAINS, GLOBAL_NETWORK_CONDITIONS
    SIMULATION_STATE.clear()
    SIMULATION_STATE.update(get_initial_simulation_state())
    
    EVENT_TIMELINE.clear()
    EVENT_TIMELINE.append({"time": "12:00:00", "event": "Simulation Reset. Train 12004 restored.", "type": "INFO"})
    
    ACTIVE_TRAINS.clear()
    ACTIVE_TRAINS.update(get_initial_trains())
    
    GLOBAL_NETWORK_CONDITIONS.clear()
    GLOBAL_NETWORK_CONDITIONS.update(get_initial_network())
