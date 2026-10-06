from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class TicketCreateDTO(BaseModel):
    title: str = Field(..., min_length=5, max_length=100, example="Не працює монітор у кабінеті 204")
    description: str = Field(..., min_length=10, example="Екран блимає та вимикається під час роботи")
    category: str = Field(..., example="Hardware")  # Security, Hardware, Software
    priority: int = Field(..., ge=1, le=4, example=3)  # Від 1 (Low) до 4 (Critical)
    sla_hours: Optional[int] = Field(default=48, ge=1, example=24)

class TicketResponseDTO(BaseModel):
    id: int
    title: str
    category: str
    priority: int
    status: str
    created_at: datetime
    sla_hours: int
    dynamic_urgency: Optional[float] = None

    class Config:
        from_attributes = True

class TicketStatusUpdateDTO(BaseModel):
    status: str = Field(..., example="Closed")  # Open, In Progress, Closed

class SimilarTicketDTO(BaseModel):
    id: int
    title: str
    description: str
    similarity: float