# RailPredict AI — Prototype Implementation Plan

## 1. Project Overview

**Project:** RailPredict AI — Dynamic & Context-Aware Train ETA Prediction

**Purpose:** Build a working prototype that demonstrates how a train's future arrival times can be continuously predicted and updated as the train state and railway conditions change.

The prototype is a **simulation-based proof of concept**. It should use synthetic/replay data during development and must not claim to be connected to live Indian Railways RTIS/NTES data unless an authorized live data source is actually integrated.

### Core problem

A useful ETA system should not only answer:

> "Where is the train now?"

It should also estimate:

> "When will the train arrive at each upcoming station as conditions evolve?"

### Core prototype loop

```text
Train State + Route/Section Data + Historical/Context Features
                         ↓
                  Prediction / ETA Engine
                         ↓
              Next-Section Travel Time
                         ↓
             Delay Recovery / Accumulation
                         ↓
             Network-Aware Delay Propagation
                         ↓
              Station-Wise Dynamic ETA
                    + Delay Risk
                + Confidence / Range
                         ↓
                  New Simulation Data
                         ↺
                 Continuous Recalculation
```

---

## 2. Development Philosophy

Build the prototype **incrementally**.

Each stage must:
1. Be implemented independently.
2. Be manually tested.
3. Be verified against expected behavior.
4. Become the foundation for the next stage.

### Antigravity rules

- Inspect the existing implementation before changing code.
- Reuse working components.
- Do not rewrite working code unnecessarily.
- Do not redesign the UI unless specifically requested.
- Do not fabricate AI/model outputs.
- Do not hardcode changing values merely to make the UI look functional.
- Do not claim a feature works until it has been tested.
- Prefer small implementation prompts, one feature at a time.

---

## 3. Current Prototype Status

The current prototype contains the dashboard/UI foundation:

- RailPredict AI Operations dashboard
- Train 12004 — Shatabdi Express display
- Current location, speed and delay
- Next station
- AI ETA display
- Delay risk
- Route map and station markers
- Station-wise ETA table
- Simulation clock
- Start/Pause/Reset controls
- Simulation speed controls
- Disruption scenario buttons
- Simulation event timeline
- "Why did ETA change?" panel

### Current functional state

The simulation clock and basic simulation state have been partially implemented and visually tested.

The following still need implementation and verification:

- Genuine train movement
- Correct baseline ETA calculation
- Dynamic ETA recalculation
- Congestion effects
- Speed restriction effects
- Operational halt
- Previous-vs-new ETA tracking
- Delay propagation
- Delay recovery
- Actual prediction/model integration
- Explainable prediction factors
- Event timeline integration
- Evaluation metrics

The UI must not be treated as proof that these functions exist.

---

# 4. Target Architecture

Keep the first prototype simple. Avoid unnecessary microservices.

```text
                 ┌─────────────────────────┐
                 │ React Operations UI     │
                 └────────────┬────────────┘
                              ↓
                 ┌─────────────────────────┐
                 │ Simulation State        │
                 │ Clock + Train + Events  │
                 └────────────┬────────────┘
                              ↓
                 ┌─────────────────────────┐
                 │ Dynamic ETA Engine      │
                 │                         │
                 │ Baseline ETA            │
                 │ Section Prediction      │
                 │ Delay Adjustment        │
                 │ Propagation             │
                 └────────────┬────────────┘
                              ↓
                 ┌─────────────────────────┐
                 │ Prediction Outputs      │
                 │ Station ETAs             │
                 │ Delay / Risk             │
                 │ Confidence / Range       │
                 └────────────┬────────────┘
                              ↓
                 ┌─────────────────────────┐
                 │ Map / Table / Timeline  │
                 │ Explanation              │
                 └─────────────────────────┘
```

A Python/FastAPI backend and ML service can be introduced where useful, especially for the model, but the initial simulation should remain simple.

---

# 5. Development Phases

## Phase 0 — Codebase Audit

### Goal
Understand the current project before implementing new functionality.

Inspect:
- frontend structure
- components
- state management
- map implementation
- simulation clock
- train data
- route data
- ETA logic
- backend/API
- WebSocket implementation, if present
- existing model code
- disruption handlers

Create a short map of:

```text
File → Responsibility → State/Data Used
```

Identify what is:
- functional
- hardcoded
- simulated
- placeholder
- disconnected

Do not perform a major refactor during this phase.

---

## Phase 1 — Simulation Engine

### Goal
Create a reliable deterministic railway simulation.

