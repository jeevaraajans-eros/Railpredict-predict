# Dynamic ETA Engine: Mathematical Flow

The RailPredict AI Engine breaks away from traditional static standard-average tables by utilizing a **Markov-Chain-style Iterative Forward Propagation Algorithm**.

## 1. Modular Separation Components
*   **ML Predictor Block (`ml.predict.predict_actual_time`):** Treats a localized block section prediction asynchronously given bounded static node-inputs.
*   **Delay Propagation Module (`backend.engine.delay_propagation`):** Pure deterministic cascade logic. Handles deterministic summation mapping, bounding, and variance risk extrapolation.
*   **Dynamic ETA Engine (`backend.engine.eta_engine`):** The chronometric orchestration event loop.

## 2. Iterative Mathematical Flow
Let:
*   $T_{sch}$ = Scheduled section traversal time
*   $T_{pred}$ = ML Predicted actual section traversal time
*   $D_n$ = Current delay entering section $n$
*   $W_n$ = Platform Dwell time at station $n$

**Step 1: Section Prediction Inference**
$$ T_{pred} = f_{XGBoost}(T_{sch}, D_n, Congestion, Weather, Distance, ...) $$

**Step 2: Propagation Logic (Recovery vs Accumulation)**
$$ \Delta Delay = T_{pred} - T_{sch} $$
$$ D_{n+1} = \max(0, D_n + \Delta Delay) $$

**Step 3: Temporal Progression Stepping**
$$ ETA_{arrival(n+1)} = Clock_{n} + T_{pred} $$
$$ Clock_{n+1} = ETA_{arrival(n+1)} + W_{n+1} $$

## 3. Propagation Cascade Example
If a train is 15 minutes late entering Section 1 ($D_1=15$), and encounters a congested block where the ML predicts it will lose 5 extra mathematical minutes compared to its strict schedule ($\Delta Delay=+5$):
- $D_2 = 15 + 5 = 20 \text{ minutes late arrival at Section 2}$.

The engine then inherently passes $D_2 = 20$ into the inputs for Section 2 processing phase dynamically. 

If Section 2 is completely clear and historically allows this High-priority train to physically recover 5 minutes to limit trailing blocks ($\Delta Delay=-5$):
- $D_3 = 20 - 5 = 15 \text{ minutes late output}$.

This algorithm allows delays to organically bubble constraints or be 'soaked up' by trailing nodes without statically inflating absolute timeline arrival expectations!
