import asyncio
from datetime import datetime, timedelta
import logging
import json
from backend.store import ACTIVE_TRAINS, ROUTE_DATA, SIMULATION_STATE, GLOBAL_NETWORK_CONDITIONS
from backend.api.websockets import manager
from backend.engine.eta_engine import run_dynamic_eta_engine

logger = logging.getLogger(__name__)

async def simulation_loop():
    logger.info("Chronological Simulation Engine Mounted.")
    while True:
        await asyncio.sleep(1.0)
        
        if not SIMULATION_STATE.get('is_running', False):
            continue
            
        # 1 real second = N simulation minutes
        advance_minutes = SIMULATION_STATE.get('speed_multiplier', 1)
        SIMULATION_STATE['current_time'] += timedelta(minutes=advance_minutes)
        
        for train_id, train in ACTIVE_TRAINS.items():
            if train.get('status') != 'EN_ROUTE':
                continue
                
            route = ROUTE_DATA.get(train_id, [])
            current_speed = GLOBAL_NETWORK_CONDITIONS.get('average_speed_kmph', 80.0)
            
            # Calculate geometric mapping step
            distance_advanced = (current_speed / 60.0) * advance_minutes
            train['distance_covered_in_section_km'] += distance_advanced
            
            # Lookup exact current geometry
            current_section = next((s for s in route if s['section_id'] == train['current_section_id']), None)
            
            if current_section:
                if train['distance_covered_in_section_km'] >= current_section['distance_km']:
                    # Node completely crossed - anchor to next station
                    train['current_station'] = current_section['destination_station']
                    train['distance_covered_in_section_km'] = 0.0
                    
                    idx = route.index(current_section)
                    if idx + 1 < len(route):
                        train['current_section_id'] = route[idx + 1]['section_id']
                    else:
                        train['status'] = 'COMPLETED'
                        train['current_section_id'] = None
                        
            # Execute native ETA generation dynamically based on topological progression
            if train['current_section_id']:
                current_idx = next((i for i, s in enumerate(route) if s['section_id'] == train['current_section_id']), 0)
                remaining_route = route[current_idx:]
                try:
                    engine_output = run_dynamic_eta_engine(
                        current_time=SIMULATION_STATE['current_time'],
                        train_state=train,
                        remaining_route=remaining_route,
                        network_conditions=GLOBAL_NETWORK_CONDITIONS
                    )
                    train['latest_eta'] = engine_output
                except Exception as e:
                    logger.error(f"XGBoost Cascade Failure: {e}")
                    
        # Synchronous transmission of universal matrices
        tick_data = {
            "type": "SIMULATION_TICK",
            "time": SIMULATION_STATE['current_time'].strftime("%Y-%m-%d %H:%M:%S"),
            "trains": ACTIVE_TRAINS,
            "network": GLOBAL_NETWORK_CONDITIONS
        }
        await manager.broadcast(json.dumps(tick_data))
