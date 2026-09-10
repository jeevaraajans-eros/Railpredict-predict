# RailPredict AI 🚄

Dynamic & Context-Aware Train ETA Prediction System prototype.

## Project Monorepo Structure

*   `backend/`: FastAPI application handling API, WebSocket, and predicting logic flow.
*   `frontend/`: React + Vite application for real-time visualization dashboard and maps.
*   `ml/`: Model training scripts, feature engineering, and pickled XGBoost models.
*   `data/`:
    *   `raw/`: Unprocessed/simulated historical data logs.
    *   `processed/`: Cleaned data ready for model training.
*   `simulator/`: Script to simulate real-time train movement and push updates to the backend.
*   `docs/`: Architecture and development documentation.

## Running the Backend

```powershell
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```
Navigate to `http://localhost:8000/docs` to see the API documentation.

## Running the Frontend

```powershell
cd frontend
npm install
npm run dev
```
Navigate to the local URL provided by Vite (usually `http://localhost:5173`).
