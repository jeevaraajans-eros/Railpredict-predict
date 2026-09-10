import pytest
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.engine.delay_propagation import calculate_downstream_delay, calculate_delay_risk
from backend.engine.eta_engine import run_dynamic_eta_engine

def test_calculate_downstream_delay():
    # Deterministic Recovery
    assert calculate_downstream_delay(actual_travel_time_min=30, scheduled_travel_time_min=30, current_delay_min=0) == 0
    # Additive Accumulation 
    assert calculate_downstream_delay(40, 30, 10) == 20 
    # Compensative Run (Recovery by high priority train running 5 min faster than schedule)
    assert calculate_downstream_delay(25, 30, 15) == 10
    # Negative Cap Protection (It won't arrive "early" by mapping delays negatively structurally)
    assert calculate_downstream_delay(20, 30, 5) == 0

def test_calculate_delay_risk():
    assert calculate_delay_risk(5) == "Low"
    assert calculate_delay_risk(30) == "Medium"
    assert calculate_delay_risk(60) == "High"

def test_run_dynamic_eta_engine():
    current_time = datetime(2025, 1, 1, 10, 0)
    train_state = {
        'train_id': '12004', 
        'current_delay_min': 10, 
        'current_station': 'NDLS'
    }
    
    remaining_route = [
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
        }
    ]
    
    network_conditions = {
        'congestion_level': 0.2,
        'weather_condition': 'Clear',
        'operational_event': 'Normal',
        'average_speed_kmph': 80.0
    }
    
    output = run_dynamic_eta_engine(current_time, train_state, remaining_route, network_conditions)
    
    assert 'initial_train_state' in output
    assert 'station_wise_etas' in output
    
    etas = output['station_wise_etas']
    assert len(etas) == 2
    assert etas[0]['station'] == 'GZB'
    assert 'predicted_arrival' in etas[0]
    assert 'predicted_travel_time_min' in etas[0]
    assert 'accumulated_delay_min' in etas[0]
    assert 'delay_risk' in etas[0]
