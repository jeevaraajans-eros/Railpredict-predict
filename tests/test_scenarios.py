import pytest
from datetime import datetime
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.engine.eta_engine import run_dynamic_eta_engine

def build_base_state():
    return {
        'current_time': datetime(2025, 1, 1, 10, 0),
        'train_state': {'train_id': '12004', 'current_delay_min': 0, 'current_station': 'NDLS'},
        'remaining_route': [
            {'section_id': 'S1', 'destination_station': 'STN_A', 'distance_km': 60.0, 'scheduled_section_time_min': 45, 'dwell_time_min': 5, 'historical_section_avg_time': 45},
            {'section_id': 'S2', 'destination_station': 'STN_B', 'distance_km': 60.0, 'scheduled_section_time_min': 45, 'dwell_time_min': 5, 'historical_section_avg_time': 45},
        ],
        'network_conditions': {'congestion_level': 0.1, 'weather_condition': 'Clear', 'operational_event': 'Normal', 'average_speed_kmph': 80.0}
    }

def test_scenario_A_normal_run():
    base = build_base_state()
    out = run_dynamic_eta_engine(**base)
    for st in out['station_wise_etas']:
        assert st['accumulated_delay_min'] <= 5 

def test_scenario_B_starts_late():
    base = build_base_state()
    base['train_state']['current_delay_min'] = 10
    out = run_dynamic_eta_engine(**base)
    stn_a_delay = out['station_wise_etas'][0]['accumulated_delay_min']
    assert 0 <= stn_a_delay <= 15  
    assert "carryover" in out['station_wise_etas'][0]['explanation'].lower()
    
def test_scenario_C_congestion():
    base_normal = build_base_state()
    base_congested = build_base_state()
    base_congested['network_conditions']['congestion_level'] = 1.0 # Severe choke
    base_congested['network_conditions']['average_speed_kmph'] = 45.0
    
    out_normal = run_dynamic_eta_engine(**base_normal)
    out_congested = run_dynamic_eta_engine(**base_congested)
    
    travel_normal = out_normal['station_wise_etas'][0]['predicted_travel_time_min']
    travel_congested = out_congested['station_wise_etas'][0]['predicted_travel_time_min']
    assert travel_congested > travel_normal

def test_scenario_D_speed_restriction():
    base_normal = build_base_state()
    base_restricted = build_base_state()
    base_restricted['network_conditions']['average_speed_kmph'] = 40.0 # Direct restriction
    
    out_normal = run_dynamic_eta_engine(**base_normal)
    out_restricted = run_dynamic_eta_engine(**base_restricted)
    
    assert out_restricted['station_wise_etas'][0]['predicted_travel_time_min'] > out_normal['station_wise_etas'][0]['predicted_travel_time_min']

def test_scenario_E_congestion_clears():
    base_congested = build_base_state()
    base_congested['network_conditions']['congestion_level'] = 1.0
    base_congested['network_conditions']['average_speed_kmph'] = 45.0
    out_congested = run_dynamic_eta_engine(**base_congested)
    
    base_cleared = build_base_state()
    base_cleared['network_conditions']['congestion_level'] = 0.0
    base_cleared['network_conditions']['average_speed_kmph'] = 80.0
    base_cleared['train_state']['current_delay_min'] = out_congested['station_wise_etas'][0]['accumulated_delay_min']
    
    out_cleared = run_dynamic_eta_engine(**base_cleared)
    
    travel_s1_congested = out_congested['station_wise_etas'][0]['predicted_travel_time_min']
    travel_s2_cleared = out_cleared['station_wise_etas'][1]['predicted_travel_time_min']
    
    assert travel_s2_cleared < travel_s1_congested

def test_scenario_F_delay_partially_recovers():
    base = build_base_state()
    base['train_state']['current_delay_min'] = 30 # Severe constraint
    
    out = run_dynamic_eta_engine(**base)
    final_delay = out['final_destination_delay_min']
    assert final_delay <= 30
