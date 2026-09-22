import pandas as pd
import numpy as np
from sklearn.metrics import mean_absolute_error, mean_squared_error
import joblib
import json
import os
import warnings

warnings.filterwarnings('ignore')

def calculate_metrics(y_true, y_pred):
    mae = float(mean_absolute_error(y_true, y_pred))
    rmse = float(np.sqrt(mean_squared_error(y_true, y_pred)))
    
    diff = np.abs(y_true - y_pred)
    within_5 = float(np.mean(diff <= 5) * 100)
    within_10 = float(np.mean(diff <= 10) * 100)
    within_15 = float(np.mean(diff <= 15) * 100)
    
    return {
        "mae": round(mae, 2),
        "rmse": round(rmse, 2),
        "within_5_min": round(within_5, 2),
        "within_10_min": round(within_10, 2),
        "within_15_min": round(within_15, 2)
    }

def run_evaluation():
    print("==================================================")
    print("      ETA MODEL vs BASELINE EVALUATION            ")
    print("      (SIMULATION/REPLAY EVALUATION)              ")
    print("==================================================\n")
    
    data_path = 'data/processed/test.csv'
    model_path = 'ml/models/eta_xgboost_pipeline.pkl'
    
    if not os.path.exists(data_path):
        print(f"Error: Evaluation data not found at {data_path}")
        return
        
    if not os.path.exists(model_path):
        print(f"Error: Model not found at {model_path}")
        return
        
    df = pd.read_csv(data_path)
    df = df.dropna()
    
    FEATURES = [
        'scheduled_section_time_min', 'current_delay_min', 'average_speed_kmph',
        'congestion_level', 'weather_condition', 'distance_km', 'dwell_time_min',
        'historical_section_avg_time', 'operational_event'
    ]
    
    # Target
    y_true = df['actual_section_time_min']
    
    # Baseline
    y_baseline = df['scheduled_section_time_min']
    
    # Model
    model = joblib.load(model_path)
    y_model = model.predict(df[FEATURES])
    
    print("Target: next-section travel time (actual_section_time_min)")
    print(f"Dataset Size: {len(df)} samples")
    print("Source: Simulated historical replay (No real-world data)\n")
    
    baseline_metrics = calculate_metrics(y_true, y_baseline)
    model_metrics = calculate_metrics(y_true, y_model)
    
    print("--- BASELINE (Scheduled Time) ---")
    print(f"MAE:  {baseline_metrics['mae']:.2f} min")
    print(f"RMSE: {baseline_metrics['rmse']:.2f} min")
    print(f"Accuracy within 5m:  {baseline_metrics['within_5_min']}%")
    print(f"Accuracy within 10m: {baseline_metrics['within_10_min']}%")
    print(f"Accuracy within 15m: {baseline_metrics['within_15_min']}%\n")
    
    print("--- RAILPREDICT AI (XGBoost) ---")
    print(f"MAE:  {model_metrics['mae']:.2f} min")
    print(f"RMSE: {model_metrics['rmse']:.2f} min")
    print(f"Accuracy within 5m:  {model_metrics['within_5_min']}%")
    print(f"Accuracy within 10m: {model_metrics['within_10_min']}%")
    print(f"Accuracy within 15m: {model_metrics['within_15_min']}%\n")
    
    results = {
        "dataset_type": "SIMULATION/REPLAY",
        "target": "actual_section_time_min",
        "baseline_definition": "scheduled_section_time_min",
        "samples_evaluated": len(df),
        "metrics": {
            "model": model_metrics,
            "baseline": baseline_metrics
        }
    }
    
    out_path = "ml/evaluation_results.json"
    with open(out_path, 'w') as f:
        json.dump(results, f, indent=4)
        
    print(f"Evaluation complete. Results saved to {out_path}.")

if __name__ == "__main__":
    run_evaluation()
