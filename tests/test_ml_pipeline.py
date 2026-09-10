import pytest
import pandas as pd
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml.predict import load_model, predict_actual_time

@pytest.fixture
def model():
    # Load identical pickle state architecture utilized by dynamic operational engines
    return load_model("ml/models/eta_xgboost_pipeline.pkl")

def test_dataset_preprocessing_features():
    # Synthetically generated historical chronological dataset structural validations
    df = pd.read_csv("data/processed/train.csv")
    assert not df.empty
    features = ['scheduled_section_time_min', 'current_delay_min', 'congestion_level']
    for f in features:
        assert f in df.columns

def test_ml_prediction_bounds(model):
    test_input = {
        'scheduled_section_time_min': 45,
        'current_delay_min': 0,
        'average_speed_kmph': 80.0,
        'congestion_level': 0.1,
        'weather_condition': 'Clear',
        'distance_km': 60.0,
        'dwell_time_min': 5,
        'historical_section_avg_time': 45,
        'operational_event': 'Normal'
    }
    # Validates deterministic bounds structure logic mapping close back to schedule constraints reliably
    pred = predict_actual_time(model, test_input)
    assert 30 <= pred <= 60

def test_ml_priority_congestion_sensitivity(model):
    test_input_normal = {
        'scheduled_section_time_min': 45, 'current_delay_min': 0, 'average_speed_kmph': 80.0,
        'congestion_level': 0.1, 'weather_condition': 'Clear', 'distance_km': 60.0,
        'dwell_time_min': 5, 'historical_section_avg_time': 45, 'operational_event': 'Normal'
    }
    
    test_input_congested = test_input_normal.copy()
    test_input_congested['congestion_level'] = 1.0 # Force extreme topological strain
    
    pred_normal = predict_actual_time(model, test_input_normal)
    pred_congested = predict_actual_time(model, test_input_congested)
    
    # Explicitly verify the core pipeline mechanism validates physics: 
    # Congestion dynamically enforces mathematical node traversal slowdown automatically via learned logic!
    assert pred_congested > pred_normal
