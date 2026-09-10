import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

print("Generating Synthetic Railway Dataset...")

NUM_DAYS = 90
TRAINS = [
    {"id": "12004", "type": "Shatabdi", "priority": 1, "speed_factor": 1.2},
    {"id": "12301", "type": "Rajdhani", "priority": 1, "speed_factor": 1.25},
    {"id": "14163", "type": "Express", "priority": 2, "speed_factor": 0.9},
    {"id": "19031", "type": "Passenger", "priority": 3, "speed_factor": 0.7},
]

ROUTE_STATIONS = ["NDLS", "GZB", "ALJN", "CNB", "LKO"]
SECTIONS = []
for i in range(len(ROUTE_STATIONS)-1):
    dist = np.random.randint(40, 150)
    SECTIONS.append({
        "section_id": f"{ROUTE_STATIONS[i]}-{ROUTE_STATIONS[i+1]}",
        "origin_station": ROUTE_STATIONS[i],
        "destination_station": ROUTE_STATIONS[i+1],
        "distance_km": dist,
        "base_time": int((dist / 80) * 60) 
    })

start_date = datetime(2025, 1, 1)
data = []

np.random.seed(42) # Reproducible

for day in range(NUM_DAYS):
    current_date = start_date + timedelta(days=day)
    is_winter = current_date.month in [1, 12, 11]
    base_fog = np.random.choice([0, 1, 2], p=[0.7, 0.2, 0.1]) if is_winter else 0
    
    for train in TRAINS:
        current_delay = max(0, int(np.random.normal(10, 20))) 
        
        for section in SECTIONS:
            weather_condition = "Clear"
            if base_fog == 2: weather_condition = "Dense Fog"
            elif base_fog == 1: weather_condition = "Light Fog"
            elif np.random.rand() < 0.05: weather_condition = "Heavy Rain"
            
            operational_event = "Normal"
            if np.random.rand() < 0.01:
                operational_event = np.random.choice(["Signal Failure", "Loco Issue", "Cattle Runover"])
                
            congestion_level = round(np.random.uniform(0.1, 1.0), 2)
            
            delay_factor = 0
            if weather_condition == "Dense Fog": delay_factor += np.random.randint(30, 90)
            if weather_condition == "Light Fog": delay_factor += np.random.randint(10, 30)
            if operational_event != "Normal": delay_factor += np.random.randint(45, 180)
            
            delay_factor += int(congestion_level * 20)
            delay_factor = max(0, delay_factor - ((3 - train["priority"]) * 10))
            
            dwell_time = np.random.randint(2, 10)
            
            scheduled_time = section["base_time"]
            ideal_time = scheduled_time / train["speed_factor"]
            
            actual_time = ideal_time + delay_factor + dwell_time
            new_delay = current_delay + (actual_time - scheduled_time)
            
            record = {
                "date": current_date.strftime("%Y-%m-%d"),
                "train_id": train["id"],
                "route_id": "Route_North_1",
                "section_id": section["section_id"],
                "origin_station": section["origin_station"],
                "destination_station": section["destination_station"],
                "distance_km": section["distance_km"],
                "scheduled_section_time_min": scheduled_time,
                "actual_section_time_min": int(actual_time),
                "current_delay_min": int(current_delay),
                "average_speed_kmph": round(section["distance_km"] / (actual_time / 60), 1),
                "congestion_level": congestion_level,
                "weather_condition": weather_condition,
                "operational_event": operational_event,
                "dwell_time_min": dwell_time
            }
            data.append(record)
            current_delay = max(0, int(new_delay))

df = pd.DataFrame(data)

# Splitting Data chronologically prevents leakage
train_end = start_date + timedelta(days=int(NUM_DAYS * 0.7))
val_end = start_date + timedelta(days=int(NUM_DAYS * 0.85))

df['date_ts'] = pd.to_datetime(df['date'])

train_mask = df['date_ts'] < train_end

# Leakage Prevention: Calculate historical moving averages only mapped from the training period.
section_means = df[train_mask].groupby('section_id')['actual_section_time_min'].mean().astype(int).to_dict()
df['historical_section_avg_time'] = df['section_id'].map(section_means)

train_df = df[train_mask].copy()
val_df = df[(df['date_ts'] >= train_end) & (df['date_ts'] < val_end)].copy()
test_df = df[df['date_ts'] >= val_end].copy()

# Drop helper timestamp
for d in [train_df, val_df, test_df, df]:
    d.drop(columns=['date_ts'], inplace=True)

# Save Outputs
os.makedirs("data/raw", exist_ok=True)
os.makedirs("data/processed", exist_ok=True)

df.to_csv("data/raw/synthetic_dataset.csv", index=False)
train_df.to_csv("data/processed/train.csv", index=False)
val_df.to_csv("data/processed/val.csv", index=False)
test_df.to_csv("data/processed/test.csv", index=False)

print(f"Total Rows: {len(df)}")
print(f"Train/Val/Test split: {len(train_df)}/{len(val_df)}/{len(test_df)}")
print("SUCCESS: Datasets built without leakage.")