### 1.1 Simulation clock
Implement:
- Start
- Pause
- Reset
- 1x
- 5x
- 10x
- 60x

The clock must be application state, not merely visual animation.

### 1.2 Train state

At minimum:

```text
trainId
currentSection
sectionProgress
currentSpeed
currentDelay
simulationTime
nextStation
```

### 1.3 Route model

Represent the route as ordered sections/stations.

Example:

```text
NDLS → GZB → ALJN → CNB
```

Each section should contain suitable information such as:
- section ID
- from station
- to station
- distance
- base running time
- scheduled arrival/departure

### 1.4 Train movement

Movement must be derived from simulation state.

The same state must control:
- map position
- current section
- progress
- next station
- displayed speed

Do not use an independent frontend animation.

### Acceptance test

```text
RESET
→ START
→ clock advances
→ train moves
→ section progress changes
→ current section changes
→ next station changes
→ PAUSE
→ movement stops
→ START
→ movement resumes
→ RESET
→ original state restored
```

---

## Phase 2 — Baseline ETA Engine

### Goal
Create a correct deterministic ETA system before introducing ML.

Do not initially claim that XGBoost predicts the whole ETA.

For the current section, use an appropriate travel-time calculation based on:
- remaining distance
- effective speed

For future sections, estimate:

```text
ETA = current simulation time
    + remaining section travel times
    + applicable dwell times
```

Use the route representation actually implemented.

### Inputs

At minimum:
- simulation time
- current position
- current section
- current speed
- remaining distance/travel time
- section base running time
- station dwell time
- current delay

### Outputs

For every upcoming station:
- station
- predicted ETA
- delay
- risk

### Acceptance test

As the train moves:
- position changes
- remaining travel time changes
- ETA remains connected to simulation state
- reaching a station changes the next station
- future ETAs update

No disruption logic yet.

---

## Phase 3 — ETA History and Dynamic Change

### Goal
Show genuine prediction updates.

For each station maintain:

```text
previousETA
newETA
etaChange
```

Calculate:

```text
etaChange = newETA - previousETA
```

Never hardcode the displayed change.

Example only:

```text
GZB   20:04 → 20:11   +7m
ALJN  21:19 → 21:28   +9m
CNB   22:55 → 23:07   +12m
```

Actual values must come from the engine.

---

## Phase 4 — Disruption Framework

### Goal
Create a common event model.

Represent an event approximately as:

```text
eventId
type
affectedSection
startTime
duration
severity
active
createdAt
```

Initial event types:

```text
CONGESTION
SPEED_RESTRICTION
OPERATIONAL_HALT
```

Build the common event state before implementing every event behavior.

---

## Phase 5 — Congestion

### Goal
Demonstrate the first meaningful dynamic prediction scenario.

Flow:

```text
Normal operation
→ Inject congestion
→ affected section becomes slower
→ predicted travel time changes
→ next-station ETA changes
→ downstream ETAs change
```

When congestion is triggered:
1. Create the event.
2. Identify affected section.
3. Modify simulation/network state.
4. Recalculate section travel time.
5. Recalculate station ETAs.
6. Propagate to downstream stations.
7. Store previous/new ETA.
8. Update risk if implemented.
9. Update timeline.

Do not simply do:

```text
ETA = ETA + 10 minutes
```

The event must affect the underlying calculation.

---

## Phase 6 — Speed Restriction

### Goal
Model temporary lower effective speed.

Flow:

```text
Normal speed
→ speed restriction
→ lower effective speed
→ longer section travel time
→ ETA changes
```

Requirements:
- identify affected section
- apply restriction
- calculate effective speed
- recalculate section travel time
- recalculate station ETAs
- update ETA history
- update timeline

Do not randomly add delay.

---

## Phase 7 — Operational Halt

### Goal
Simulate an operational stop.

When active:
- train movement stops
- simulation clock continues
- position remains fixed
- delay increases according to simulated halt duration
- future ETAs recalculate

When cleared:
- train resumes
- ETA recalculates

---

## Phase 8 — Delay Propagation

### Goal
Demonstrate a central project concept.

Flow:

```text
Disruption
→ section travel time increases
→ GZB ETA changes
→ remaining journey shifts
→ ALJN ETA changes
→ CNB ETA changes
```

Propagation must be calculated through the route model.

Do not hardcode individual downstream delay values.

Future enhancement may include multi-train interaction, shared sections and operational constraints, but the first prototype should demonstrate the concept with a controlled scenario.

---

## Phase 9 — Delay Recovery / Accumulation

### Goal
Model changing delay over future sections.

Basic concept:

