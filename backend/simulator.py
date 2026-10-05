import asyncio
import random
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
        
        # 1 real second = N simulation minutes
        advance_minutes = SIMULATION_STATE.get('speed_multiplier', 1)
        
        if SIMULATION_STATE.get('is_running', False):
            SIMULATION_STATE['current_time'] += timedelta(minutes=advance_minutes)
        
            # --- Dynamic ABS Proximity Sensor (Real-Time Micro Collision Avoidance) ---
            main_train = ACTIVE_TRAINS.get('12004')
            abs_collision_imminent = False
            
            if main_train and main_train.get('status') == 'EN_ROUTE':
                main_idx = next((i for i, s in enumerate(ROUTE_DATA['12004']) if s['section_id'] == main_train['current_section_id']), -1)
                main_progress = main_train.get('distance_covered_in_section_km', 0.0)
                
                for other_id, other_train in ACTIVE_TRAINS.items():
                    if other_id != '12004' and other_train.get('status') == 'EN_ROUTE':
                        other_idx = next((i for i, s in enumerate(ROUTE_DATA[other_id]) if s['section_id'] == other_train['current_section_id']), -1)
                        if main_idx == other_idx and main_idx != -1:
                            other_progress = other_train.get('distance_covered_in_section_km', 0.0)
                            distance_gap = other_progress - main_progress
                            if 0 < distance_gap <= 5.0:  # 5km strict safety buffer block
                                abs_collision_imminent = True
                                break
                                
            # Force speed override based on structural ABS
            if abs_collision_imminent:
                GLOBAL_NETWORK_CONDITIONS['target_speed_kmph'] = 20.0
                if GLOBAL_NETWORK_CONDITIONS.get('operational_event') != 'ABS Buffer Lock':
                    GLOBAL_NETWORK_CONDITIONS['operational_event'] = 'ABS Buffer Lock'
                    EVENT_TIMELINE.append({"time": SIMULATION_STATE['current_time'].strftime("%H:%M:%S"), "event": "Spatial Prediction Engine: Dynamic Obstruction (<5km). AI Block Signaling enforcing bounds.", "type": "WARNING"})
            elif GLOBAL_NETWORK_CONDITIONS.get('operational_event') == 'ABS Buffer Lock':
                GLOBAL_NETWORK_CONDITIONS['operational_event'] = 'Normal'
                GLOBAL_NETWORK_CONDITIONS['target_speed_kmph'] = 80.0

            # --- Real-Time Speed Inertia & Fluctuations ---
            target = GLOBAL_NETWORK_CONDITIONS.get('target_speed_kmph', 80.0)
            current = GLOBAL_NETWORK_CONDITIONS.get('average_speed_kmph', 80.0)
            is_halted = GLOBAL_NETWORK_CONDITIONS.get('operational_event') not in ['Normal', 'ABS Buffer Lock']
            
            if is_halted:
                target = 0.0
            
            max_change = 10.0 * advance_minutes  # 10 km/h acceleration per minute
            
            if abs(target - current) <= max_change:
                current = target
            elif current < target:
                current += max_change
            elif current > target:
                current -= max_change
                
            if current == target and target > 0 and not is_halted:
                current += random.uniform(-1.5, 1.5)
            
            if current < target - 1.0:
                trend = '<'
            elif current > target + 1.0:
                trend = '>'
            else:
                trend = '='
                
            GLOBAL_NETWORK_CONDITIONS['average_speed_kmph'] = max(0.0, current)
            GLOBAL_NETWORK_CONDITIONS['speed_trend'] = trend
            # -----------------------------------------------
            
            for train_id, train in ACTIVE_TRAINS.items():
                if train.get('status') not in ['EN_ROUTE', 'SIDING']:
                    continue
                    
                route = ROUTE_DATA.get(train_id, [])
                if train_id != '12004':
                    current_speed = 20.0 # Restrict ghost dummy variables structurally to guarantee catch-up mapping
                else:
                    current_speed = GLOBAL_NETWORK_CONDITIONS.get('average_speed_kmph', 80.0)
                
                if GLOBAL_NETWORK_CONDITIONS.get('operational_event') not in ['Normal', 'ABS Buffer Lock'] and train_id == '12004':
                    distance_advanced = 0.0
                    train['current_delay_min'] += advance_minutes
                else:
                    distance_advanced = (current_speed / 60.0) * advance_minutes
                
                train['distance_covered_in_section_km'] += distance_advanced
                
                # --- AUTO-SHUNT GHOST TRAINS FOR DEMONSTRATION CLEARS ---
                if train_id != '12004':
                    train_dist = train.get('distance_covered_in_section_km', 0.0)
                    main_t = ACTIVE_TRAINS.get('12004')
                    
                    is_same_section = main_t and main_t.get('current_section_id') == train.get('current_section_id')
                    main_t_dist = main_t.get('distance_covered_in_section_km', -999.0) if is_same_section else -999.0
                    
                    if train_dist >= 35.0 and train.get('status') == 'EN_ROUTE':
                        # Only wait if the Blue train is actually behind us on the exact same track
                        if is_same_section and main_t_dist < 35.0:
                            train['status'] = 'SIDING'
                            EVENT_TIMELINE.append({"time": SIMULATION_STATE['current_time'].strftime("%H:%M:%S"), "event": f"AI Vector Update: Train {train_id} dynamically shunted. Priority trajectory cleared.", "type": "INFO"})

                    if train.get('status') == 'SIDING':
                        # Sit perfectly still on the map
                        train['distance_covered_in_section_km'] = 35.0 
                        
                        # Once priority blue train safely passes + 1km buffer, OR if the blue train left the section completely
                        if (is_same_section and main_t_dist > 36.0) or (main_t and main_t.get('status') == 'EN_ROUTE' and not is_same_section):
                            train['status'] = 'EN_ROUTE'
                            EVENT_TIMELINE.append({"time": SIMULATION_STATE['current_time'].strftime("%H:%M:%S"), "event": f"Geometric Overtake Verified. Predictive matrix dynamically unlocking for {train_id}.", "type": "INFO"})

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
                        train['current_location'] = [
                            start_lat + (end_lat - start_lat) * fraction,
                            start_lon + (end_lon - start_lon) * fraction
                        ]
                elif train['status'] == 'COMPLETED' and train.get('current_station') in STATION_COORDS:
                    train['current_location'] = STATION_COORDS[train['current_station']]
                            
                # Execute native ETA generation dynamically based on topological progression
                if train['current_section_id']:
                    current_idx = next((i for i, s in enumerate(route) if s['section_id'] == train['current_section_id']), 0)
                    remaining_route = route[current_idx:]
                    try:
                        engine_output = run_dynamic_eta_engine(
                            current_time=SIMULATION_STATE['current_time'],
                            train_state=train,
                            remaining_route=remaining_route,
                            network_conditions=GLOBAL_NETWORK_CONDITIONS,
                            active_trains=ACTIVE_TRAINS
                        )
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
