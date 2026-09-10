import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import joblib
import numpy as np
import warnings
warnings.filterwarnings('ignore')

model = joblib.load('ml/models/eta_xgboost_pipeline.pkl')
for split in ['val', 'test']:
    df = pd.read_csv(f'data/processed/{split}.csv')
    df = df.dropna()
    FEATURES = [
        'scheduled_section_time_min', 'current_delay_min', 'average_speed_kmph',
        'congestion_level', 'weather_condition', 'distance_km', 'dwell_time_min',
        'historical_section_avg_time', 'operational_event'
    ]
    X = df[FEATURES]
    y_true = df['actual_section_time_min']
    y_pred = model.predict(X)
    
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"{split.upper()} - MAE: {mae:.2f}, RMSE: {rmse:.2f}, R2: {r2:.4f}")
