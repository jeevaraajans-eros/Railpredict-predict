from typing import List, Dict, Any
from datetime import datetime, timedelta

def run_dynamic_eta_engine(
    current_time: datetime,
    train_state: Dict[str, Any],
    remaining_route: List[Dict[str, Any]],
    network_conditions: Dict[str, Any],
    previous_eta: Dict[str, Any] = None
) -> Dict[str, Any]:
    
    current_delay = train_state.get('current_delay_min', 0)
    simulated_clock = current_time
    station_predictions = []
    
    for section in remaining_route:
        # 1. Identify tracking limits
        is_active_section = (section['section_id'] == train_state.get('current_section_id'))
        section_disruption = network_conditions.get('active_disruptions', {}).get(section['section_id'])
        is_congested = section_disruption and section_disruption.get('type') == 'congestion'
        
        if is_active_section:
            distance_covered = train_state.get('distance_covered_in_section_km', 0.0)
            remaining_distance = max(0.0, section['distance_km'] - distance_covered)
            base_speed = network_conditions.get('average_speed_kmph', 80.0)
            base_time = int((remaining_distance / 80.0) * 60)
            
            if is_congested:
                effective_speed = max(20.0, base_speed * (1.0 - section_disruption.get('severity', 0)))
                predicted_travel_time = int((remaining_distance / effective_speed) * 60)
            else:
                effective_speed = base_speed
                if current_delay > 0:
                    recovery_speed = base_speed * 1.1
                    fastest_time = int((remaining_distance / recovery_speed) * 60)
                    max_recovery = max(0, base_time - fastest_time)
                    recovery_min = min(current_delay, max_recovery)
                    predicted_travel_time = base_time - recovery_min
                else:
                    predicted_travel_time = int((remaining_distance / effective_speed) * 60) if effective_speed > 0 else 0
        else:
            base_time = section.get('scheduled_section_time_min', int((section['distance_km'] / 80.0) * 60))
            if is_congested:
                speed_factor = max(0.25, 1.0 - section_disruption.get('severity', 0))
                predicted_travel_time = int(base_time / speed_factor)
            else:
                if current_delay > 0:
                    max_recovery = int(base_time * 0.1)
                    recovery_min = min(current_delay, max_recovery)
                    predicted_travel_time = base_time - recovery_min
                else:
                    predicted_travel_time = base_time
            
        # Calculate new delay generated or recovered by this section's conditions
        if predicted_travel_time > base_time:
            new_delay = predicted_travel_time - base_time
            current_delay += new_delay
            delay_risk = "HIGH" if is_congested else "MEDIUM"
            explanation = f"Accumulation: +{new_delay}m delay from this section."
        elif predicted_travel_time < base_time:
            recovered = base_time - predicted_travel_time
            current_delay -= recovered
            delay_risk = "LOW"
            explanation = f"Recovery: -{recovered}m delay recovered in this section."
        else:
            delay_risk = "LOW"
            explanation = "Driven safely by physical geographical velocity structures baseline."
            
        arrival_time = simulated_clock + timedelta(minutes=predicted_travel_time)
        departure_time = arrival_time + timedelta(minutes=section.get('dwell_time_min', 5))
        
        station_predictions.append({
            'station': section['destination_station'],
            'predicted_travel_time_min': predicted_travel_time,
            'accumulated_delay_min': current_delay,
            'predicted_arrival': arrival_time.strftime("%Y-%m-%d %H:%M:%S"),
            'predicted_departure': departure_time.strftime("%Y-%m-%d %H:%M:%S"),
            'delay_risk': delay_risk,
            'confidence_interval': [0, 0],
            'explanation': explanation
        })
        
        simulated_clock = departure_time
        
    causal_breakdown = []
    
    if previous_eta:
        old_delay = previous_eta.get('final_destination_delay_min', 0)
        net_change = current_delay - old_delay
        
        if net_change != 0:
            active_section = train_state.get('current_section_id') or "Unknown"
            causal_breakdown.append({"label": "Affected section", "value": active_section})
            
            if net_change > 0:
                section_disruption = network_conditions.get('active_disruptions', {}).get(active_section)
                if section_disruption and section_disruption.get('type') == 'congestion':
                    causal_breakdown.append({"label": "Congestion in upcoming section", "value": "Delay increased"})
                elif network_conditions.get('average_speed_kmph', 80.0) < 75.0:
                    causal_breakdown.append({"label": "Increased section travel time", "value": "Speed restriction"})
                elif network_conditions.get('operational_event') != 'Normal':
                    causal_breakdown.append({"label": "Operational event", "value": "Halt / Delay added"})
                else:
                    causal_breakdown.append({"label": "Downstream delay propagation", "value": "Accumulated delay"})
            else:
                causal_breakdown.append({"label": "Delay recovery", "value": "Improved predicted time"})

            causal_breakdown.append({"label": "Net change", "value": f"{'+' if net_change > 0 else ''}{net_change}m"})
        else:
            causal_breakdown = previous_eta.get('causal_breakdown') or [{"label": "Simulation Base", "value": "Active"}]
    else:
        causal_breakdown = [{"label": "Simulation Base", "value": "Active"}]

    return {
        'station_wise_etas': station_predictions,
        'final_destination_delay_min': current_delay,
        'causal_breakdown': causal_breakdown
    }
