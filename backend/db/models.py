from sqlalchemy import Column, Integer, String, Float, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import relationship, declarative_base
from datetime import datetime

Base = declarative_base()

class Station(Base):
    __tablename__ = "stations"
    code = Column(String(10), primary_key=True)
    name = Column(String(100), nullable=False)
    lat = Column(Float, nullable=True)
    lon = Column(Float, nullable=True)

class Train(Base):
    __tablename__ = "trains"
    train_id = Column(String(20), primary_key=True)
    train_name = Column(String(100), nullable=False)
    priority_class = Column(Integer, default=3) # 1=High (Shatabdi), 2=Medium, 3=Low
    
    # Clear Identification of Prototype Mock Data
    is_synthetic_data = Column(Boolean, default=True) 

class Section(Base):
    """Normalized route geometry segments"""
    __tablename__ = "sections"
    section_id = Column(String(50), primary_key=True) # e.g. "NDLS-GZB"
    origin_station = Column(String(10), ForeignKey("stations.code"))
    destination_station = Column(String(10), ForeignKey("stations.code"))
    distance_km = Column(Float, nullable=False)

class Route(Base):
    """Timetable routing mapping a train structurally through contiguous block sections"""
    __tablename__ = "routes"
    id = Column(Integer, primary_key=True, autoincrement=True)
    train_id = Column(String(20), ForeignKey("trains.train_id"))
    section_id = Column(String(50), ForeignKey("sections.section_id"))
    sequence_no = Column(Integer, nullable=False)
    scheduled_section_time_min = Column(Integer, nullable=False)
    dwell_time_min = Column(Integer, default=5)

class TrainMovement(Base):
    """Dynamic Live state representation of the train including real-time accumulated deviation"""
    __tablename__ = "train_movements"
    id = Column(Integer, primary_key=True, autoincrement=True)
    train_id = Column(String(20), ForeignKey("trains.train_id"))
    current_station = Column(String(10), ForeignKey("stations.code"))
    current_delay_min = Column(Integer, default=0)
    last_updated = Column(DateTime, default=datetime.utcnow)
    
    is_simulated_event = Column(Boolean, default=True)

class HistoricalSectionTime(Base):
    """Stores the aggregated static ML baseline dependency structurally without requiring large raw file logs"""
    __tablename__ = "historical_section_times"
    id = Column(Integer, primary_key=True, autoincrement=True)
    train_id = Column(String(20), ForeignKey("trains.train_id"))
    section_id = Column(String(50), ForeignKey("sections.section_id"))
    historical_avg_time_min = Column(Integer, nullable=False)

class OperationalEvent(Base):
    """Event table for registering live constraints disrupting the mathematical model constraints"""
    __tablename__ = "operational_events"
    id = Column(Integer, primary_key=True, autoincrement=True)
    train_id = Column(String(20), ForeignKey("trains.train_id"))
    event_type = Column(String(50), nullable=False) # e.g. "Congestion", "Loco Failure"
    severity_multiplier = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    is_simulated = Column(Boolean, default=True)

class Prediction(Base):
    """Audit table logging outputted vectors from the ETA dynamic engine"""
    __tablename__ = "predictions"
    id = Column(Integer, primary_key=True, autoincrement=True)
    train_id = Column(String(20), ForeignKey("trains.train_id"))
    target_station = Column(String(10), ForeignKey("stations.code"))
    predicted_travel_time_min = Column(Integer)
    accumulated_delay_min = Column(Integer)
    predicted_arrival = Column(DateTime)
    predicted_departure = Column(DateTime)
    delay_risk = Column(String(20)) # "Low", "Medium", "High"
    created_at = Column(DateTime, default=datetime.utcnow)
