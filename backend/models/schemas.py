from pydantic import BaseModel, Field
from typing import Optional

class SimulationEvent(BaseModel):
    train_id: str = Field(..., description="Unique train identifier")
    event_type: str = Field(..., description="e.g., congestion, speed restriction, operational halt, clear disruption")
    severity: float = Field(0.0, description="Severity multiplier (0.0 to 1.0)", ge=0.0, le=1.0)
    details: Optional[str] = None
