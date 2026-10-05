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
    """Train starts with 10-min delay; clear conditions let it recover partially."""
    base = build_base_state()
    base['train_state']['current_delay_min'] = 10
    out = run_dynamic_eta_engine(**base)
    stn_a_delay = out['station_wise_etas'][0]['accumulated_delay_min']
    assert 0 <= stn_a_delay <= 15
    # Engine now generates explanations with 'carryover'
    assert "carryover" in out['station_wise_etas'][0]['explanation'].lower()

def test_scenario_C_congestion():
    base_normal = build_base_state()
    base_congested = build_base_state()
    base_congested['network_conditions']['congestion_level'] = 1.0
    base_congested['network_conditions']['average_speed_kmph'] = 45.0

    out_normal = run_dynamic_eta_engine(**base_normal)
    out_congested = run_dynamic_eta_engine(**base_congested)

    travel_normal = out_normal['station_wise_etas'][0]['predicted_travel_time_min']
    travel_congested = out_congested['station_wise_etas'][0]['predicted_travel_time_min']
    assert travel_congested > travel_normal

def test_scenario_D_speed_restriction():
    base_normal = build_base_state()
    base_restricted = build_base_state()
    base_restricted['network_conditions']['average_speed_kmph'] = 40.0

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
    base['train_state']['current_delay_min'] = 30

    out = run_dynamic_eta_engine(**base)
    final_delay = out['final_destination_delay_min']
    assert final_delay <= 30

# ─── NEW Phase-9 Tests ───────────────────────────────────────────────────────

def test_scenario_recovery():
    """
    Scenario A — Recovery:
    Train has 10-min delay entering a section where it will run much faster
    than the schedule (80 km/h over a distance that has a generous scheduled time).
    Delay at final station must be strictly less than the initial delay.
    """
    state = {
        'current_time': datetime(2025, 1, 1, 10, 0),
        'train_state': {'train_id': '12004', 'current_delay_min': 10, 'current_station': 'NDLS'},
        'remaining_route': [
            # distance 60 km @ 80 km/h = 45 min actual, scheduled = 60 min → gains 15 min (capped at 5)
            {'section_id': 'S1', 'destination_station': 'STN_A', 'distance_km': 60.0, 'scheduled_section_time_min': 60, 'dwell_time_min': 3, 'historical_section_avg_time': 62},
            # distance 60 km @ 80 km/h = 45 min actual, scheduled = 60 min → another 5 min recovery
            {'section_id': 'S2', 'destination_station': 'STN_B', 'distance_km': 60.0, 'scheduled_section_time_min': 60, 'dwell_time_min': 3, 'historical_section_avg_time': 62},
        ],
        'network_conditions': {'congestion_level': 0.0, 'weather_condition': 'Clear', 'operational_event': 'Normal', 'average_speed_kmph': 80.0}
    }
    out = run_dynamic_eta_engine(**state)
    initial_delay = state['train_state']['current_delay_min']
    final_delay = out['final_destination_delay_min']
    stn_a_delay = out['station_wise_etas'][0]['accumulated_delay_min']
    stn_b_delay = out['station_wise_etas'][1]['accumulated_delay_min']

    # Delay must be strictly reducing
    assert stn_a_delay < initial_delay, f"Expected recovery at STN_A, got {stn_a_delay} (initial {initial_delay})"
    assert stn_b_delay <= stn_a_delay, f"Expected further recovery at STN_B, got {stn_b_delay} vs {stn_a_delay}"
    assert final_delay < initial_delay, f"Final delay {final_delay} not less than initial {initial_delay}"

    # Explanations must mention recovery
    for st in out['station_wise_etas']:
        assert "recovering" in st['explanation'] or "delay" in st['explanation'].lower()


def test_scenario_accumulation():
    """
    Scenario B — Accumulation:
    Train has 5-min delay. Heavy congestion causes actual travel time to exceed schedule.
    Delay at final station must be strictly greater than the initial delay.
    """
    state = {
        'current_time': datetime(2025, 1, 1, 10, 0),
        'train_state': {'train_id': '12004', 'current_delay_min': 5, 'current_station': 'NDLS'},
        'remaining_route': [
            {'section_id': 'S1', 'destination_station': 'STN_A', 'distance_km': 60.0, 'scheduled_section_time_min': 45, 'dwell_time_min': 3, 'historical_section_avg_time': 47},
            {'section_id': 'S2', 'destination_station': 'STN_B', 'distance_km': 60.0, 'scheduled_section_time_min': 45, 'dwell_time_min': 3, 'historical_section_avg_time': 47},
        ],
        # Severe congestion: 45 km/h, congestion_level=1.0 → mult=1.8 → actual ≈ 144 min vs 45 scheduled
        'network_conditions': {'congestion_level': 1.0, 'weather_condition': 'Clear', 'operational_event': 'Normal', 'average_speed_kmph': 45.0}
    }
    out = run_dynamic_eta_engine(**state)
    initial_delay = state['train_state']['current_delay_min']
    final_delay = out['final_destination_delay_min']
    stn_a_delay = out['station_wise_etas'][0]['accumulated_delay_min']

    assert stn_a_delay > initial_delay, f"Expected accumulation at STN_A, got {stn_a_delay} (initial {initial_delay})"
    assert final_delay > initial_delay, f"Final delay {final_delay} not greater than initial {initial_delay}"

    # Explanations must mention accumulating
    for st in out['station_wise_etas']:
        assert "accumulating" in st['explanation'] or "behind" in st['explanation'].lower()


