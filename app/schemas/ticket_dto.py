from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime

class TicketCreateDTO(BaseModel):
    title: str = Field(..., min_length=5, max_length=100, examples=["Не працює монітор у кабінеті 204"])
    description: str = Field(..., min_length=10, examples=["Екран блимає та вимикається під час роботи"])
    category: str = Field(..., examples=["Hardware"])  # Security, Hardware, Software
    priority: int = Field(..., ge=1, le=4, examples=[3])  # Від 1 (Low) до 4 (Critical)
    sla_hours: Optional[int] = Field(default=48, ge=1, examples=[24])

class TicketResponseDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    category: str
    priority: int
    status: str
    created_at: datetime
    sla_hours: int
    dynamic_urgency: Optional[float] = None

class TicketStatusUpdateDTO(BaseModel):
    status: str = Field(..., examples=["Closed"])  # Open, In Progress, Closed

class SimilarTicketDTO(BaseModel):
    id: int
    title: str
    description: str
    similarity: float