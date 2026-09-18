from typing import List, Dict, Any
from datetime import datetime, timedelta

def run_dynamic_eta_engine(
    current_time: datetime,
    train_state: Dict[str, Any],
    remaining_route: List[Dict[str, Any]],
    network_conditions: Dict[str, Any]
) -> Dict[str, Any]:
    
    current_delay = train_state.get('current_delay_min', 0)
    simulated_clock = current_time
    station_predictions = []
    
    for section in remaining_route:
        # 1. Identify tracking limits
        is_active_section = (section['section_id'] == train_state.get('current_section_id'))
        distance_km = section['distance_km']
        
        # 2. Subtract purely covered geometry dynamically as the train bounds forward
        if is_active_section:
            distance_covered = train_state.get('distance_covered_in_section_km', 0.0)
            distance_km = max(0.0, distance_km - distance_covered)
            
        current_speed = network_conditions.get('average_speed_kmph', 80.0)
        
        # 3. Calculate Base Dynamic ETA natively across physical distances
        if current_speed > 0:
            predicted_travel_time = int((distance_km / current_speed) * 60)
        else:
            predicted_travel_time = 0
            
        arrival_time = simulated_clock + timedelta(minutes=predicted_travel_time)
        departure_time = arrival_time + timedelta(minutes=section.get('dwell_time_min', 5))
        
        station_predictions.append({
            'station': section['destination_station'],
            'predicted_travel_time_min': predicted_travel_time,
            'accumulated_delay_min': current_delay,
            'predicted_arrival': arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            'predicted_departure': departure_time.strftime("%Y-%m-%d %H:%M:%S"),
            'delay_risk': "LOW",
            'confidence_interval': [0, 0],
            'explanation': "Driven safely by physical geographical velocity structures baseline."
        })
        
        simulated_clock = departure_time
        
    return {
        'station_wise_etas': station_predictions,
        'final_destination_delay_min': current_delay,
        'causal_breakdown': [{"label": "Simulation Base", "value": "Active"}]
    }
