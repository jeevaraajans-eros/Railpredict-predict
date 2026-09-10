import pandas as pd
import joblib

def load_model(model_path="ml/models/eta_xgboost_pipeline.pkl"):
    """Loads the trained XGBoost preprocessing and prediction pipeline."""
    return joblib.load(model_path)

def predict_actual_time(model, input_features: dict) -> float:
    """Predicts actual travel time for a single section."""
    df = pd.DataFrame([input_features])
    prediction = model.predict(df)
    return round(prediction[0], 2)

if __name__ == "__main__":
    print("\n--- Running Prediction Test Script ---")
    model = load_model()
    
    # Simple Test Case matching our schema variables
    test_case = {
        'scheduled_section_time_min': 55,
        'current_delay_min': 15,
        'average_speed_kmph': 80.0,
        'congestion_level': 0.8,
        'weather_condition': 'Light Fog',
        'distance_km': 75.0,
        'dwell_time_min': 5,
        'historical_section_avg_time': 60,
        'operational_event': 'Normal'
    }
    
    pred_time = predict_actual_time(model, test_case)
    
    print("Input Conditions:")
    for k, v in test_case.items():
        print(f"  {k}: {v}")
    print(f"\n>> Predicted Actual Travel Time: {pred_time} minutes")
    print(f">> Expected Delay added this section: {round(pred_time - test_case['scheduled_section_time_min'], 2)} minutes")
