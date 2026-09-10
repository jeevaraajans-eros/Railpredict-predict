# RailPredict AI: Dataset Schema Design

This document describes the schema for the `historical_section_runs` dataset, which will be the primary data foundation for the XGBoost ML model designed to predict Next-Section Travel Time. 

> **Important Note on Data Generation:** Our prototype does *not* claim access to live Indian Railways (NTES/COA) operational databases. The dataset designed below reflects exactly what a production ML model would require, but for our prototype, these data points will be structurally simulated using realistic railway physics and delay distributions.

---

## The Target Variable
### 1. `actual_run_time_min` (Integer)
1. **What it represents:** The exact total time in minutes a train took to traverse from the starting station of a section to the ending station.
2. **Why it matters:** This is the Ground Truth label (`y`). The core ML task is predicting this value given the contextual inputs.
3. **Temporality:** Historical (used for training).
4. **Availability:** In reality, derived from Control Office Application (COA) arrival/departure logs. In the prototype, it will be synthetically generated using scheduled times plus injected noise.

---

## Train & Route Context
### 2. `train_no` (Category/String)
1. **What it represents:** The unique identifier of the coaching train (e.g., '12004'). 
2. **Why it matters:** Specific trains have distinct rakes (LHB vs ICF), max permissible speeds (MPS), schedules, and recovery capabilities.
3. **Temporality:** Contextual/Static.
4. **Availability:** Publicly available timetable data. 

### 3. `train_priority_class` (Integer/Category)
1. **What it represents:** Priority level mapping (e.g., 1=Vande Bharat/Rajdhani, 2=Superfast, 3=Express, 4=Passenger).
2. **Why it matters:** Highly critical for modeling traffic resolution. When the network is congested, a high-priority train is given the "clear signal" over a lower-priority train waitlisted on a loop line.
3. **Temporality:** Contextual/Static.
4. **Availability:** Derived statically from Train Type classifications.

---

## Infrastructure & Geography
### 4. `section_id` (String)
1. **What it represents:** Unique identifier for the block section (e.g., `NDLS-CNB` or specifically Station A - Station B).
2. **Why it matters:** Each section possesses unique geographical constraints, gradients, curvature, and Permanent Speed Restrictions (PSR) which form the baseline structural travel time.
3. **Temporality:** Contextual/Static.
4. **Availability:** Static infrastructure maps.

### 5. `distance_km` (Float)
1. **What it represents:** The distance between the start and end of the section.
2. **Why it matters:** Interacts closely with allowable speeds. A fundamental predictor for time.
3. **Temporality:** Contextual/Static.
4. **Availability:** Available publicly.

---

## Time & Delay Metrics
### 6. `scheduled_run_time_min` (Integer)
1. **What it represents:** The official timetable allotment for the section.
2. **Why it matters:** Provides the baseline. The ML model primarily predicts the "deviation" from this baseline rather than absolute time.
3. **Temporality:** Contextual/Static.
4. **Availability:** Publicly available timetable data.

### 7. `arrival_delay_min` (Integer)
1. **What it represents:** The delay time the train had *at the instance it departed* the starting station of this section.
2. **Why it matters:** Trains arriving late often attempt to "make up" time by running at MPS (Delay Recovery), or, conversely, fall further behind due to cascading network constraints (Delay Accumulation). This is the single strongest predictor of dynamic behavior.
3. **Temporality:** Real-time (at inference), Historical (at training).
4. **Availability:** Real NTES data in deployment; injected dynamically by the Python simulator in our prototype.

### 8. `dwell_time_min` (Integer)
1. **What it represents:** How long the train stood at the starting station before beginning the section run.
2. **Why it matters:** Long dwell times (due to parcel unloading, loco reversal, or waiting for clearance) inflate the initial delay.
3. **Temporality:** Real-time/Historical.
4. **Availability:** NTES/COA in reality; mathematically simulated locally for prototype.

---

## Network & Environmental Dynamics
### 9. `section_congestion_index` (Float)
1. **What it represents:** An index (e.g., 0.0 to 1.0) representing how congested the overall route/division is right now.
2. **Why it matters:** A train moving into a congested sector will experience unscheduled halts at outer signals. 
3. **Temporality:** Real-time (Dynamic).
4. **Availability:** In a real deployment, derived from live tracking of all fleet movements within the division. For the prototype, we will randomize this to simulate varying traffic constraints.

### 10. `weather_condition` (Categorical)
1. **What it represents:** Encodings like `Clear`, `Rain`, `Fog`.
2. **Why it matters:** Winter fog (specifically in the Northern zones) enforces strict speed restrictions (e.g., max 60 kmph), guaranteeing massive delays.
3. **Temporality:** Real-time (Dynamic).
4. **Availability:** Real-world weather APIs. In prototype, structurally simulated (e.g., we can artificially "turn on fog" in the simulator).

### 11. `operational_event_flag` (Categorical)
1. **What it represents:** Exceptional disruptions (`Normal`, `Chain Pulling`, `Loco Failure`, `Track Maintenance Block`).
2. **Why it matters:** Non-linear disruptions. When `Loco Failure` is True, predicted run time jumps by hours regardless of train priority.
3. **Temporality:** Real-time (Dynamic/Contextual).
4. **Availability:** Railway exception logs. Injected manually into the simulator API for demonstration purposes during the hackathon.

### 12. `time_of_day_slot` (Categorical)
1. **What it represents:** `Morning (06-12)`, `Afternoon (12-18)`, `Evening (18-00)`, `Night (00-06)`.
2. **Why it matters:** Freight traffic density and maintenance blocks differ heavily by time of day.
3. **Temporality:** Derived Contextual.
4. **Availability:** Automatically calculated from the timestamp.

---

## Summary
By combining **Historical section averages**, **Train identity**, **Current carrying delay**, and **Simulated network congestion/weather**, the XGBoost model will dynamically predict `actual_run_time_min` iteratively across every remaining section to construct the final ETA.