def test_scenario_combined_recovery_then_accumulation():
    """
    Scenario C — Combined:
    Section 1: Clear conditions, scheduled time generous → delay recovers.
    Section 2: Heavy congestion → delay accumulates.
    Final delay must be between the recovered and accumulated values.
    """
    state = {
        'current_time': datetime(2025, 1, 1, 10, 0),
        'train_state': {'train_id': '12004', 'current_delay_min': 10, 'current_station': 'NDLS'},
        'remaining_route': [
            # S1: Recovery section — generous schedule (60 min), fast run @ 80 km/h (45 min)
            {'section_id': 'S1', 'destination_station': 'STN_A', 'distance_km': 60.0, 'scheduled_section_time_min': 60, 'dwell_time_min': 3, 'historical_section_avg_time': 62},
            # S2: Congestion section — tight schedule (45 min), slow @ 40 km/h with mult → much longer
            {'section_id': 'S2', 'destination_station': 'STN_B', 'distance_km': 60.0, 'scheduled_section_time_min': 45, 'dwell_time_min': 3, 'historical_section_avg_time': 47},
        ],
        # We simulate the network mid-journey; congestion affects both sections in the engine.
        # To isolate S2 accumulation we run two calls: first clear, then congested.
        'network_conditions': {'congestion_level': 0.0, 'weather_condition': 'Clear', 'operational_event': 'Normal', 'average_speed_kmph': 80.0}
    }

    # Step 1: run S1 under clear conditions to get recovered delay into STN_A
    out_s1 = run_dynamic_eta_engine(**state)
    delay_after_s1 = out_s1['station_wise_etas'][0]['accumulated_delay_min']
    assert delay_after_s1 < 10, f"Expected recovery in S1, got delay {delay_after_s1}"

    # Step 2: simulate S2 with recovered delay + congestion
    state_s2 = {
        'current_time': out_s1['station_wise_etas'][0]['predicted_departure'],
        'train_state': {'train_id': '12004', 'current_delay_min': delay_after_s1, 'current_station': 'STN_A'},
        'remaining_route': [
            {'section_id': 'S2', 'destination_station': 'STN_B', 'distance_km': 60.0, 'scheduled_section_time_min': 45, 'dwell_time_min': 3, 'historical_section_avg_time': 47},
        ],
        'network_conditions': {'congestion_level': 1.0, 'weather_condition': 'Clear', 'operational_event': 'Normal', 'average_speed_kmph': 45.0}
    }
    # current_time passed as string from strftime, convert back
    if isinstance(state_s2['current_time'], str):
        state_s2['current_time'] = datetime.strptime(state_s2['current_time'], "%Y-%m-%d %H:%M:%S")

    out_s2 = run_dynamic_eta_engine(**state_s2)
    delay_after_s2 = out_s2['station_wise_etas'][0]['accumulated_delay_min']

    # After S2 with congestion, delay must be higher than after S1 recovery
    assert delay_after_s2 > delay_after_s1, (
        f"Expected accumulation in S2: delay_after_s2={delay_after_s2} should be > delay_after_s1={delay_after_s1}"
    )
    # Final delay should reflect the accumulated value
    assert out_s2['final_destination_delay_min'] == delay_after_s2


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

# ─── NEW Phase-11 Tests (Network-Aware) ──────────────────────────────────────

def test_network_scenario_A_normal():
    """Phase 11: Normal train movement, no network disruption, verify baseline."""
    base = build_base_state()
    base['train_state']['current_section_id'] = 'S1'
    # active_trains has no other trains
    base['active_trains'] = {}
    out = run_dynamic_eta_engine(**base)
    # verify baseline
    assert 'Occupied' not in out['station_wise_etas'][0]['explanation']

def test_network_scenario_B_occupied():
    """Phase 11: Another train occupies the upcoming section."""
    base = build_base_state()
    base['train_state']['current_section_id'] = 'S1'
    base['active_trains'] = {
        '99999': {
            'train_id': '99999',
            'status': 'EN_ROUTE',
            'current_section_id': 'S1' # Occupying the first section
        }
    }
    out = run_dynamic_eta_engine(**base)
    stn_a_eta = out['station_wise_etas'][0]
    # The penalty should add 15 minutes to S1 travel time
    assert '[Network: Occupied by 99999]' in stn_a_eta['explanation']
    # Downstream ETA (S2) accumulated delay should be higher than normal due to S1 delay
    assert out['station_wise_etas'][1]['accumulated_delay_min'] > 0

def test_network_scenario_C_cleared():
    """Phase 11: Network condition is cleared."""
    base_occupied = build_base_state()
    base_occupied['train_state']['current_section_id'] = 'S1'
    base_occupied['active_trains'] = {
        '99999': {
            'train_id': '99999',
            'status': 'EN_ROUTE',
            'current_section_id': 'S1'
        }
    }
    out_occupied = run_dynamic_eta_engine(**base_occupied)
    
    # Cleared: 99999 moved out of S1 (to S99)
    base_cleared = build_base_state()
    base_cleared['train_state']['current_section_id'] = 'S1'
    base_cleared['active_trains'] = {
        '99999': {
            'train_id': '99999',
            'status': 'EN_ROUTE',
            'current_section_id': 'S99'
        }
    }
    out_cleared = run_dynamic_eta_engine(**base_cleared)
    
    travel_occupied = out_occupied['station_wise_etas'][0]['predicted_travel_time_min']
    travel_cleared = out_cleared['station_wise_etas'][0]['predicted_travel_time_min']
    
    # Recalculates back based on updated state
    assert travel_cleared < travel_occupied
    assert '[Network: Occupied by 99999]' not in out_cleared['station_wise_etas'][0]['explanation']