```text
Updated delay
= current delay
+ new section delay
- possible recovery
```

Recovery must be bounded by realistic simulation assumptions.

Avoid nonsensical outputs such as a small current delay suddenly producing an enormous negative recovery.

Acceptance scenario:

```text
Initial delay
→ disruption
→ delay increases
→ disruption clears
→ favorable section
→ partial recovery
```

---

## Phase 10 — XGBoost Prediction Layer

### Goal
Introduce ML only after the deterministic system works.

Define a clear prediction target.

Recommended first target:

> Predict expected travel time or travel-time deviation for the next railway section.

Avoid vague claims such as:

> "XGBoost predicts ETA."

Possible features, depending on available data:

```text
current speed
section distance
scheduled section running time
current delay
time of day
day of week
historical section travel time
historical delay
section characteristics
active restriction
congestion indicator
other available context
```

Possible targets:

```text
actual section travel time
```

or:

```text
section travel-time deviation
```

The target must match the dataset.

### Training flow

```text
Historical / synthetic data
→ preprocessing
→ train/validation split
→ XGBoost training
→ prediction
→ evaluation
→ save model
→ prediction API
→ ETA engine
```

Never invent model accuracy.

---

## Phase 11 — Network-Aware Prediction

### Goal
Add railway network context gradually.

Potential factors:
- congestion
- active operational events
- affected sections
- simulated other trains
- shared route sections
- preceding-train delay
- section capacity assumptions

Concept:

```text
Train State
+
Section State
+
Network State
↓
Prediction
```

Do not attempt to build a complete railway traffic-control system.

---

## Phase 12 — Confidence / ETA Range

### Goal
Avoid presenting every prediction as an exact guarantee.

Example:

```text
GZB

ETA: 20:14

Expected range:
20:11 – 20:18

Risk:
Medium
```

The calculation method must be documented.

Do not call an arbitrary range a statistical confidence interval unless the implementation supports that interpretation.

---

## Phase 13 — "Why Did ETA Change?"

### Goal
Explain predictions using actual calculation/model inputs.

Example:

```text
WHY DID ETA CHANGE?

Affected section:
NDLS → GZB

Current speed:
80 → 55 km/h

Section travel-time impact:
+6 min

Existing delay:
+10 min

Estimated recovery:
-2 min

Net ETA change:
+4 min
```

All values must come from the actual engine.

Do not use an LLM to fabricate technical explanations.

---

## Phase 14 — Event Timeline

Automatically record events using simulation time.

Example:

```text
12:00  Simulation started
12:07  Train entered NDLS → GZB
12:12  Congestion detected
12:12  ETA recalculation triggered
12:12  GZB ETA updated
12:13  Downstream ETAs updated
12:20  Congestion cleared
12:20  ETA recalculated
```

---

## Phase 15 — Map Integration

The map should clearly show:
- route
- stations
- train position
- current section
- affected section
- disruption location

The train marker must be driven by simulation state.

Avoid unnecessary animations.

---

## Phase 16 — Evaluation

### Goal
Demonstrate that predictions can be measured.

Possible metrics:
- MAE
- RMSE
- Median Absolute Error
- percentage within ±5 minutes
- percentage within ±10 minutes
- percentage within ±15 minutes
- intermediate-station ETA accuracy
- early delay detection
- recovery prediction performance

### Baseline

Use a clearly defined baseline, for example:

```text
Scheduled time + current observed delay
```

The exact baseline must be documented.

Never put an accuracy percentage in the presentation until it has actually been measured on a defined test set.

---

# 6. Data Strategy

## Stage A — Synthetic data

Initially use clearly labelled synthetic data for:
- routes
- stations
- section distances
- base running times
- historical section travel times
- delays
- congestion
- speed restrictions
- operational halts

Dashboard label:

```text
SIMULATION MODE
SYNTHETIC / REPLAY DATA
```

## Stage B — Historical/replay data

If a suitable dataset becomes available:

```text
Historical data
→ preprocessing
→ replay as time sequence
→ simulation
→ prediction
```

## Stage C — Authorized live data

Only implement after obtaining an authorized, technically usable source.

Never claim live RTIS/NTES integration without actual access.

---

# 7. Final SIH Demonstration Scenario

Use one controlled scenario rather than trying to demonstrate every feature.

```text
1. RESET
2. START SIMULATION
3. Train moves on map
4. Clock advances
5. Current section/progress updates
6. Baseline ETA updates
7. INJECT CONGESTION
8. Affected section becomes slower
9. Prediction recalculates
10. Next station ETA changes
11. Downstream ETAs change
12. "Why did ETA change?" shows actual factors
13. Event appears in timeline
14. CLEAR DISRUPTION
15. ETA recalculates
16. Recovery/updated delay appears if implemented
17. Train continues
```

