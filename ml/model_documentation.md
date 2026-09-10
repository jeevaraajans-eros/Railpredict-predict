# XGBoost Next-Section Travel Time Model

## 1. Input Features
The model consumes 9 dynamic and static features carefully modeled after real operational parameters:
- **Numerical:** `scheduled_section_time_min`, `current_delay_min`, `average_speed_kmph`, `congestion_level`, `distance_km`, `dwell_time_min`, `historical_section_avg_time`
- **Categorical:** `weather_condition`, `operational_event`

## 2. Target Variable
- **`actual_section_time_min` (Regression Target):** The exact simulated time taken for the train to clear the section block. Our model predicts this integer mapping directly rather than just predicting pure "delay".

## 3. Preprocessing Pipeline
- **Categorical Variables:** Passed via Scikit-Learn `OneHotEncoder` (ignores unknown inputs in new unobserved situations).
- **Numerical Variables:** Passed through dynamically, as XGBoost fundamentally relies on decision trees which naturally handle unstandardized bounding spaces and scaling.
- **Data Splitting:** Data structurally respects Chronological sorting (70% Train, 15% Val, 15% Test) to strictly enforce zero data knowledge leakage from the future. 

## 4. Model Architecture
- Algorithm: `XGBRegressor` (XGBoost)
- Objective Function: `reg:squarederror`
- Hyperparameters: `n_estimators=150`, `max_depth=5`, `learning_rate=0.1`

## 5. Evaluation Statistics
Metrics evaluated against untouched Test Set constraints:
- **MAE (Mean Absolute Error):** Outlines pure minute variance.
- **RMSE (Root Mean Square Error):** Penalizes extreme outlier delays drastically.
- **R² (Determination):** Tracks proportional variance effectively covered compared to standard mean models.

## 6. Limitations of Prototype Modeling
- **Synthetic Congestion:** `congestion_level` behaves as an uncorrelated statistical parameter locally simulated, rather than accurately querying live pathing capacity from contiguous block bounds.
- **Simulated Operating Failures:** Real world network events generate 'butterfly effects' that propagate wildly; evaluating models locally assumes single-node failures rather than network breakdown topologies.
