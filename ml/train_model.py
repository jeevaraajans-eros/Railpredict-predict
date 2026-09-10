import pandas as pd
import numpy as np
import xgboost as xgb
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
import joblib
import os

print("Starting XGBoost Model Training...")

# 1. Load Data
try:
    train_df = pd.read_csv("data/processed/train.csv")
    val_df = pd.read_csv("data/processed/val.csv")
    test_df = pd.read_csv("data/processed/test.csv")
except Exception as e:
    print(f"Error loading datasets: {e}")
    exit(1)

# Define Features and Target
FEATURES = [
    'scheduled_section_time_min',
    'current_delay_min',
    'average_speed_kmph',
    'congestion_level',
    'weather_condition',
    'distance_km',
    'dwell_time_min',
    'historical_section_avg_time',
    'operational_event'
]
TARGET = 'actual_section_time_min'

CATEGORICAL_FEATURES = ['weather_condition', 'operational_event']
NUMERICAL_FEATURES = [f for f in FEATURES if f not in CATEGORICAL_FEATURES]

# Ensure valid data
train_df = train_df.dropna(subset=FEATURES + [TARGET])
val_df = val_df.dropna(subset=FEATURES + [TARGET])
test_df = test_df.dropna(subset=FEATURES + [TARGET])

# 2. Preprocessing
preprocessor = ColumnTransformer(
    transformers=[
        ('num', 'passthrough', NUMERICAL_FEATURES),
        ('cat', OneHotEncoder(handle_unknown='ignore', sparse_output=False), CATEGORICAL_FEATURES)
    ])

# 3. Pipeline Design
pipeline = Pipeline(steps=[
    ('preprocessor', preprocessor),
    ('regressor', xgb.XGBRegressor(
        n_estimators=150, 
        learning_rate=0.1, 
        max_depth=5, 
        random_state=42, 
        objective='reg:squarederror'))
])

X_train, y_train = train_df[FEATURES], train_df[TARGET]
X_val, y_val = val_df[FEATURES], val_df[TARGET]
X_test, y_test = test_df[FEATURES], test_df[TARGET]

# 4. Train Model
print("Training XGBoost...")
pipeline.fit(X_train, y_train)

# 5. Evaluate on Validation and Test
y_pred_val = pipeline.predict(X_val)
y_pred_test = pipeline.predict(X_test)

def evaluate(y_true, y_pred, name):
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    r2 = r2_score(y_true, y_pred)
    print(f"\n--- {name} Metrics ---")
    print(f"MAE:  {mae:.2f} minutes")
    print(f"RMSE: {rmse:.2f} minutes")
    print(f"R²:   {r2:.4f}")
    print("-" * 25)

evaluate(y_val, y_pred_val, "Validation")
evaluate(y_test, y_pred_test, "Test")

# 6. Save Model
os.makedirs("ml/models", exist_ok=True)
model_path = "ml/models/eta_xgboost_pipeline.pkl"
joblib.dump(pipeline, model_path)
print(f"\nModel successfully saved to {model_path}")
