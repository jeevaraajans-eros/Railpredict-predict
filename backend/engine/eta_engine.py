from typing import List, Dict, Any
from datetime import datetime, timedelta
import os
from backend.engine.delay_propagation import calculate_downstream_delay, calculate_delay_risk

# Maximum minutes of delay a single section can recover.
# Prevents nonsensical large negative swings (master plan §9).
MAX_RECOVERY_PER_SECTION_MIN = 5

_ML_MODEL = None
_ML_MODEL_LOADED = False

def _get_ml_model():
    global _ML_MODEL, _ML_MODEL_LOADED
    if not _ML_MODEL_LOADED:
        try:
            from ml.predict import load_model
            model_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', 'ml', 'models', 'eta_xgboost_pipeline.pkl'))
            if os.path.exists(model_path):
                _ML_MODEL = load_model(model_path)
            else:
                _ML_MODEL = None
        except Exception as e:
            print(f"Failed to load ML model: {e}")
            _ML_MODEL = None
        finally:
            _ML_MODEL_LOADED = True
    return _ML_MODEL

def _compute_congestion_multiplier(congestion_level: float) -> float:
    """
    Returns a travel-time multiplier based on network congestion.
    congestion_level 0.0 → no effect (1.0x)
    congestion_level 1.0 → 1.8x travel time (severe)
    Linear interpolation between 0.3 (onset threshold) and 1.0.
    """
    if congestion_level <= 0.3:
        return 1.0
    # Scale from 1.0 at onset to 1.8 at maximum
    excess = (congestion_level - 0.3) / 0.7          # 0..1
    return 1.0 + excess * 0.8


