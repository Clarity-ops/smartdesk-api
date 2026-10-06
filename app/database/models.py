from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database.database import Base

class Ticket(Base):
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    
    # Категорія визначатиме стратегію (наприклад: "Security", "Hardware", "Access")
    category = Column(String, nullable=False, index=True)
    
    # Статуси: Open, In Progress, Closed
    status = Column(String, default="Open", index=True)
    
    # Статичний пріоритет від 1 (Low) до 4 (Critical)
    priority = Column(Integer, nullable=False)
    
    # Вектор для NLP. Дозволяємо бути порожнім на випадок збою генерації
    embedding = Column(JSON, nullable=True) 
    
    # Час створення (заповнюється автоматично)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Скільки годин дається на вирішення (SLA)
    sla_hours = Column(Integer, default=48)