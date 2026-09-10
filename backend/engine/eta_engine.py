from typing import List, Dict, Any
from datetime import datetime, timedelta
import sys
import os
import warnings

# Mute sklearn warnings locally during cascade prediction
warnings.filterwarnings('ignore')

# Loosely coupled relative pathing for local script execution
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from ml.predict import load_model, predict_actual_time
from backend.engine.delay_propagation import calculate_downstream_delay, calculate_delay_risk, estimate_confidence_interval

# Initialize Engine Global ML Weight
try:
    eta_model = load_model("ml/models/eta_xgboost_pipeline.pkl")
except Exception as e:
    eta_model = None
    print(f"Engine Warning: XGBoost model not loaded. Switching to scheduled fallback logic. {e}")

def run_dynamic_eta_engine(
    current_time: datetime,
    train_state: Dict[str, Any],
    remaining_route: List[Dict[str, Any]],
    network_conditions: Dict[str, Any]
) -> Dict[str, Any]:
    """
    The Orchestrator. Evaluates the remaining path forward section-by-section.
    """
    current_delay = train_state.get('current_delay_min', 0)
    simulated_clock = current_time
    station_predictions = []
    
    for section in remaining_route:
        # Build feature vector combining Dynamic State with Contextual Route Geometry
        ml_input = {
            'scheduled_section_time_min': section['scheduled_section_time_min'],
            'current_delay_min': current_delay, # Key cascading feature
            'average_speed_kmph': network_conditions.get('average_speed_kmph', 80.0),
            'congestion_level': network_conditions.get('congestion_level', 0.5),
            'weather_condition': network_conditions.get('weather_condition', 'Clear'),
            'distance_km': section['distance_km'],
            'dwell_time_min': section.get('dwell_time_min', 5),
            'historical_section_avg_time': section.get('historical_section_avg_time', section['scheduled_section_time_min']),
            'operational_event': network_conditions.get('operational_event', 'Normal')
        }
        
        predicted_travel_time = 0
        if eta_model:
            predicted_travel_time = int(predict_actual_time(eta_model, ml_input))
        else:
            predicted_travel_time = section['scheduled_section_time_min']
            
        new_delay = calculate_downstream_delay(
            actual_travel_time_min=predicted_travel_time,
            scheduled_travel_time_min=section['scheduled_section_time_min'],
            current_delay_min=current_delay
        )
        
        # Chronological Spatial Forward-Passing
        arrival_time = simulated_clock + timedelta(minutes=predicted_travel_time)
        departure_time = arrival_time + timedelta(minutes=section.get('dwell_time_min', 5))
        
        # Determine the cascading driving factors mathematically
        factors = []
        if current_delay > 0:
            factors.append(f"Initial delay carryover (+{current_delay}m)")
            
        time_diff = predicted_travel_time - section['scheduled_section_time_min']
        
        has_speed_strict = network_conditions.get('average_speed_kmph', 80.0) < 70.0
        has_congestion = network_conditions.get('congestion_level', 0.5) >= 0.7
        has_halt = network_conditions.get('operational_event') != 'Normal'
        
        if time_diff > 0:
            if has_halt: factors.append(f"Operational halt slowing section (+{time_diff}m)")
            elif has_congestion: factors.append(f"Congestion impact (+{time_diff}m)")
            elif has_speed_strict: factors.append(f"Speed restriction (+{time_diff}m)")
            else: factors.append(f"Model-computed trajectory slowdown (+{time_diff}m)")
        elif time_diff < 0:
            factors.append(f"Section traversal delay recovery (-{abs(time_diff)}m)")
            
        if new_delay > current_delay:
            factors.append(f"Net downstream propagation accumulation")
        elif new_delay < current_delay:
            factors.append(f"Successful propagation recovery")
        elif new_delay == 0 and current_delay == 0:
            factors.append("Nominal bounds tracking securely")

        explanation = " → ".join(factors)

        # Format ETA Delta Output incorporating prediction logic vectors
        station_predictions.append({
            'station': section['destination_station'],
            'predicted_travel_time_min': predicted_travel_time,
            'accumulated_delay_min': new_delay,
            'predicted_arrival': arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            'predicted_departure': departure_time.strftime("%Y-%m-%d %H:%M:%S"),
            'delay_risk': calculate_delay_risk(new_delay),
            'confidence_interval': estimate_confidence_interval(new_delay),
            'explanation': explanation
        })
        
        # Feed-forward current_delay and clock state to the next iter step
        current_delay = new_delay
        simulated_clock = departure_time
        
    return {
        'initial_train_state': train_state,
        'station_wise_etas': station_predictions,
        'final_destination_delay_min': current_delay
    }
