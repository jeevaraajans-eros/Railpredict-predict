from datetime import datetime

SIMULATION_STATE = {
    'is_running': False,
    'current_time': datetime(2025, 1, 1, 12, 0, 0),
    'speed_multiplier': 1, 
}

ACTIVE_TRAINS = {
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

GLOBAL_NETWORK_CONDITIONS = {
    'congestion_level': 0.3,
    'weather_condition': 'Clear',
    'operational_event': 'Normal',
    'average_speed_kmph': 80.0
}
