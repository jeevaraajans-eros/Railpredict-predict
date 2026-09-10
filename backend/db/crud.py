from sqlalchemy.orm import Session
from backend.db.models import TrainMovement, Route, Section, HistoricalSectionTime

def fetch_active_train_state(db: Session, train_id: str) -> dict:
    """Interrogates standard movement table querying latest positional snapshot."""
    state_rec = db.query(TrainMovement).filter(TrainMovement.train_id == train_id).order_by(TrainMovement.last_updated.desc()).first()
    if not state_rec:
        return {}
    return {
        'train_id': state_rec.train_id,
        'current_delay_min': state_rec.current_delay_min,
        'current_station': state_rec.current_station,
        'is_simulated_event': state_rec.is_simulated_event
    }

def fetch_remaining_route_for_engine(db: Session, train_id: str, current_station: str) -> list:
    """
    Returns an ordered list of route dictionaries precisely formatted for XGBoost Engine ingestion loop.
    Iterates linearly tracking section topography until detecting train, triggering downstream cascade buffering.
    """
    route_records = db.query(Route).filter(Route.train_id == train_id).order_by(Route.sequence_no).all()
    
    formatted_route = []
    capture_flag = False
    
    for rt in route_records:
        section = db.query(Section).filter(Section.section_id == rt.section_id).first()
        if not section:
            continue
            
        if section.origin_station == current_station:
            capture_flag = True  # Detected origin! Now map remaining linear segments
            
        if capture_flag:
            hist_time = db.query(HistoricalSectionTime).filter(
                HistoricalSectionTime.train_id == train_id,
                HistoricalSectionTime.section_id == section.section_id
            ).first()
            
            formatted_route.append({
                'section_id': section.section_id,
                'destination_station': section.destination_station,
                'distance_km': section.distance_km,
                'scheduled_section_time_min': rt.scheduled_section_time_min,
                'dwell_time_min': rt.dwell_time_min,
                'historical_section_avg_time': hist_time.historical_avg_time_min if hist_time else rt.scheduled_section_time_min
            })
            
    return formatted_route