This is the primary prototype demonstration.

---

# 8. Technology Strategy

### Frontend
- React
- Tailwind CSS
- Leaflet/map library

### Backend
- Python
- FastAPI

### ML
- XGBoost
- scikit-learn for preprocessing/evaluation

### Data
Initially:
- JSON/CSV
- in-memory simulation state

Later, if required:
- PostgreSQL / TimescaleDB

### Real-time
Use WebSockets only if the implementation actually benefits from them.

Do not add Kafka or complex infrastructure simply to make the architecture look advanced.

---

# 9. What NOT to Build

The prototype is not intended to become:
- a complete railway control system
- a replacement for RTIS
- a signal-control system
- a timetable-generation system
- a ticket booking platform
- a PNR system
- a generic "Where Is My Train?" tracker
- a complete national railway digital twin
- a full railway traffic optimization platform

The main contribution is:

> **Dynamic prediction of future train arrival times using current train state, section-level travel-time prediction, operational context and downstream delay effects.**

---

# 10. Definition of Done

The prototype is functionally complete when a judge can perform:

```text
RESET
↓
START
↓
Train moves
↓
ETA updates
↓
Inject disruption
↓
Prediction changes
↓
Station ETA changes
↓
Downstream impact appears
↓
Reason is displayed
↓
Clear disruption
↓
ETA recalculates
↓
Recovery/updated delay appears
```

The team must be able to explain:
1. What data enters the system.
2. What the ETA engine calculates.
3. What the ML model predicts.
4. How section travel time is estimated.
5. How delay propagates.
6. How new information triggers recalculation.
7. How the model is evaluated.
8. Which data is synthetic versus real.
9. What is implemented versus proposed for future deployment.

---

# 11. Master Development Checklist

- [x] Initial dashboard UI
- [x] Train information panel
- [x] Route map
- [x] Station-wise ETA UI
- [x] Simulation clock UI
- [x] Basic simulation clock/state
- [ ] Train movement fully verified
- [ ] Baseline ETA engine
- [ ] Dynamic ETA updates
- [ ] ETA history / change calculation
- [ ] Common disruption event model
- [ ] Congestion
- [ ] Speed restriction
- [ ] Operational halt
- [ ] Delay propagation
- [ ] Delay recovery/accumulation
- [ ] XGBoost prediction
- [ ] Network-aware features
- [ ] Risk calculation
- [ ] Uncertainty / ETA range
- [ ] Prediction explanation
- [ ] Event timeline integration
- [ ] Evaluation metrics
- [ ] Baseline comparison
- [ ] Final demo scenario
- [ ] Final testing
- [ ] SIH presentation/demo preparation

---

# 12. Manual Knowledge vs Antigravity

## Antigravity can implement
- React components
- simulation state/timer
- UI state
- map marker updates
- event handling
- API scaffolding
- deterministic ETA logic
- data structures
- debugging assistance

## Team should personally understand
- sectional running time
- ETA calculation
- delay accumulation
- delay recovery
- delay propagation
- baseline definition
- ML target
- model features
- train/test split
- evaluation metrics
- why XGBoost is used
- difference between simulation and live railway data

These are the parts most important for technical judging.

---

# 13. Antigravity Prompting Rules

Use **one feature per prompt**.

Good:

```text
Implement only baseline ETA calculation.
Do not modify the UI.
Do not implement ML or disruptions.
```

Then test.

Next:

```text
Implement only congestion.
Use the existing ETA engine.
```

Then test.

Avoid giant prompts that simultaneously request:
- UI redesign
- simulation
- ML training
- APIs
- disruptions
- analytics
- authentication
- animations

Build the system through small, verified increments.

---

# 14. Final Product Layers

## Layer 1 — Simulation

```text
Where is the train?
What is happening now?
```

## Layer 2 — Prediction

```text
How long will the next section take?
What will happen to the delay?
When will the train reach upcoming stations?
```

## Layer 3 — Decision Support

```text
Why did the ETA change?
Which stations are affected?
How severe is the predicted delay?
What happens if the disruption is cleared?
```

Keep these three layers conceptually separate.

---

## Core Project Message

> **RailPredict AI does not simply track the train's current position. It uses the current train state and evolving railway conditions to continuously predict future section travel times and station-wise arrival times, while accounting for delay accumulation, recovery and downstream effects.**
