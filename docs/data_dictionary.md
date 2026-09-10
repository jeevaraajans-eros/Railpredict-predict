# Synthetic Dataset Data Dictionary

> **DISCLAIMER:** This dataset is **100% SYNTHETIC and SIMULATED**. It does not contain or represent actual Indian Railways operational data. It is constructed solely for the purpose of training and evaluating the prototype XGBoost ETA Predictor.

## Data Source
Generated via `data/generate_dataset.py` using randomized distributions patterned after standard railway physics (distance, priority constraints, line capacity limitations) and meteorological events.

## File Structure
*   `data/raw/synthetic_dataset.csv`: The complete synthesized timeline.
*   `data/processed/train.csv`: Chronological Train split (first 70% of days).
*   `data/processed/val.csv`: Chronological Validation split (next 15% of days).
*   `data/processed/test.csv`: Chronological Test split (final 15% of days).
*Note: A strict chronological split guarantees zero data leakage since the ML model evaluates strictly on "future" simulated days.*

## Columns

| Column | Data Type | Description |
| :--- | :--- | :--- |
| `date` | Date (YYYY-MM-DD) | The simulated date of the section run. |
| `train_id` | String | Unique identifier for the train (e.g., '12004'). |
| `route_id` | String | The corridor identifier. |
| `section_id` | String | Unique identifier composed of `Origin-Destination`. |
| `origin_station` | String | Departure station base code. |
| `destination_station` | String | Arrival station base code. |
| `distance_km` | Float | Physical distance of the block section in kilometers. |
| `scheduled_section_time_min` | Integer | Baseline travel time allowed by the static timetable. |
| `actual_section_time_min` | Integer | **TARGET (y)**: Simulated exact time containing delays. |
| `current_delay_min` | Integer | Cascading delay carried entering this section. |
| `average_speed_kmph` | Float | Rate derived from distance over actual time. |
| `congestion_level` | Float | Multiplier randomly generated between 0.1 (Free track) and 1.0 (Congested). |
| `weather_condition` | Category | 'Clear', 'Light Fog', 'Dense Fog', 'Heavy Rain'. |
| `operational_event` | Category | 'Normal', 'Loco Issue', 'Signal Failure', 'Cattle Runover'. |
| `dwell_time_min` | Integer | The platform waiting halt at the origin station. |
| `historical_section_avg_time`| Integer | Baseline static historical moving average (Calculated exclusively off the `Train` split to prevent future-data leakage!). |
