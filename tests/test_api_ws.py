import pytest
from fastapi.testclient import TestClient
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from backend.main import app

client = TestClient(app)

def test_dataset_api_endpoints():
    response = client.get("/trains")
    assert response.status_code == 200
    assert len(response.json()) > 0

def test_eta_calculation_endpoint():
    response = client.get("/trains/12004/eta")
    assert response.status_code == 200
    data = response.json()
    assert "station_wise_etas" in data
    assert len(data['station_wise_etas']) > 0

def test_simulation_events_webhook():
    payload = {
        "train_id": "12004",
        "event_type": "congestion",
        "severity": 0.8,
        "details": "Automated Pytest Disruption Validation"
    }
    response = client.post("/simulation/event", json=payload)
    assert response.status_code == 200
    # Confirms webhook structurally accepted the mutation constraints
    assert "recalculation triggered" in response.json()['status']

def test_websocket_updates_logic():
    with client.websocket_connect("/ws/live") as websocket:
        # Trigger an API event locally pushing constraint bounds directly forcing asynchronous ETA engine matrix evaluation
        payload = {
            "train_id": "12004",
            "event_type": "clear disruption",
            "severity": 0.0
        }
        client.post("/simulation/event", json=payload)
        
        # Test client strictly intercepts broadcasted array from background evaluation loop correctly routing
        data = websocket.receive_json()
        assert data['type'] in ['NETWORK_EVENT', 'ETA_UPDATE']
