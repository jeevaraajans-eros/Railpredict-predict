import asyncio
from datetime import datetime, timedelta
import logging
import json
from backend.store import ACTIVE_TRAINS, ROUTE_DATA, SIMULATION_STATE, GLOBAL_NETWORK_CONDITIONS, EVENT_TIMELINE, STATION_COORDS
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
            
            section_disruption = GLOBAL_NETWORK_CONDITIONS.get('active_disruptions', {}).get(train.get('current_section_id'))
            if section_disruption and section_disruption.get('type') == 'congestion':
                effective_speed = max(20.0, current_speed * (1.0 - section_disruption.get('severity', 0)))
            else:
                effective_speed = current_speed
            
            if GLOBAL_NETWORK_CONDITIONS.get('operational_event') != 'Normal':
                distance_advanced = 0.0
                train['current_delay_min'] += advance_minutes
            else:
                distance_advanced = (effective_speed / 60.0) * advance_minutes
            
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
                        
                # Update current_section to reflect any completion of the previous node
                current_section = next((s for s in route if s['section_id'] == train['current_section_id']), None)
                
            if current_section:
                start_station = train.get('current_station')
                end_station = current_section.get('destination_station')
                if start_station in STATION_COORDS and end_station in STATION_COORDS:
                    start_lat, start_lon = STATION_COORDS[start_station]
                    end_lat, end_lon = STATION_COORDS[end_station]
                    fraction = min(1.0, train['distance_covered_in_section_km'] / current_section['distance_km'])
                    train['current_location'] = {
                        "lat": start_lat + (end_lat - start_lat) * fraction,
                        "lon": start_lon + (end_lon - start_lon) * fraction
                    }
            elif train['status'] == 'COMPLETED' and train.get('current_station') in STATION_COORDS:
                train['current_location'] = {
                    "lat": STATION_COORDS[train['current_station']][0],
                    "lon": STATION_COORDS[train['current_station']][1]
                }
                        
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
                    
                    # Track delay changes to trigger propagation events exactly once
                    latest_eta = train.get('latest_eta') or {}
                    old_delay = latest_eta.get('final_destination_delay_min', train['current_delay_min'])
                    new_delay = engine_output.get('final_destination_delay_min', 0)
                    if new_delay > old_delay:
                        delay_diff = new_delay - old_delay
                        sim_time_str = SIMULATION_STATE['current_time'].strftime("%H:%M:%S")
                        EVENT_TIMELINE.append({"time": sim_time_str, "event": f"Delay Propagation Detected: +{delay_diff}m to downstream network", "type": "WARNING"})
                        
                    train['latest_eta'] = engine_output
                except Exception as e:
                    logger.error(f"XGBoost Cascade Failure: {e}")
                    
        # Synchronous transmission of universal matrices
        tick_data = {
            "type": "SIMULATION_TICK",
            "time": SIMULATION_STATE['current_time'].strftime("%H:%M:%S"),
            "trains": ACTIVE_TRAINS,
            "network": GLOBAL_NETWORK_CONDITIONS,
            "sim_state": {
                "is_running": SIMULATION_STATE.get('is_running', False),
                "speed_multiplier": SIMULATION_STATE.get('speed_multiplier', 1),
                "timeline": EVENT_TIMELINE
            }
        }
        await manager.broadcast(json.dumps(tick_data))