def run_dynamic_eta_engine(
    current_time: datetime,
    train_state: Dict[str, Any],
    remaining_route: List[Dict[str, Any]],
    network_conditions: Dict[str, Any],
    active_trains: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    For every remaining section the engine:
      1. Computes the raw travel time (either ML predicted for active section, or physics-based).
      2. If physics-based, applies a congestion multiplier.
      3. Pro-rates the scheduled section time for the active (partially covered) section.
      4. Calls calculate_downstream_delay() with (actual, scheduled, current_delay).
      5. Caps any single-section recovery at MAX_RECOVERY_PER_SECTION_MIN.
      6. Propagates the updated delay to the next section.
    """
    current_delay = train_state.get('current_delay_min', 0)
    simulated_clock = current_time
    station_predictions = []

    congestion_level = network_conditions.get('congestion_level', 0.1)
    congestion_mult = _compute_congestion_multiplier(congestion_level)
    base_speed = network_conditions.get('average_speed_kmph', 80.0)
    is_operational_halt = network_conditions.get('operational_event', 'Normal') != 'Normal'
    model = _get_ml_model()
    ml_active = False

    accumulated_uncertainty_min = 0.0

    for section in remaining_route:
        total_distance_km = section['distance_km']
        scheduled_section_time = section.get('scheduled_section_time_min', 45)
        is_active_section = (section['section_id'] == train_state.get('current_section_id'))

        # --- 1. Remaining distance for this section ---
        distance_km = total_distance_km
        if is_active_section:
            distance_covered = train_state.get('distance_covered_in_section_km', 0.0)
            distance_km = max(0.0, total_distance_km - distance_covered)

        # Pro-rate the scheduled time to match the remaining distance fraction
        remaining_fraction = (distance_km / total_distance_km) if total_distance_km > 0 else 1.0
        effective_scheduled_time = scheduled_section_time * remaining_fraction

        # --- 2. & 3. Travel time calculation (ML for active, Physics for rest) ---
        ml_prediction_used = False
        
        # Check network occupancy for this section
        occupying_trains = []
        if active_trains:
            for t_id, t_info in active_trains.items():
                if t_id != train_state.get('train_id') and t_info.get('status') == 'EN_ROUTE':
                    if t_info.get('current_section_id') == section['section_id']:
                        occupying_trains.append(t_id)
        
        network_penalty_min = 0
        network_prefix = ""
        if occupying_trains:
            network_penalty_min = 15 * len(occupying_trains)
            network_prefix = f"[Network: Occupied by {', '.join(occupying_trains)}] "

        if is_operational_halt:
            # Train is stationary; position doesn't advance
            actual_travel_time = 0
            explanation_prefix = "Halted."
        else:
            if is_active_section and model:
                try:
                    from ml.predict import predict_actual_time
                    input_features = {
                        'scheduled_section_time_min': section.get('scheduled_section_time_min', 45),
                        'current_delay_min': current_delay,
                        'average_speed_kmph': base_speed,
                        'congestion_level': congestion_level,
                        'weather_condition': network_conditions.get('weather_condition', 'Clear'),
                        'distance_km': distance_km,  # ML model expects remaining distance for active section too
                        'dwell_time_min': section.get('dwell_time_min', 5),
                        'historical_section_avg_time': section.get('historical_section_avg_time', 45),
                        'operational_event': network_conditions.get('operational_event', 'Normal')
                    }
                    actual_travel_time = predict_actual_time(model, input_features)
                    actual_travel_time += network_penalty_min
                    # Because ML intrinsically models congestion/weather if trained on it, we do not multiply it further
                    ml_prediction_used = True
                    ml_active = True
                    explanation_prefix = f"{network_prefix}[ML Predicted]"
                except Exception as e:
                    print(f"ML prediction failed: {e}")
            
            if not ml_prediction_used:
                if base_speed > 0:
                    raw_travel_time = (distance_km / base_speed) * 60.0
                else:
                    raw_travel_time = 0.0
                actual_travel_time = (raw_travel_time * congestion_mult) + network_penalty_min
                explanation_prefix = network_prefix.strip() + (" " if network_prefix else "")

        # --- 4. Determine delay change via existing propagation formula ---
        uncapped_new_delay = calculate_downstream_delay(
            actual_travel_time_min=int(actual_travel_time),
            scheduled_travel_time_min=int(effective_scheduled_time),
            current_delay_min=current_delay
        )

        # --- 5. Cap recovery so a single fast section can't wipe all delay ---
        delay_change = uncapped_new_delay - current_delay
        if delay_change < 0:
            # Negative change = recovery; cap it
            capped_change = max(delay_change, -MAX_RECOVERY_PER_SECTION_MIN)
            new_delay = max(0, current_delay + capped_change)
        else:
            new_delay = uncapped_new_delay

        # --- 6. Build a plain-English explanation ---
        delta = new_delay - current_delay
        if delta < 0:
            explanation = (
                f"{explanation_prefix} Section running {abs(delta):.0f} min ahead of schedule "
                f"(actual {actual_travel_time:.0f} min vs scheduled {effective_scheduled_time:.0f} min). "
                f"Delay recovering: {current_delay}m → {new_delay}m. [carryover: partial]"
            ).strip()
        elif delta > 0:
            congestion_note = f" Congestion ×{congestion_mult:.2f}." if (congestion_mult > 1.0 and not ml_prediction_used) else ""
            explanation = (
                f"{explanation_prefix} Section running {delta:.0f} min behind schedule "
                f"(actual {actual_travel_time:.0f} min vs scheduled {effective_scheduled_time:.0f} min).{congestion_note} "
                f"Delay accumulating: {current_delay}m → {new_delay}m. [carryover: extended]"
            ).strip()
        else:
            explanation = (
                f"{explanation_prefix} Section on schedule (actual {actual_travel_time:.0f} min ≈ scheduled {effective_scheduled_time:.0f} min). "
                f"Delay held at {new_delay}m. [carryover: unchanged]"
            ).strip()

        arrival_time = simulated_clock + timedelta(minutes=int(actual_travel_time))
        departure_time = arrival_time + timedelta(minutes=section.get('dwell_time_min', 5))

        # Calculate uncertainty based on state
        base_unc = distance_km * 0.05
        current_unc = base_unc * (1.0 + congestion_level)
        if is_operational_halt:
            current_unc += 10.0
        if occupying_trains:
            current_unc += (5.0 * len(occupying_trains))
        if ml_prediction_used:
            current_unc = max(current_unc, 6.31) # XGBoost RMSE Test threshold
            
        accumulated_uncertainty_min += current_unc
        
        lower_bound = arrival_time - timedelta(minutes=int(accumulated_uncertainty_min * 0.25))
        upper_bound = arrival_time + timedelta(minutes=int(accumulated_uncertainty_min * 0.75))
        
        if accumulated_uncertainty_min < 10:
            confidence = 'High'
        elif accumulated_uncertainty_min < 25:
            confidence = 'Medium'
        else:
            confidence = 'Low'

        station_predictions.append({
            'station': section['destination_station'],
            'predicted_travel_time_min': int(actual_travel_time),
            'accumulated_delay_min': new_delay,
            'predicted_arrival': arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            'predicted_departure': departure_time.strftime("%Y-%m-%d %H:%M:%S"),
            'lower_bound': lower_bound.strftime("%Y-%m-%d %H:%M:%S"),
            'upper_bound': upper_bound.strftime("%Y-%m-%d %H:%M:%S"),
            'confidence': confidence,
            'delay_risk': calculate_delay_risk(new_delay),
            'delay_change_min': round(delta, 1),
            'confidence_interval': [
                int(-accumulated_uncertainty_min * 0.25),
                int(accumulated_uncertainty_min * 0.75)
            ],
            'explanation': explanation
        })

        simulated_clock = departure_time
        current_delay = new_delay   # propagate to next section

    final_delay = station_predictions[-1]['accumulated_delay_min'] if station_predictions else train_state.get('current_delay_min', 0)

    return {
        'initial_train_state': {k: v for k, v in train_state.items() if k != 'latest_eta'},
        'station_wise_etas': station_predictions,
        'final_destination_delay_min': final_delay,
        'causal_breakdown': [
            {"label": "XGBoost Engine", "value": "Active" if ml_active else "Inactive"},
            {"label": "Congestion Multiplier", "value": f"{congestion_mult:.2f}x"},
            {"label": "Recovery Cap (per section)", "value": f"{MAX_RECOVERY_PER_SECTION_MIN} min"},
            {"label": "Simulation Base", "value": "Active"}
        ]
    }


