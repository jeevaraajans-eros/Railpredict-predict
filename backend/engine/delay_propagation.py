def calculate_downstream_delay(actual_travel_time_min: int, scheduled_travel_time_min: int, current_delay_min: int) -> int:
    """
    Deterministically computes the new cascading delay immediately after exiting a section block.
    Formula: D_new = D_current + (T_actual - T_scheduled)
    A train running faster than schedule represents negative deviation, effectively recovering lost time.
    """
    new_delay = current_delay_min + (actual_travel_time_min - scheduled_travel_time_min)
    # Delay mathematically cannot be negative in railway context (early arrivals hold at outers usually or map to 0 delay)
    return max(0, int(new_delay))

def calculate_delay_risk(predicted_delay_min: int) -> str:
    """
    Simple severity classification for UI/Dashboard.
    """
    if predicted_delay_min <= 15:
        return "Low"
    elif predicted_delay_min <= 45:
        return "Medium"
    else:
        return "High"

def estimate_confidence_interval(predicted_delay_min: int) -> dict:
    """
    Calculates a variance margin predicting best/worst-case limits.
    """
    margin = max(5, int(predicted_delay_min * 0.15)) 
    return {
        "lower_bound_min": max(0, predicted_delay_min - margin), 
        "upper_bound_min": predicted_delay_min + margin
    }
