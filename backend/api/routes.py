from fastapi import APIRouter, HTTPException, BackgroundTasks
from datetime import datetime
import json
import logging
from backend.models.schemas import SimulationEvent
from backend.engine.eta_engine import run_dynamic_eta_engine
from backend.api.websockets import manager
from backend.store import ACTIVE_TRAINS, ROUTE_DATA, GLOBAL_NETWORK_CONDITIONS, SIMULATION_STATE, EVENT_TIMELINE
from pydantic import BaseModel

class SimControl(BaseModel):
    action: str
    speed_multiplier: int = 1

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/trains")
def get_trains():
    return list(ACTIVE_TRAINS.values())

@router.get("/trains/{train_id}")
def get_train_details(train_id: str):
    if train_id not in ACTIVE_TRAINS:
        raise HTTPException(status_code=404, detail="Train not found")
    return {"train": ACTIVE_TRAINS[train_id], "route": ROUTE_DATA.get(train_id, [])}

@router.get("/trains/{train_id}/eta")
async def get_train_eta(train_id: str):
    if train_id not in ACTIVE_TRAINS:
        raise HTTPException(status_code=404, detail="Train not found")
        
    try:
        engine_output = run_dynamic_eta_engine(
            current_time=SIMULATION_STATE['current_time'],
            train_state=ACTIVE_TRAINS[train_id],
            remaining_route=ROUTE_DATA.get(train_id, []),
            network_conditions=GLOBAL_NETWORK_CONDITIONS
        )
        return engine_output
    except Exception as e:
        logger.error(f"ETA Engine failed: {e}")
        raise HTTPException(status_code=500, detail="Internal ETA Engine Calculation Failed")

@router.get("/trains/{train_id}/prediction")
async def get_train_prediction(train_id: str):
    eta = await get_train_eta(train_id)
    return {"predictions": eta['station_wise_etas']}

async def trigger_eta_recalculation(train_id: str):
    eta = await get_train_eta(train_id)
    message = {
        "type": "ETA_UPDATE",
        "train_id": train_id,
        "data": eta
    }
    await manager.broadcast(json.dumps(message))

@router.post("/simulation/control")
def handle_simulation_control(control: SimControl):
    from backend.store import reset_simulation
    if control.action == "START":
        SIMULATION_STATE['is_running'] = True
        SIMULATION_STATE['speed_multiplier'] = control.speed_multiplier
    elif control.action == "PAUSE":
        SIMULATION_STATE['is_running'] = False
    elif control.action == "SPEED":
        SIMULATION_STATE['speed_multiplier'] = control.speed_multiplier
    elif control.action == "RESET":
        reset_simulation()
    return {"status": "success"}

@router.post("/simulation/event")
async def receive_simulation_event(event: SimulationEvent, background_tasks: BackgroundTasks):
    logger.info(f"Received Simulation Event: {event.event_type} for train {event.train_id}")
    
    if event.train_id not in ACTIVE_TRAINS:
        raise HTTPException(status_code=404, detail="Train not found")
        
    sim_time_str = SIMULATION_STATE['current_time'].strftime("%H:%M:%S")

    # Translate simulation commands to mathematical engine states
    if event.event_type == "congestion":
        active_section = ACTIVE_TRAINS[event.train_id].get('current_section_id')
        if 'active_disruptions' not in GLOBAL_NETWORK_CONDITIONS:
            GLOBAL_NETWORK_CONDITIONS['active_disruptions'] = {}
        GLOBAL_NETWORK_CONDITIONS['active_disruptions'][active_section] = {
            "type": "congestion",
            "severity": event.severity
        }
        GLOBAL_NETWORK_CONDITIONS['congestion_level'] = event.severity
        EVENT_TIMELINE.append({"time": sim_time_str, "event": f"Congestion detected on {active_section}", "type": "WARNING"})
    elif event.event_type == "speed restriction":
        GLOBAL_NETWORK_CONDITIONS['average_speed_kmph'] = 80.0 * (1.0 - event.severity)
        EVENT_TIMELINE.append({"time": sim_time_str, "event": f"Speed drops to {GLOBAL_NETWORK_CONDITIONS['average_speed_kmph']} km/h", "type": "WARNING"})
    elif event.event_type == "operational halt":
        GLOBAL_NETWORK_CONDITIONS['operational_event'] = 'Signal Failure'
        ACTIVE_TRAINS[event.train_id]['current_delay_min'] += int(30 * event.severity)
        EVENT_TIMELINE.append({"time": sim_time_str, "event": f"Operational Halt deployed. +{int(30 * event.severity)}m delay.", "type": "WARNING"})
    elif event.event_type == "clear disruption":
        GLOBAL_NETWORK_CONDITIONS['congestion_level'] = 0.1
        GLOBAL_NETWORK_CONDITIONS['operational_event'] = 'Normal'
        GLOBAL_NETWORK_CONDITIONS['average_speed_kmph'] = 80.0
        GLOBAL_NETWORK_CONDITIONS['active_disruptions'] = {}
        EVENT_TIMELINE.append({"time": sim_time_str, "event": "Clear Disruption authorized. Matrix relaxing.", "type": "INFO"})
        EVENT_TIMELINE.append({"time": sim_time_str, "event": "Delay recovery constraints unlocking dynamically.", "type": "INFO"})
    else:
        raise HTTPException(status_code=400, detail="Invalid event type")
    
    event_msg = {
        "type": "NETWORK_EVENT",
        "event": event.model_dump() if hasattr(event, 'model_dump') else event.dict()
    }
    await manager.broadcast(json.dumps(event_msg))
    
    # Asynchronously recalculate ETA bounds so API returns fast
    background_tasks.add_task(trigger_eta_recalculation, event.train_id)
    return {"status": "Event processed and dynamic ETA recalculation triggered"}
